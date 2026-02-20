import random
from dataclasses import dataclass

from pydantic import BaseModel, Field

from app.llm.ollama import ollama_client
from app.schemas.quiz import Difficulty, QuestionType, Topic


@dataclass
class GeneratedQuestion:
    type: QuestionType
    topic_tags: list[Topic]
    difficulty: Difficulty
    prompt: str
    options: list[str] | None
    correct_option_index: int | None
    expected_answer: str | None
    acceptable_variants: list[str] | None
    grading_rubric: str | None
    explanation: str


class LLMGeneratedQuestion(BaseModel):
    type: QuestionType
    topic_tags: list[Topic] = Field(min_length=1)
    difficulty: Difficulty
    prompt: str
    options: list[str] | None = None
    correct_option_index: int | None = None
    expected_answer: str | None = None
    acceptable_variants: list[str] | None = None
    grading_rubric: str | None = None
    explanation: str


class LLMGeneratedQuestions(BaseModel):
    questions: list[LLMGeneratedQuestion]


TOPIC_BANK: dict[Topic, dict[str, dict[str, object]]] = {
    Topic.machine_learning: {
        "mcq": {
            "prompt": "Which split is primarily used to tune model hyperparameters?",
            "options": ["Training set", "Validation set", "Test set", "Production set"],
            "correct_option_index": 1,
            "explanation": "Hyperparameters are tuned on the validation set. The test set should stay untouched for final evaluation only.",
        },
        "short-answer": {
            "prompt": "What is overfitting in machine learning?",
            "expected_answer": "A model learns training noise and fails to generalize.",
            "acceptable_variants": ["memorizes training data", "poor generalization on unseen data"],
            "grading_rubric": "Answer must mention training-fit with poor unseen/generalization performance.",
            "explanation": "Overfitting means the model captures patterns that do not transfer to new data. It usually performs much better on training than on validation/test.",
        },
    },
    Topic.deep_learning: {
        "mcq": {
            "prompt": "What is the primary purpose of dropout during training?",
            "options": ["Speed up inference", "Reduce overfitting", "Normalize activations", "Increase model depth"],
            "correct_option_index": 1,
            "explanation": "Dropout randomly disables units during training, reducing co-adaptation and improving generalization.",
        },
        "short-answer": {
            "prompt": "Why are activation functions needed in deep neural networks?",
            "expected_answer": "They introduce non-linearity so networks can model complex relationships.",
            "acceptable_variants": ["without activations layers collapse into linear mapping", "enable complex function approximation"],
            "grading_rubric": "Must explicitly mention non-linearity and representational power.",
            "explanation": "Without non-linear activations, stacked linear layers are still linear. Activations let deep nets learn complex patterns.",
        },
    },
    Topic.statistics: {
        "mcq": {
            "prompt": "What does a p-value represent in hypothesis testing?",
            "options": [
                "Probability the null hypothesis is true",
                "Probability of observing data this extreme if null is true",
                "Probability the alternative hypothesis is true",
                "Type I error rate",
            ],
            "correct_option_index": 1,
            "explanation": "A p-value measures how extreme the observed data is under the null hypothesis, not the probability that the null is true.",
        },
        "short-answer": {
            "prompt": "What is the difference between variance and standard deviation?",
            "expected_answer": "Standard deviation is the square root of variance.",
            "acceptable_variants": ["variance is squared spread; std dev in original units"],
            "grading_rubric": "Must mention sqrt relationship and/or unit difference.",
            "explanation": "Variance measures spread in squared units. Standard deviation is its square root and uses the original unit scale.",
        },
    },
    Topic.generative_ai: {
        "mcq": {
            "prompt": "In transformer decoding, what does temperature mainly control?",
            "options": ["Model size", "Randomness of token sampling", "Context window length", "Embedding dimension"],
            "correct_option_index": 1,
            "explanation": "Higher temperature flattens token probabilities and increases randomness. Lower values make outputs more deterministic.",
        },
        "short-answer": {
            "prompt": "What is retrieval-augmented generation (RAG)?",
            "expected_answer": "An approach that retrieves external documents and uses them in generation.",
            "acceptable_variants": ["LLM + retrieval", "injects retrieved context into prompt"],
            "grading_rubric": "Must mention retrieval of external knowledge and conditioning generation on it.",
            "explanation": "RAG supplements model knowledge with retrieved context at query time. This improves factuality and freshness for domain-specific questions.",
        },
    },
    Topic.mlops: {
        "mcq": {
            "prompt": "What is the main purpose of model versioning in MLOps workflows?",
            "options": ["Reduce model size", "Track and reproduce model changes", "Increase training speed", "Avoid data labeling"],
            "correct_option_index": 1,
            "explanation": "Versioning tracks model artifacts, code, and metadata so teams can reproduce and audit model behavior.",
        },
        "short-answer": {
            "prompt": "Why is data drift monitoring important in production ML systems?",
            "expected_answer": "It detects when input distributions change and model performance may degrade.",
            "acceptable_variants": ["distribution shift monitoring", "catches changing data patterns"],
            "grading_rubric": "Must connect input-distribution change with risk to performance.",
            "explanation": "Production data can move away from training conditions. Drift monitoring signals when retraining or intervention is needed.",
        },
    },
    Topic.agentic_ai: {
        "mcq": {
            "prompt": "What best describes an AI agent tool call?",
            "options": ["A random text output", "A structured invocation of an external capability", "A larger context window", "A hidden model layer"],
            "correct_option_index": 1,
            "explanation": "Tool calls let an agent trigger external functions with structured arguments to complete tasks beyond text generation.",
        },
        "short-answer": {
            "prompt": "What is a planning loop in agentic AI?",
            "expected_answer": "An iterative cycle of plan, act, observe, and update.",
            "acceptable_variants": ["reason-act-observe loop", "iterative planning with feedback"],
            "grading_rubric": "Must describe iterative planning and feedback from observations.",
            "explanation": "Agentic systems often operate iteratively: they plan steps, execute actions, observe outcomes, and adapt the plan.",
        },
    },
    Topic.api_technical_concepts: {
        "mcq": {
            "prompt": "Which HTTP method is typically used for idempotent partial updates?",
            "options": ["GET", "POST", "PATCH", "CONNECT"],
            "correct_option_index": 2,
            "explanation": "PATCH applies partial updates to a resource representation. GET retrieves data and POST is generally non-idempotent for creation.",
        },
        "short-answer": {
            "prompt": "What does a 429 HTTP status code indicate?",
            "expected_answer": "Too many requests; the client has been rate limited.",
            "acceptable_variants": ["rate limit exceeded", "request throttled by server"],
            "grading_rubric": "Must mention rate limiting or request throttling.",
            "explanation": "HTTP 429 signals that the client sent too many requests in a given window. Clients should back off and retry according to policy.",
        },
    },
    Topic.llm_foundational_model_concepts: {
        "mcq": {
            "prompt": "What is the main function of tokenization in LLM pipelines?",
            "options": ["Encrypt user input", "Convert text into model-processable token IDs", "Reduce GPU memory to zero", "Guarantee factual outputs"],
            "correct_option_index": 1,
            "explanation": "Tokenization maps text into discrete IDs the model understands. It is a preprocessing step before embedding and transformer computation.",
        },
        "short-answer": {
            "prompt": "What is context window in a foundational language model?",
            "expected_answer": "The maximum amount of tokenized input the model can attend to in one inference.",
            "acceptable_variants": ["max tokens the model can process at once", "attention span limit in tokens"],
            "grading_rubric": "Must mention a token limit for single-pass model attention/input.",
            "explanation": "A context window defines how many tokens the model can use at inference time. Inputs beyond that window are truncated or handled with other strategies.",
        },
    },
}


def _build_fallback_question(topic: Topic, difficulty: Difficulty, question_type: QuestionType) -> GeneratedQuestion:
    source = TOPIC_BANK[topic][question_type.value]
    return GeneratedQuestion(
        type=question_type,
        topic_tags=[topic],
        difficulty=difficulty,
        prompt=str(source["prompt"]),
        options=source.get("options"),  # type: ignore[arg-type]
        correct_option_index=source.get("correct_option_index"),  # type: ignore[arg-type]
        expected_answer=source.get("expected_answer"),  # type: ignore[arg-type]
        acceptable_variants=source.get("acceptable_variants"),  # type: ignore[arg-type]
        grading_rubric=source.get("grading_rubric"),  # type: ignore[arg-type]
        explanation=str(source["explanation"]),
    )


def _is_valid_generated_question(question: LLMGeneratedQuestion) -> bool:
    if question.type == QuestionType.mcq:
        return (
            question.options is not None
            and len(question.options) == 4
            and question.correct_option_index is not None
            and 0 <= question.correct_option_index < 4
        )
    return bool(question.expected_answer and question.acceptable_variants is not None and question.grading_rubric)


def _build_llm_prompt(
    *,
    topics: list[Topic],
    difficulty: Difficulty,
    question_type: QuestionType,
    num_questions: int,
) -> str:
    return (
        "Generate quiz questions as strict JSON only.\n"
        "Output schema: {\"questions\": [{"
        "\"type\": \"mcq|short-answer\", "
        "\"topic_tags\": [\"Machine Learning technical concepts|Deep Learning technical concepts|Statistics|Generative AI|MLOps technical concepts|Agentic AI technical concepts|API technical concepts|LLM and Foundational Model concepts\"], "
        "\"difficulty\": \"easy|medium|hard\", "
        "\"prompt\": \"string\", "
        "\"options\": [\"a\",\"b\",\"c\",\"d\"] or null, "
        "\"correct_option_index\": 0..3 or null, "
        "\"expected_answer\": \"string\" or null, "
        "\"acceptable_variants\": [\"string\"] or null, "
        "\"grading_rubric\": \"string\" or null, "
        "\"explanation\": \"2-6 sentence explanation\""
        "}]}.\n"
        "Rules: concise, unambiguous, non-opinionated, no long copyrighted text, exactly 4 MCQ options, one correct option.\n"
        f"Requested topics: {[topic.value for topic in topics]}.\n"
        f"Difficulty: {difficulty.value}.\n"
        f"Question type: {question_type.value}.\n"
        f"Num questions: {num_questions}.\n"
    )


def _normalize_prompt(value: str) -> str:
    return " ".join(value.lower().strip().split())


def _with_prompt(question: GeneratedQuestion, prompt: str) -> GeneratedQuestion:
    return GeneratedQuestion(
        type=question.type,
        topic_tags=question.topic_tags,
        difficulty=question.difficulty,
        prompt=prompt,
        options=question.options,
        correct_option_index=question.correct_option_index,
        expected_answer=question.expected_answer,
        acceptable_variants=question.acceptable_variants,
        grading_rubric=question.grading_rubric,
        explanation=question.explanation,
    )


def _regenerate_duplicate_question(
    *,
    original: GeneratedQuestion,
    used_prompts: set[str],
) -> GeneratedQuestion | None:
    allowed_topics = "|".join(topic.value for topic in Topic)
    prompt = (
        "Generate exactly one quiz question as strict JSON only.\n"
        "Output schema: {\"questions\": [{"
        "\"type\": \"mcq|short-answer\", "
        f"\"topic_tags\": [\"{allowed_topics}\"], "
        "\"difficulty\": \"easy|medium|hard\", "
        "\"prompt\": \"string\", "
        "\"options\": [\"a\",\"b\",\"c\",\"d\"] or null, "
        "\"correct_option_index\": 0..3 or null, "
        "\"expected_answer\": \"string\" or null, "
        "\"acceptable_variants\": [\"string\"] or null, "
        "\"grading_rubric\": \"string\" or null, "
        "\"explanation\": \"2-6 sentence explanation\""
        "}]}.\n"
        f"Required type: {original.type.value}\n"
        f"Required difficulty: {original.difficulty.value}\n"
        f"Required topic tag: {original.topic_tags[0].value}\n"
        f"Avoid prompts matching any of these normalized prompts: {sorted(used_prompts)}\n"
    )
    response = ollama_client.generate_json(prompt=prompt, response_model=LLMGeneratedQuestions, max_retries=2)
    if not response or len(response.questions) != 1:
        return None

    candidate = response.questions[0]
    if not _is_valid_generated_question(candidate):
        return None
    if candidate.type != original.type:
        return None
    if original.topic_tags[0] not in candidate.topic_tags:
        return None
    if _normalize_prompt(candidate.prompt) in used_prompts:
        return None

    return GeneratedQuestion(
        type=candidate.type,
        topic_tags=candidate.topic_tags,
        difficulty=candidate.difficulty,
        prompt=candidate.prompt,
        options=candidate.options,
        correct_option_index=candidate.correct_option_index,
        expected_answer=candidate.expected_answer,
        acceptable_variants=candidate.acceptable_variants,
        grading_rubric=candidate.grading_rubric,
        explanation=candidate.explanation,
    )


def _deduplicate_questions(questions: list[GeneratedQuestion]) -> list[GeneratedQuestion]:
    deduplicated: list[GeneratedQuestion] = []
    used_prompts: set[str] = set()

    for question in questions:
        candidate = question
        attempts = 0
        while _normalize_prompt(candidate.prompt) in used_prompts and attempts < 3:
            regenerated = _regenerate_duplicate_question(original=candidate, used_prompts=used_prompts)
            if regenerated is None:
                break
            candidate = regenerated
            attempts += 1

        normalized_candidate_prompt = _normalize_prompt(candidate.prompt)
        if normalized_candidate_prompt in used_prompts:
            variant_number = 2
            while _normalize_prompt(f"{candidate.prompt} (variation {variant_number})") in used_prompts:
                variant_number += 1
            candidate = _with_prompt(candidate, f"{candidate.prompt} (variation {variant_number})")
            normalized_candidate_prompt = _normalize_prompt(candidate.prompt)

        deduplicated.append(candidate)
        used_prompts.add(normalized_candidate_prompt)

    return deduplicated


def _fallback_questions(
    *,
    topics: list[Topic],
    difficulty: Difficulty,
    question_type: QuestionType,
    num_questions: int,
) -> list[GeneratedQuestion]:
    seed_material = "|".join(
        [
            ",".join(topic.value for topic in topics),
            difficulty.value,
            question_type.value,
            str(num_questions),
        ]
    )
    rng = random.Random(seed_material)
    questions: list[GeneratedQuestion] = []
    topic_count = len(topics)

    for index in range(num_questions):
        topic = topics[index % topic_count]
        resolved_type = question_type
        if question_type == QuestionType.mixed:
            resolved_type = rng.choice([QuestionType.mcq, QuestionType.short_answer])
        questions.append(_build_fallback_question(topic=topic, difficulty=difficulty, question_type=resolved_type))

    return questions


def generate_questions(
    topics: list[Topic],
    difficulty: Difficulty,
    question_type: QuestionType,
    num_questions: int,
) -> list[GeneratedQuestion]:
    prompt = _build_llm_prompt(
        topics=topics,
        difficulty=difficulty,
        question_type=question_type,
        num_questions=num_questions,
    )
    llm_response = ollama_client.generate_json(prompt=prompt, response_model=LLMGeneratedQuestions, max_retries=2)
    if not llm_response or len(llm_response.questions) != num_questions:
        return _deduplicate_questions(
            _fallback_questions(
                topics=topics,
                difficulty=difficulty,
                question_type=question_type,
                num_questions=num_questions,
            )
        )

    generated: list[GeneratedQuestion] = []
    for question in llm_response.questions:
        if not _is_valid_generated_question(question):
            return _deduplicate_questions(
                _fallback_questions(
                    topics=topics,
                    difficulty=difficulty,
                    question_type=question_type,
                    num_questions=num_questions,
                )
            )
        generated.append(
            GeneratedQuestion(
                type=question.type,
                topic_tags=question.topic_tags,
                difficulty=question.difficulty,
                prompt=question.prompt,
                options=question.options,
                correct_option_index=question.correct_option_index,
                expected_answer=question.expected_answer,
                acceptable_variants=question.acceptable_variants,
                grading_rubric=question.grading_rubric,
                explanation=question.explanation,
            )
        )

    return _deduplicate_questions(generated)
