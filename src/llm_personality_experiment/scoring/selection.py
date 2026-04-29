"""Weighted sampling with epsilon exploration."""

from __future__ import annotations

import math
import random

from llm_personality_experiment.agents.models import AgentState
from llm_personality_experiment.scoring.models import ScoreObservation, SelectionOutcome


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
    weight_update_rule: str = "metric_average",
) -> dict[str, float]:
    """Compute the current selection weights for all agents."""

    # START: WEIGHT COMPUTATION FOR ALL AGENTS
    if weight_update_rule == "metric_average":
        weights_by_agent = {
            agent.name: compute_weight(agent.metrics.to_dict(), metric_weights)
            for agent in agents
        }
    elif weight_update_rule == "exponential":
        weights_by_agent = {
            agent.name: max(float(agent.selection_weight), 1e-12)
            for agent in agents
        }
    else:
        raise ValueError(f"Unsupported weight_update_rule: {weight_update_rule}")
    # END: WEIGHT COMPUTATION FOR ALL AGENTS
    return weights_by_agent


def compute_probabilities(weights: dict[str, float]) -> dict[str, float]:
    """Normalize agent weights into probabilities."""

    total_weight = sum(weights.values())
    if total_weight <= 0:
        uniform_probability = 1.0 / len(weights)
        return {name: uniform_probability for name in weights}
    return {name: value / total_weight for name, value in weights.items()}


def select_agents(
    agents: list[AgentState],
    metric_weights: dict[str, float],
    epsilon: float,
    agents_per_task: int,
    rng: random.Random,
    weight_update_rule: str = "metric_average",
) -> SelectionOutcome:
    """Select `k` agents by epsilon-greedy weighted random sampling without replacement."""

    if agents_per_task > len(agents):
        raise ValueError("agents_per_task cannot exceed the number of available agents")

    # START: PREPARE WEIGHTS AND PROBABILITIES FOR SELECTION
    weights = compute_weights_by_agent(agents, metric_weights, weight_update_rule=weight_update_rule)
    probabilities = compute_probabilities(weights)
    # END: PREPARE WEIGHTS AND PROBABILITIES FOR SELECTION

    # START: EPSILON EXPLORATION VS WEIGHTED EXPLOITATION
    if rng.random() < epsilon:
        # START: EPSILON EXPLORATION BRANCH
        selected_agents = tuple(agent.name for agent in rng.sample(agents, k=agents_per_task))
        explored = True
        # END: EPSILON EXPLORATION BRANCH
    else:
        # START: WEIGHTED SAMPLING WITHOUT REPLACEMENT
        remaining_names = [agent.name for agent in agents]
        selected_names: list[str] = []
        while len(selected_names) < agents_per_task:
            remaining_probabilities = compute_probabilities({name: probabilities[name] for name in remaining_names})
            chosen_name = rng.choices(
                remaining_names,
                weights=[remaining_probabilities[name] for name in remaining_names],
                k=1,
            )[0]
            selected_names.append(chosen_name)
            remaining_names.remove(chosen_name)
        selected_agents = tuple(selected_names)
        explored = False
        # END: WEIGHTED SAMPLING WITHOUT REPLACEMENT
    # END: EPSILON EXPLORATION VS WEIGHTED EXPLOITATION

    return SelectionOutcome(
        selected_agents=selected_agents,
        explored=explored,
        probabilities=probabilities,
        weights=weights,
    )


def initialize_exponential_weights(
    agents: list[AgentState],
    metric_weights: dict[str, float],
) -> None:
    """Initialize direct selection weights from the current metric state."""

    initial_weights = compute_weights_by_agent(agents, metric_weights, weight_update_rule="metric_average")
    total_weight = sum(initial_weights.values())
    if total_weight <= 0:
        uniform_weight = 1.0 / len(agents)
        for agent in agents:
            agent.selection_weight = uniform_weight
        return

    for agent in agents:
        agent.selection_weight = initial_weights[agent.name] / total_weight


def update_exponential_weights(
    agents: list[AgentState],
    observations_by_agent: dict[str, ScoreObservation],
    metric_weights: dict[str, float],
    eta: float,
) -> None:
    """Apply multiplicative exponential updates and renormalize the selection weights."""

    updated_values: dict[str, float] = {}
    for agent in agents:
        reward = 0.0
        if agent.name in observations_by_agent:
            reward = compute_weight(observations_by_agent[agent.name].to_dict(), metric_weights)
        updated_values[agent.name] = max(agent.selection_weight, 1e-12) * math.exp(eta * reward)

    normalized_weights = compute_probabilities(updated_values)
    for agent in agents:
        agent.selection_weight = normalized_weights[agent.name]
