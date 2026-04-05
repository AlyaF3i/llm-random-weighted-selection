from __future__ import annotations

from llm_personality_experiment.scoring.models import AgentMetrics, ScoreObservation
from llm_personality_experiment.scoring.scoring import compute_raw_scores
from llm_personality_experiment.scoring.updates import update_metrics
from llm_personality_experiment.tasks.models import ExamSolution
from llm_personality_experiment.tasks.verifier import VerificationResult


def test_compute_raw_scores_for_perfect_exam() -> None:
    solution = ExamSolution(answer_key={"q1": "5"}, total_points=1, question_count=1)
    verification = VerificationResult(
        json_valid=True,
        schema_valid=True,
        parsed_output={"submission": {"answers": [{"question_id": "q1", "answer": "5"}], "feedback": "Great work!"}},
        answers={"q1": "5"},
        feedback="Great work!",
        answered_count=1,
        correct_count=1,
        score_earned=1,
        total_points=1,
        correctness_score=1.0,
        completeness_score=1.0,
        supportiveness_score=0.8,
        reliability=1.0,
        failure_types=(),
    )

    observation = compute_raw_scores(solution, verification)

    assert observation == ScoreObservation(1.0, 1.0, 0.8, 1.0)


def test_update_metrics_uses_baseline_sensitive_rates(config) -> None:
    current = AgentMetrics(correctness=0.4, completeness=0.6, supportiveness=0.4, reliability=0.6)
    observation = ScoreObservation(correctness=1.0, completeness=0.0, supportiveness=1.0, reliability=0.0)

    updated = update_metrics(current, observation, config.metrics, config.updates)

    assert round(updated.correctness, 4) == 0.472
    assert round(updated.completeness, 4) == 0.552
    assert round(updated.supportiveness, 4) == 0.472
    assert round(updated.reliability, 4) == 0.552
