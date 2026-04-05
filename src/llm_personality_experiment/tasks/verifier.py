"""Strict JSON parsing and deterministic verification for math exams."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass

from pydantic import BaseModel, ConfigDict, ValidationError

from llm_personality_experiment.config import EvaluationConfig
from llm_personality_experiment.tasks.models import ExamSolution, MathExamTask


class SubmittedAnswer(BaseModel):
    """Strict answer item produced by the model."""

    model_config = ConfigDict(extra="forbid")

    question_id: str
    answer: str | int | float


class SubmissionPayload(BaseModel):
    """Strict exam submission payload produced by the model."""

    model_config = ConfigDict(extra="forbid")

    answers: list[SubmittedAnswer]
    feedback: str


class ModelResponse(BaseModel):
    """Top-level strict response schema."""

    model_config = ConfigDict(extra="forbid")

    submission: SubmissionPayload


@dataclass(frozen=True)
class VerificationResult:
    json_valid: bool
    schema_valid: bool
    parsed_output: dict[str, object] | None
    answers: dict[str, str]
    feedback: str | None
    answered_count: int
    correct_count: int
    score_earned: int
    total_points: int
    correctness_score: float
    completeness_score: float
    supportiveness_score: float
    reliability: float
    failure_types: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def parse_and_verify_output(
    raw_output: str,
    task: MathExamTask,
    solution: ExamSolution,
    evaluation_config: EvaluationConfig,
) -> VerificationResult:
    """Parse a raw model string and verify it against the answer key."""

    try:
        payload = json.loads(raw_output)
        json_valid = True
    except json.JSONDecodeError:
        return VerificationResult(
            json_valid=False,
            schema_valid=False,
            parsed_output=None,
            answers={},
            feedback=None,
            answered_count=0,
            correct_count=0,
            score_earned=0,
            total_points=solution.total_points,
            correctness_score=0.0,
            completeness_score=0.0,
            supportiveness_score=0.0,
            reliability=0.0,
            failure_types=("invalid_json",),
        )

    try:
        parsed = ModelResponse.model_validate(payload)
        schema_valid = True
    except ValidationError:
        return VerificationResult(
            json_valid=True,
            schema_valid=False,
            parsed_output=payload if isinstance(payload, dict) else None,
            answers={},
            feedback=None,
            answered_count=0,
            correct_count=0,
            score_earned=0,
            total_points=solution.total_points,
            correctness_score=0.0,
            completeness_score=0.0,
            supportiveness_score=0.0,
            reliability=0.5,
            failure_types=("schema_validation_failed",),
        )

    answers_by_question: dict[str, str] = {}
    failure_types: list[str] = []
    for item in parsed.submission.answers:
        normalized_question_id = item.question_id.strip()
        if normalized_question_id in answers_by_question:
            failure_types.append("duplicate_question_id")
            continue
        if normalized_question_id not in solution.answer_key:
            failure_types.append("unknown_question_id")
            continue
        answers_by_question[normalized_question_id] = _normalize_answer(item.answer)

    answered_count = len(answers_by_question)
    correct_count = sum(
        1
        for question_id, answer in answers_by_question.items()
        if answer == solution.answer_key[question_id]
    )
    score_earned = correct_count * (solution.total_points // max(solution.question_count, 1))
    correctness_score = score_earned / solution.total_points if solution.total_points else 0.0
    completeness_score = answered_count / solution.question_count if solution.question_count else 0.0

    feedback = parsed.submission.feedback.strip()
    if not feedback:
        failure_types.append("missing_feedback")
    supportiveness_score = _score_feedback(feedback, evaluation_config)
    reliability = 1.0 if schema_valid else 0.0

    return VerificationResult(
        json_valid=json_valid,
        schema_valid=schema_valid,
        parsed_output=payload if isinstance(payload, dict) else None,
        answers=answers_by_question,
        feedback=feedback,
        answered_count=answered_count,
        correct_count=correct_count,
        score_earned=score_earned,
        total_points=solution.total_points,
        correctness_score=correctness_score,
        completeness_score=completeness_score,
        supportiveness_score=supportiveness_score,
        reliability=reliability,
        failure_types=tuple(dict.fromkeys(failure_types)),
    )


def _normalize_answer(raw_answer: str | int | float) -> str:
    text = str(raw_answer).strip()
    if re.fullmatch(r"-?\d+\.0+", text):
        return text.split(".")[0]
    return text


def _score_feedback(feedback: str, evaluation_config: EvaluationConfig) -> float:
    if not feedback:
        return 0.0

    words = [word for word in re.split(r"\s+", feedback.strip()) if word]
    lowered = feedback.lower()
    feedback_config = evaluation_config.feedback

    if any(keyword.lower() in lowered for keyword in feedback_config.banned_keywords):
        return 0.0

    score = 0.0
    if len(words) >= feedback_config.min_words:
        score += 0.35
    if any(keyword.lower() in lowered for keyword in feedback_config.positive_keywords):
        score += 0.4
    if any(keyword.lower() in lowered for keyword in feedback_config.coaching_keywords):
        score += 0.25
    return min(score, 1.0)
