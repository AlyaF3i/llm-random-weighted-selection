"""Deterministic task solver and path evaluator."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass

from llm_personality_experiment.tasks.models import NavigationTask, PathEvaluation, SolverResult


@dataclass(frozen=True)
class _SearchState:
    position: int
    checkpoints_visited: frozenset[int]
    required_moves_used: frozenset[str]
    visited_positions: frozenset[int]
    recent_moves: tuple[str, ...]


def evaluate_moves(task: NavigationTask, moves: tuple[str, ...] | list[str]) -> PathEvaluation:
    """Evaluate a move sequence against task bounds and constraints."""

    move_sequence = tuple(moves)
    position = task.start
    visited_positions = [task.start]
    checkpoints_visited = {task.start} if task.start in task.constraints.checkpoints else set()
    required_moves_used: set[str] = set()
    recent_moves: list[str] = []
    max_pattern_length = max((len(pattern) for pattern in task.constraints.forbidden_move_patterns), default=0)
    failure_reasons: list[str] = []
    invalid_move = False
    violated_forbidden_position = False
    violated_forbidden_pattern = False
    revisited_position = False

    if task.constraints.max_moves is not None and len(move_sequence) > task.constraints.max_moves:
        failure_reasons.append("max_moves_exceeded")

    for move_label in move_sequence:
        if move_label not in task.allowed_moves:
            invalid_move = True
            failure_reasons.append("invalid_move")
            break

        next_position = position + task.allowed_moves[move_label]
        if next_position < task.min_position or next_position > task.max_position:
            failure_reasons.append("out_of_bounds")
            break
        if next_position in task.constraints.forbidden_positions:
            violated_forbidden_position = True
            failure_reasons.append("forbidden_position")
            break
        if task.constraints.no_revisits and next_position in visited_positions:
            revisited_position = True
            failure_reasons.append("revisited_position")
            break

        if max_pattern_length > 0:
            candidate_recent_moves = tuple((recent_moves + [move_label])[-max_pattern_length:])
            if any(
                len(pattern) <= len(candidate_recent_moves)
                and candidate_recent_moves[-len(pattern):] == pattern
                for pattern in task.constraints.forbidden_move_patterns
            ):
                violated_forbidden_pattern = True
                failure_reasons.append("forbidden_pattern")
                break
            recent_moves = list(candidate_recent_moves)

        position = next_position
        visited_positions.append(position)
        if position in task.constraints.checkpoints:
            checkpoints_visited.add(position)
        if move_label in task.constraints.required_moves:
            required_moves_used.add(move_label)

    goal_reached = position == task.goal
    checkpoints_satisfied = all(checkpoint in checkpoints_visited for checkpoint in task.constraints.checkpoints)
    required_moves_satisfied = all(move in required_moves_used for move in task.constraints.required_moves)
    max_moves_satisfied = task.constraints.max_moves is None or len(move_sequence) <= task.constraints.max_moves

    if not goal_reached and "invalid_move" not in failure_reasons and "out_of_bounds" not in failure_reasons:
        failure_reasons.append("goal_not_reached")
    if goal_reached and not checkpoints_satisfied:
        failure_reasons.append("missing_checkpoint")
    if goal_reached and not required_moves_satisfied:
        failure_reasons.append("missing_required_move")

    valid = (
        not failure_reasons
        and goal_reached
        and checkpoints_satisfied
        and required_moves_satisfied
        and max_moves_satisfied
    )

    return PathEvaluation(
        valid=valid,
        goal_reached=goal_reached,
        final_position=position,
        visited_positions=tuple(visited_positions),
        checkpoints_satisfied=checkpoints_satisfied,
        required_moves_satisfied=required_moves_satisfied,
        max_moves_satisfied=max_moves_satisfied,
        violated_forbidden_position=violated_forbidden_position,
        violated_forbidden_pattern=violated_forbidden_pattern,
        revisited_position=revisited_position,
        invalid_move=invalid_move,
        failure_reasons=tuple(failure_reasons),
    )


def solve_task(task: NavigationTask) -> SolverResult:
    """Find the shortest valid solution using BFS under all task constraints."""

    max_pattern_length = max((len(pattern) for pattern in task.constraints.forbidden_move_patterns), default=0)
    initial_state = _SearchState(
        position=task.start,
        checkpoints_visited=frozenset({task.start} if task.start in task.constraints.checkpoints else set()),
        required_moves_used=frozenset(),
        visited_positions=frozenset({task.start}) if task.constraints.no_revisits else frozenset(),
        recent_moves=(),
    )
    queue: deque[tuple[_SearchState, tuple[str, ...]]] = deque([(initial_state, ())])
    seen: set[_SearchState] = {initial_state}
    explored_states = 0

    while queue:
        state, path = queue.popleft()
        explored_states += 1

        if (
            state.position == task.goal
            and all(checkpoint in state.checkpoints_visited for checkpoint in task.constraints.checkpoints)
            and all(move in state.required_moves_used for move in task.constraints.required_moves)
        ):
            return SolverResult(
                solvable=True,
                optimal_moves=path,
                optimal_length=len(path),
                explored_states=explored_states,
            )

        if task.constraints.max_moves is not None and len(path) >= task.constraints.max_moves:
            continue

        for move_label, delta in task.allowed_moves.items():
            next_position = state.position + delta
            if next_position < task.min_position or next_position > task.max_position:
                continue
            if next_position in task.constraints.forbidden_positions:
                continue
            if task.constraints.no_revisits and next_position in state.visited_positions:
                continue

            recent_moves = state.recent_moves
            if max_pattern_length > 0:
                candidate_recent_moves = tuple((list(recent_moves) + [move_label])[-max_pattern_length:])
                if any(
                    len(pattern) <= len(candidate_recent_moves)
                    and candidate_recent_moves[-len(pattern):] == pattern
                    for pattern in task.constraints.forbidden_move_patterns
                ):
                    continue
                recent_moves = candidate_recent_moves

            next_state = _SearchState(
                position=next_position,
                checkpoints_visited=frozenset(
                    set(state.checkpoints_visited)
                    | ({next_position} if next_position in task.constraints.checkpoints else set())
                ),
                required_moves_used=frozenset(
                    set(state.required_moves_used)
                    | ({move_label} if move_label in task.constraints.required_moves else set())
                ),
                visited_positions=(
                    frozenset(set(state.visited_positions) | {next_position})
                    if task.constraints.no_revisits
                    else frozenset()
                ),
                recent_moves=recent_moves,
            )
            if next_state in seen:
                continue
            seen.add(next_state)
            queue.append((next_state, path + (move_label,)))

    return SolverResult(
        solvable=False,
        optimal_moves=(),
        optimal_length=None,
        explored_states=explored_states,
    )
