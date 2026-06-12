"""Resume text extraction and topic suggestion."""

import io
import json

from app.services.llm_service import GEMINI_MODEL, _strip_code_fence


def extract_text(file_bytes: bytes, filename: str) -> str:
    if filename.lower().endswith(".pdf"):
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(file_bytes))
        return "\n".join(page.extract_text() or "" for page in reader.pages)

    # Fallback: treat as plain text (.txt, .md)
    return file_bytes.decode("utf-8", errors="ignore")


def suggest_topics(resume_text: str, provider: str = "gemini") -> list[str]:
    """Use an LLM to suggest study topics based on resume content."""
    from app.config import settings

    prompt = (
        "Based on the resume text below, list the technical topics, skills, and tools the "
        "candidate should be ready to discuss in an interview (e.g. languages, frameworks, "
        "databases, cloud services, concepts). Keep each topic short (1-4 words). "
        "Respond ONLY with a JSON array of strings, no markdown fences, no duplicates, "
        "max 20 topics.\n\n"
        f"Resume text:\n{resume_text[:8000]}"
    )

    if provider == "groq":
        from groq import Groq

        client = Groq(api_key=settings.groq_api_key)
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
        )
        raw = completion.choices[0].message.content
    else:
        from google import genai

        client = genai.Client(api_key=settings.gemini_api_key)
        response = client.models.generate_content(model=GEMINI_MODEL, contents=prompt)
        raw = response.text

    return json.loads(_strip_code_fence(raw))
