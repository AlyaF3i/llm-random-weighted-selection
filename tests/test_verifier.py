from __future__ import annotations

from llm_personality_experiment.config import EvaluationConfig
from llm_personality_experiment.tasks.models import MathExamTask, MathQuestion, OperationType, ScenarioType
from llm_personality_experiment.tasks.solver import solve_task
from llm_personality_experiment.tasks.verifier import parse_and_verify_output


def _task() -> MathExamTask:
    return MathExamTask(
        task_id="exam-1",
        iteration=1,
        seed=1,
        scenario_type=ScenarioType.ADDITION,
        grade_label="elementary school",
        instructions="Answer carefully.",
        questions=(
            MathQuestion("q1", "What is 2 + 3?", OperationType.ADDITION, (2, 3), 1),
            MathQuestion("q2", "What is 5 + 1?", OperationType.ADDITION, (5, 1), 1),
        ),
        total_points=2,
    )


def _evaluation_config() -> EvaluationConfig:
    return EvaluationConfig.model_validate(
        {
            "feedback": {
                "positive_keywords": ["great", "well done"],
                "coaching_keywords": ["keep practicing", "check"],
                "banned_keywords": ["bad", "stupid"],
                "min_words": 4,
            }
        }
    )


def test_verifier_accepts_valid_submission() -> None:
    task = _task()
    solution = solve_task(task)

    verification = parse_and_verify_output(
        raw_output='{"submission":{"answers":[{"question_id":"q1","answer":"5"},{"question_id":"q2","answer":"6"}],"feedback":"Great work, keep practicing every day."}}',
        task=task,
        solution=solution,
        evaluation_config=_evaluation_config(),
    )

    assert verification.json_valid is True
    assert verification.schema_valid is True
    assert verification.correct_count == 2
    assert verification.score_earned == 2
    assert verification.correctness_score == 1.0
    assert verification.completeness_score == 1.0
    assert verification.supportiveness_score > 0.0
    assert verification.failure_types == ()


def test_verifier_rejects_invalid_json() -> None:
    task = _task()
    solution = solve_task(task)

    verification = parse_and_verify_output(
        raw_output="not json",
        task=task,
        solution=solution,
        evaluation_config=_evaluation_config(),
    )

    assert verification.json_valid is False
    assert verification.failure_types == ("invalid_json",)


def test_verifier_detects_duplicate_question_ids() -> None:
    task = _task()
    solution = solve_task(task)

    verification = parse_and_verify_output(
        raw_output='{"submission":{"answers":[{"question_id":"q1","answer":"5"},{"question_id":"q1","answer":"7"}],"feedback":"Great work, keep practicing."}}',
        task=task,
        solution=solution,
        evaluation_config=_evaluation_config(),
    )

    assert "duplicate_question_id" in verification.failure_types
    assert verification.answered_count == 1


def test_verifier_supportiveness_drops_with_banned_language() -> None:
    task = _task()
    solution = solve_task(task)

    verification = parse_and_verify_output(
        raw_output='{"submission":{"answers":[{"question_id":"q1","answer":"5"}],"feedback":"Bad work, check again."}}',
        task=task,
        solution=solution,
        evaluation_config=_evaluation_config(),
    )

    assert verification.supportiveness_score == 0.0
