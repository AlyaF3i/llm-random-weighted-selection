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

    # START: BASELINE-AWARE METRIC UPDATE FOR ALL TRACKED METRICS
    baseline = AgentMetrics.from_dict(defaults.baseline)
    updated_metrics = AgentMetrics(
        correctness=_update_value(current.correctness, observation.correctness, baseline.correctness, defaults, rules),
        completeness=_update_value(current.completeness, observation.completeness, baseline.completeness, defaults, rules),
        supportiveness=_update_value(current.supportiveness, observation.supportiveness, baseline.supportiveness, defaults, rules),
        reliability=_update_value(current.reliability, observation.reliability, baseline.reliability, defaults, rules),
    )
    # END: BASELINE-AWARE METRIC UPDATE FOR ALL TRACKED METRICS
    return updated_metrics


def _update_value(
    current_value: float,
    observed_value: float,
    baseline: float,
    defaults: MetricDefaultsConfig,
    rules: UpdateRulesConfig,
) -> float:
    # START: SINGLE METRIC UPDATE RULE
    band = rules.above_baseline if current_value >= baseline else rules.below_baseline
    if observed_value >= current_value:
        updated_value = current_value + band.increase_rate * (observed_value - current_value)
    else:
        updated_value = current_value - band.decrease_rate * (current_value - observed_value)
    clamped_value = max(defaults.min_value, min(defaults.max_value, updated_value))
    # END: SINGLE METRIC UPDATE RULE
    return clamped_value
