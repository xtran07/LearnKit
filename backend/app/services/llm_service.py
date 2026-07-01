"""Unified interface for free-tier LLM providers (Gemini, Groq, OpenRouter).

Both providers are used for:
- Generating interview-style questions (with an ideal answer) for a topic
- Grading a user's answer against the ideal answer
- Building copy-paste prompts the user can run in other chatbots
"""

import json

import httpx

from app.config import settings

GEMINI_MODEL = "gemini-2.5-flash"
GROQ_MODEL = "llama-3.3-70b-versatile"

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Curated free-tier models available on OpenRouter, keyed by the "provider" value
# sent from the frontend.
OPENROUTER_MODELS = {
    "openrouter-llama": "meta-llama/llama-3.3-70b-instruct:free",
    "openrouter-gemma": "google/gemma-4-31b-it:free",
    "openrouter-gpt": "openai/gpt-oss-120b:free",
    "openrouter-nex": "nexaai/nex-n2-pro:free",
}

# Ordered list of all free models used as the fallback chain for OpenRouter requests.
# When the primary model is unavailable, OpenRouter tries the next one in order.
_OPENROUTER_FREE_MODELS = list(OPENROUTER_MODELS.values())


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


def _extract_json(text: str) -> str:
    """Return the first complete JSON array or object from text, stripping code fences and trailing content."""
    import re

    text = text.strip()
    # Strip markdown code fence (```json ... ``` or ``` ... ```)
    text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
    text = re.sub(r"\n?```\s*$", "", text)
    text = text.strip()

    # Find the opening bracket/brace
    start = -1
    opener = None
    for i, ch in enumerate(text):
        if ch in ("[", "{"):
            start = i
            opener = ch
            break

    if start == -1:
        return text

    closer = "]" if opener == "[" else "}"
    depth = 0
    in_string = False
    i = start
    while i < len(text):
        ch = text[i]
        if in_string:
            if ch == "\\":
                i += 2
                continue
            if ch == '"':
                in_string = False
        else:
            if ch == '"':
                in_string = True
            elif ch == opener:
                depth += 1
            elif ch == closer:
                depth -= 1
                if depth == 0:
                    return text[start : i + 1]
        i += 1

    return text[start:]


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


def _call_openrouter(prompt: str, model: str) -> str:
    # Put the requested model first; use the rest as automatic fallbacks.
    fallback_chain = [model] + [m for m in _OPENROUTER_FREE_MODELS if m != model]

    response = httpx.post(
        OPENROUTER_API_URL,
        headers={
            "Authorization": f"Bearer {settings.openrouter_api_key}",
            "Content-Type": "application/json",
        },
        json={
            "models": fallback_chain,
            "route": "fallback",
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=60,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]


def question_source_for_provider(provider: str) -> str:
    """Maps a "provider" value from the frontend to a QuestionSource enum value."""
    if provider == "groq":
        return "groq"
    if provider in OPENROUTER_MODELS:
        return "openrouter"
    return "gemini"


def _call_provider(prompt: str, provider: str) -> str:
    if provider == "groq":
        return _call_groq(prompt)
    if provider in OPENROUTER_MODELS:
        return _call_openrouter(prompt, OPENROUTER_MODELS[provider])
    return _call_gemini(prompt)


def generate_questions(
    topic_name: str, resume_context: str, count: int, difficulty: str, provider: str = "gemini"
) -> list[dict]:
    raw = _call_provider(_question_gen_prompt(topic_name, resume_context, count, difficulty), provider)
    data = json.loads(_extract_json(raw))
    return data


def grade_answer(question: str, ideal_answer: str | None, user_answer: str, provider: str = "gemini") -> dict:
    raw = _call_provider(_grading_prompt(question, ideal_answer, user_answer), provider)
    data = json.loads(_extract_json(raw))
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
    return json.loads(_extract_json(raw))


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
    return json.loads(_extract_json(raw))


def _job_search_prompt(query: str, location: str | None, resume_context: str) -> str:
    location_part = f" in {location}" if location else ""
    return (
        f"Search the web right now for active, open job postings matching '{query}'{location_part}. "
        "Use Google Search to find real listings posted in the last 30 days. "
        "Use the candidate's resume excerpt only for relevance filtering, not as search terms.\n\n"
        f"Resume excerpt:\n{resume_context or '(none provided)'}\n\n"
        "Return up to 8 results as a JSON array (no markdown fences, no extra text before or after), "
        "where each item has the shape:\n"
        '{"title": "...", "company": "...", "role": "...", "link": "https://...", '
        '"source": "...", "snippet": "..."}\n\n'
        "Rules:\n"
        "- 'link' must be a direct URL to the specific job posting page (not a search page). "
        "Copy the exact URL from the search result — do NOT construct or guess URLs.\n"
        "- 'source' is the site name exactly as it appears in the search result "
        "(e.g. LinkedIn, Indeed, Glassdoor, company careers page name).\n"
        "- 'snippet' is a 1-2 sentence summary from the search result snippet.\n"
        "- Omit any result where you are not confident the link is a real, live job posting."
    )


def _call_gemini_with_search(prompt: str) -> str:
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=settings.gemini_api_key)
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(tools=[types.Tool(google_search=types.GoogleSearch())]),
    )
    return response.text


def search_job_leads(query: str, location: str | None, resume_context: str) -> list[dict]:
    raw = _call_gemini_with_search(_job_search_prompt(query, location, resume_context))
    return json.loads(_extract_json(raw))


def friendly_llm_error(exc: Exception, action: str = "generation") -> str:
    """Return a user-friendly message for any LLM call failure."""
    if isinstance(exc, json.JSONDecodeError):
        return "The AI returned an unexpected response. Please try again or switch providers."
    if isinstance(exc, httpx.TimeoutException):
        return "The AI service timed out. Please try again in a moment."
    if isinstance(exc, (httpx.ConnectError, httpx.NetworkError)):
        return "Could not reach the AI service. Please check your connection and try again."
    if isinstance(exc, httpx.HTTPStatusError):
        code = exc.response.status_code
        if code == 429:
            return "AI service rate limit reached. Please wait a moment and try again."
        if code in (503, 502):
            return "The AI service is experiencing high demand. Please try again in a moment or switch providers."
        if code >= 500:
            return "The AI service is temporarily unavailable. Please try again later."

    # Catch Gemini / google-genai 503 errors (raised as SDK exceptions, not httpx)
    exc_str = str(exc)
    if "503" in exc_str or "UNAVAILABLE" in exc_str or "high demand" in exc_str.lower():
        return "The AI service is experiencing high demand. Please try again in a moment or switch providers."
    if "429" in exc_str or "RESOURCE_EXHAUSTED" in exc_str or "quota" in exc_str.lower():
        return "AI service rate limit reached. Please wait a moment and try again."

    return f"AI {action} failed. Please try again or switch to a different provider."
