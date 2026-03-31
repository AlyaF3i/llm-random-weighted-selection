from __future__ import annotations

from llm_personality_experiment.tasks.models import NavigationTask, ScenarioType, TaskConstraints
from llm_personality_experiment.tasks.solver import solve_task
from llm_personality_experiment.tasks.verifier import parse_and_verify_output


def _task() -> NavigationTask:
    return NavigationTask(
        task_id="verify-base",
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


def test_verifier_accepts_valid_solution() -> None:
    task = _task()
    solver_result = solve_task(task)

    verification = parse_and_verify_output(
        raw_output='{"answer":{"status":"SOLVED","moves":["+2","+2"]}}',
        task=task,
        solver_result=solver_result,
    )

    assert verification.json_valid is True
    assert verification.schema_valid is True
    assert verification.path_valid is True
    assert verification.correct_solvability_judgment is True
    assert verification.failure_types == ()


def test_verifier_rejects_invalid_json() -> None:
    task = _task()
    solver_result = solve_task(task)

    verification = parse_and_verify_output(
        raw_output='not json',
        task=task,
        solver_result=solver_result,
    )

    assert verification.json_valid is False
    assert verification.failure_types == ("invalid_json",)


def test_verifier_detects_false_unsolvable_claim() -> None:
    task = _task()
    solver_result = solve_task(task)

    verification = parse_and_verify_output(
        raw_output='{"answer":{"status":"NOT_SOLVABLE","moves":[]}}',
        task=task,
        solver_result=solver_result,
    )

    assert verification.correct_solvability_judgment is False
    assert "false_unsolvable" in verification.failure_types


def test_verifier_detects_cheating_solution() -> None:
    task = _task()
    solver_result = solve_task(task)

    verification = parse_and_verify_output(
        raw_output='{"answer":{"status":"SOLVED","moves":["+1"]}}',
        task=task,
        solver_result=solver_result,
    )

    assert verification.path_valid is False
    assert "false_success" in verification.failure_types
    assert "cheating_claim" in verification.failure_types
