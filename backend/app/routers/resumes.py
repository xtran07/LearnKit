from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Resume, Topic, TopicSource
from app.schemas import ResumeOut, TopicOut
from app.services import resume_parser, storage

router = APIRouter(prefix="/resumes", tags=["resumes"])


@router.post("/upload", response_model=ResumeOut)
async def upload_resume(file: UploadFile, db: AsyncSession = Depends(get_db)):
    if not file.filename.lower().endswith((".pdf", ".txt", ".md")):
        raise HTTPException(status_code=400, detail="Only PDF, TXT, or MD files are supported")

    file_bytes = await file.read()
    raw_text = resume_parser.extract_text(file_bytes, file.filename)
    if not raw_text.strip():
        raise HTTPException(status_code=400, detail="Could not extract any text from the file")

    storage_path = storage.upload_resume(file.filename, file_bytes, file.content_type or "application/octet-stream")

    resume = Resume(filename=file.filename, storage_path=storage_path, raw_text=raw_text)
    db.add(resume)
    await db.commit()
    await db.refresh(resume)
    return resume


@router.get("", response_model=list[ResumeOut])
async def list_resumes(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Resume).order_by(Resume.created_at.desc()))
    return result.scalars().all()


@router.post("/{resume_id}/suggest-topics", response_model=list[TopicOut])
async def suggest_topics(resume_id: int, provider: str = "gemini", db: AsyncSession = Depends(get_db)):
    resume = await db.get(Resume, resume_id)
    if resume is None:
        raise HTTPException(status_code=404, detail="Resume not found")

    topic_names = resume_parser.suggest_topics(resume.raw_text, provider)

    existing = await db.execute(select(Topic.name).where(Topic.resume_id == resume_id))
    existing_names = {name.lower() for name in existing.scalars().all()}

    created = []
    for name in topic_names:
        if name.lower() in existing_names:
            continue
        topic = Topic(resume_id=resume_id, name=name, source=TopicSource.resume)
        db.add(topic)
        created.append(topic)
        existing_names.add(name.lower())

    await db.commit()
    for topic in created:
        await db.refresh(topic)
    return created
