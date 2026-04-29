"""Cross-run comparison utilities."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from llm_personality_experiment.analysis.records import flatten_attempts, get_run_metadata
from llm_personality_experiment.analysis.plots import BAD_COLOR, GOOD_COLOR, REFERENCE_COLOR
from llm_personality_experiment.utils.io import ensure_directory, read_jsonl, write_json


@dataclass(frozen=True)
class ComparisonRun:
    label: str
    run_dir: Path
    records: list[dict[str, object]]
    attempts: list[dict[str, object]]
    run_metadata: dict[str, object] | None


def compare_runs(
    run_dirs: list[str | Path],
    output_dir: str | Path,
    labels: list[str] | None = None,
) -> dict[str, object]:
    """Generate comparison plots and a compact summary for multiple runs."""

    comparison_runs = _load_runs(run_dirs, labels)
    target_dir = ensure_directory(output_dir)
    plots = [
        _plot_family_final_weights(comparison_runs, target_dir / "family_final_weights_comparison.png"),
        _plot_family_full_credit_rates(comparison_runs, target_dir / "family_full_credit_rates_comparison.png"),
        _plot_family_selection_counts(comparison_runs, target_dir / "family_selection_counts_comparison.png"),
        _plot_family_weight_trajectories(comparison_runs, target_dir / "family_weight_trajectories_comparison.png"),
        _plot_task_correctness(comparison_runs, target_dir / "task_correctness_comparison.png"),
    ]
    summary = {
        "runs": [_build_run_summary(run) for run in comparison_runs],
        "plots": [str(plot) for plot in plots],
    }
    write_json(target_dir / "comparison_summary.json", summary)
    return summary


def _load_runs(run_dirs: list[str | Path], labels: list[str] | None) -> list[ComparisonRun]:
    resolved_labels = labels or []
    runs: list[ComparisonRun] = []
    for index, run_dir in enumerate(run_dirs):
        path = Path(run_dir)
        records = read_jsonl(path / "experiment.jsonl")
        label = resolved_labels[index] if index < len(resolved_labels) else path.name
        runs.append(
            ComparisonRun(
                label=label,
                run_dir=path,
                records=records,
                attempts=flatten_attempts(records),
                run_metadata=get_run_metadata(records),
            )
        )
    return runs


def _build_run_summary(run: ComparisonRun) -> dict[str, object]:
    final_record = run.records[-1] if run.records else {}
    final_weights = final_record.get("weights_after", {})
    family_weights: dict[str, list[float]] = defaultdict(list)
    family_selection_counts = Counter(
        _family_name(str(agent_name))
        for record in run.records
        for agent_name in record["selection"]["selected_agents"]
    )
    family_attempt_counts = Counter()
    family_full_credit_counts = Counter()

    for agent_name, weight in final_weights.items():
        family_weights[_family_name(str(agent_name))].append(float(weight))

    for flattened_attempt in run.attempts:
        attempt = flattened_attempt["attempt"]
        family_name = _family_name(str(attempt["agent_name"]))
        family_attempt_counts[family_name] += 1
        if _is_full_credit_attempt(attempt):
            family_full_credit_counts[family_name] += 1

    return {
        "label": run.label,
        "run_dir": str(run.run_dir),
        "selection_rule": (run.run_metadata or {}).get("selection", {}).get("weight_update_rule"),
        "model_name": (run.run_metadata or {}).get("backend", {}).get("model_name"),
        "family_final_weights": {
            family_name: _mean(weights)
            for family_name, weights in family_weights.items()
        },
        "family_selection_counts": dict(family_selection_counts),
        "family_full_credit_rates": {
            family_name: (
                family_full_credit_counts[family_name] / family_attempt_counts[family_name]
                if family_attempt_counts[family_name]
                else 0.0
            )
            for family_name in family_attempt_counts
        },
    }


def _plot_family_final_weights(runs: list[ComparisonRun], output_path: Path) -> Path:
    families = _all_families(runs)
    figure, axis = plt.subplots(figsize=(10, 5))
    bar_width = 0.8 / max(len(runs), 1)
    x_positions = list(range(len(families)))

    for run_index, run in enumerate(runs):
        final_weights = _family_final_weights(run)
        offsets = [position - 0.4 + (bar_width / 2) + (run_index * bar_width) for position in x_positions]
        axis.bar(offsets, [final_weights.get(family, 0.0) for family in families], width=bar_width, label=run.label)

    axis.set_xticks(x_positions)
    axis.set_xticklabels(families)
    axis.set_ylim(0.0, 1.0)
    axis.set_ylabel("Average Final Weight")
    axis.set_title("Family Final Weight Comparison")
    axis.grid(axis="y", alpha=0.3)
    axis.legend()
    figure.tight_layout()
    figure.savefig(output_path)
    plt.close(figure)
    return output_path


def _plot_family_full_credit_rates(runs: list[ComparisonRun], output_path: Path) -> Path:
    families = _all_families(runs)
    figure, axis = plt.subplots(figsize=(10, 5))
    bar_width = 0.8 / max(len(runs), 1)
    x_positions = list(range(len(families)))

    for run_index, run in enumerate(runs):
        rates = _family_full_credit_rates(run)
        offsets = [position - 0.4 + (bar_width / 2) + (run_index * bar_width) for position in x_positions]
        axis.bar(offsets, [rates.get(family, 0.0) for family in families], width=bar_width, label=run.label)

    axis.set_xticks(x_positions)
    axis.set_xticklabels(families)
    axis.set_ylim(0.0, 1.0)
    axis.set_ylabel("Full-Credit Rate")
    axis.set_title("Family Full-Credit Rate Comparison")
    axis.grid(axis="y", alpha=0.3)
    axis.legend()
    figure.tight_layout()
    figure.savefig(output_path)
    plt.close(figure)
    return output_path


def _plot_family_selection_counts(runs: list[ComparisonRun], output_path: Path) -> Path:
    families = _all_families(runs)
    figure, axis = plt.subplots(figsize=(10, 5))
    bar_width = 0.8 / max(len(runs), 1)
    x_positions = list(range(len(families)))

    for run_index, run in enumerate(runs):
        counts = _family_selection_counts(run)
        offsets = [position - 0.4 + (bar_width / 2) + (run_index * bar_width) for position in x_positions]
        axis.bar(offsets, [counts.get(family, 0) for family in families], width=bar_width, label=run.label)

    axis.set_xticks(x_positions)
    axis.set_xticklabels(families)
    axis.set_ylabel("Selections")
    axis.set_title("Family Selection Count Comparison")
    axis.grid(axis="y", alpha=0.3)
    axis.legend()
    figure.tight_layout()
    figure.savefig(output_path)
    plt.close(figure)
    return output_path


def _plot_family_weight_trajectories(runs: list[ComparisonRun], output_path: Path) -> Path:
    families = _all_families(runs)
    figure, axes = plt.subplots(len(families), 1, figsize=(10, max(4, len(families) * 3)), sharex=True)
    if len(families) == 1:
        axes = [axes]

    for axis, family_name in zip(axes, families, strict=True):
        for run in runs:
            trajectory = _family_weight_trajectory(run, family_name)
            axis.plot(trajectory["iterations"], trajectory["weights"], label=run.label, linewidth=2)
        axis.set_ylim(0.0, 1.0)
        axis.set_ylabel("Weight")
        axis.set_title(f"{family_name} Weight Trajectory")
        axis.grid(alpha=0.3)
        axis.legend()

    axes[-1].set_xlabel("Iteration")
    figure.tight_layout()
    figure.savefig(output_path)
    plt.close(figure)
    return output_path


def _plot_task_correctness(runs: list[ComparisonRun], output_path: Path) -> Path:
    figure, axis = plt.subplots(figsize=(10, 5))
    for run in runs:
        iterations = [int(record["iteration"]) for record in run.records]
        correctness = [
            _mean(float(attempt["verification"]["correctness_score"]) for attempt in record["agent_attempts"])
            for record in run.records
        ]
        axis.plot(iterations, correctness, label=run.label, linewidth=2)

    axis.axhspan(0.0, 0.5, color=BAD_COLOR, alpha=0.08)
    axis.axhspan(0.5, 1.0, color=GOOD_COLOR, alpha=0.08)
    axis.axhline(0.5, color=REFERENCE_COLOR, linestyle="--", linewidth=1, label="Correctness Baseline")
    axis.set_ylim(0.0, 1.0)
    axis.set_xlabel("Iteration")
    axis.set_ylabel("Average Task Correctness")
    axis.set_title("Task Correctness Comparison")
    axis.grid(alpha=0.3)
    axis.legend()
    figure.tight_layout()
    figure.savefig(output_path)
    plt.close(figure)
    return output_path


def _all_families(runs: list[ComparisonRun]) -> list[str]:
    return sorted(
        {
            _family_name(str(flattened_attempt["attempt"]["agent_name"]))
            for run in runs
            for flattened_attempt in run.attempts
        }
    )


def _family_final_weights(run: ComparisonRun) -> dict[str, float]:
    final_record = run.records[-1] if run.records else {}
    grouped: dict[str, list[float]] = defaultdict(list)
    for agent_name, weight in final_record.get("weights_after", {}).items():
        grouped[_family_name(str(agent_name))].append(float(weight))
    return {family_name: _mean(values) for family_name, values in grouped.items()}


def _family_full_credit_rates(run: ComparisonRun) -> dict[str, float]:
    totals = Counter()
    full_credit = Counter()
    for flattened_attempt in run.attempts:
        attempt = flattened_attempt["attempt"]
        family_name = _family_name(str(attempt["agent_name"]))
        totals[family_name] += 1
        if _is_full_credit_attempt(attempt):
            full_credit[family_name] += 1
    return {
        family_name: full_credit[family_name] / totals[family_name]
        for family_name in totals
    }


def _family_selection_counts(run: ComparisonRun) -> dict[str, int]:
    return dict(
        Counter(
            _family_name(str(agent_name))
            for record in run.records
            for agent_name in record["selection"]["selected_agents"]
        )
    )


def _family_weight_trajectory(run: ComparisonRun, family_name: str) -> dict[str, list[float]]:
    iterations = [int(record["iteration"]) for record in run.records]
    weights: list[float] = []
    for record in run.records:
        grouped_weights = [
            float(weight)
            for agent_name, weight in record["weights_after"].items()
            if _family_name(str(agent_name)) == family_name
        ]
        weights.append(_mean(grouped_weights))
    return {"iterations": iterations, "weights": weights}


def _family_name(agent_name: str) -> str:
    return agent_name.split("__", maxsplit=1)[0]


def _is_full_credit_attempt(attempt: dict[str, object]) -> bool:
    if attempt["had_failure"]:
        return False
    return float(attempt["verification"]["correctness_score"]) >= 0.999999


def _mean(values: object) -> float:
    values_list = list(values)
    if not values_list:
        return 0.0
    return float(sum(values_list) / len(values_list))
