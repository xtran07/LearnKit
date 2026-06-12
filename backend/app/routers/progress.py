from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Attempt, Question, Topic
from app.schemas import AttemptCreate, AttemptOut, TopicProgress
from app.services import llm_service

router = APIRouter(tags=["progress"])


@router.post("/attempts", response_model=AttemptOut)
async def submit_attempt(payload: AttemptCreate, db: AsyncSession = Depends(get_db)):
    question = await db.get(Question, payload.question_id)
    if question is None:
        raise HTTPException(status_code=404, detail="Question not found")

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
async def list_attempts(question_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Attempt).where(Attempt.question_id == question_id).order_by(Attempt.created_at.desc())
    )
    return result.scalars().all()


@router.get("/progress", response_model=list[TopicProgress])
async def topic_progress(db: AsyncSession = Depends(get_db)):
    topics = (await db.execute(select(Topic))).scalars().all()

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
