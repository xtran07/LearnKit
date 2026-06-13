import jwt
from fastapi import Header, HTTPException

from app.config import settings


async def get_current_user_id(authorization: str | None = Header(default=None)) -> str:
    """Verifies the Supabase-issued JWT sent in the Authorization header and returns the user id."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    token = authorization.removeprefix("Bearer ")
    try:
        payload = jwt.decode(
            token,
            settings.supabase_jwt_secret,
            algorithms=["HS256"],
            audience="authenticated",
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=401, detail="Invalid or expired token") from exc

    return payload["sub"]
