"""Plot utilities for task-level experiment outputs."""

from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt

from llm_personality_experiment.analysis.records import (
    flatten_attempts,
    get_metric_baselines,
    get_run_metadata,
)
from llm_personality_experiment.utils.io import ensure_directory, read_jsonl


GOOD_COLOR = "#2E8B57"
BAD_COLOR = "#C0392B"
NEUTRAL_COLOR = "#4C72B0"
REFERENCE_COLOR = "#444444"


def generate_plots(log_path: str | Path, output_dir: str | Path) -> list[Path]:
    """Generate the standard analysis figures for one run."""

    records = read_jsonl(log_path)
    attempts = flatten_attempts(records)
    run_metadata = get_run_metadata(records)
    baselines = get_metric_baselines(run_metadata)
    target_dir = ensure_directory(output_dir)
    generated_files = [
        _plot_metrics(records, baselines, target_dir / "metrics_over_time.png"),
        _plot_weights(records, target_dir / "weights_over_time.png"),
        _plot_family_weights(records, target_dir / "family_weights_over_time.png"),
        _plot_family_correctness(records, baselines, target_dir / "family_correctness_over_time.png"),
        _plot_failure_rates(records, attempts, target_dir / "failure_rates.png"),
        _plot_scenario_scores(attempts, target_dir / "scenario_scores.png"),
        _plot_selection_counts(records, target_dir / "selection_counts.png"),
        _plot_family_selection_counts(records, target_dir / "family_selection_counts.png"),
        _plot_exam_scores(records, target_dir / "exam_scores_over_time.png"),
        _plot_json_validity(attempts, target_dir / "json_validity_over_time.png"),
        _plot_agent_failure_counts(attempts, target_dir / "agent_failure_counts.png"),
        _plot_agent_success_rates(attempts, target_dir / "agent_success_rates.png"),
        _plot_question_volume(records, target_dir / "question_volume_over_time.png"),
        _plot_failure_type_heatmap(attempts, target_dir / "failure_type_heatmap.png"),
        _plot_final_metric_snapshot(records, baselines, target_dir / "final_metric_snapshot.png"),
        _plot_outcome_breakdown_by_family(attempts, target_dir / "outcome_breakdown_by_family.png"),
        _plot_task_outcome_mix(records, target_dir / "task_outcome_mix_over_time.png"),
        _plot_family_scorecard(records, attempts, target_dir / "family_scorecard.png"),
    ]
    return generated_files


def _plot_metrics(records: list[dict[str, Any]], baselines: dict[str, float], output_path: Path) -> Path:
    metrics_by_agent: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    iterations = [int(record["iteration"]) for record in records]
    for record in records:
        all_metrics = record["all_agents_metrics_after"]
        for agent_name, metric_values in all_metrics.items():
            for metric_name, value in metric_values.items():
                metrics_by_agent[agent_name][metric_name].append(float(value))

    figure, axes = plt.subplots(2, 2, figsize=(12, 8), sharex=True)
    metric_names = ["correctness", "completeness", "supportiveness", "reliability"]
    for axis, metric_name in zip(axes.flat, metric_names, strict=True):
        baseline = baselines.get(metric_name, 0.5)
        axis.axhspan(0.0, baseline, color=BAD_COLOR, alpha=0.08)
        axis.axhspan(baseline, 1.0, color=GOOD_COLOR, alpha=0.08)
        axis.axhline(baseline, color=REFERENCE_COLOR, linestyle="--", linewidth=1)
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


def _plot_weights(records: list[dict[str, Any]], output_path: Path) -> Path:
    weights_by_agent: dict[str, list[float]] = defaultdict(list)
    iterations = [int(record["iteration"]) for record in records]
    for record in records:
        for agent_name, weight in record["weights_after"].items():
            weights_by_agent[agent_name].append(float(weight))

    overall_average = _mean(
        weight
        for agent_weights in weights_by_agent.values()
        for weight in agent_weights
    )
    figure, axis = plt.subplots(figsize=(10, 5))
    axis.axhline(overall_average, color=REFERENCE_COLOR, linestyle="--", linewidth=1, label="Average Weight")
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


def _plot_family_weights(records: list[dict[str, Any]], output_path: Path) -> Path:
    family_weights: dict[str, list[float]] = defaultdict(list)
    iterations = [int(record["iteration"]) for record in records]
    for record in records:
        grouped: dict[str, list[float]] = defaultdict(list)
        for agent_name, weight in record["weights_after"].items():
            grouped[_family_name(str(agent_name))].append(float(weight))
        for family_name, values in grouped.items():
            family_weights[family_name].append(_mean(values))

    overall_average = _mean(
        weight
        for values in family_weights.values()
        for weight in values
    )
    figure, axis = plt.subplots(figsize=(10, 5))
    axis.axhspan(0.0, overall_average, color=BAD_COLOR, alpha=0.08)
    axis.axhspan(overall_average, 1.0, color=GOOD_COLOR, alpha=0.08)
    axis.axhline(overall_average, color=REFERENCE_COLOR, linestyle="--", linewidth=1, label="Run Average")
    for family_name, values in family_weights.items():
        axis.plot(iterations, values, label=family_name, linewidth=2.2)
    axis.set_title("Family Average Weights Over Time")
    axis.set_xlabel("Iteration")
    axis.set_ylabel("Average Weight")
    axis.grid(alpha=0.3)
    axis.legend()
    figure.tight_layout()
    figure.savefig(output_path)
    plt.close(figure)
    return output_path


def _plot_family_correctness(
    records: list[dict[str, Any]],
    baselines: dict[str, float],
    output_path: Path,
) -> Path:
    family_correctness: dict[str, list[float]] = defaultdict(list)
    iterations = [int(record["iteration"]) for record in records]
    for record in records:
        grouped: dict[str, list[float]] = defaultdict(list)
        for agent_name, metrics_after in record["all_agents_metrics_after"].items():
            grouped[_family_name(str(agent_name))].append(float(metrics_after["correctness"]))
        for family_name, values in grouped.items():
            family_correctness[family_name].append(_mean(values))

    baseline = baselines.get("correctness", 0.5)
    figure, axis = plt.subplots(figsize=(10, 5))
    axis.axhspan(0.0, baseline, color=BAD_COLOR, alpha=0.08)
    axis.axhspan(baseline, 1.0, color=GOOD_COLOR, alpha=0.08)
    axis.axhline(baseline, color=REFERENCE_COLOR, linestyle="--", linewidth=1, label="Baseline")
    for family_name, values in family_correctness.items():
        axis.plot(iterations, values, label=family_name, linewidth=2.2)
    axis.set_title("Family Correctness Metric Over Time")
    axis.set_xlabel("Iteration")
    axis.set_ylabel("Correctness Metric")
    axis.set_ylim(0.0, 1.0)
    axis.grid(alpha=0.3)
    axis.legend()
    figure.tight_layout()
    figure.savefig(output_path)
    plt.close(figure)
    return output_path


def _plot_failure_rates(
    records: list[dict[str, Any]],
    attempts: list[dict[str, Any]],
    output_path: Path,
) -> Path:
    iterations = [int(record["iteration"]) for record in records]
    task_failure_share = [
        _mean(1.0 if attempt["had_failure"] else 0.0 for attempt in record["agent_attempts"])
        for record in records
    ]
    cumulative_attempt_failure_rate: list[float] = []
    total_failures = 0
    for index, attempt in enumerate(attempts, start=1):
        if attempt["attempt"]["had_failure"]:
            total_failures += 1
        cumulative_attempt_failure_rate.append(total_failures / index)

    average_task_failure = _mean(task_failure_share)
    figure, axes = plt.subplots(2, 1, figsize=(10, 8), sharex=False)
    colors = [GOOD_COLOR if value <= average_task_failure else BAD_COLOR for value in task_failure_share]
    axes[0].bar(iterations, task_failure_share, color=colors)
    axes[0].axhline(average_task_failure, color=REFERENCE_COLOR, linestyle="--", linewidth=1)
    axes[0].set_title("Task Failure Share")
    axes[0].set_xlabel("Iteration")
    axes[0].set_ylabel("Failure Share")
    axes[0].set_ylim(0.0, 1.0)
    axes[0].grid(axis="y", alpha=0.3)

    axes[1].plot(range(1, len(attempts) + 1), cumulative_attempt_failure_rate, color=NEUTRAL_COLOR)
    axes[1].fill_between(range(1, len(attempts) + 1), cumulative_attempt_failure_rate, color=BAD_COLOR, alpha=0.12)
    axes[1].set_title("Cumulative Attempt Failure Rate")
    axes[1].set_xlabel("Attempt")
    axes[1].set_ylabel("Failure Rate")
    axes[1].set_ylim(0.0, 1.0)
    axes[1].grid(alpha=0.3)

    figure.tight_layout()
    figure.savefig(output_path)
    plt.close(figure)
    return output_path


def _plot_scenario_scores(attempts: list[dict[str, Any]], output_path: Path) -> Path:
    grouped: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for flattened_attempt in attempts:
        scenario = str(flattened_attempt["task"]["scenario_type"])
        verification = flattened_attempt["attempt"]["verification"]
        grouped[scenario]["correctness"].append(float(verification["correctness_score"]))
        grouped[scenario]["completeness"].append(float(verification["completeness_score"]))
        grouped[scenario]["supportiveness"].append(float(verification["supportiveness_score"]))

    scenarios = list(grouped.keys())
    correctness = [sum(grouped[scenario]["correctness"]) / len(grouped[scenario]["correctness"]) for scenario in scenarios]
    completeness = [sum(grouped[scenario]["completeness"]) / len(grouped[scenario]["completeness"]) for scenario in scenarios]
    supportiveness = [sum(grouped[scenario]["supportiveness"]) / len(grouped[scenario]["supportiveness"]) for scenario in scenarios]
    overall_average = _mean(correctness + completeness + supportiveness)

    x_positions = range(len(scenarios))
    figure, axis = plt.subplots(figsize=(10, 5))
    axis.bar(
        [position - 0.25 for position in x_positions],
        correctness,
        width=0.25,
        label="Correctness",
        color=[GOOD_COLOR if value >= overall_average else BAD_COLOR for value in correctness],
    )
    axis.bar(
        list(x_positions),
        completeness,
        width=0.25,
        label="Completeness",
        color=[GOOD_COLOR if value >= overall_average else BAD_COLOR for value in completeness],
    )
    axis.bar(
        [position + 0.25 for position in x_positions],
        supportiveness,
        width=0.25,
        label="Supportiveness",
        color=[GOOD_COLOR if value >= overall_average else BAD_COLOR for value in supportiveness],
    )
    axis.axhline(overall_average, color=REFERENCE_COLOR, linestyle="--", linewidth=1)
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


def _plot_selection_counts(records: list[dict[str, Any]], output_path: Path) -> Path:
    selection_counts = Counter(
        str(agent_name)
        for record in records
        for agent_name in record["selection"]["selected_agents"]
    )
    average_count = _mean(selection_counts.values())
    colors = [GOOD_COLOR if value >= average_count else BAD_COLOR for value in selection_counts.values()]
    figure, axis = plt.subplots(figsize=(10, 5))
    axis.bar(selection_counts.keys(), selection_counts.values(), color=colors)
    axis.axhline(average_count, color=REFERENCE_COLOR, linestyle="--", linewidth=1)
    axis.set_title("Agent Selection Counts")
    axis.set_ylabel("Selections")
    axis.tick_params(axis="x", rotation=30)
    axis.grid(axis="y", alpha=0.3)
    figure.tight_layout()
    figure.savefig(output_path)
    plt.close(figure)
    return output_path


def _plot_family_selection_counts(records: list[dict[str, Any]], output_path: Path) -> Path:
    selection_counts = Counter(
        _family_name(str(agent_name))
        for record in records
        for agent_name in record["selection"]["selected_agents"]
    )
    average_count = _mean(selection_counts.values())
    colors = [GOOD_COLOR if value >= average_count else BAD_COLOR for value in selection_counts.values()]
    figure, axis = plt.subplots(figsize=(9, 5))
    axis.bar(selection_counts.keys(), selection_counts.values(), color=colors)
    axis.axhline(average_count, color=REFERENCE_COLOR, linestyle="--", linewidth=1, label="Average")
    axis.set_title("Family Selection Counts")
    axis.set_ylabel("Selections")
    axis.grid(axis="y", alpha=0.3)
    axis.legend()
    figure.tight_layout()
    figure.savefig(output_path)
    plt.close(figure)
    return output_path


def _plot_exam_scores(records: list[dict[str, Any]], output_path: Path) -> Path:
    iterations = [int(record["iteration"]) for record in records]
    average_correctness = [
        _mean(float(attempt["verification"]["correctness_score"]) for attempt in record["agent_attempts"])
        for record in records
    ]
    average_completeness = [
        _mean(float(attempt["verification"]["completeness_score"]) for attempt in record["agent_attempts"])
        for record in records
    ]
    average_supportiveness = [
        _mean(float(attempt["verification"]["supportiveness_score"]) for attempt in record["agent_attempts"])
        for record in records
    ]

    figure, axis = plt.subplots(figsize=(10, 5))
    axis.plot(iterations, average_correctness, label="Correctness", color=NEUTRAL_COLOR)
    axis.plot(iterations, average_completeness, label="Completeness", color=GOOD_COLOR)
    axis.plot(iterations, average_supportiveness, label="Supportiveness", color="#DD8452")
    axis.axhline(_mean(average_correctness), color=NEUTRAL_COLOR, linestyle="--", linewidth=1)
    axis.axhline(_mean(average_completeness), color=GOOD_COLOR, linestyle="--", linewidth=1)
    axis.axhline(_mean(average_supportiveness), color="#DD8452", linestyle="--", linewidth=1)
    axis.set_title("Average Exam Scores Per Task")
    axis.set_xlabel("Iteration")
    axis.set_ylabel("Score")
    axis.set_ylim(0.0, 1.0)
    axis.grid(alpha=0.3)
    axis.legend()
    figure.tight_layout()
    figure.savefig(output_path)
    plt.close(figure)
    return output_path


def _plot_json_validity(attempts: list[dict[str, Any]], output_path: Path) -> Path:
    attempt_ids = [int(flattened_attempt["attempt"]["attempt_id"]) for flattened_attempt in attempts]
    json_valid_rates: list[float] = []
    schema_valid_rates: list[float] = []
    json_valid_total = 0
    schema_valid_total = 0
    for index, flattened_attempt in enumerate(attempts, start=1):
        verification = flattened_attempt["attempt"]["verification"]
        if verification["json_valid"]:
            json_valid_total += 1
        if verification["schema_valid"]:
            schema_valid_total += 1
        json_valid_rates.append(json_valid_total / index)
        schema_valid_rates.append(schema_valid_total / index)

    figure, axis = plt.subplots(figsize=(10, 5))
    axis.axhspan(0.0, 0.8, color=BAD_COLOR, alpha=0.08)
    axis.axhspan(0.8, 1.0, color=GOOD_COLOR, alpha=0.08)
    axis.axhline(0.8, color=REFERENCE_COLOR, linestyle="--", linewidth=1, label="Target 0.8")
    axis.plot(attempt_ids, json_valid_rates, label="JSON Valid Rate", color=NEUTRAL_COLOR)
    axis.plot(attempt_ids, schema_valid_rates, label="Schema Valid Rate", color=GOOD_COLOR)
    axis.set_title("Output Validity Over Time")
    axis.set_xlabel("Attempt")
    axis.set_ylabel("Rate")
    axis.set_ylim(0.0, 1.0)
    axis.grid(alpha=0.3)
    axis.legend()
    figure.tight_layout()
    figure.savefig(output_path)
    plt.close(figure)
    return output_path


def _plot_agent_failure_counts(attempts: list[dict[str, Any]], output_path: Path) -> Path:
    failure_counts = Counter(
        str(flattened_attempt["attempt"]["agent_name"])
        for flattened_attempt in attempts
        if flattened_attempt["attempt"]["had_failure"]
    )
    average_failures = _mean(failure_counts.values())
    colors = [GOOD_COLOR if value <= average_failures else BAD_COLOR for value in failure_counts.values()]
    figure, axis = plt.subplots(figsize=(10, 5))
    axis.bar(failure_counts.keys(), failure_counts.values(), color=colors)
    axis.axhline(average_failures, color=REFERENCE_COLOR, linestyle="--", linewidth=1)
    axis.set_title("Agent Failure Counts")
    axis.set_ylabel("Failures")
    axis.tick_params(axis="x", rotation=30)
    axis.grid(axis="y", alpha=0.3)
    figure.tight_layout()
    figure.savefig(output_path)
    plt.close(figure)
    return output_path


def _plot_agent_success_rates(attempts: list[dict[str, Any]], output_path: Path) -> Path:
    totals = Counter(str(flattened_attempt["attempt"]["agent_name"]) for flattened_attempt in attempts)
    successes = Counter(
        str(flattened_attempt["attempt"]["agent_name"])
        for flattened_attempt in attempts
        if not flattened_attempt["attempt"]["had_failure"]
    )
    success_rates = {
        agent_name: successes[agent_name] / totals[agent_name]
        for agent_name in totals
    }
    average_rate = _mean(success_rates.values())
    colors = [GOOD_COLOR if value >= average_rate else BAD_COLOR for value in success_rates.values()]
    figure, axis = plt.subplots(figsize=(10, 5))
    axis.bar(success_rates.keys(), success_rates.values(), color=colors)
    axis.axhline(average_rate, color=REFERENCE_COLOR, linestyle="--", linewidth=1)
    axis.set_title("Agent Success Rates")
    axis.set_ylabel("Success Rate")
    axis.set_ylim(0.0, 1.0)
    axis.tick_params(axis="x", rotation=30)
    axis.grid(axis="y", alpha=0.3)
    figure.tight_layout()
    figure.savefig(output_path)
    plt.close(figure)
    return output_path


def _plot_question_volume(records: list[dict[str, Any]], output_path: Path) -> Path:
    iterations = [int(record["iteration"]) for record in records]
    question_counts = [len(record["task"]["questions"]) for record in records]
    total_points = [int(record["task"]["total_points"]) for record in records]
    question_average = _mean(question_counts)

    figure, axis = plt.subplots(figsize=(10, 5))
    axis.bar(
        iterations,
        question_counts,
        color=[GOOD_COLOR if count >= question_average else BAD_COLOR for count in question_counts],
        alpha=0.7,
        label="Question Count",
    )
    axis.plot(iterations, total_points, color=NEUTRAL_COLOR, linewidth=2, label="Total Points")
    axis.axhline(question_average, color=REFERENCE_COLOR, linestyle="--", linewidth=1)
    axis.set_title("Question Volume Over Time")
    axis.set_xlabel("Iteration")
    axis.set_ylabel("Count")
    axis.grid(axis="y", alpha=0.3)
    axis.legend()
    figure.tight_layout()
    figure.savefig(output_path)
    plt.close(figure)
    return output_path


def _plot_failure_type_heatmap(attempts: list[dict[str, Any]], output_path: Path) -> Path:
    agents = sorted({str(flattened_attempt["attempt"]["agent_name"]) for flattened_attempt in attempts})
    failure_types = sorted(
        {
            str(failure)
            for flattened_attempt in attempts
            for failure in flattened_attempt["attempt"]["verification"]["failure_types"]
        }
    )
    if not failure_types:
        failure_types = ["no_failures"]

    matrix: list[list[int]] = []
    for agent_name in agents:
        row: list[int] = []
        for failure_type in failure_types:
            if failure_type == "no_failures":
                count = sum(
                    1
                    for flattened_attempt in attempts
                    if flattened_attempt["attempt"]["agent_name"] == agent_name
                    and not flattened_attempt["attempt"]["verification"]["failure_types"]
                )
            else:
                count = sum(
                    1
                    for flattened_attempt in attempts
                    if flattened_attempt["attempt"]["agent_name"] == agent_name
                    and failure_type in flattened_attempt["attempt"]["verification"]["failure_types"]
                )
            row.append(count)
        matrix.append(row)

    figure, axis = plt.subplots(figsize=(max(8, len(failure_types) * 1.1), max(4, len(agents) * 0.6)))
    image = axis.imshow(matrix, cmap="YlOrRd", aspect="auto")
    axis.set_xticks(range(len(failure_types)))
    axis.set_xticklabels(failure_types, rotation=30, ha="right")
    axis.set_yticks(range(len(agents)))
    axis.set_yticklabels(agents)
    axis.set_title("Failure Type Heatmap")
    figure.colorbar(image, ax=axis, label="Count")
    figure.tight_layout()
    figure.savefig(output_path)
    plt.close(figure)
    return output_path


def _plot_final_metric_snapshot(
    records: list[dict[str, Any]],
    baselines: dict[str, float],
    output_path: Path,
) -> Path:
    final_metrics = records[-1]["all_agents_metrics_after"] if records else {}
    agents = list(final_metrics.keys())
    metric_names = ["correctness", "completeness", "supportiveness", "reliability"]

    figure, axes = plt.subplots(2, 2, figsize=(12, 8), sharey=True)
    for axis, metric_name in zip(axes.flat, metric_names, strict=True):
        values = [float(final_metrics[agent][metric_name]) for agent in agents]
        baseline = baselines.get(metric_name, 0.5)
        colors = [GOOD_COLOR if value >= baseline else BAD_COLOR for value in values]
        axis.bar(agents, values, color=colors)
        axis.axhline(baseline, color=REFERENCE_COLOR, linestyle="--", linewidth=1)
        axis.set_title(f"Final {metric_name.title()}")
        axis.set_ylim(0.0, 1.0)
        axis.tick_params(axis="x", rotation=30)
        axis.grid(axis="y", alpha=0.3)
    figure.tight_layout()
    figure.savefig(output_path)
    plt.close(figure)
    return output_path


def _plot_outcome_breakdown_by_family(attempts: list[dict[str, Any]], output_path: Path) -> Path:
    families = sorted({_family_name(str(flattened_attempt["attempt"]["agent_name"])) for flattened_attempt in attempts})
    full_credit_rates: list[float] = []
    wrong_answer_rates: list[float] = []
    format_failure_rates: list[float] = []

    for family_name in families:
        family_attempts = [
            flattened_attempt["attempt"]
            for flattened_attempt in attempts
            if _family_name(str(flattened_attempt["attempt"]["agent_name"])) == family_name
        ]
        total = len(family_attempts)
        if total == 0:
            full_credit_rates.append(0.0)
            wrong_answer_rates.append(0.0)
            format_failure_rates.append(0.0)
            continue
        full_credit_rates.append(
            sum(1 for attempt in family_attempts if _is_full_credit_attempt(attempt)) / total
        )
        wrong_answer_rates.append(
            sum(1 for attempt in family_attempts if _is_wrong_answer_attempt(attempt)) / total
        )
        format_failure_rates.append(
            sum(1 for attempt in family_attempts if _is_format_failure_attempt(attempt)) / total
        )

    figure, axis = plt.subplots(figsize=(10, 5))
    axis.bar(families, full_credit_rates, color=GOOD_COLOR, label="Full Credit")
    axis.bar(families, wrong_answer_rates, bottom=full_credit_rates, color="#F39C12", label="Wrong Answer")
    stacked_bottom = [full_credit_rates[index] + wrong_answer_rates[index] for index in range(len(families))]
    axis.bar(families, format_failure_rates, bottom=stacked_bottom, color=BAD_COLOR, label="Format Failure")
    axis.set_title("Outcome Breakdown By Family")
    axis.set_ylabel("Share of Attempts")
    axis.set_ylim(0.0, 1.0)
    axis.grid(axis="y", alpha=0.3)
    axis.legend()
    figure.tight_layout()
    figure.savefig(output_path)
    plt.close(figure)
    return output_path


def _plot_task_outcome_mix(records: list[dict[str, Any]], output_path: Path) -> Path:
    iterations = [int(record["iteration"]) for record in records]
    full_credit_share: list[float] = []
    wrong_answer_share: list[float] = []
    format_failure_share: list[float] = []

    for record in records:
        attempts = record["agent_attempts"]
        total = max(len(attempts), 1)
        full_credit_share.append(sum(1 for attempt in attempts if _is_full_credit_attempt(attempt)) / total)
        wrong_answer_share.append(sum(1 for attempt in attempts if _is_wrong_answer_attempt(attempt)) / total)
        format_failure_share.append(sum(1 for attempt in attempts if _is_format_failure_attempt(attempt)) / total)

    figure, axis = plt.subplots(figsize=(11, 5))
    axis.bar(iterations, full_credit_share, color=GOOD_COLOR, label="Full Credit")
    axis.bar(iterations, wrong_answer_share, bottom=full_credit_share, color="#F39C12", label="Wrong Answer")
    stacked_bottom = [full_credit_share[index] + wrong_answer_share[index] for index in range(len(iterations))]
    axis.bar(iterations, format_failure_share, bottom=stacked_bottom, color=BAD_COLOR, label="Format Failure")
    axis.set_title("Selected-Agent Outcome Mix Per Task")
    axis.set_xlabel("Iteration")
    axis.set_ylabel("Share of Selected Agents")
    axis.set_ylim(0.0, 1.0)
    axis.grid(axis="y", alpha=0.3)
    axis.legend()
    figure.tight_layout()
    figure.savefig(output_path)
    plt.close(figure)
    return output_path


def _plot_family_scorecard(
    records: list[dict[str, Any]],
    attempts: list[dict[str, Any]],
    output_path: Path,
) -> Path:
    families = sorted({_family_name(str(flattened_attempt["attempt"]["agent_name"])) for flattened_attempt in attempts})
    last_record = records[-1] if records else {}
    final_weights = last_record.get("weights_after", {})

    full_credit_rates: list[float] = []
    average_final_weights: list[float] = []
    average_selection_share: list[float] = []
    family_selection_counts = Counter(
        _family_name(str(agent_name))
        for record in records
        for agent_name in record["selection"]["selected_agents"]
    )
    max_selection_count = max(family_selection_counts.values(), default=1)

    for family_name in families:
        family_attempts = [
            flattened_attempt["attempt"]
            for flattened_attempt in attempts
            if _family_name(str(flattened_attempt["attempt"]["agent_name"])) == family_name
        ]
        total_attempts = len(family_attempts) or 1
        full_credit_rates.append(
            sum(1 for attempt in family_attempts if _is_full_credit_attempt(attempt)) / total_attempts
        )
        family_weights = [
            float(weight)
            for agent_name, weight in final_weights.items()
            if _family_name(str(agent_name)) == family_name
        ]
        average_final_weights.append(_mean(family_weights))
        average_selection_share.append(family_selection_counts[family_name] / max_selection_count)

    x_positions = list(range(len(families)))
    figure, axis = plt.subplots(figsize=(10, 5))
    axis.bar(
        [position - 0.2 for position in x_positions],
        full_credit_rates,
        width=0.4,
        color=GOOD_COLOR,
        label="Full-Credit Rate",
    )
    axis.bar(
        [position + 0.2 for position in x_positions],
        average_final_weights,
        width=0.4,
        color=NEUTRAL_COLOR,
        label="Average Final Weight",
    )
    axis.plot(
        x_positions,
        average_selection_share,
        color=REFERENCE_COLOR,
        marker="o",
        linewidth=2,
        label="Selection Share (normalized)",
    )
    axis.set_xticks(x_positions)
    axis.set_xticklabels(families)
    axis.set_ylim(0.0, 1.0)
    axis.set_ylabel("Normalized Value")
    axis.set_title("Family Performance, Weight, And Selection")
    axis.grid(axis="y", alpha=0.3)
    axis.legend()
    figure.tight_layout()
    figure.savefig(output_path)
    plt.close(figure)
    return output_path


def _mean(values: Any) -> float:
    values_list = list(values)
    if not values_list:
        return 0.0
    return float(sum(values_list) / len(values_list))


def _family_name(agent_name: str) -> str:
    return agent_name.split("__", maxsplit=1)[0]


def _is_format_failure_attempt(attempt: dict[str, Any]) -> bool:
    return bool(attempt["had_failure"])


def _is_full_credit_attempt(attempt: dict[str, Any]) -> bool:
    if _is_format_failure_attempt(attempt):
        return False
    return float(attempt["verification"]["correctness_score"]) >= 0.999999


def _is_wrong_answer_attempt(attempt: dict[str, Any]) -> bool:
    if _is_format_failure_attempt(attempt):
        return False
    return not _is_full_credit_attempt(attempt)
