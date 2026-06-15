from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models import ApplicationStatus, QuestionDifficulty, QuestionSource, TopicSource, TopicStatus


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


# ---- Job Applications ----
class ApplicationBase(BaseModel):
    name: str
    company: str
    role: str
    status: ApplicationStatus = ApplicationStatus.applied
    source: str | None = None
    job_post_link: str | None = None
    job_portal_link: str | None = None
    poc: str | None = None
    notes: str | None = None
    practice_interview_done: bool = False


class ApplicationCreate(ApplicationBase):
    pass


class ApplicationUpdate(BaseModel):
    name: str | None = None
    company: str | None = None
    role: str | None = None
    status: ApplicationStatus | None = None
    source: str | None = None
    job_post_link: str | None = None
    job_portal_link: str | None = None
    poc: str | None = None
    notes: str | None = None
    practice_interview_done: bool | None = None


class ApplicationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    company: str
    role: str
    status: ApplicationStatus
    source: str | None
    job_post_link: str | None
    job_portal_link: str | None
    poc: str | None
    notes: str | None
    practice_interview_done: bool
    created_at: datetime
    updated_at: datetime


class ApplicationResolveRequest(BaseModel):
    url: str


class ApplicationResolveResult(BaseModel):
    name: str | None = None
    company: str | None = None
    role: str | None = None
    source: str | None = None


# ---- Application (mock interview) Questions ----
class AppQuestionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    application_id: int
    question_text: str
    ideal_answer: str | None
    difficulty: QuestionDifficulty
    source: QuestionSource
    created_at: datetime


class AppQuestionGenerateRequest(BaseModel):
    count: int = 5
    difficulty: QuestionDifficulty = QuestionDifficulty.medium
    provider: str = "gemini"
