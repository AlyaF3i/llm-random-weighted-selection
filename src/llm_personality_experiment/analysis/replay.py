"""Interactive replay utilities for live experiment demos."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

from llm_personality_experiment.utils.io import read_jsonl


@dataclass(frozen=True)
class ReplayFrame:
    """Compact replay frame for one logged task iteration."""

    iteration: int
    task_id: str
    question_prompt: str
    selected_agents: tuple[str, ...]
    weights_before: dict[str, float]
    weights_after: dict[str, float]
    selected_attempts: tuple[dict[str, Any], ...]


def load_replay_frames(log_path: str | Path) -> list[ReplayFrame]:
    """Load task-level log records and convert them to replay frames."""

    records = read_jsonl(log_path)
    frames: list[ReplayFrame] = []
    for record in records:
        questions = record["task"]["questions"]
        first_prompt = str(questions[0]["prompt"]) if questions else "(no question)"
        frames.append(
            ReplayFrame(
                iteration=int(record["iteration"]),
                task_id=str(record["task"]["task_id"]),
                question_prompt=first_prompt,
                selected_agents=tuple(str(name) for name in record["selection"]["selected_agents"]),
                weights_before={str(name): float(value) for name, value in record["weights_before"].items()},
                weights_after={str(name): float(value) for name, value in record["weights_after"].items()},
                selected_attempts=tuple(record["agent_attempts"]),
            )
        )
    return frames


def launch_weight_replay(
    run_dir: str | Path,
    interval_ms: int = 1200,
    family_view: bool = False,
) -> None:
    """Open an animated matplotlib replay of weight changes over the run."""

    run_path = Path(run_dir)
    frames = load_replay_frames(run_path / "experiment.jsonl")
    if not frames:
        raise ValueError(f"No replay frames found in {run_path}")

    figure, axes = plt.subplots(2, 2, figsize=(14, 9))
    figure.suptitle(f"Live Weight Replay: {run_path.name}")
    line_axis = axes[0, 0]
    bar_axis = axes[0, 1]
    correctness_axis = axes[1, 0]
    text_axis = axes[1, 1]

    entity_names = _resolve_entity_names(frames[0].weights_after, family_view=family_view)
    weight_history: dict[str, list[float]] = {name: [] for name in entity_names}
    iteration_history: list[int] = []

    def update(frame_index: int) -> None:
        frame = frames[frame_index]
        iteration_history.append(frame.iteration)
        aggregated_weights = _aggregate_weights(frame.weights_after, family_view=family_view)
        for name in entity_names:
            weight_history[name].append(aggregated_weights.get(name, 0.0))

        line_axis.clear()
        line_axis.set_title("Weight Trajectories")
        line_axis.set_xlabel("Iteration")
        line_axis.set_ylabel("Weight")
        line_axis.set_ylim(0.0, 1.0)
        line_axis.grid(alpha=0.3)
        for name in entity_names:
            line_axis.plot(iteration_history, weight_history[name], label=name)
        line_axis.legend(loc="upper left", fontsize=8)

        bar_axis.clear()
        current_selected = set(_normalize_selected_names(frame.selected_agents, family_view=family_view))
        colors = ["#2E8B57" if name in current_selected else "#4C72B0" for name in entity_names]
        bar_axis.bar(entity_names, [aggregated_weights.get(name, 0.0) for name in entity_names], color=colors)
        bar_axis.set_title(f"Current Weights At Iteration {frame.iteration}")
        bar_axis.set_ylabel("Weight")
        bar_axis.set_ylim(0.0, 1.0)
        bar_axis.tick_params(axis="x", rotation=25)
        bar_axis.grid(axis="y", alpha=0.3)

        correctness_axis.clear()
        attempt_names = [str(attempt["agent_name"]) for attempt in frame.selected_attempts]
        attempt_scores = [float(attempt["verification"]["correctness_score"]) for attempt in frame.selected_attempts]
        attempt_colors = ["#C0392B" if float(score) < 1.0 else "#2E8B57" for score in attempt_scores]
        correctness_axis.bar(attempt_names, attempt_scores, color=attempt_colors)
        correctness_axis.set_title("Selected Agents: Correctness On Current Task")
        correctness_axis.set_ylabel("Correctness")
        correctness_axis.set_ylim(0.0, 1.0)
        correctness_axis.tick_params(axis="x", rotation=25)
        correctness_axis.grid(axis="y", alpha=0.3)

        text_axis.clear()
        text_axis.axis("off")
        attempt_lines = []
        for attempt in frame.selected_attempts:
            attempt_lines.append(
                f"{attempt['agent_name']}: score={attempt['verification']['correctness_score']:.2f}, "
                f"json={'yes' if attempt['verification']['json_valid'] else 'no'}, "
                f"failure={'yes' if attempt['had_failure'] else 'no'}"
            )
        text_axis.text(
            0.0,
            1.0,
            "\n".join(
                [
                    f"Iteration: {frame.iteration}",
                    f"Task ID: {frame.task_id}",
                    f"Question: {frame.question_prompt}",
                    f"Selected: {', '.join(frame.selected_agents)}",
                    "",
                    "Current Outcomes:",
                    *attempt_lines,
                ]
            ),
            va="top",
            ha="left",
            fontsize=10,
            family="monospace",
        )

    FuncAnimation(figure, update, frames=len(frames), interval=interval_ms, repeat=False)
    figure.tight_layout()
    plt.show()


def _base_name(agent_name: str) -> str:
    return agent_name.split("__")[0]


def _resolve_entity_names(weights: dict[str, float], family_view: bool) -> list[str]:
    if not family_view:
        return sorted(weights)
    return sorted({_base_name(name) for name in weights})


def _aggregate_weights(weights: dict[str, float], family_view: bool) -> dict[str, float]:
    if not family_view:
        return dict(weights)
    grouped: dict[str, list[float]] = defaultdict(list)
    for name, value in weights.items():
        grouped[_base_name(name)].append(float(value))
    return {name: sum(values) / len(values) for name, values in grouped.items()}


def _normalize_selected_names(selected_agents: tuple[str, ...], family_view: bool) -> tuple[str, ...]:
    if not family_view:
        return selected_agents
    return tuple(sorted({_base_name(name) for name in selected_agents}))
