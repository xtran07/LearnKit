import re

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user_id
from app.database import get_db
from app.models import ApplicationQuestion, ApplicationStatus, JobApplication, QuestionSource, Resume
from app.schemas import (
    ApplicationCreate,
    ApplicationOut,
    ApplicationResolveRequest,
    ApplicationResolveResult,
    ApplicationUpdate,
    AppQuestionGenerateRequest,
    AppQuestionOut,
)
from app.services import llm_service

router = APIRouter(prefix="/applications", tags=["applications"])

_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def _strip_html(html: str) -> str:
    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


async def _get_owned_application(application_id: int, user_id: str, db: AsyncSession) -> JobApplication:
    application = await db.get(JobApplication, application_id)
    if application is None or application.user_id != user_id:
        raise HTTPException(status_code=404, detail="Application not found")
    return application


@router.get("", response_model=list[ApplicationOut])
async def list_applications(
    status: ApplicationStatus | None = None,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    query = select(JobApplication).where(JobApplication.user_id == user_id).order_by(JobApplication.created_at.desc())
    if status is not None:
        query = query.where(JobApplication.status == status)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("", response_model=ApplicationOut)
async def create_application(
    payload: ApplicationCreate, db: AsyncSession = Depends(get_db), user_id: str = Depends(get_current_user_id)
):
    application = JobApplication(user_id=user_id, **payload.model_dump())
    db.add(application)
    await db.commit()
    await db.refresh(application)
    return application


@router.patch("/{application_id}", response_model=ApplicationOut)
async def update_application(
    application_id: int,
    payload: ApplicationUpdate,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    application = await _get_owned_application(application_id, user_id, db)

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(application, field, value)

    await db.commit()
    await db.refresh(application)
    return application


@router.delete("/{application_id}", status_code=204)
async def delete_application(
    application_id: int, db: AsyncSession = Depends(get_db), user_id: str = Depends(get_current_user_id)
):
    application = await _get_owned_application(application_id, user_id, db)
    await db.delete(application)
    await db.commit()


@router.post("/resolve", response_model=ApplicationResolveResult)
async def resolve_application(
    payload: ApplicationResolveRequest, user_id: str = Depends(get_current_user_id)
):
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=10.0) as client:
            response = await client.get(payload.url, headers={"User-Agent": _USER_AGENT})
            response.raise_for_status()
        page_text = _strip_html(response.text)
        data = llm_service.resolve_job_posting(page_text)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Could not resolve job posting: {exc}") from exc

    return ApplicationResolveResult(**data)


@router.get("/{application_id}/questions", response_model=list[AppQuestionOut])
async def list_application_questions(
    application_id: int, db: AsyncSession = Depends(get_db), user_id: str = Depends(get_current_user_id)
):
    await _get_owned_application(application_id, user_id, db)
    result = await db.execute(
        select(ApplicationQuestion)
        .where(ApplicationQuestion.application_id == application_id)
        .order_by(ApplicationQuestion.created_at.desc())
    )
    return result.scalars().all()


@router.post("/{application_id}/questions/generate", response_model=list[AppQuestionOut])
async def generate_application_questions(
    application_id: int,
    payload: AppQuestionGenerateRequest,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    application = await _get_owned_application(application_id, user_id, db)

    resume_result = await db.execute(
        select(Resume).where(Resume.user_id == user_id).order_by(Resume.created_at.desc()).limit(1)
    )
    resume = resume_result.scalars().first()
    resume_context = resume.raw_text if resume else ""

    try:
        generated = llm_service.generate_application_questions(
            application.company, application.role, resume_context, payload.count, payload.difficulty.value, payload.provider
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"LLM generation failed: {exc}") from exc

    source = QuestionSource.groq if payload.provider == "groq" else QuestionSource.gemini

    created = []
    for item in generated:
        question = ApplicationQuestion(
            application_id=application.id,
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


@router.delete("/questions/{question_id}", status_code=204)
async def delete_application_question(
    question_id: int, db: AsyncSession = Depends(get_db), user_id: str = Depends(get_current_user_id)
):
    question = await db.get(ApplicationQuestion, question_id)
    if question is None:
        raise HTTPException(status_code=404, detail="Question not found")
    await _get_owned_application(question.application_id, user_id, db)
    await db.delete(question)
    await db.commit()
