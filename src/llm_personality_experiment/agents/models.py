"""Agent-facing dataclasses."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from llm_personality_experiment.scoring.models import AgentMetrics


@dataclass(frozen=True)
class PersonalityDefinition:
    """Personality instructions loaded from disk."""

    name: str
    prompt_text: str
    source_path: Path

    def to_dict(self) -> dict[str, str]:
        return {
            "name": self.name,
            "source_path": str(self.source_path),
        }


@dataclass
class AgentState:
    """Mutable runtime state for one personality-driven agent."""

    name: str
    personality: PersonalityDefinition
    metrics: AgentMetrics
    interactions: int = 0

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "personality": self.personality.to_dict(),
            "metrics": self.metrics.to_dict(),
            "interactions": self.interactions,
        }
