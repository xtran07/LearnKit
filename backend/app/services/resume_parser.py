"""Resume text extraction and topic suggestion."""

import io
import json

from app.services.llm_service import _call_provider, _extract_json


def extract_text(file_bytes: bytes, filename: str) -> str:
    if filename.lower().endswith(".pdf"):
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(file_bytes))
        return "\n".join(page.extract_text() or "" for page in reader.pages)

    # Fallback: treat as plain text (.txt, .md)
    return file_bytes.decode("utf-8", errors="ignore")


def suggest_topics(resume_text: str, provider: str = "gemini") -> list[str]:
    """Use an LLM to suggest study topics based on resume content."""
    prompt = (
        "Based on the resume text below, list the technical topics, skills, and tools the "
        "candidate should be ready to discuss in an interview (e.g. languages, frameworks, "
        "databases, cloud services, concepts). Keep each topic short (1-4 words). "
        "Respond ONLY with a JSON array of strings, no markdown fences, no duplicates, "
        "max 20 topics.\n\n"
        f"Resume text:\n{resume_text[:8000]}"
    )

    raw = _call_provider(prompt, provider)
    return json.loads(_extract_json(raw))
