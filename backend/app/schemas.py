from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models import QuestionDifficulty, QuestionSource, TopicSource, TopicStatus


# ---- Resume ----
class ResumeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    storage_path: str
    created_at: datetime


# ---- Topic ----
class TopicCreate(BaseModel):
    name: str


class TopicUpdate(BaseModel):
    name: str | None = None
    status: TopicStatus | None = None


class TopicOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    resume_id: int | None
    name: str
    status: TopicStatus
    source: TopicSource
    created_at: datetime


# ---- Question ----
class QuestionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    topic_id: int
    question_text: str
    ideal_answer: str | None
    difficulty: QuestionDifficulty
    source: QuestionSource
    created_at: datetime


class QuestionGenerateRequest(BaseModel):
    topic_id: int
    count: int = 5
    difficulty: QuestionDifficulty = QuestionDifficulty.medium
    provider: str = "gemini"  # "gemini" or "groq"


class QuestionCreateManual(BaseModel):
    topic_id: int
    question_text: str
    ideal_answer: str | None = None
    difficulty: QuestionDifficulty = QuestionDifficulty.medium


class ExternalPromptResponse(BaseModel):
    prompt: str


# ---- Attempt / Progress ----
class AttemptCreate(BaseModel):
    question_id: int
    user_answer: str
    provider: str = "gemini"  # which LLM grades the answer


class AttemptOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    question_id: int
    user_answer: str
    score: int
    feedback: str | None
    created_at: datetime


class TopicProgress(BaseModel):
    topic_id: int
    topic_name: str
    status: TopicStatus
    total_questions: int
    attempted_questions: int
    average_score: float | None
