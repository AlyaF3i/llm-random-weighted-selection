"""Central configuration loader for the experiment."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, model_validator


class PathConfig(BaseModel):
    output_root: str = "artifacts"
    runs_dirname: str = "runs"
    analysis_dirname: str = "analysis"
    logs_filename: str = "experiment.jsonl"
    config_snapshot_filename: str = "config_snapshot.yaml"
    summary_filename: str = "summary.json"


class BackendConfig(BaseModel):
    provider: str = "ollama"
    base_url: str = "http://127.0.0.1:11434"
    model_name: str
    timeout_seconds: float = 60.0
    temperature: float = 0.0


class SelectionConfig(BaseModel):
    epsilon: float = Field(ge=0.0, le=1.0)
    metric_weights: dict[str, float]

    @model_validator(mode="after")
    def validate_weights(self) -> "SelectionConfig":
        if not self.metric_weights:
            raise ValueError("metric_weights must not be empty")
        if any(value < 0 for value in self.metric_weights.values()):
            raise ValueError("metric_weights must be non-negative")
        if sum(self.metric_weights.values()) <= 0:
            raise ValueError("metric_weights must sum to a positive value")
        return self


class MetricDefaultsConfig(BaseModel):
    initial: dict[str, float]
    baseline: dict[str, float]
    min_value: float = 0.0
    max_value: float = 1.0


class UpdateBandConfig(BaseModel):
    increase_rate: float = Field(gt=0.0, le=1.0)
    decrease_rate: float = Field(gt=0.0, le=1.0)


class UpdateRulesConfig(BaseModel):
    above_baseline: UpdateBandConfig
    below_baseline: UpdateBandConfig


class DifficultyConfig(BaseModel):
    position_upper_bound_min: int = Field(ge=4)
    position_upper_bound_max: int = Field(ge=4)
    min_move_options: int = Field(ge=2)
    max_move_options: int = Field(ge=2)
    trap_attempts: int = Field(ge=1)
    max_generation_attempts: int = Field(ge=1)

    @model_validator(mode="after")
    def validate_range(self) -> "DifficultyConfig":
        if self.position_upper_bound_max < self.position_upper_bound_min:
            raise ValueError("position_upper_bound_max must be >= position_upper_bound_min")
        if self.max_move_options < self.min_move_options:
            raise ValueError("max_move_options must be >= min_move_options")
        return self


class TaskGenerationConfig(BaseModel):
    available_moves: list[int]
    difficulty: DifficultyConfig
    constraint_presets: dict[str, Any]

    @model_validator(mode="after")
    def validate_available_moves(self) -> "TaskGenerationConfig":
        if len(self.available_moves) < 2:
            raise ValueError("available_moves must contain at least two moves")
        if 0 in self.available_moves:
            raise ValueError("available_moves must not contain 0")
        return self


class AnalysisConfig(BaseModel):
    aggregate_every: int = Field(default=10, ge=1)
    generate_after_run: bool = True


class ExperimentConfig(BaseModel):
    seed: int
    iterations: int = Field(ge=1)
    personalities_dir: str = "personalities"
    paths: PathConfig
    backend: BackendConfig
    selection: SelectionConfig
    metrics: MetricDefaultsConfig
    updates: UpdateRulesConfig
    task_generation: TaskGenerationConfig
    scenario_mix: dict[str, float]
    analysis: AnalysisConfig

    @model_validator(mode="after")
    def validate_scenario_mix(self) -> "ExperimentConfig":
        if not self.scenario_mix:
            raise ValueError("scenario_mix must not be empty")
        if any(value < 0 for value in self.scenario_mix.values()):
            raise ValueError("scenario_mix must be non-negative")
        total = sum(self.scenario_mix.values())
        if total <= 0:
            raise ValueError("scenario_mix must sum to a positive value")
        return self


def load_config(path: str | Path) -> ExperimentConfig:
    """Load and validate the YAML configuration file."""

    config_path = Path(path)
    with config_path.open("r", encoding="utf-8") as handle:
        raw_config = yaml.safe_load(handle)
    if not isinstance(raw_config, dict):
        raise ValueError("Configuration file must contain a YAML mapping at the top level")
    return ExperimentConfig.model_validate(raw_config)


def dump_config(config: ExperimentConfig, path: str | Path) -> None:
    """Persist a validated configuration snapshot."""

    config_path = Path(path)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with config_path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(config.model_dump(mode="json"), handle, sort_keys=False)
