from __future__ import annotations

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from llm_personality_experiment.config import ExperimentConfig


@pytest.fixture()
def config() -> ExperimentConfig:
    return ExperimentConfig.model_validate(
        {
            "seed": 123,
            "iterations": 8,
            "personalities_dir": "personalities",
            "paths": {
                "output_root": "artifacts",
                "runs_dirname": "runs",
                "analysis_dirname": "analysis",
                "logs_filename": "experiment.jsonl",
                "config_snapshot_filename": "config_snapshot.yaml",
                "summary_filename": "summary.json",
            },
            "backend": {
                "provider": "ollama",
                "base_url": "http://127.0.0.1:11434",
                "model_name": "test-model",
                "timeout_seconds": 5.0,
                "temperature": 0.0,
            },
            "selection": {
                "epsilon": 0.1,
                "metric_weights": {
                    "efficiency": 0.3,
                    "honesty": 0.25,
                    "discernment": 0.2,
                    "reliability": 0.25,
                },
            },
            "metrics": {
                "initial": {
                    "efficiency": 0.5,
                    "honesty": 0.5,
                    "discernment": 0.5,
                    "reliability": 0.5,
                },
                "baseline": {
                    "efficiency": 0.5,
                    "honesty": 0.5,
                    "discernment": 0.5,
                    "reliability": 0.5,
                },
                "min_value": 0.0,
                "max_value": 1.0,
            },
            "updates": {
                "above_baseline": {
                    "increase_rate": 0.05,
                    "decrease_rate": 0.08,
                },
                "below_baseline": {
                    "increase_rate": 0.12,
                    "decrease_rate": 0.20,
                },
            },
            "task_generation": {
                "available_moves": [-2, -1, 1, 2, 3],
                "difficulty": {
                    "position_upper_bound_min": 6,
                    "position_upper_bound_max": 8,
                    "min_move_options": 3,
                    "max_move_options": 4,
                    "trap_attempts": 20,
                    "max_generation_attempts": 300,
                },
                "constraint_presets": {
                    "checkpoints_max": 2,
                    "max_move_slack_min": 1,
                    "max_move_slack_max": 3,
                },
            },
            "scenario_mix": {
                "solvable": 0.25,
                "unsolvable": 0.25,
                "trap": 0.25,
                "constraint_heavy": 0.25,
            },
            "analysis": {
                "aggregate_every": 4,
                "generate_after_run": False,
            },
        }
    )
