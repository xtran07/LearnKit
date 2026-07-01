from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user_id
from app.database import get_db
from app.models import Question, QuestionSource, Resume, Topic
from app.schemas import (
    ExternalPromptResponse,
    QuestionCreateManual,
    QuestionGenerateRequest,
    QuestionOut,
)
from app.services import llm_service

router = APIRouter(prefix="/questions", tags=["questions"])


async def _topic_resume_context(topic: Topic, db: AsyncSession) -> str:
    if topic.resume_id is None:
        return ""
    resume = await db.get(Resume, topic.resume_id)
    return resume.raw_text if resume else ""


async def _get_owned_topic(topic_id: int, user_id: str, db: AsyncSession) -> Topic:
    topic = await db.get(Topic, topic_id)
    if topic is None or topic.user_id != user_id:
        raise HTTPException(status_code=404, detail="Topic not found")
    return topic


@router.get("", response_model=list[QuestionOut])
async def list_questions(
    topic_id: int, db: AsyncSession = Depends(get_db), user_id: str = Depends(get_current_user_id)
):
    await _get_owned_topic(topic_id, user_id, db)
    result = await db.execute(select(Question).where(Question.topic_id == topic_id).order_by(Question.created_at.desc()))
    return result.scalars().all()


@router.post("/generate", response_model=list[QuestionOut])
async def generate_questions(
    payload: QuestionGenerateRequest, db: AsyncSession = Depends(get_db), user_id: str = Depends(get_current_user_id)
):
    topic = await _get_owned_topic(payload.topic_id, user_id, db)

    resume_context = await _topic_resume_context(topic, db)

    try:
        generated = llm_service.generate_questions(
            topic.name, resume_context, payload.count, payload.difficulty.value, payload.provider
        )
    except Exception as exc:
        detail = llm_service.friendly_llm_error(exc)
        raise HTTPException(status_code=502, detail=detail) from exc

    source = QuestionSource(llm_service.question_source_for_provider(payload.provider))

    created = []
    for item in generated:
        question = Question(
            topic_id=topic.id,
            question_text=item["question"],
            ideal_answer=item.get("ideal_answer"),
            difficulty=payload.difficulty,
            source=source,
        )
        db.add(question)
        created.append(question)

    await db.commit()
    for question in created:
        await db.refresh(question)
    return created


@router.post("/manual", response_model=QuestionOut)
async def create_question_manual(
    payload: QuestionCreateManual, db: AsyncSession = Depends(get_db), user_id: str = Depends(get_current_user_id)
):
    await _get_owned_topic(payload.topic_id, user_id, db)

    question = Question(
        topic_id=payload.topic_id,
        question_text=payload.question_text,
        ideal_answer=payload.ideal_answer,
        difficulty=payload.difficulty,
        source=QuestionSource.manual,
    )
    db.add(question)
    await db.commit()
    await db.refresh(question)
    return question


@router.delete("/{question_id}", status_code=204)
async def delete_question(
    question_id: int, db: AsyncSession = Depends(get_db), user_id: str = Depends(get_current_user_id)
):
    question = await db.get(Question, question_id)
    if question is None:
        raise HTTPException(status_code=404, detail="Question not found")
    await _get_owned_topic(question.topic_id, user_id, db)
    await db.delete(question)
    await db.commit()


@router.get("/external-prompt", response_model=ExternalPromptResponse)
async def external_prompt(
    topic_id: int,
    difficulty: str = "medium",
    count: int = 5,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    topic = await _get_owned_topic(topic_id, user_id, db)

    resume_context = await _topic_resume_context(topic, db)
    prompt = llm_service.build_external_prompt(topic.name, resume_context, difficulty, count)
    return ExternalPromptResponse(prompt=prompt)
