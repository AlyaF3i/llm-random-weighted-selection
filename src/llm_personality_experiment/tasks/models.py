"""Shared math-exam task models."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum


class ScenarioType(str, Enum):
    ADDITION = "addition"
    SUBTRACTION = "subtraction"
    MULTIPLICATION = "multiplication"
    MIXED_REVIEW = "mixed_review"


class OperationType(str, Enum):
    ADDITION = "addition"
    SUBTRACTION = "subtraction"
    MULTIPLICATION = "multiplication"


@dataclass(frozen=True)
class MathQuestion:
    question_id: str
    prompt: str
    operation: OperationType
    operands: tuple[int, int]
    points: int

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["operation"] = self.operation.value
        return payload


@dataclass(frozen=True)
class MathExamTask:
    task_id: str
    iteration: int
    seed: int
    scenario_type: ScenarioType
    grade_label: str
    instructions: str
    questions: tuple[MathQuestion, ...]
    total_points: int

    def to_dict(self) -> dict[str, object]:
        return {
            "task_id": self.task_id,
            "iteration": self.iteration,
            "seed": self.seed,
            "scenario_type": self.scenario_type.value,
            "grade_label": self.grade_label,
            "instructions": self.instructions,
            "questions": [question.to_dict() for question in self.questions],
            "total_points": self.total_points,
        }


@dataclass(frozen=True)
class ExamSolution:
    answer_key: dict[str, str]
    total_points: int
    question_count: int

    def to_dict(self) -> dict[str, object]:
        return asdict(self)
