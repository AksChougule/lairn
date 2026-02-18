from datetime import UTC, datetime
from typing import Any, Optional
from uuid import uuid4

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


class QuizSession(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    topics: list[str] = Field(sa_column=Column(JSON, nullable=False))
    difficulty: str = Field(nullable=False)
    question_type: str = Field(nullable=False)
    num_questions: int = Field(nullable=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC), nullable=False)
    completed_at: Optional[datetime] = Field(default=None, nullable=True)


class QuizQuestion(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    session_id: str = Field(foreign_key="quizsession.id", index=True, nullable=False)
    order_index: int = Field(nullable=False)
    type: str = Field(nullable=False)
    topic_tags: list[str] = Field(sa_column=Column(JSON, nullable=False))
    difficulty: str = Field(nullable=False)
    prompt: str = Field(nullable=False)
    options: Optional[list[str]] = Field(default=None, sa_column=Column(JSON, nullable=True))
    correct_option_index: Optional[int] = Field(default=None, nullable=True)
    expected_answer: Optional[str] = Field(default=None, nullable=True)
    acceptable_variants: Optional[list[str]] = Field(default=None, sa_column=Column(JSON, nullable=True))
    grading_rubric: Optional[str] = Field(default=None, nullable=True)
    explanation: str = Field(nullable=False)


class QuizAnswer(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    session_id: str = Field(foreign_key="quizsession.id", index=True, nullable=False)
    question_id: str = Field(foreign_key="quizquestion.id", index=True, nullable=False)
    user_answer: Optional[str] = Field(default=None, nullable=True)
    option_index: Optional[int] = Field(default=None, nullable=True)
    normalized_user_answer: str = Field(nullable=False)
    is_correct: bool = Field(nullable=False)
    feedback: str = Field(nullable=False)
    why_others_wrong: Optional[list[str]] = Field(default=None, sa_column=Column(JSON, nullable=True))
    judge_trace: Optional[dict[str, Any]] = Field(default=None, sa_column=Column(JSON, nullable=True))
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC), nullable=False)
