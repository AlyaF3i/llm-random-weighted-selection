"""Aggregate experiment summaries from task-level JSONL logs."""

from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from llm_personality_experiment.analysis.records import flatten_attempts, get_run_metadata
from llm_personality_experiment.utils.io import read_jsonl, write_json


def summarize_run(
    log_path: str | Path,
    aggregate_every: int,
    run_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a compact summary from task-level iteration logs."""

    records = read_jsonl(log_path)
    attempts = flatten_attempts(records)
    effective_run_metadata = run_metadata or get_run_metadata(records)

    failure_counter: Counter[str] = Counter()
    scenario_totals: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    agent_counts: Counter[str] = Counter()
    agent_success_counts: Counter[str] = Counter()
    agent_failure_counts: Counter[str] = Counter()
    agent_metric_sums: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    agent_failure_breakdown: dict[str, Counter[str]] = defaultdict(Counter)
    aggregate_windows: list[dict[str, Any]] = []

    for flattened_attempt in attempts:
        record = flattened_attempt
        attempt = record["attempt"]
        agent_name = str(attempt["agent_name"])
        scenario_type = str(record["task"]["scenario_type"])
        verification = attempt["verification"]

        agent_counts[agent_name] += 1
        if attempt["had_failure"]:
            agent_failure_counts[agent_name] += 1
        else:
            agent_success_counts[agent_name] += 1

        for failure in verification["failure_types"]:
            failure_name = str(failure)
            failure_counter[failure_name] += 1
            agent_failure_breakdown[agent_name][failure_name] += 1

        scenario_totals[scenario_type]["count"] += 1
        scenario_totals[scenario_type]["correctness"] += float(verification["correctness_score"])
        scenario_totals[scenario_type]["completeness"] += float(verification["completeness_score"])
        scenario_totals[scenario_type]["supportiveness"] += float(verification["supportiveness_score"])
        scenario_totals[scenario_type]["reliability"] += float(verification["reliability"])

        for metric_name, value in attempt["metrics_after"].items():
            agent_metric_sums[agent_name][metric_name] += float(value)

    for end_index in range(aggregate_every, len(records) + aggregate_every, aggregate_every):
        window_records = records[max(0, end_index - aggregate_every):min(end_index, len(records))]
        if not window_records:
            continue
        window_attempts = flatten_attempts(window_records)
        aggregate_windows.append(
            {
                "end_iteration": int(window_records[-1]["iteration"]),
                "failure_rate": _mean(1.0 if attempt["attempt"]["had_failure"] else 0.0 for attempt in window_attempts),
                "correctness": _mean(
                    float(attempt["attempt"]["verification"]["correctness_score"])
                    for attempt in window_attempts
                ),
                "completeness": _mean(
                    float(attempt["attempt"]["verification"]["completeness_score"])
                    for attempt in window_attempts
                ),
                "supportiveness": _mean(
                    float(attempt["attempt"]["verification"]["supportiveness_score"])
                    for attempt in window_attempts
                ),
                "reliability": _mean(
                    float(attempt["attempt"]["verification"]["reliability"])
                    for attempt in window_attempts
                ),
            }
        )

    scenario_scores = {
        scenario: {
            "correctness": counts["correctness"] / counts["count"] if counts["count"] else 0.0,
            "completeness": counts["completeness"] / counts["count"] if counts["count"] else 0.0,
            "supportiveness": counts["supportiveness"] / counts["count"] if counts["count"] else 0.0,
            "reliability": counts["reliability"] / counts["count"] if counts["count"] else 0.0,
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
    agent_outcomes = {
        agent_name: {
            "attempts": int(agent_counts[agent_name]),
            "successes": int(agent_success_counts[agent_name]),
            "failures": int(agent_failure_counts[agent_name]),
            "failure_rate": agent_failure_counts[agent_name] / agent_counts[agent_name] if agent_counts[agent_name] else 0.0,
            "failure_types": dict(agent_failure_breakdown[agent_name]),
        }
        for agent_name in agent_counts
    }
    task_failure_overview = [
        {
            "iteration": int(record["iteration"]),
            "scenario_type": str(record["task"]["scenario_type"]),
            "question_count": len(record["task"]["questions"]),
            "selected_agents": list(record["selection"]["selected_agents"]),
            "failing_agents": [
                str(attempt["agent_name"])
                for attempt in record["agent_attempts"]
                if attempt["had_failure"]
            ],
            "successful_agents": [
                str(attempt["agent_name"])
                for attempt in record["agent_attempts"]
                if not attempt["had_failure"]
            ],
        }
        for record in records
    ]

    summary: dict[str, Any] = {
        "total_tasks": len(records),
        "total_attempts": len(attempts),
        "agent_selection_counts": dict(agent_counts),
        "average_agent_metrics": average_agent_metrics,
        "agent_outcomes": agent_outcomes,
        "failure_counts": dict(failure_counter),
        "format_failure_count": int(failure_counter["invalid_json"] + failure_counter["schema_validation_failed"]),
        "scenario_scores": scenario_scores,
        "task_failure_overview": task_failure_overview,
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
