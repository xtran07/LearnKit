import asyncio
from datetime import datetime, timedelta, timezone

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user_id
from app.database import get_db
from app.models import ApplicationStatus, JobApplication, JobLead, Resume
from app.schemas import ApplicationOut, JobLeadOut, JobLeadSearchRequest
from app.services import llm_service

router = APIRouter(prefix="/job-leads", tags=["job-leads"])

_VERIFY_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; LearnKit/1.0)"}


async def _link_is_reachable(url: str) -> bool:
    """Return True if the URL responds with anything other than 404/410."""
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=6.0) as client:
            r = await client.head(url, headers=_VERIFY_HEADERS)
            if r.status_code == 405:
                r = await client.get(url, headers=_VERIFY_HEADERS)
            return r.status_code not in (404, 410)
    except Exception:
        return False

LEAD_RETENTION_DAYS = 14
MAX_UNREVIEWED_LEADS = 50


async def _get_owned_lead(lead_id: int, user_id: str, db: AsyncSession) -> JobLead:
    lead = await db.get(JobLead, lead_id)
    if lead is None or lead.user_id != user_id:
        raise HTTPException(status_code=404, detail="Job lead not found")
    return lead


async def _cleanup_leads(user_id: str, db: AsyncSession) -> None:
    """Drops leads older than the retention window and trims to the unreviewed cap."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=LEAD_RETENTION_DAYS)
    await db.execute(delete(JobLead).where(JobLead.user_id == user_id, JobLead.created_at < cutoff))

    result = await db.execute(
        select(JobLead.id).where(JobLead.user_id == user_id).order_by(JobLead.created_at.desc())
    )
    ids = result.scalars().all()
    stale_ids = ids[MAX_UNREVIEWED_LEADS:]
    if stale_ids:
        await db.execute(delete(JobLead).where(JobLead.id.in_(stale_ids)))


@router.get("", response_model=list[JobLeadOut])
async def list_job_leads(db: AsyncSession = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    await _cleanup_leads(user_id, db)
    await db.commit()
    result = await db.execute(
        select(JobLead).where(JobLead.user_id == user_id).order_by(JobLead.created_at.desc())
    )
    return result.scalars().all()


@router.post("/search", response_model=list[JobLeadOut])
async def search_job_leads(
    payload: JobLeadSearchRequest,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    resume_result = await db.execute(
        select(Resume).where(Resume.user_id == user_id).order_by(Resume.created_at.desc()).limit(1)
    )
    resume = resume_result.scalars().first()
    resume_context = resume.raw_text if resume else ""

    try:
        results = llm_service.search_job_leads(payload.query, payload.location, resume_context)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=llm_service.friendly_llm_error(exc, "job search")) from exc

    await _cleanup_leads(user_id, db)

    existing_result = await db.execute(select(JobLead.link).where(JobLead.user_id == user_id))
    existing_links = set(existing_result.scalars().all())

    # Filter to candidates not already saved
    candidates = [item for item in results if item.get("link") and item["link"] not in existing_links]

    # Verify all links concurrently (drop dead ones)
    reachable_flags = await asyncio.gather(*[_link_is_reachable(item["link"]) for item in candidates])

    created = []
    for item, reachable in zip(candidates, reachable_flags):
        if not reachable:
            continue
        link = item["link"]
        existing_links.add(link)
        lead = JobLead(
            user_id=user_id,
            title=item.get("title") or "Untitled posting",
            company=item.get("company"),
            role=item.get("role"),
            link=link,
            source=item.get("source"),
            snippet=item.get("snippet"),
        )
        db.add(lead)
        created.append(lead)

    await db.commit()
    for lead in created:
        await db.refresh(lead)
    return created


@router.post("/{lead_id}/add", response_model=ApplicationOut)
async def add_job_lead(
    lead_id: int, db: AsyncSession = Depends(get_db), user_id: str = Depends(get_current_user_id)
):
    lead = await _get_owned_lead(lead_id, user_id, db)

    application = JobApplication(
        user_id=user_id,
        name=lead.title,
        company=lead.company or "",
        role=lead.role or "",
        status=ApplicationStatus.new,
        source=lead.source,
        job_post_link=lead.link,
    )
    db.add(application)
    await db.delete(lead)
    await db.commit()
    await db.refresh(application)
    return application


@router.delete("/{lead_id}", status_code=204)
async def dismiss_job_lead(
    lead_id: int, db: AsyncSession = Depends(get_db), user_id: str = Depends(get_current_user_id)
):
    lead = await _get_owned_lead(lead_id, user_id, db)
    await db.delete(lead)
    await db.commit()
