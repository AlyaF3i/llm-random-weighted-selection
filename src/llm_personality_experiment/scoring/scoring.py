"""Observation scoring from math-exam verification outcomes."""

from __future__ import annotations

from llm_personality_experiment.scoring.models import ScoreObservation
from llm_personality_experiment.tasks.models import ExamSolution
from llm_personality_experiment.tasks.verifier import VerificationResult


def compute_raw_scores(
    solver_result: ExamSolution,
    verification_result: VerificationResult,
) -> ScoreObservation:
    """Map deterministic verification data to metric observations."""

    _ = solver_result
    correctness = verification_result.correctness_score
    completeness = verification_result.completeness_score
    supportiveness = verification_result.supportiveness_score
    reliability = verification_result.reliability

    return ScoreObservation(
        correctness=correctness,
        completeness=completeness,
        supportiveness=supportiveness,
        reliability=reliability,
    )
