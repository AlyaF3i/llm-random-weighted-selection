"""Aggregate experiment summaries from JSONL logs."""

from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from llm_personality_experiment.utils.io import read_jsonl, write_json


def summarize_run(log_path: str | Path, aggregate_every: int) -> dict[str, Any]:
    """Build a compact summary from iteration logs."""

    records = read_jsonl(log_path)
    failure_counter: Counter[str] = Counter()
    scenario_totals: dict[str, Counter[str]] = defaultdict(Counter)
    agent_counts: Counter[str] = Counter()
    aggregate_windows: list[dict[str, Any]] = []

    for index, record in enumerate(records, start=1):
        agent_name = str(record["agent"]["name"])
        scenario_type = str(record["task"]["scenario_type"])
        agent_counts[agent_name] += 1

        for failure in record["verification"]["failure_types"]:
            failure_counter[str(failure)] += 1

        scenario_totals[scenario_type]["count"] += 1
        if record["verification"]["correct_solvability_judgment"]:
            scenario_totals[scenario_type]["correct"] += 1

        if index % aggregate_every == 0 or index == len(records):
            window_records = records[max(0, index - aggregate_every):index]
            aggregate_windows.append(
                {
                    "end_iteration": index,
                    "failure_rate": _mean(
                        1.0 if record_item["verification"]["failure_types"] else 0.0
                        for record_item in window_records
                    ),
                    "accuracy": _mean(
                        1.0 if record_item["verification"]["correct_solvability_judgment"] else 0.0
                        for record_item in window_records
                    ),
                }
            )

    scenario_accuracy = {
        scenario: (
            counts["correct"] / counts["count"] if counts["count"] else 0.0
        )
        for scenario, counts in scenario_totals.items()
    }

    return {
        "total_iterations": len(records),
        "agent_selection_counts": dict(agent_counts),
        "failure_counts": dict(failure_counter),
        "format_failure_count": int(failure_counter["invalid_json"] + failure_counter["schema_validation_failed"]),
        "scenario_accuracy": scenario_accuracy,
        "aggregate_windows": aggregate_windows,
    }


def write_summary(log_path: str | Path, output_path: str | Path, aggregate_every: int) -> dict[str, Any]:
    """Create and persist a run summary JSON file."""

    summary = summarize_run(log_path=log_path, aggregate_every=aggregate_every)
    write_json(output_path, summary)
    return summary


def _mean(values: Any) -> float:
    values_list = list(values)
    if not values_list:
        return 0.0
    return float(sum(values_list) / len(values_list))
