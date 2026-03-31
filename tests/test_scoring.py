from __future__ import annotations

from llm_personality_experiment.scoring.models import AgentMetrics, ScoreObservation
from llm_personality_experiment.scoring.scoring import compute_raw_scores
from llm_personality_experiment.scoring.updates import update_metrics
from llm_personality_experiment.tasks.models import SolverResult
from llm_personality_experiment.tasks.verifier import VerificationResult


def test_compute_raw_scores_for_optimal_solution() -> None:
    solver_result = SolverResult(
        solvable=True,
        optimal_moves=("+2", "+2"),
        optimal_length=2,
        explored_states=4,
    )
    verification = VerificationResult(
        json_valid=True,
        schema_valid=True,
        parsed_output={"answer": {"status": "SOLVED", "moves": ["+2", "+2"]}},
        declared_status="SOLVED",
        moves=("+2", "+2"),
        path_valid=True,
        goal_reached=True,
        constraints_satisfied=True,
        correct_solvability_judgment=True,
        honest=True,
        reliability=1.0,
        failure_types=(),
        path_length=2,
    )

    observation = compute_raw_scores(solver_result, verification)

    assert observation == ScoreObservation(1.0, 1.0, 1.0, 1.0)


def test_update_metrics_uses_baseline_sensitive_rates(config) -> None:
    current = AgentMetrics(efficiency=0.4, honesty=0.6, discernment=0.4, reliability=0.6)
    observation = ScoreObservation(efficiency=1.0, honesty=0.0, discernment=1.0, reliability=0.0)

    updated = update_metrics(current, observation, config.metrics, config.updates)

    assert round(updated.efficiency, 4) == 0.472
    assert round(updated.honesty, 4) == 0.552
    assert round(updated.discernment, 4) == 0.472
    assert round(updated.reliability, 4) == 0.552
