from pydantic import BaseModel

from app.llm.ollama import ollama_client


class ShortAnswerJudgeResult(BaseModel):
    is_correct: bool
    rationale: str


def normalize_answer(value: str | None) -> str:
    return (value or "").strip().lower()


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
    normalized_variants = {normalize_answer(variant) for variant in acceptable_variants}
    if normalized_user == normalized_expected or normalized_user in normalized_variants:
        return True, "Matched expected answer or acceptable variant.", {"path": "exact_or_variant_match"}

    prompt_text = (
        "You are a strict quiz grader. Return JSON only.\n"
        "Schema: {\"is_correct\": boolean, \"rationale\": \"short string\"}.\n"
        "Judge the user answer using only the rubric below.\n"
        f"Question: {prompt}\n"
        f"Expected answer: {expected_answer}\n"
        f"Acceptable variants: {acceptable_variants}\n"
        f"Rubric: {grading_rubric}\n"
        f"User answer: {user_answer}\n"
    )
    judged = ollama_client.generate_json(prompt=prompt_text, response_model=ShortAnswerJudgeResult, max_retries=2)
    if judged:
        trace = {"path": "llm_judge", "rationale": judged.rationale}
        return judged.is_correct, judged.rationale, trace

    trace = {"path": "llm_fallback", "rationale": "LLM judge unavailable; marked incorrect."}
    return False, "Could not verify answer against rubric.", trace
