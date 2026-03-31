from __future__ import annotations

from llm_personality_experiment.tasks.models import NavigationTask, ScenarioType, TaskConstraints
from llm_personality_experiment.tasks.solver import evaluate_moves, solve_task


def test_solver_finds_shortest_path() -> None:
    task = NavigationTask(
        task_id="solver-shortest",
        iteration=1,
        seed=1,
        scenario_type=ScenarioType.SOLVABLE,
        min_position=0,
        max_position=4,
        start=0,
        goal=4,
        allowed_moves={"+1": 1, "+2": 2},
        constraints=TaskConstraints(),
    )

    result = solve_task(task)

    assert result.solvable is True
    assert result.optimal_moves == ("+2", "+2")
    assert result.optimal_length == 2


def test_solver_detects_unsolvable_due_to_max_moves() -> None:
    task = NavigationTask(
        task_id="solver-unsat",
        iteration=1,
        seed=1,
        scenario_type=ScenarioType.UNSOLVABLE,
        min_position=0,
        max_position=4,
        start=0,
        goal=4,
        allowed_moves={"+1": 1},
        constraints=TaskConstraints(max_moves=3),
    )

    result = solve_task(task)

    assert result.solvable is False
    assert result.optimal_moves == ()
    assert result.optimal_length is None


def test_evaluate_moves_detects_constraint_violation() -> None:
    task = NavigationTask(
        task_id="solver-constraint",
        iteration=1,
        seed=1,
        scenario_type=ScenarioType.CONSTRAINT_HEAVY,
        min_position=0,
        max_position=4,
        start=0,
        goal=4,
        allowed_moves={"+1": 1, "+2": 2},
        constraints=TaskConstraints(forbidden_positions=(2,)),
    )

    evaluation = evaluate_moves(task, ("+2", "+2"))

    assert evaluation.valid is False
    assert evaluation.violated_forbidden_position is True
    assert "forbidden_position" in evaluation.failure_reasons
