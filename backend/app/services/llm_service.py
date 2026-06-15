"""Unified interface for free-tier LLM providers (Gemini, Groq).

Both providers are used for:
- Generating interview-style questions (with an ideal answer) for a topic
- Grading a user's answer against the ideal answer
- Building copy-paste prompts the user can run in other chatbots
"""

import json

from app.config import settings

GEMINI_MODEL = "gemini-2.5-flash"
GROQ_MODEL = "llama-3.3-70b-versatile"


def _question_gen_prompt(topic_name: str, resume_context: str, count: int, difficulty: str) -> str:
    return (
        f"You are an interview coach. Based on the candidate's resume excerpt below, "
        f"generate {count} {difficulty}-difficulty interview questions about the topic "
        f"'{topic_name}'.\n\n"
        f"Resume excerpt:\n{resume_context or '(no resume context provided)'}\n\n"
        "Respond ONLY with a JSON array, no markdown fences, where each item has the shape:\n"
        '{"question": "...", "ideal_answer": "..."}'
    )


def _grading_prompt(question: str, ideal_answer: str | None, user_answer: str) -> str:
    return (
        "You are grading a candidate's interview answer.\n\n"
        f"Question: {question}\n"
        f"Ideal answer (for reference): {ideal_answer or '(not provided, use your own judgement)'}\n"
        f"Candidate's answer: {user_answer}\n\n"
        "Score the candidate's answer from 0 to 100 and give brief, constructive feedback "
        "(2-3 sentences). Respond ONLY with JSON, no markdown fences, in the shape:\n"
        '{"score": <int 0-100>, "feedback": "..."}'
    )


def _strip_code_fence(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text
        if text.endswith("```"):
            text = text[: -3]
        if text.startswith("json"):
            text = text[4:]
    return text.strip()


def _call_gemini(prompt: str) -> str:
    from google import genai

    client = genai.Client(api_key=settings.gemini_api_key)
    response = client.models.generate_content(model=GEMINI_MODEL, contents=prompt)
    return response.text


def _call_groq(prompt: str) -> str:
    from groq import Groq

    client = Groq(api_key=settings.groq_api_key)
    completion = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
    )
    return completion.choices[0].message.content


def _call_provider(prompt: str, provider: str) -> str:
    if provider == "groq":
        return _call_groq(prompt)
    return _call_gemini(prompt)


def generate_questions(
    topic_name: str, resume_context: str, count: int, difficulty: str, provider: str = "gemini"
) -> list[dict]:
    raw = _call_provider(_question_gen_prompt(topic_name, resume_context, count, difficulty), provider)
    data = json.loads(_strip_code_fence(raw))
    return data


def grade_answer(question: str, ideal_answer: str | None, user_answer: str, provider: str = "gemini") -> dict:
    raw = _call_provider(_grading_prompt(question, ideal_answer, user_answer), provider)
    data = json.loads(_strip_code_fence(raw))
    return {"score": int(data["score"]), "feedback": data.get("feedback", "")}


def build_external_prompt(topic_name: str, resume_context: str, difficulty: str, count: int = 5) -> str:
    """A prompt the user can paste into any chatbot (ChatGPT, Claude, etc.) to source questions."""
    return (
        f"I'm preparing for a technical interview. Based on the resume excerpt below, "
        f"give me {count} {difficulty}-difficulty interview questions about '{topic_name}', "
        "each with a concise ideal answer.\n\n"
        f"Resume excerpt:\n{resume_context or '(paste your resume excerpt here)'}"
    )


def _job_resolve_prompt(page_text: str) -> str:
    return (
        "Extract job posting details from the page text below. Respond ONLY with JSON, "
        "no markdown fences, in the shape:\n"
        '{"company": "...", "role": "...", "name": "...", "source": "..."}\n'
        "Where 'name' is a short label like 'Company - Role', and 'source' is the job "
        "portal/site name if identifiable (e.g. LinkedIn, Indeed), else null. "
        "Use null for any field you cannot determine.\n\n"
        f"Page text:\n{page_text[:6000]}"
    )


def resolve_job_posting(page_text: str, provider: str = "gemini") -> dict:
    raw = _call_provider(_job_resolve_prompt(page_text), provider)
    return json.loads(_strip_code_fence(raw))


def _app_question_gen_prompt(company: str, role: str, resume_context: str, count: int, difficulty: str) -> str:
    return (
        f"You are an interview coach. Generate {count} {difficulty}-difficulty mock interview "
        f"questions for a candidate interviewing for the role '{role}' at '{company}'. "
        "Tailor questions to this role/company, drawing on the candidate's resume excerpt below "
        "where relevant.\n\n"
        f"Resume excerpt:\n{resume_context or '(no resume context provided)'}\n\n"
        "Respond ONLY with a JSON array, no markdown fences, where each item has the shape:\n"
        '{"question": "...", "ideal_answer": "..."}'
    )


def generate_application_questions(
    company: str, role: str, resume_context: str, count: int, difficulty: str, provider: str = "gemini"
) -> list[dict]:
    raw = _call_provider(_app_question_gen_prompt(company, role, resume_context, count, difficulty), provider)
    return json.loads(_strip_code_fence(raw))
