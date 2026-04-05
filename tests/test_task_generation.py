from __future__ import annotations

from llm_personality_experiment.tasks.generator import TaskGenerator
from llm_personality_experiment.tasks.models import OperationType, ScenarioType


def test_task_generation_is_deterministic(config) -> None:
    generator_a = TaskGenerator(config)
    generator_b = TaskGenerator(config)

    tasks_a = [
        generator_a.generate(iteration=iteration, scenario_type=ScenarioType.ADDITION).to_dict()
        for iteration in range(1, 4)
    ]
    tasks_b = [
        generator_b.generate(iteration=iteration, scenario_type=ScenarioType.ADDITION).to_dict()
        for iteration in range(1, 4)
    ]

    assert tasks_a == tasks_b


def test_generated_addition_exam_only_contains_addition(config) -> None:
    generator = TaskGenerator(config)
    task = generator.generate(iteration=1, scenario_type=ScenarioType.ADDITION)

    assert task.scenario_type is ScenarioType.ADDITION
    assert all(question.operation is OperationType.ADDITION for question in task.questions)


def test_generated_mixed_exam_uses_supported_operations(config) -> None:
    generator = TaskGenerator(config)
    task = generator.generate(iteration=2, scenario_type=ScenarioType.MIXED_REVIEW)

    assert task.scenario_type is ScenarioType.MIXED_REVIEW
    assert all(
        question.operation in {OperationType.ADDITION, OperationType.SUBTRACTION, OperationType.MULTIPLICATION}
        for question in task.questions
    )
