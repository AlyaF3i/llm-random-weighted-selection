"""Plot utilities for experiment outputs."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt

from llm_personality_experiment.utils.io import ensure_directory, read_jsonl


def generate_plots(log_path: str | Path, output_dir: str | Path) -> list[Path]:
    """Generate the standard analysis figures for one run."""

    records = read_jsonl(log_path)
    target_dir = ensure_directory(output_dir)
    generated_files = [
        _plot_metrics(records, target_dir / "metrics_over_time.png"),
        _plot_weights(records, target_dir / "weights_over_time.png"),
        _plot_failure_rates(records, target_dir / "failure_rates.png"),
        _plot_scenario_performance(records, target_dir / "scenario_performance.png"),
    ]
    return generated_files


def _plot_metrics(records: list[dict[str, object]], output_path: Path) -> Path:
    metrics_by_agent: dict[str, dict[str, list[float]]] = defaultdict(
        lambda: defaultdict(list)
    )
    iterations: list[int] = []
    for record in records:
        iterations.append(int(record["iteration"]))
        all_metrics = record["all_agents_metrics_after"]
        for agent_name, metric_values in all_metrics.items():
            for metric_name, value in metric_values.items():
                metrics_by_agent[agent_name][metric_name].append(float(value))

    figure, axes = plt.subplots(2, 2, figsize=(12, 8), sharex=True)
    metric_names = ["efficiency", "honesty", "discernment", "reliability"]
    for axis, metric_name in zip(axes.flat, metric_names, strict=True):
        for agent_name, metric_map in metrics_by_agent.items():
            axis.plot(iterations, metric_map[metric_name], label=agent_name)
        axis.set_title(metric_name.replace("_", " ").title())
        axis.set_ylim(0.0, 1.0)
        axis.grid(alpha=0.3)
    axes[0, 0].legend()
    figure.tight_layout()
    figure.savefig(output_path)
    plt.close(figure)
    return output_path


def _plot_weights(records: list[dict[str, object]], output_path: Path) -> Path:
    weights_by_agent: dict[str, list[float]] = defaultdict(list)
    iterations: list[int] = []
    for record in records:
        iterations.append(int(record["iteration"]))
        for agent_name, weight in record["weights_after"].items():
            weights_by_agent[agent_name].append(float(weight))

    figure, axis = plt.subplots(figsize=(10, 5))
    for agent_name, values in weights_by_agent.items():
        axis.plot(iterations, values, label=agent_name)
    axis.set_title("Weights Over Time")
    axis.set_xlabel("Iteration")
    axis.set_ylabel("Weight")
    axis.grid(alpha=0.3)
    axis.legend()
    figure.tight_layout()
    figure.savefig(output_path)
    plt.close(figure)
    return output_path


def _plot_failure_rates(records: list[dict[str, object]], output_path: Path) -> Path:
    iterations = [int(record["iteration"]) for record in records]
    cumulative_failure_rates: list[float] = []
    format_failures: list[int] = []
    total_failures = 0
    format_failure_total = 0
    for index, record in enumerate(records, start=1):
        if record["verification"]["failure_types"]:
            total_failures += 1
        if any(
            failure in {"invalid_json", "schema_validation_failed"}
            for failure in record["verification"]["failure_types"]
        ):
            format_failure_total += 1
        cumulative_failure_rates.append(total_failures / index)
        format_failures.append(format_failure_total)

    figure, axis_left = plt.subplots(figsize=(10, 5))
    axis_left.plot(iterations, cumulative_failure_rates, label="Cumulative Failure Rate")
    axis_left.set_xlabel("Iteration")
    axis_left.set_ylabel("Failure Rate")
    axis_left.set_ylim(0.0, 1.0)
    axis_left.grid(alpha=0.3)

    axis_right = axis_left.twinx()
    axis_right.plot(iterations, format_failures, color="tab:red", label="Format Failures")
    axis_right.set_ylabel("Format Failure Count")
    figure.tight_layout()
    figure.savefig(output_path)
    plt.close(figure)
    return output_path


def _plot_scenario_performance(records: list[dict[str, object]], output_path: Path) -> Path:
    scenario_names: list[str] = []
    scenario_accuracy: list[float] = []
    grouped: dict[str, list[float]] = defaultdict(list)
    for record in records:
        grouped[str(record["task"]["scenario_type"])].append(
            1.0 if record["verification"]["correct_solvability_judgment"] else 0.0
        )
    for scenario_name, values in grouped.items():
        scenario_names.append(scenario_name)
        scenario_accuracy.append(sum(values) / len(values))

    figure, axis = plt.subplots(figsize=(8, 5))
    axis.bar(scenario_names, scenario_accuracy)
    axis.set_ylim(0.0, 1.0)
    axis.set_title("Scenario Accuracy")
    axis.set_ylabel("Accuracy")
    axis.grid(axis="y", alpha=0.3)
    figure.tight_layout()
    figure.savefig(output_path)
    plt.close(figure)
    return output_path
