"""Helpers for working with task-level experiment records."""

from __future__ import annotations

from typing import Any


def flatten_attempts(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Expand task-level records into attempt-level rows for analysis."""

    flattened: list[dict[str, Any]] = []
    for record in records:
        base = {
            "iteration": int(record["iteration"]),
            "task": record["task"],
            "selection": record["selection"],
            "weights_before": record["weights_before"],
            "weights_after": record["weights_after"],
            "all_agents_metrics_before": record["all_agents_metrics_before"],
            "all_agents_metrics_after": record["all_agents_metrics_after"],
            "run_metadata": record.get("run_metadata"),
        }
        for attempt in record["agent_attempts"]:
            flattened.append(base | {"attempt": attempt})
    return flattened


def get_run_metadata(records: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Extract embedded run metadata when present."""

    if not records:
        return None
    metadata = records[0].get("run_metadata")
    return metadata if isinstance(metadata, dict) else None


def get_metric_baselines(run_metadata: dict[str, Any] | None) -> dict[str, float]:
    """Return configured metric baselines for threshold-aware plots."""

    if run_metadata is None:
        return {}
    metrics = run_metadata.get("metrics")
    if not isinstance(metrics, dict):
        return {}
    baseline = metrics.get("baseline")
    if not isinstance(baseline, dict):
        return {}
    return {str(key): float(value) for key, value in baseline.items()}
