from __future__ import annotations

import random
from pathlib import Path

import pytest

from llm_personality_experiment.agents.models import AgentState, PersonalityDefinition
from llm_personality_experiment.scoring.models import AgentMetrics
from llm_personality_experiment.scoring.selection import compute_probabilities, compute_weight, select_agents


def _agent(name: str, correctness: float) -> AgentState:
    return AgentState(
        name=name,
        personality=PersonalityDefinition(name=name, prompt_text="prompt", source_path=Path(".")),
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
