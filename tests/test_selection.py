from __future__ import annotations

import random
from pathlib import Path

import pytest

from llm_personality_experiment.agents.models import AgentState, PersonalityDefinition
from llm_personality_experiment.scoring.models import AgentMetrics
from llm_personality_experiment.scoring.selection import compute_probabilities, compute_weight, select_agent


def _agent(name: str, efficiency: float) -> AgentState:
    return AgentState(
        name=name,
        personality=PersonalityDefinition(name=name, system_prompt="prompt", source_path=Path(".")),
        metrics=AgentMetrics(
            efficiency=efficiency,
            honesty=0.5,
            discernment=0.5,
            reliability=0.5,
        ),
    )


def test_compute_weight_uses_weighted_average() -> None:
    weight = compute_weight(
        metrics={
            "efficiency": 1.0,
            "honesty": 0.5,
            "discernment": 0.0,
            "reliability": 0.5,
        },
        metric_weights={
            "efficiency": 0.4,
            "honesty": 0.2,
            "discernment": 0.2,
            "reliability": 0.2,
        },
    )

    assert weight == pytest.approx(0.6)


def test_compute_probabilities_normalizes_weights() -> None:
    probabilities = compute_probabilities({"a": 0.2, "b": 0.3, "c": 0.5})

    assert probabilities == {"a": 0.2, "b": 0.3, "c": 0.5}


def test_select_agent_can_explore() -> None:
    rng = random.Random(7)
    agents = [_agent("a", 0.2), _agent("b", 0.9)]

    outcome = select_agent(
        agents=agents,
        metric_weights={
            "efficiency": 1.0,
            "honesty": 0.0,
            "discernment": 0.0,
            "reliability": 0.0,
        },
        epsilon=1.0,
        rng=rng,
    )

    assert outcome.explored is True
    assert outcome.selected_agent in {"a", "b"}
