"""Experiment run models."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class RunPaths:
    """Filesystem locations for one experiment run."""

    run_dir: str
    log_path: str
    tasks_path: str
    analysis_dir: str
    metadata_path: str
    summary_path: str
    config_snapshot_path: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)
