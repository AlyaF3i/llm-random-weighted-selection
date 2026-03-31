"""Metric update rules."""

from __future__ import annotations

from llm_personality_experiment.config import MetricDefaultsConfig, UpdateRulesConfig
from llm_personality_experiment.scoring.models import AgentMetrics, ScoreObservation


def update_metrics(
    current: AgentMetrics,
    observation: ScoreObservation,
    defaults: MetricDefaultsConfig,
    rules: UpdateRulesConfig,
) -> AgentMetrics:
    """Update every metric using the configured baseline-aware rates."""

    baseline = AgentMetrics.from_dict(defaults.baseline)
    return AgentMetrics(
        efficiency=_update_value(current.efficiency, observation.efficiency, baseline.efficiency, defaults, rules),
        honesty=_update_value(current.honesty, observation.honesty, baseline.honesty, defaults, rules),
        discernment=_update_value(current.discernment, observation.discernment, baseline.discernment, defaults, rules),
        reliability=_update_value(current.reliability, observation.reliability, baseline.reliability, defaults, rules),
    )


def _update_value(
    current_value: float,
    observed_value: float,
    baseline: float,
    defaults: MetricDefaultsConfig,
    rules: UpdateRulesConfig,
) -> float:
    band = rules.above_baseline if current_value >= baseline else rules.below_baseline
    if observed_value >= current_value:
        updated_value = current_value + band.increase_rate * (observed_value - current_value)
    else:
        updated_value = current_value - band.decrease_rate * (current_value - observed_value)
    return max(defaults.min_value, min(defaults.max_value, updated_value))
