"""Aggregate experiment summaries from JSONL logs."""

from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from llm_personality_experiment.utils.io import read_jsonl, write_json


def summarize_run(
    log_path: str | Path,
    aggregate_every: int,
    run_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a compact summary from iteration logs."""

    records = read_jsonl(log_path)
    effective_run_metadata = run_metadata
    if effective_run_metadata is None and records:
        record_level_metadata = records[0].get("run_metadata")
        if isinstance(record_level_metadata, dict):
            effective_run_metadata = record_level_metadata
    failure_counter: Counter[str] = Counter()
    scenario_totals: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    agent_counts: Counter[str] = Counter()
    agent_metric_sums: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    aggregate_windows: list[dict[str, Any]] = []

    for index, record in enumerate(records, start=1):
        agent_name = str(record["agent"]["name"])
        scenario_type = str(record["task"]["scenario_type"])
        agent_counts[agent_name] += 1

        for failure in record["verification"]["failure_types"]:
            failure_counter[str(failure)] += 1

        verification = record["verification"]
        scenario_totals[scenario_type]["count"] += 1
        scenario_totals[scenario_type]["correctness"] += float(verification["correctness_score"])
        scenario_totals[scenario_type]["completeness"] += float(verification["completeness_score"])
        scenario_totals[scenario_type]["supportiveness"] += float(verification["supportiveness_score"])

        for metric_name, value in record["metrics_after"].items():
            agent_metric_sums[agent_name][metric_name] += float(value)

        if index % aggregate_every == 0 or index == len(records):
            window_records = records[max(0, index - aggregate_every):index]
            aggregate_windows.append(
                {
                    "end_iteration": index,
                    "failure_rate": _mean(
                        1.0 if record_item["verification"]["failure_types"] else 0.0
                        for record_item in window_records
                    ),
                    "correctness": _mean(
                        float(record_item["verification"]["correctness_score"])
                        for record_item in window_records
                    ),
                    "completeness": _mean(
                        float(record_item["verification"]["completeness_score"])
                        for record_item in window_records
                    ),
                    "supportiveness": _mean(
                        float(record_item["verification"]["supportiveness_score"])
                        for record_item in window_records
                    ),
                    "reliability": _mean(
                        float(record_item["verification"]["reliability"])
                        for record_item in window_records
                    ),
                }
            )

    scenario_scores = {
        scenario: {
            "correctness": counts["correctness"] / counts["count"] if counts["count"] else 0.0,
            "completeness": counts["completeness"] / counts["count"] if counts["count"] else 0.0,
            "supportiveness": counts["supportiveness"] / counts["count"] if counts["count"] else 0.0,
        }
        for scenario, counts in scenario_totals.items()
    }
    average_agent_metrics = {
        agent_name: {
            metric_name: total / agent_counts[agent_name]
            for metric_name, total in metric_totals.items()
        }
        for agent_name, metric_totals in agent_metric_sums.items()
    }

    summary: dict[str, Any] = {
        "total_tasks": len({int(record["iteration"]) for record in records}),
        "total_attempts": len(records),
        "agent_selection_counts": dict(agent_counts),
        "average_agent_metrics": average_agent_metrics,
        "failure_counts": dict(failure_counter),
        "format_failure_count": int(failure_counter["invalid_json"] + failure_counter["schema_validation_failed"]),
        "scenario_scores": scenario_scores,
        "aggregate_windows": aggregate_windows,
    }
    if effective_run_metadata is not None:
        summary["run_metadata"] = effective_run_metadata
    return summary


def write_summary(
    log_path: str | Path,
    output_path: str | Path,
    aggregate_every: int,
    run_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create and persist a run summary JSON file."""

    summary = summarize_run(log_path=log_path, aggregate_every=aggregate_every, run_metadata=run_metadata)
    write_json(output_path, summary)
    return summary


def _mean(values: Any) -> float:
    values_list = list(values)
    if not values_list:
        return 0.0
    return float(sum(values_list) / len(values_list))
