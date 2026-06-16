from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user_id
from app.database import get_db
from app.models import Attempt, Question, Topic
from app.schemas import AttemptCreate, AttemptOut, TopicProgress
from app.services import llm_service

router = APIRouter(tags=["progress"])


async def _get_owned_question(question_id: int, user_id: str, db: AsyncSession) -> Question:
    question = await db.get(Question, question_id)
    if question is None:
        raise HTTPException(status_code=404, detail="Question not found")
    topic = await db.get(Topic, question.topic_id)
    if topic is None or topic.user_id != user_id:
        raise HTTPException(status_code=404, detail="Question not found")
    return question


@router.post("/attempts", response_model=AttemptOut)
async def submit_attempt(
    payload: AttemptCreate, db: AsyncSession = Depends(get_db), user_id: str = Depends(get_current_user_id)
):
    question = await _get_owned_question(payload.question_id, user_id, db)

    try:
        result = llm_service.grade_answer(
            question.question_text, question.ideal_answer, payload.user_answer, payload.provider
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"LLM grading failed: {exc}") from exc

    attempt = Attempt(
        question_id=question.id,
        user_answer=payload.user_answer,
        score=result["score"],
        feedback=result["feedback"],
    )
    db.add(attempt)
    await db.commit()
    await db.refresh(attempt)
    return attempt


@router.get("/attempts", response_model=list[AttemptOut])
async def list_attempts(
    question_id: int | None = None,
    topic_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    if question_id is not None:
        await _get_owned_question(question_id, user_id, db)
        result = await db.execute(
            select(Attempt).where(Attempt.question_id == question_id).order_by(Attempt.created_at.desc())
        )
        return result.scalars().all()

    if topic_id is not None:
        topic = await db.get(Topic, topic_id)
        if topic is None or topic.user_id != user_id:
            raise HTTPException(status_code=404, detail="Topic not found")
        question_ids = (
            await db.execute(select(Question.id).where(Question.topic_id == topic_id))
        ).scalars().all()
        if not question_ids:
            return []
        # Return the latest attempt for each question
        subq = (
            select(Attempt.question_id, func.max(Attempt.created_at).label("max_ts"))
            .where(Attempt.question_id.in_(question_ids))
            .group_by(Attempt.question_id)
            .subquery()
        )
        result = await db.execute(
            select(Attempt).join(
                subq,
                (Attempt.question_id == subq.c.question_id)
                & (Attempt.created_at == subq.c.max_ts),
            )
        )
        return result.scalars().all()

    raise HTTPException(status_code=400, detail="Provide question_id or topic_id")


@router.get("/progress", response_model=list[TopicProgress])
async def topic_progress(db: AsyncSession = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    topics = (await db.execute(select(Topic).where(Topic.user_id == user_id))).scalars().all()

    summaries = []
    for topic in topics:
        questions = (await db.execute(select(Question.id).where(Question.topic_id == topic.id))).scalars().all()
        total_questions = len(questions)

        attempted_questions = 0
        average_score = None
        if questions:
            stats = await db.execute(
                select(func.count(func.distinct(Attempt.question_id)), func.avg(Attempt.score))
                .where(Attempt.question_id.in_(questions))
            )
            attempted_questions, avg_score = stats.one()
            average_score = float(avg_score) if avg_score is not None else None

        summaries.append(
            TopicProgress(
                topic_id=topic.id,
                topic_name=topic.name,
                status=topic.status,
                total_questions=total_questions,
                attempted_questions=attempted_questions or 0,
                average_score=average_score,
            )
        )

    return summaries
