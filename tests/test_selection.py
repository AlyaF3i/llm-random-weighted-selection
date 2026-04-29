from __future__ import annotations

import random
from pathlib import Path

import pytest

from llm_personality_experiment.agents.models import AgentState, PersonalityDefinition
from llm_personality_experiment.agents.sampling import SamplingParameters
from llm_personality_experiment.scoring.models import AgentMetrics, ScoreObservation
from llm_personality_experiment.scoring.selection import (
    compute_probabilities,
    compute_weight,
    compute_weights_by_agent,
    initialize_exponential_weights,
    select_agents,
    update_exponential_weights,
)


def _agent(name: str, correctness: float) -> AgentState:
    return AgentState(
        name=name,
        personality=PersonalityDefinition(
            name=name,
            prompt_text="prompt",
            source_path=Path("."),
            sampling_parameters=SamplingParameters(temperature=0.1, p_sample=0.3, k_sample=10),
        ),
        metrics=AgentMetrics(
            correctness=correctness,
            completeness=0.5,
            supportiveness=0.5,
            reliability=0.5,
        ),
    )


def test_compute_weight_uses_weighted_average() -> None:
    weight = compute_weight(
        metrics={
            "correctness": 1.0,
            "completeness": 0.5,
            "supportiveness": 0.0,
            "reliability": 0.5,
        },
        metric_weights={
            "correctness": 0.4,
            "completeness": 0.2,
            "supportiveness": 0.2,
            "reliability": 0.2,
        },
    )

    assert weight == pytest.approx(0.6)


def test_compute_probabilities_normalizes_weights() -> None:
    probabilities = compute_probabilities({"a": 0.2, "b": 0.3, "c": 0.5})

    assert probabilities == {"a": 0.2, "b": 0.3, "c": 0.5}


def test_select_agents_can_explore() -> None:
    rng = random.Random(7)
    agents = [_agent("a", 0.2), _agent("b", 0.9)]

    outcome = select_agents(
        agents=agents,
        metric_weights={
            "correctness": 1.0,
            "completeness": 0.0,
            "supportiveness": 0.0,
            "reliability": 0.0,
        },
        epsilon=1.0,
        agents_per_task=2,
        rng=rng,
    )

    assert outcome.explored is True
    assert set(outcome.selected_agents) == {"a", "b"}


def test_compute_weights_by_agent_uses_stored_selection_weight_for_exponential_rule() -> None:
    agents = [_agent("a", 0.2), _agent("b", 0.9)]
    agents[0].selection_weight = 0.25
    agents[1].selection_weight = 0.75

    weights = compute_weights_by_agent(
        agents=agents,
        metric_weights={
            "correctness": 1.0,
            "completeness": 0.0,
            "supportiveness": 0.0,
            "reliability": 0.0,
        },
        weight_update_rule="exponential",
    )

    assert weights == {"a": 0.25, "b": 0.75}


def test_exponential_weight_update_increases_better_agent_share() -> None:
    agents = [_agent("a", 0.5), _agent("b", 0.5)]
    initialize_exponential_weights(
        agents=agents,
        metric_weights={
            "correctness": 1.0,
            "completeness": 0.0,
            "supportiveness": 0.0,
            "reliability": 0.0,
        },
    )

    update_exponential_weights(
        agents=agents,
        observations_by_agent={
            "a": ScoreObservation(correctness=1.0, completeness=0.0, supportiveness=0.0, reliability=0.0),
            "b": ScoreObservation(correctness=0.0, completeness=0.0, supportiveness=0.0, reliability=0.0),
        },
        metric_weights={
            "correctness": 1.0,
            "completeness": 0.0,
            "supportiveness": 0.0,
            "reliability": 0.0,
        },
        eta=1.5,
    )

    assert agents[0].selection_weight > agents[1].selection_weight
    assert sum(agent.selection_weight for agent in agents) == pytest.approx(1.0)
