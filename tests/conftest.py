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
            "experiment_name": "test_experiment",
            "seed": 123,
            "iterations": 6,
            "personalities_dir": "personalities",
            "personalities": {
                "duplication": {
                    "always_correct": 2,
                },
                "sampling_parameters_path": "configs/personality_sampling.json",
            },
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
                "p_sample": 0.9,
                "k_sample": 40,
            },
            "selection": {
                "epsilon": 0.1,
                "agents_per_task": 2,
                "metric_weights": {
                    "correctness": 0.45,
                    "completeness": 0.2,
                    "supportiveness": 0.15,
                    "reliability": 0.2,
                },
            },
            "metrics": {
                "initial": {
                    "correctness": 0.5,
                    "completeness": 0.5,
                    "supportiveness": 0.5,
                    "reliability": 0.5,
                },
                "baseline": {
                    "correctness": 0.5,
                    "completeness": 0.5,
                    "supportiveness": 0.5,
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
                    "decrease_rate": 0.2,
                },
            },
            "task_generation": {
                "grade_label": "elementary school",
                "questions_per_exam_min": 3,
                "questions_per_exam_max": 4,
                "points_per_question": 1,
                "operations": {
                    "addition": {
                        "min_operand": 0,
                        "max_operand": 10,
                        "non_negative_only": True,
                    },
                    "subtraction": {
                        "min_operand": 0,
                        "max_operand": 10,
                        "non_negative_only": True,
                    },
                    "multiplication": {
                        "min_operand": 0,
                        "max_operand": 6,
                        "non_negative_only": True,
                    },
                },
                "mixed_operation_pool": ["addition", "subtraction", "multiplication"],
            },
            "evaluation": {
                "feedback": {
                    "positive_keywords": ["great", "good job", "well done"],
                    "coaching_keywords": ["keep practicing", "check"],
                    "banned_keywords": ["bad", "stupid"],
                    "min_words": 4,
                }
            },
            "scenario_mix": {
                "addition": 0.4,
                "subtraction": 0.3,
                "multiplication": 0.2,
                "mixed_review": 0.1,
            },
            "analysis": {
                "aggregate_every": 3,
                "generate_after_run": False,
            },
        }
    )
