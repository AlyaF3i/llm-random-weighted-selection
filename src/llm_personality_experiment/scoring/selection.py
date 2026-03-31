"""Weighted sampling with epsilon exploration."""

from __future__ import annotations

import random

from llm_personality_experiment.agents.models import AgentState
from llm_personality_experiment.scoring.models import SelectionOutcome


def compute_weight(metrics: dict[str, float], metric_weights: dict[str, float]) -> float:
    """Compute the weighted average score for one agent."""

    numerator = sum(metric_weights[key] * metrics[key] for key in metric_weights)
    denominator = sum(metric_weights.values())
    if denominator <= 0:
        raise ValueError("Metric weights must sum to a positive value")
    return numerator / denominator


def compute_weights_by_agent(
    agents: list[AgentState],
    metric_weights: dict[str, float],
) -> dict[str, float]:
    """Compute the current selection weights for all agents."""

    return {
        agent.name: compute_weight(agent.metrics.to_dict(), metric_weights)
        for agent in agents
    }


def compute_probabilities(weights: dict[str, float]) -> dict[str, float]:
    """Normalize agent weights into probabilities."""

    total_weight = sum(weights.values())
    if total_weight <= 0:
        uniform_probability = 1.0 / len(weights)
        return {name: uniform_probability for name in weights}
    return {name: value / total_weight for name, value in weights.items()}


def select_agent(
    agents: list[AgentState],
    metric_weights: dict[str, float],
    epsilon: float,
    rng: random.Random,
) -> SelectionOutcome:
    """Select one agent by epsilon-greedy weighted random sampling."""

    weights = compute_weights_by_agent(agents, metric_weights)
    probabilities = compute_probabilities(weights)
    if rng.random() < epsilon:
        selected_agent = rng.choice(agents).name
        explored = True
    else:
        population = [agent.name for agent in agents]
        weight_values = [probabilities[agent.name] for agent in agents]
        selected_agent = rng.choices(population, weights=weight_values, k=1)[0]
        explored = False
    return SelectionOutcome(
        selected_agent=selected_agent,
        explored=explored,
        probabilities=probabilities,
        weights=weights,
    )
