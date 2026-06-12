"""Supabase Storage helpers for resume files."""

from app.config import settings


def _client():
    from supabase import create_client

    return create_client(settings.supabase_url, settings.supabase_service_key)


def upload_resume(filename: str, file_bytes: bytes, content_type: str) -> str:
    """Uploads the file to Supabase Storage and returns the storage path."""
    path = f"resumes/{filename}"
    _client().storage.from_(settings.supabase_bucket).upload(
        path, file_bytes, {"content-type": content_type, "x-upsert": "true"}
    )
    return path


def get_resume_url(storage_path: str) -> str:
    return _client().storage.from_(settings.supabase_bucket).get_public_url(storage_path)
