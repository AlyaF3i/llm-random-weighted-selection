"""Shared task models."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum


class ScenarioType(str, Enum):
    SOLVABLE = "solvable"
    UNSOLVABLE = "unsolvable"
    TRAP = "trap"
    CONSTRAINT_HEAVY = "constraint_heavy"


@dataclass(frozen=True)
class TaskConstraints:
    checkpoints: tuple[int, ...] = ()
    max_moves: int | None = None
    forbidden_positions: tuple[int, ...] = ()
    required_moves: tuple[str, ...] = ()
    forbidden_move_patterns: tuple[tuple[str, ...], ...] = ()
    no_revisits: bool = False

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class NavigationTask:
    task_id: str
    iteration: int
    seed: int
    scenario_type: ScenarioType
    min_position: int
    max_position: int
    start: int
    goal: int
    allowed_moves: dict[str, int]
    constraints: TaskConstraints

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["scenario_type"] = self.scenario_type.value
        return payload


@dataclass(frozen=True)
class PathEvaluation:
    valid: bool
    goal_reached: bool
    final_position: int
    visited_positions: tuple[int, ...]
    checkpoints_satisfied: bool
    required_moves_satisfied: bool
    max_moves_satisfied: bool
    violated_forbidden_position: bool
    violated_forbidden_pattern: bool
    revisited_position: bool
    invalid_move: bool
    failure_reasons: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class SolverResult:
    solvable: bool
    optimal_moves: tuple[str, ...]
    optimal_length: int | None
    explored_states: int

    def to_dict(self) -> dict[str, object]:
        return asdict(self)
