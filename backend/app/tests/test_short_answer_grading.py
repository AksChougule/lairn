from pydantic import BaseModel

from app.llm.ollama import OllamaClient
from app.quiz.evaluator import evaluate_short_answer


class _JudgePayload(BaseModel):
    is_correct: bool
    rationale: str


def test_short_answer_uses_deterministic_fallback_when_llm_unavailable(monkeypatch):
    monkeypatch.setattr("app.quiz.evaluator.ollama_client.generate_json", lambda **_: None)

    is_correct, explanation, trace = evaluate_short_answer(
        prompt="What is overfitting?",
        expected_answer="A model learns training noise and fails to generalize.",
        acceptable_variants=["memorizes training data", "poor generalization on unseen data"],
        grading_rubric="Must mention memorization and poor generalization.",
        user_answer="The model memorizes training data and performs poorly on unseen examples.",
    )

    assert is_correct is True
    assert "Expected answer:" in explanation
    assert trace["path"] == "deterministic_fallback"


def test_ollama_client_recovers_from_json_parse_error_with_retry(monkeypatch):
    class _FakeResponse:
        def __init__(self, response_value):
            self._response_value = response_value

        def raise_for_status(self):
            return None

        def json(self):
            return {"response": self._response_value}

    class _FakeHttpClient:
        def __init__(self):
            self.calls = 0

        def post(self, *_args, **_kwargs):
            self.calls += 1
            if self.calls == 1:
                return _FakeResponse("not-json-at-all")
            return _FakeResponse('{"is_correct": true, "rationale": "Recovered on retry."}')

    client = OllamaClient()
    fake_http_client = _FakeHttpClient()
    monkeypatch.setattr(client, "_client", fake_http_client)

    parsed = client.generate_json(
        prompt="judge this",
        response_model=_JudgePayload,
        max_retries=2,
    )

    assert parsed is not None
    assert parsed.is_correct is True
    assert parsed.rationale == "Recovered on retry."
    assert fake_http_client.calls == 2
