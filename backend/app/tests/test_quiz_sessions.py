from pathlib import Path

from sqlmodel import Session, SQLModel, create_engine, select

from app.api.quiz import create_quiz_session, get_session_summary, list_sessions, submit_answer
from app.db.models import QuizQuestion
from app.schemas.quiz import CreateQuizSessionRequest, Difficulty, QuestionType, SubmitAnswerRequest, Topic


def test_create_quiz_session_hides_correct_answers():
    test_db_path = Path("./test_sessions.db")
    if test_db_path.exists():
        test_db_path.unlink()

    engine = create_engine(f"sqlite:///{test_db_path}", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)

    payload = CreateQuizSessionRequest(
        topics=[Topic.machine_learning, Topic.mlops],
        difficulty=Difficulty.medium,
        question_type=QuestionType.mixed,
        num_questions=4,
    )
    try:
        with Session(engine) as db:
            response = create_quiz_session(payload, db)

        assert response.session_id
        assert len(response.questions) == 4
        assert response.config == payload
        assert {question.type for question in response.questions} == {QuestionType.mcq, QuestionType.short_answer}
        for question in response.questions:
            serialized = question.model_dump()
            assert "correct_option_index" not in serialized
            assert "expected_answer" not in serialized
            assert "acceptable_variants" not in serialized
            assert "explanation" not in serialized
    finally:
        if test_db_path.exists():
            test_db_path.unlink()


def test_submit_answer_summary_and_list():
    test_db_path = Path("./test_answers.db")
    if test_db_path.exists():
        test_db_path.unlink()

    engine = create_engine(f"sqlite:///{test_db_path}", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    try:
        with Session(engine) as db:
            created = create_quiz_session(
                CreateQuizSessionRequest(
                    topics=[Topic.machine_learning],
                    difficulty=Difficulty.easy,
                    question_type=QuestionType.mcq,
                    num_questions=1,
                ),
                db,
            )
            question = db.exec(select(QuizQuestion).where(QuizQuestion.session_id == created.session_id)).first()
            assert question is not None
            assert question.correct_option_index is not None

            answer_response = submit_answer(
                created.session_id,
                question.id,
                SubmitAnswerRequest(option_index=question.correct_option_index),
                db,
            )
            assert answer_response.is_correct is True

            summary = get_session_summary(created.session_id, db)
            assert summary.score.correct == 1
            assert summary.score.total == 1
            assert summary.completed_at is not None

            sessions = list_sessions(limit=20, offset=0, db=db)
            assert len(sessions.items) == 1
            assert sessions.items[0].session_id == created.session_id
    finally:
        if test_db_path.exists():
            test_db_path.unlink()
