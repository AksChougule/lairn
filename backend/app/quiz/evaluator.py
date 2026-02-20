import re

from pydantic import BaseModel

from app.llm.ollama import ollama_client


class ShortAnswerJudgeResult(BaseModel):
    is_correct: bool
    rationale: str


def normalize_answer(value: str | None) -> str:
    lowered = (value or "").strip().lower()
    alnum = re.sub(r"[^a-z0-9\s]", " ", lowered)
    return re.sub(r"\s+", " ", alnum).strip()


def _tokenize(value: str) -> set[str]:
    return {token for token in normalize_answer(value).split(" ") if token}


def _deterministic_fallback(
    *,
    expected_answer: str,
    acceptable_variants: list[str],
    user_answer: str,
) -> tuple[bool, str, dict[str, str]]:
    expected_tokens = _tokenize(expected_answer)
    variant_tokens = [_tokenize(variant) for variant in acceptable_variants]
    user_tokens = _tokenize(user_answer)

    token_overlap = 0.0
    if expected_tokens:
        token_overlap = len(expected_tokens & user_tokens) / len(expected_tokens)
    variant_overlap = max((len(tokens & user_tokens) / len(tokens) for tokens in variant_tokens if tokens), default=0.0)
    best_overlap = max(token_overlap, variant_overlap)

    is_correct = best_overlap >= 0.6
    explanation = (
        f"Expected answer: {expected_answer}. "
        f"Accepted variants include: {', '.join(acceptable_variants) if acceptable_variants else 'none'}. "
        f"Your response was evaluated using deterministic token overlap ({best_overlap:.2f})."
    )
    return is_correct, explanation, {"path": "deterministic_fallback", "overlap": f"{best_overlap:.2f}"}


def evaluate_short_answer(
    *,
    prompt: str,
    expected_answer: str,
    acceptable_variants: list[str],
    grading_rubric: str,
    user_answer: str,
) -> tuple[bool, str, dict[str, str]]:
    normalized_user = normalize_answer(user_answer)
    normalized_expected = normalize_answer(expected_answer)
    normalized_variants = {normalize_answer(variant) for variant in acceptable_variants if normalize_answer(variant)}

    if normalized_user and normalized_expected and (
        normalized_user in normalized_expected or normalized_expected in normalized_user
    ):
        return True, "Matched expected answer after normalization.", {"path": "normalized_contains_match"}

    if normalized_user == normalized_expected or normalized_user in normalized_variants:
        return True, "Matched expected answer or acceptable variant.", {"path": "exact_or_variant_match"}

    prompt_text = (
        "You are a strict quiz grader. Return JSON only.\n"
        "Schema: {\"is_correct\": boolean, \"rationale\": \"2-4 concise sentences\"}.\n"
        "Do not include markdown, code fences, or additional keys.\n"
        "Judge the user answer using only the rubric below.\n"
        f"Question: {prompt}\n"
        f"Expected answer: {expected_answer}\n"
        f"Acceptable variants: {acceptable_variants}\n"
        f"Rubric: {grading_rubric}\n"
        f"User answer: {user_answer}\n"
    )
    judged = ollama_client.generate_json(prompt=prompt_text, response_model=ShortAnswerJudgeResult, max_retries=2)
    if judged and judged.rationale.strip():
        trace = {"path": "llm_judge", "rationale": judged.rationale}
        return judged.is_correct, judged.rationale, trace

    return _deterministic_fallback(
        expected_answer=expected_answer,
        acceptable_variants=acceptable_variants,
        user_answer=user_answer,
    )
