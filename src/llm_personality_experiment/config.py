"""Central configuration loader for the experiment."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field, model_validator


class PathConfig(BaseModel):
    output_root: str = "artifacts"
    runs_dirname: str = "runs"
    analysis_dirname: str = "analysis"
    logs_filename: str = "experiment.jsonl"
    tasks_filename: str = "tasks.jsonl"
    metadata_filename: str = "run_metadata.json"
    config_snapshot_filename: str = "config_snapshot.yaml"
    summary_filename: str = "summary.json"


class BackendConfig(BaseModel):
    provider: str = "ollama"
    base_url: str = "http://127.0.0.1:11434"
    model_name: str
    timeout_seconds: float = 60.0
    temperature: float = 0.0
    p_sample: float = Field(default=0.9, ge=0.0, le=1.0)
    k_sample: int = Field(default=40, ge=1)


class PersonalitiesConfig(BaseModel):
    duplication: dict[str, int] = Field(default_factory=dict)
    sampling_parameters_path: str = "configs/personality_sampling.json"

    @model_validator(mode="after")
    def validate_duplication(self) -> "PersonalitiesConfig":
        if any(value < 0 for value in self.duplication.values()):
            raise ValueError("personality duplication counts must be non-negative")
        return self


class SelectionConfig(BaseModel):
    epsilon: float = Field(ge=0.0, le=1.0)
    agents_per_task: int = Field(ge=1)
    metric_weights: dict[str, float]
    weight_update_rule: Literal["metric_average", "exponential"] = "metric_average"
    exponential_eta: float = Field(default=1.0, gt=0.0)

    @model_validator(mode="after")
    def validate_weights(self) -> "SelectionConfig":
        required = {"correctness", "completeness", "supportiveness", "reliability"}
        if set(self.metric_weights) != required:
            raise ValueError(f"metric_weights must contain exactly {sorted(required)}")
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

    @model_validator(mode="after")
    def validate_metrics(self) -> "MetricDefaultsConfig":
        required = {"correctness", "completeness", "supportiveness", "reliability"}
        if set(self.initial) != required or set(self.baseline) != required:
            raise ValueError(f"metrics.initial and metrics.baseline must contain exactly {sorted(required)}")
        return self


class UpdateBandConfig(BaseModel):
    increase_rate: float = Field(gt=0.0, le=1.0)
    decrease_rate: float = Field(gt=0.0, le=1.0)


class UpdateRulesConfig(BaseModel):
    above_baseline: UpdateBandConfig
    below_baseline: UpdateBandConfig


class OperationConfig(BaseModel):
    min_operand: int = Field(ge=0)
    max_operand: int = Field(ge=0)
    non_negative_only: bool = True

    @model_validator(mode="after")
    def validate_range(self) -> "OperationConfig":
        if self.max_operand < self.min_operand:
            raise ValueError("operation max_operand must be >= min_operand")
        return self


class TaskGenerationConfig(BaseModel):
    grade_label: str
    questions_per_exam_min: int = Field(ge=1)
    questions_per_exam_max: int = Field(ge=1)
    points_per_question: int = Field(ge=1)
    include_reference_answers: bool = False
    operations: dict[str, OperationConfig]
    mixed_operation_pool: list[str]

    @model_validator(mode="after")
    def validate_ranges(self) -> "TaskGenerationConfig":
        if self.questions_per_exam_max < self.questions_per_exam_min:
            raise ValueError("questions_per_exam_max must be >= questions_per_exam_min")
        if not self.operations:
            raise ValueError("task_generation.operations must not be empty")
        for operation_name in self.mixed_operation_pool:
            if operation_name not in self.operations:
                raise ValueError(f"mixed operation {operation_name} is missing from operations")
        return self


class FeedbackEvaluationConfig(BaseModel):
    positive_keywords: list[str]
    coaching_keywords: list[str]
    banned_keywords: list[str]
    min_words: int = Field(ge=1)


class EvaluationConfig(BaseModel):
    feedback: FeedbackEvaluationConfig


class AnalysisConfig(BaseModel):
    aggregate_every: int = Field(default=10, ge=1)
    generate_after_run: bool = True


class ExperimentConfig(BaseModel):
    experiment_name: str = "experiment"
    seed: int
    iterations: int = Field(ge=1)
    personalities_dir: str = "personalities"
    personalities: PersonalitiesConfig = Field(default_factory=PersonalitiesConfig)
    paths: PathConfig
    backend: BackendConfig
    selection: SelectionConfig
    metrics: MetricDefaultsConfig
    updates: UpdateRulesConfig
    task_generation: TaskGenerationConfig
    evaluation: EvaluationConfig
    scenario_mix: dict[str, float]
    analysis: AnalysisConfig

    @model_validator(mode="after")
    def validate_scenario_mix(self) -> "ExperimentConfig":
        if not self.experiment_name.strip():
            raise ValueError("experiment_name must not be empty")
        required = {"addition", "subtraction", "multiplication", "mixed_review"}
        if set(self.scenario_mix) != required:
            raise ValueError(f"scenario_mix must contain exactly {sorted(required)}")
        if any(value < 0 for value in self.scenario_mix.values()):
            raise ValueError("scenario_mix must be non-negative")
        total = sum(self.scenario_mix.values())
        if total <= 0:
            raise ValueError("scenario_mix must sum to a positive value")
        return self


def load_config(path: str | Path) -> ExperimentConfig:
    """Load and validate the YAML configuration file."""

    # START: YAML CONFIG LOADING AND VALIDATION
    config_path = Path(path)
    with config_path.open("r", encoding="utf-8") as handle:
        raw_config = yaml.safe_load(handle)
    if not isinstance(raw_config, dict):
        raise ValueError("Configuration file must contain a YAML mapping at the top level")
    validated_config = ExperimentConfig.model_validate(raw_config)
    # END: YAML CONFIG LOADING AND VALIDATION
    return validated_config


def dump_config(config: ExperimentConfig, path: str | Path) -> None:
    """Persist a validated configuration snapshot."""

    # START: CONFIG SNAPSHOT WRITING
    config_path = Path(path)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with config_path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(config.model_dump(mode="json"), handle, sort_keys=False)
    # END: CONFIG SNAPSHOT WRITING
