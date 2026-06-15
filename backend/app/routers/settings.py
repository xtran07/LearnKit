from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user_id
from app.database import get_db
from app.models import UserSettings
from app.schemas import UserSettingsOut, UserSettingsUpdate

router = APIRouter(prefix="/settings", tags=["settings"])


async def _get_or_create_settings(user_id: str, db: AsyncSession) -> UserSettings:
    result = await db.execute(select(UserSettings).where(UserSettings.user_id == user_id))
    user_settings = result.scalars().first()
    if user_settings is None:
        user_settings = UserSettings(user_id=user_id)
        db.add(user_settings)
        await db.commit()
        await db.refresh(user_settings)
    return user_settings


@router.get("", response_model=UserSettingsOut)
async def get_settings(db: AsyncSession = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    return await _get_or_create_settings(user_id, db)


@router.patch("", response_model=UserSettingsOut)
async def update_settings(
    payload: UserSettingsUpdate,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    user_settings = await _get_or_create_settings(user_id, db)
    user_settings.preferred_provider = payload.preferred_provider
    await db.commit()
    await db.refresh(user_settings)
    return user_settings
