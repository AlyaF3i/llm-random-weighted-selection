"""JSONL logger for full experiment replay."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class JSONLExperimentLogger:
    """Append-only structured logger."""

    def __init__(self, log_path: str | Path) -> None:
        self._log_path = Path(log_path)
        self._log_path.parent.mkdir(parents=True, exist_ok=True)

    @property
    def path(self) -> Path:
        return self._log_path

    def log(self, record: dict[str, Any]) -> None:
        with self._log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, sort_keys=True))
            handle.write("\n")
