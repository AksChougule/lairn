from pydantic import ValidationError

from app.quiz.generator import LLMGeneratedQuestion, LLMGeneratedQuestions, generate_questions
from app.schemas.quiz import CreateQuizSessionRequest, Difficulty, QuestionType, Topic


def test_create_session_request_rejects_more_than_15_questions():
    try:
        CreateQuizSessionRequest(
            topics=[Topic.machine_learning],
            difficulty=Difficulty.medium,
            question_type=QuestionType.mixed,
            num_questions=16,
        )
    except ValidationError:
        return
    raise AssertionError("Expected validation to fail for num_questions > 15")


def test_generate_questions_deduplicates_prompts_with_targeted_regeneration(monkeypatch):
    calls: list[int] = []

    initial = LLMGeneratedQuestions(
        questions=[
            LLMGeneratedQuestion(
                type=QuestionType.mcq,
                topic_tags=[Topic.machine_learning],
                difficulty=Difficulty.medium,
                prompt="Duplicate prompt",
                options=["A", "B", "C", "D"],
                correct_option_index=1,
                expected_answer=None,
                acceptable_variants=None,
                grading_rubric=None,
                explanation="Explanation 1",
            ),
            LLMGeneratedQuestion(
                type=QuestionType.mcq,
                topic_tags=[Topic.deep_learning],
                difficulty=Difficulty.medium,
                prompt="Duplicate prompt",
                options=["A", "B", "C", "D"],
                correct_option_index=2,
                expected_answer=None,
                acceptable_variants=None,
                grading_rubric=None,
                explanation="Explanation 2",
            ),
            LLMGeneratedQuestion(
                type=QuestionType.mcq,
                topic_tags=[Topic.statistics],
                difficulty=Difficulty.medium,
                prompt="Unique prompt",
                options=["A", "B", "C", "D"],
                correct_option_index=3,
                expected_answer=None,
                acceptable_variants=None,
                grading_rubric=None,
                explanation="Explanation 3",
            ),
        ]
    )
    regenerated = LLMGeneratedQuestions(
        questions=[
            LLMGeneratedQuestion(
                type=QuestionType.mcq,
                topic_tags=[Topic.deep_learning],
                difficulty=Difficulty.medium,
                prompt="Regenerated unique prompt",
                options=["A", "B", "C", "D"],
                correct_option_index=0,
                expected_answer=None,
                acceptable_variants=None,
                grading_rubric=None,
                explanation="Regenerated explanation",
            )
        ]
    )

    def fake_generate_json(**_kwargs):
        calls.append(1)
        if len(calls) == 1:
            return initial
        return regenerated

    monkeypatch.setattr("app.quiz.generator.ollama_client.generate_json", fake_generate_json)

    questions = generate_questions(
        topics=[Topic.machine_learning, Topic.deep_learning, Topic.statistics],
        difficulty=Difficulty.medium,
        question_type=QuestionType.mcq,
        num_questions=3,
    )
    prompts = [question.prompt for question in questions]

    assert len(prompts) == 3
    assert len(set(prompts)) == 3
    assert "Regenerated unique prompt" in prompts
    assert len(calls) == 2
