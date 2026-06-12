from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Topic, TopicSource, TopicStatus
from app.schemas import TopicCreate, TopicOut, TopicUpdate

router = APIRouter(prefix="/topics", tags=["topics"])


@router.get("", response_model=list[TopicOut])
async def list_topics(status: TopicStatus | None = None, db: AsyncSession = Depends(get_db)):
    query = select(Topic).order_by(Topic.created_at.desc())
    if status is not None:
        query = query.where(Topic.status == status)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("", response_model=TopicOut)
async def create_topic(payload: TopicCreate, db: AsyncSession = Depends(get_db)):
    topic = Topic(name=payload.name, source=TopicSource.manual)
    db.add(topic)
    await db.commit()
    await db.refresh(topic)
    return topic


@router.patch("/{topic_id}", response_model=TopicOut)
async def update_topic(topic_id: int, payload: TopicUpdate, db: AsyncSession = Depends(get_db)):
    topic = await db.get(Topic, topic_id)
    if topic is None:
        raise HTTPException(status_code=404, detail="Topic not found")

    if payload.name is not None:
        topic.name = payload.name
    if payload.status is not None:
        topic.status = payload.status

    await db.commit()
    await db.refresh(topic)
    return topic


@router.delete("/{topic_id}", status_code=204)
async def delete_topic(topic_id: int, db: AsyncSession = Depends(get_db)):
    topic = await db.get(Topic, topic_id)
    if topic is None:
        raise HTTPException(status_code=404, detail="Topic not found")
    await db.delete(topic)
    await db.commit()
