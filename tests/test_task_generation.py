from __future__ import annotations

from dataclasses import replace

from llm_personality_experiment.tasks.generator import TaskGenerator
from llm_personality_experiment.tasks.models import ScenarioType, TaskConstraints
from llm_personality_experiment.tasks.solver import solve_task


def test_task_generation_is_deterministic(config) -> None:
    generator_a = TaskGenerator(config)
    generator_b = TaskGenerator(config)

    tasks_a = [
        generator_a.generate(iteration=iteration, scenario_type=ScenarioType.SOLVABLE).to_dict()
        for iteration in range(1, 4)
    ]
    tasks_b = [
        generator_b.generate(iteration=iteration, scenario_type=ScenarioType.SOLVABLE).to_dict()
        for iteration in range(1, 4)
    ]

    assert tasks_a == tasks_b


def test_generated_scenario_labels_match_solver(config) -> None:
    generator = TaskGenerator(config)

    solvable_task = generator.generate(iteration=1, scenario_type=ScenarioType.SOLVABLE)
    unsolvable_task = generator.generate(iteration=2, scenario_type=ScenarioType.UNSOLVABLE)
    trap_task = generator.generate(iteration=3, scenario_type=ScenarioType.TRAP)
    constraint_task = generator.generate(iteration=4, scenario_type=ScenarioType.CONSTRAINT_HEAVY)

    assert solve_task(solvable_task).solvable is True
    assert solve_task(unsolvable_task).solvable is False
    assert solve_task(trap_task).solvable is True
    assert trap_task.constraints.forbidden_positions
    assert solve_task(constraint_task).solvable is True
    assert constraint_task.constraints.checkpoints
    assert constraint_task.constraints.required_moves
    assert constraint_task.constraints.forbidden_move_patterns
    assert constraint_task.constraints.no_revisits is True


def test_unsolvable_task_becomes_solvable_without_tight_move_limit(config) -> None:
    generator = TaskGenerator(config)
    task = generator.generate(iteration=10, scenario_type=ScenarioType.UNSOLVABLE)

    relaxed_task = replace(task, constraints=TaskConstraints())

    assert solve_task(task).solvable is False
    assert solve_task(relaxed_task).solvable is True
