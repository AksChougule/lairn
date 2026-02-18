from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select

from app.db.models import QuizAnswer, QuizQuestion, QuizSession
from app.db.session import get_session
from app.quiz.evaluator import evaluate_short_answer, normalize_answer
from app.quiz.generator import generate_questions
from app.schemas.quiz import (
    CreateQuizSessionRequest,
    CreateQuizSessionResponse,
    Difficulty,
    QuestionType,
    QuizQuestionPublic,
    SessionListItem,
    SessionListResponse,
    SessionScore,
    SessionSummaryResponse,
    SubmitAnswerRequest,
    SubmitAnswerResponse,
    Topic,
    TopicScore,
)

router = APIRouter(tags=["quiz"])


def _as_iso8601(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _to_public_question(question: QuizQuestion) -> QuizQuestionPublic:
    return QuizQuestionPublic(
        id=question.id,
        order_index=question.order_index,
        type=question.type,
        topic_tags=question.topic_tags,
        difficulty=question.difficulty,
        prompt=question.prompt,
        options=question.options,
    )


def _session_config(session: QuizSession) -> CreateQuizSessionRequest:
    return CreateQuizSessionRequest(
        topics=[Topic(topic) for topic in session.topics],
        difficulty=Difficulty(session.difficulty),
        question_type=QuestionType(session.question_type),
        num_questions=session.num_questions,
    )


def _load_session(session_id: str, db: Session) -> QuizSession:
    quiz_session = db.get(QuizSession, session_id)
    if not quiz_session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return quiz_session


def _load_question(session_id: str, question_id: str, db: Session) -> QuizQuestion:
    question = db.get(QuizQuestion, question_id)
    if not question or question.session_id != session_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")
    return question


def _calc_summary(session_id: str, db: Session) -> tuple[SessionScore, list[TopicScore]]:
    questions = db.exec(select(QuizQuestion).where(QuizQuestion.session_id == session_id)).all()
    answers = db.exec(select(QuizAnswer).where(QuizAnswer.session_id == session_id)).all()
    answers_by_question = {answer.question_id: answer for answer in answers}

    correct_total = sum(1 for answer in answers if answer.is_correct)
    score = SessionScore(correct=correct_total, total=len(questions))

    topic_totals: dict[str, dict[str, int]] = {}
    for question in questions:
        topic = question.topic_tags[0]
        if topic not in topic_totals:
            topic_totals[topic] = {"correct": 0, "total": 0}
        topic_totals[topic]["total"] += 1
        answer = answers_by_question.get(question.id)
        if answer and answer.is_correct:
            topic_totals[topic]["correct"] += 1

    by_topic = [
        TopicScore(topic=Topic(topic), correct=counts["correct"], total=counts["total"])
        for topic, counts in topic_totals.items()
    ]
    return score, by_topic


@router.post("/quiz/sessions", response_model=CreateQuizSessionResponse, status_code=status.HTTP_201_CREATED)
def create_quiz_session(payload: CreateQuizSessionRequest, db: Session = Depends(get_session)) -> CreateQuizSessionResponse:
    generated_questions = generate_questions(
        topics=payload.topics,
        difficulty=payload.difficulty,
        question_type=payload.question_type,
        num_questions=payload.num_questions,
    )

    quiz_session = QuizSession(
        topics=[topic.value for topic in payload.topics],
        difficulty=payload.difficulty.value,
        question_type=payload.question_type.value,
        num_questions=payload.num_questions,
    )
    db.add(quiz_session)
    db.flush()

    stored_questions: list[QuizQuestionPublic] = []
    for index, generated in enumerate(generated_questions, start=1):
        question = QuizQuestion(
            session_id=quiz_session.id,
            order_index=index,
            type=generated.type.value,
            topic_tags=[topic.value for topic in generated.topic_tags],
            difficulty=generated.difficulty.value,
            prompt=generated.prompt,
            options=generated.options,
            correct_option_index=generated.correct_option_index,
            expected_answer=generated.expected_answer,
            acceptable_variants=generated.acceptable_variants,
            grading_rubric=generated.grading_rubric,
            explanation=generated.explanation,
        )
        db.add(question)
        db.flush()
        stored_questions.append(_to_public_question(question))

    db.commit()
    return CreateQuizSessionResponse(
        session_id=quiz_session.id,
        created_at=_as_iso8601(quiz_session.created_at) or "",
        config=payload,
        questions=stored_questions,
    )


@router.post(
    "/quiz/sessions/{session_id}/questions/{question_id}/answer",
    response_model=SubmitAnswerResponse,
    status_code=status.HTTP_200_OK,
)
def submit_answer(
    session_id: str,
    question_id: str,
    payload: SubmitAnswerRequest,
    db: Session = Depends(get_session),
) -> SubmitAnswerResponse:
    quiz_session = _load_session(session_id, db)
    question = _load_question(session_id, question_id, db)

    existing_answer = db.exec(
        select(QuizAnswer).where(QuizAnswer.session_id == session_id, QuizAnswer.question_id == question_id)
    ).first()
    if existing_answer:
        correct_answer = (
            question.options[question.correct_option_index] if question.type == QuestionType.mcq.value else (question.expected_answer or "")
        )
        return SubmitAnswerResponse(
            is_correct=existing_answer.is_correct,
            correct_answer=correct_answer,
            explanation=existing_answer.feedback,
            why_others_wrong=existing_answer.why_others_wrong or [],
            normalized_user_answer=existing_answer.normalized_user_answer,
        )

    is_correct = False
    rationale = question.explanation
    trace: dict[str, str] | None = None
    why_others_wrong: list[str] = []

    if question.type == QuestionType.mcq.value:
        if payload.option_index is None:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="option_index is required for MCQ")
        if question.options is None or question.correct_option_index is None:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="MCQ question is misconfigured")

        is_correct = payload.option_index == question.correct_option_index
        normalized_user_answer = normalize_answer(
            question.options[payload.option_index] if 0 <= payload.option_index < len(question.options) else ""
        )
        for idx, option in enumerate(question.options):
            if idx != question.correct_option_index:
                why_others_wrong.append(f"'{option}' is incorrect because it does not satisfy the prompt constraints.")
        correct_answer = question.options[question.correct_option_index]
    else:
        text_answer = payload.answer or ""
        if not text_answer.strip():
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="answer is required for short-answer")
        if not question.expected_answer or question.acceptable_variants is None or not question.grading_rubric:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="short-answer question is misconfigured")

        is_correct, rationale, trace = evaluate_short_answer(
            prompt=question.prompt,
            expected_answer=question.expected_answer,
            acceptable_variants=question.acceptable_variants,
            grading_rubric=question.grading_rubric,
            user_answer=text_answer,
        )
        normalized_user_answer = normalize_answer(text_answer)
        correct_answer = question.expected_answer

    answer_row = QuizAnswer(
        session_id=session_id,
        question_id=question_id,
        user_answer=payload.answer,
        option_index=payload.option_index,
        normalized_user_answer=normalized_user_answer,
        is_correct=is_correct,
        feedback=rationale,
        why_others_wrong=why_others_wrong or None,
        judge_trace=trace,
    )
    db.add(answer_row)
    db.flush()

    answered_count = db.exec(select(QuizAnswer).where(QuizAnswer.session_id == session_id)).all()
    if len(answered_count) >= quiz_session.num_questions and quiz_session.completed_at is None:
        quiz_session.completed_at = datetime.now(UTC)
        db.add(quiz_session)

    db.commit()
    return SubmitAnswerResponse(
        is_correct=is_correct,
        correct_answer=correct_answer,
        explanation=rationale,
        why_others_wrong=why_others_wrong,
        normalized_user_answer=normalized_user_answer,
    )


@router.get("/quiz/sessions/{session_id}/summary", response_model=SessionSummaryResponse, status_code=status.HTTP_200_OK)
def get_session_summary(session_id: str, db: Session = Depends(get_session)) -> SessionSummaryResponse:
    quiz_session = _load_session(session_id, db)
    score, by_topic = _calc_summary(session_id, db)
    return SessionSummaryResponse(
        session_id=quiz_session.id,
        score=score,
        by_topic=by_topic,
        created_at=_as_iso8601(quiz_session.created_at) or "",
        completed_at=_as_iso8601(quiz_session.completed_at),
    )


@router.get("/quiz/sessions", response_model=SessionListResponse, status_code=status.HTTP_200_OK)
def list_sessions(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_session),
) -> SessionListResponse:
    sessions = db.exec(select(QuizSession).offset(offset).limit(limit)).all()
    items: list[SessionListItem] = []
    for quiz_session in sessions:
        score, _ = _calc_summary(quiz_session.id, db)
        items.append(
            SessionListItem(
                session_id=quiz_session.id,
                created_at=_as_iso8601(quiz_session.created_at) or "",
                completed_at=_as_iso8601(quiz_session.completed_at),
                score=score,
                config=_session_config(quiz_session),
            )
        )
    return SessionListResponse(limit=limit, offset=offset, items=items)
