import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class TopicStatus(str, enum.Enum):
    active = "active"
    excluded = "excluded"
    mastered = "mastered"


class TopicSource(str, enum.Enum):
    resume = "resume"
    manual = "manual"


class QuestionDifficulty(str, enum.Enum):
    easy = "easy"
    medium = "medium"
    hard = "hard"


class QuestionSource(str, enum.Enum):
    gemini = "gemini"
    groq = "groq"
    manual = "manual"


class Resume(Base):
    __tablename__ = "resumes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[str] = mapped_column(String(255), index=True)
    filename: Mapped[str] = mapped_column(String(255))
    storage_path: Mapped[str] = mapped_column(String(500))
    raw_text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    topics: Mapped[list["Topic"]] = relationship(back_populates="resume", cascade="all, delete-orphan")


class Topic(Base):
    __tablename__ = "topics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[str] = mapped_column(String(255), index=True)
    resume_id: Mapped[int | None] = mapped_column(ForeignKey("resumes.id", ondelete="CASCADE"), nullable=True)
    name: Mapped[str] = mapped_column(String(255))
    status: Mapped[TopicStatus] = mapped_column(Enum(TopicStatus), default=TopicStatus.active)
    source: Mapped[TopicSource] = mapped_column(Enum(TopicSource), default=TopicSource.manual)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    resume: Mapped["Resume | None"] = relationship(back_populates="topics")
    questions: Mapped[list["Question"]] = relationship(back_populates="topic", cascade="all, delete-orphan")


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id", ondelete="CASCADE"))
    question_text: Mapped[str] = mapped_column(Text)
    ideal_answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    difficulty: Mapped[QuestionDifficulty] = mapped_column(Enum(QuestionDifficulty), default=QuestionDifficulty.medium)
    source: Mapped[QuestionSource] = mapped_column(Enum(QuestionSource), default=QuestionSource.gemini)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    topic: Mapped["Topic"] = relationship(back_populates="questions")
    attempts: Mapped[list["Attempt"]] = relationship(back_populates="question", cascade="all, delete-orphan")


class ApplicationStatus(str, enum.Enum):
    applied = "applied"
    in_progress = "in_progress"
    waiting = "waiting"
    rejected = "rejected"
    offered = "offered"


class JobApplication(Base):
    __tablename__ = "job_applications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[str] = mapped_column(String(255), index=True)
    name: Mapped[str] = mapped_column(String(255))
    company: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(255))
    status: Mapped[ApplicationStatus] = mapped_column(Enum(ApplicationStatus), default=ApplicationStatus.applied)
    source: Mapped[str | None] = mapped_column(String(255), nullable=True)
    job_post_link: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    job_portal_link: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    poc: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    practice_interview_done: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    questions: Mapped[list["ApplicationQuestion"]] = relationship(
        back_populates="application", cascade="all, delete-orphan"
    )


class ApplicationQuestion(Base):
    __tablename__ = "application_questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    application_id: Mapped[int] = mapped_column(ForeignKey("job_applications.id", ondelete="CASCADE"))
    question_text: Mapped[str] = mapped_column(Text)
    ideal_answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    difficulty: Mapped[QuestionDifficulty] = mapped_column(Enum(QuestionDifficulty), default=QuestionDifficulty.medium)
    source: Mapped[QuestionSource] = mapped_column(Enum(QuestionSource), default=QuestionSource.gemini)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    application: Mapped["JobApplication"] = relationship(back_populates="questions")


class Attempt(Base):
    __tablename__ = "attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id", ondelete="CASCADE"))
    user_answer: Mapped[str] = mapped_column(Text)
    score: Mapped[int] = mapped_column(Integer)
    feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    question: Mapped["Question"] = relationship(back_populates="attempts")
