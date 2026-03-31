"""Normalization helpers for raw observations."""

from __future__ import annotations

from llm_personality_experiment.scoring.models import ScoreObservation


def normalize_observation(observation: ScoreObservation) -> ScoreObservation:
    """Clamp observations into the stable [0, 1] interval."""

    return ScoreObservation(
        efficiency=_clamp(observation.efficiency),
        honesty=_clamp(observation.honesty),
        discernment=_clamp(observation.discernment),
        reliability=_clamp(observation.reliability),
    )


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))
