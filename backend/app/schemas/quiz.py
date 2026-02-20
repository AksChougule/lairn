from enum import Enum

from pydantic import BaseModel, Field


class Topic(str, Enum):
    machine_learning = "Machine Learning technical concepts"
    deep_learning = "Deep Learning technical concepts"
    statistics = "Statistics"
    generative_ai = "Generative AI"
    mlops = "MLOps technical concepts"
    agentic_ai = "Agentic AI technical concepts"
    api_technical_concepts = "API technical concepts"
    llm_foundational_model_concepts = "LLM and Foundational Model concepts"


class Difficulty(str, Enum):
    easy = "easy"
    medium = "medium"
    hard = "hard"


class QuestionType(str, Enum):
    mcq = "mcq"
    short_answer = "short-answer"
    mixed = "mixed"


class CreateQuizSessionRequest(BaseModel):
    topics: list[Topic] = Field(min_length=1)
    difficulty: Difficulty
    question_type: QuestionType
    num_questions: int = Field(ge=1, le=15)


class QuizQuestionPublic(BaseModel):
    id: str
    order_index: int
    type: QuestionType
    topic_tags: list[Topic]
    difficulty: Difficulty
    prompt: str
    options: list[str] | None = None


class CreateQuizSessionResponse(BaseModel):
    session_id: str
    created_at: str
    config: CreateQuizSessionRequest
    questions: list[QuizQuestionPublic]


class SubmitAnswerRequest(BaseModel):
    answer: str | None = None
    option_index: int | None = None


class SubmitAnswerResponse(BaseModel):
    is_correct: bool
    correct_answer: str
    explanation: str
    why_others_wrong: list[str]
    normalized_user_answer: str


class TopicScore(BaseModel):
    topic: Topic
    correct: int
    total: int


class SessionScore(BaseModel):
    correct: int
    total: int


class SessionSummaryResponse(BaseModel):
    session_id: str
    score: SessionScore
    by_topic: list[TopicScore]
    created_at: str
    completed_at: str | None


class SessionListItem(BaseModel):
    session_id: str
    created_at: str
    completed_at: str | None
    score: SessionScore
    config: CreateQuizSessionRequest


class SessionListResponse(BaseModel):
    limit: int
    offset: int
    items: list[SessionListItem]
