"""Plot utilities for experiment outputs."""

from __future__ import annotations

from collections import Counter, defaultdict
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
        _plot_scenario_scores(records, target_dir / "scenario_scores.png"),
        _plot_selection_counts(records, target_dir / "selection_counts.png"),
        _plot_exam_scores(records, target_dir / "exam_scores_over_time.png"),
        _plot_json_validity(records, target_dir / "json_validity_over_time.png"),
    ]
    return generated_files


def _plot_metrics(records: list[dict[str, object]], output_path: Path) -> Path:
    metrics_by_agent: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    attempt_ids: list[int] = []
    for record in records:
        attempt_ids.append(int(record.get("attempt_id", record["iteration"])))
        all_metrics = record["all_agents_metrics_after"]
        for agent_name, metric_values in all_metrics.items():
            for metric_name, value in metric_values.items():
                metrics_by_agent[agent_name][metric_name].append(float(value))

    figure, axes = plt.subplots(2, 2, figsize=(12, 8), sharex=True)
    metric_names = ["correctness", "completeness", "supportiveness", "reliability"]
    for axis, metric_name in zip(axes.flat, metric_names, strict=True):
        for agent_name, metric_map in metrics_by_agent.items():
            axis.plot(attempt_ids, metric_map[metric_name], label=agent_name)
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
    attempt_ids: list[int] = []
    for record in records:
        attempt_ids.append(int(record.get("attempt_id", record["iteration"])))
        for agent_name, weight in record["weights_after"].items():
            weights_by_agent[agent_name].append(float(weight))

    figure, axis = plt.subplots(figsize=(10, 5))
    for agent_name, values in weights_by_agent.items():
        axis.plot(attempt_ids, values, label=agent_name)
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
    attempt_ids = [int(record.get("attempt_id", record["iteration"])) for record in records]
    cumulative_failure_rates: list[float] = []
    total_failures = 0
    for index, record in enumerate(records, start=1):
        if record["verification"]["failure_types"]:
            total_failures += 1
        cumulative_failure_rates.append(total_failures / index)

    figure, axis = plt.subplots(figsize=(10, 5))
    axis.plot(attempt_ids, cumulative_failure_rates, label="Cumulative Failure Rate")
    axis.set_xlabel("Iteration")
    axis.set_ylabel("Failure Rate")
    axis.set_ylim(0.0, 1.0)
    axis.grid(alpha=0.3)
    axis.legend()
    figure.tight_layout()
    figure.savefig(output_path)
    plt.close(figure)
    return output_path


def _plot_scenario_scores(records: list[dict[str, object]], output_path: Path) -> Path:
    grouped: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for record in records:
        scenario = str(record["task"]["scenario_type"])
        verification = record["verification"]
        grouped[scenario]["correctness"].append(float(verification["correctness_score"]))
        grouped[scenario]["completeness"].append(float(verification["completeness_score"]))
        grouped[scenario]["supportiveness"].append(float(verification["supportiveness_score"]))

    scenarios = list(grouped.keys())
    correctness = [sum(grouped[scenario]["correctness"]) / len(grouped[scenario]["correctness"]) for scenario in scenarios]
    completeness = [sum(grouped[scenario]["completeness"]) / len(grouped[scenario]["completeness"]) for scenario in scenarios]
    supportiveness = [sum(grouped[scenario]["supportiveness"]) / len(grouped[scenario]["supportiveness"]) for scenario in scenarios]

    x_positions = range(len(scenarios))
    figure, axis = plt.subplots(figsize=(10, 5))
    axis.bar([position - 0.25 for position in x_positions], correctness, width=0.25, label="Correctness")
    axis.bar(list(x_positions), completeness, width=0.25, label="Completeness")
    axis.bar([position + 0.25 for position in x_positions], supportiveness, width=0.25, label="Supportiveness")
    axis.set_xticks(list(x_positions))
    axis.set_xticklabels(scenarios)
    axis.set_ylim(0.0, 1.0)
    axis.set_title("Scenario Score Breakdown")
    axis.grid(axis="y", alpha=0.3)
    axis.legend()
    figure.tight_layout()
    figure.savefig(output_path)
    plt.close(figure)
    return output_path


def _plot_selection_counts(records: list[dict[str, object]], output_path: Path) -> Path:
    selection_counts = Counter(str(record["agent"]["name"]) for record in records)
    figure, axis = plt.subplots(figsize=(10, 5))
    axis.bar(selection_counts.keys(), selection_counts.values())
    axis.set_title("Agent Selection Counts")
    axis.set_ylabel("Selections")
    axis.tick_params(axis="x", rotation=30)
    axis.grid(axis="y", alpha=0.3)
    figure.tight_layout()
    figure.savefig(output_path)
    plt.close(figure)
    return output_path


def _plot_exam_scores(records: list[dict[str, object]], output_path: Path) -> Path:
    attempt_ids = [int(record.get("attempt_id", record["iteration"])) for record in records]
    correctness_scores = [float(record["verification"]["correctness_score"]) for record in records]
    completeness_scores = [float(record["verification"]["completeness_score"]) for record in records]

    figure, axis = plt.subplots(figsize=(10, 5))
    axis.plot(attempt_ids, correctness_scores, label="Correctness Score")
    axis.plot(attempt_ids, completeness_scores, label="Completeness Score")
    axis.set_title("Exam Scores Over Time")
    axis.set_xlabel("Iteration")
    axis.set_ylabel("Score")
    axis.set_ylim(0.0, 1.0)
    axis.grid(alpha=0.3)
    axis.legend()
    figure.tight_layout()
    figure.savefig(output_path)
    plt.close(figure)
    return output_path


def _plot_json_validity(records: list[dict[str, object]], output_path: Path) -> Path:
    attempt_ids = [int(record.get("attempt_id", record["iteration"])) for record in records]
    json_valid_rates: list[float] = []
    schema_valid_rates: list[float] = []
    json_valid_total = 0
    schema_valid_total = 0
    for index, record in enumerate(records, start=1):
        if record["verification"]["json_valid"]:
            json_valid_total += 1
        if record["verification"]["schema_valid"]:
            schema_valid_total += 1
        json_valid_rates.append(json_valid_total / index)
        schema_valid_rates.append(schema_valid_total / index)

    figure, axis = plt.subplots(figsize=(10, 5))
    axis.plot(attempt_ids, json_valid_rates, label="JSON Valid Rate")
    axis.plot(attempt_ids, schema_valid_rates, label="Schema Valid Rate")
    axis.set_title("Output Validity Over Time")
    axis.set_xlabel("Iteration")
    axis.set_ylabel("Rate")
    axis.set_ylim(0.0, 1.0)
    axis.grid(alpha=0.3)
    axis.legend()
    figure.tight_layout()
    figure.savefig(output_path)
    plt.close(figure)
    return output_path
