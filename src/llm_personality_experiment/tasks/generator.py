"""Deterministic task generator for 1D navigation scenarios."""

from __future__ import annotations

from dataclasses import replace
from itertools import product
from typing import Iterable

from llm_personality_experiment.config import ExperimentConfig
from llm_personality_experiment.tasks.models import NavigationTask, ScenarioType, SolverResult, TaskConstraints
from llm_personality_experiment.tasks.solver import evaluate_moves, solve_task
from llm_personality_experiment.utils.seed import create_rng


def format_move_label(step: int) -> str:
    """Convert an integer step into a canonical string label."""

    return f"{step:+d}"


class TaskGenerator:
    """Generate scenario-labelled tasks reproducibly from the config."""

    def __init__(self, config: ExperimentConfig) -> None:
        self._config = config

    def generate(self, iteration: int, scenario_type: ScenarioType | None = None) -> NavigationTask:
        """Generate one validated task for the given iteration."""

        rng = create_rng(self._config.seed + (iteration * 7919))
        chosen_scenario = scenario_type or self._sample_scenario(rng)
        factory_map = {
            ScenarioType.SOLVABLE: self._build_solvable_task,
            ScenarioType.UNSOLVABLE: self._build_unsolvable_task,
            ScenarioType.TRAP: self._build_trap_task,
            ScenarioType.CONSTRAINT_HEAVY: self._build_constraint_heavy_task,
        }
        return factory_map[chosen_scenario](iteration, rng)

    def _sample_scenario(self, rng: object) -> ScenarioType:
        weights = self._config.scenario_mix
        total = sum(weights.values())
        threshold = getattr(rng, "random")() * total
        cumulative = 0.0
        for key, weight in weights.items():
            cumulative += weight
            if threshold <= cumulative:
                return ScenarioType(key)
        return ScenarioType(next(iter(weights)))

    def _build_solvable_task(self, iteration: int, rng: object) -> NavigationTask:
        attempts = self._config.task_generation.difficulty.max_generation_attempts
        for _ in range(attempts):
            task = self._base_task(iteration, rng, ScenarioType.SOLVABLE)
            solution = solve_task(task)
            if solution.solvable:
                return task
        raise RuntimeError("Unable to generate a solvable task within configured attempts")

    def _build_unsolvable_task(self, iteration: int, rng: object) -> NavigationTask:
        attempts = self._config.task_generation.difficulty.max_generation_attempts
        for _ in range(attempts):
            base_task = self._base_task(iteration, rng, ScenarioType.UNSOLVABLE)
            unconstrained_solution = solve_task(base_task)
            if not unconstrained_solution.solvable or unconstrained_solution.optimal_length is None:
                continue
            constrained_task = replace(
                base_task,
                constraints=TaskConstraints(
                    max_moves=max(0, unconstrained_solution.optimal_length - 1),
                ),
            )
            if not solve_task(constrained_task).solvable:
                return constrained_task
        raise RuntimeError("Unable to generate an unsolvable task within configured attempts")

    def _build_trap_task(self, iteration: int, rng: object) -> NavigationTask:
        attempts = self._config.task_generation.difficulty.max_generation_attempts
        for _ in range(attempts):
            base_task = self._base_task(
                iteration,
                rng,
                ScenarioType.TRAP,
                require_negative_move=True,
                min_positive_moves=2,
            )
            unconstrained_solution = solve_task(base_task)
            if not unconstrained_solution.solvable or unconstrained_solution.optimal_length is None:
                continue
            path_evaluation = evaluate_moves(base_task, unconstrained_solution.optimal_moves)
            intermediate_positions = [
                position
                for position in path_evaluation.visited_positions[1:-1]
                if position not in {base_task.start, base_task.goal}
            ]
            for forbidden_position in intermediate_positions:
                trapped_task = replace(
                    base_task,
                    constraints=TaskConstraints(forbidden_positions=(forbidden_position,)),
                )
                trapped_solution = solve_task(trapped_task)
                if trapped_solution.solvable and (
                    trapped_solution.optimal_length is not None
                    and trapped_solution.optimal_length > unconstrained_solution.optimal_length
                ):
                    return trapped_task
        raise RuntimeError("Unable to generate a trap task within configured attempts")

    def _build_constraint_heavy_task(self, iteration: int, rng: object) -> NavigationTask:
        attempts = self._config.task_generation.difficulty.max_generation_attempts
        slack_min = int(self._config.task_generation.constraint_presets["max_move_slack_min"])
        slack_max = int(self._config.task_generation.constraint_presets["max_move_slack_max"])

        for _ in range(attempts):
            base_task = self._base_task(
                iteration,
                rng,
                ScenarioType.CONSTRAINT_HEAVY,
                require_negative_move=True,
                min_positive_moves=2,
            )
            base_solution = solve_task(base_task)
            if not base_solution.solvable or base_solution.optimal_length is None:
                continue

            path_evaluation = evaluate_moves(base_task, base_solution.optimal_moves)
            path_positions = [
                position
                for position in path_evaluation.visited_positions[1:-1]
                if position not in {base_task.start, base_task.goal}
            ]
            if not path_positions:
                continue

            checkpoints_count = min(
                len(path_positions),
                int(self._config.task_generation.constraint_presets["checkpoints_max"]),
            )
            checkpoints = tuple(sorted(path_positions[:checkpoints_count]))
            required_moves = tuple(
                move_label
                for move_label in dict.fromkeys(base_solution.optimal_moves)
                if move_label in base_task.allowed_moves
            )
            if not required_moves:
                continue
            forbidden_pattern = self._find_absent_pattern(base_task.allowed_moves.keys(), base_solution.optimal_moves)
            if forbidden_pattern is None:
                continue

            constrained_task = replace(
                base_task,
                constraints=TaskConstraints(
                    checkpoints=checkpoints,
                    max_moves=base_solution.optimal_length + getattr(rng, "randint")(slack_min, slack_max),
                    required_moves=(required_moves[0],),
                    forbidden_move_patterns=(forbidden_pattern,),
                    no_revisits=True,
                ),
            )
            constrained_solution = solve_task(constrained_task)
            if constrained_solution.solvable and self._count_active_constraints(constrained_task.constraints) >= 4:
                return constrained_task
        raise RuntimeError("Unable to generate a constraint-heavy task within configured attempts")

    def _count_active_constraints(self, constraints: TaskConstraints) -> int:
        active_flags = [
            bool(constraints.checkpoints),
            constraints.max_moves is not None,
            bool(constraints.forbidden_positions),
            bool(constraints.required_moves),
            bool(constraints.forbidden_move_patterns),
            constraints.no_revisits,
        ]
        return sum(1 for value in active_flags if value)

    def _find_absent_pattern(
        self,
        move_labels: Iterable[str],
        existing_path: tuple[str, ...],
    ) -> tuple[str, ...] | None:
        path_pairs = {existing_path[index:index + 2] for index in range(max(len(existing_path) - 1, 0))}
        for candidate in product(move_labels, repeat=2):
            if candidate not in path_pairs:
                return tuple(candidate)
        return None

    def _base_task(
        self,
        iteration: int,
        rng: object,
        scenario_type: ScenarioType,
        require_negative_move: bool = False,
        min_positive_moves: int = 1,
    ) -> NavigationTask:
        available_moves = self._config.task_generation.available_moves
        difficulty = self._config.task_generation.difficulty

        while True:
            max_position = getattr(rng, "randint")(
                difficulty.position_upper_bound_min,
                difficulty.position_upper_bound_max,
            )
            move_count = getattr(rng, "randint")(difficulty.min_move_options, difficulty.max_move_options)
            sampled_moves = tuple(sorted(getattr(rng, "sample")(available_moves, k=move_count)))
            positive_moves = [move for move in sampled_moves if move > 0]
            negative_moves = [move for move in sampled_moves if move < 0]
            if len(positive_moves) < min_positive_moves:
                continue
            if require_negative_move and not negative_moves:
                continue

            allowed_moves = {format_move_label(step): step for step in sampled_moves}
            task = NavigationTask(
                task_id=f"task-{iteration:05d}-{scenario_type.value}",
                iteration=iteration,
                seed=self._config.seed + iteration,
                scenario_type=scenario_type,
                min_position=0,
                max_position=max_position,
                start=0,
                goal=max_position,
                allowed_moves=allowed_moves,
                constraints=TaskConstraints(),
            )
            return task
