"""Scoring dataclasses."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class AgentMetrics:
    """Per-agent metric state."""

    efficiency: float
    honesty: float
    discernment: float
    reliability: float

    @classmethod
    def from_dict(cls, payload: dict[str, float]) -> "AgentMetrics":
        return cls(
            efficiency=float(payload["efficiency"]),
            honesty=float(payload["honesty"]),
            discernment=float(payload["discernment"]),
            reliability=float(payload["reliability"]),
        )

    def to_dict(self) -> dict[str, float]:
        return asdict(self)


@dataclass(frozen=True)
class ScoreObservation:
    """Raw or normalized observation for one iteration."""

    efficiency: float
    honesty: float
    discernment: float
    reliability: float

    @classmethod
    def from_dict(cls, payload: dict[str, float]) -> "ScoreObservation":
        return cls(
            efficiency=float(payload["efficiency"]),
            honesty=float(payload["honesty"]),
            discernment=float(payload["discernment"]),
            reliability=float(payload["reliability"]),
        )

    def to_dict(self) -> dict[str, float]:
        return asdict(self)


@dataclass(frozen=True)
class SelectionOutcome:
    """Selection decision metadata."""

    selected_agent: str
    explored: bool
    probabilities: dict[str, float]
    weights: dict[str, float]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)
