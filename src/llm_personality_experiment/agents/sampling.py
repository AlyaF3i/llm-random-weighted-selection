"""Sampling profile models and JSON loader."""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, Field

from llm_personality_experiment.config import BackendConfig


class SamplingParameters(BaseModel):
    """Per-personality sampling parameters used for generation."""

    temperature: float = Field(ge=0.0, le=2.0)
    p_sample: float = Field(ge=0.0, le=1.0)
    k_sample: int = Field(ge=1)

    @classmethod
    def from_backend_defaults(cls, backend_config: BackendConfig) -> "SamplingParameters":
        return cls(
            temperature=backend_config.temperature,
            p_sample=backend_config.p_sample,
            k_sample=backend_config.k_sample,
        )


def load_sampling_profiles(
    path: str | Path,
    personality_names: list[str],
    backend_config: BackendConfig,
) -> dict[str, SamplingParameters]:
    """Load JSON sampling parameters and resolve one profile per personality."""

    profiles_path = Path(path)
    if not profiles_path.exists():
        raise FileNotFoundError(f"Sampling parameters JSON not found: {profiles_path}")

    with profiles_path.open("r", encoding="utf-8") as handle:
        raw_payload = json.load(handle)
    if not isinstance(raw_payload, dict):
        raise ValueError("Sampling parameters JSON must contain a top-level object")

    default_parameters = SamplingParameters.from_backend_defaults(backend_config)
    if "default" in raw_payload:
        default_parameters = SamplingParameters.model_validate(raw_payload["default"])

    resolved_profiles: dict[str, SamplingParameters] = {}
    for personality_name in personality_names:
        raw_profile = raw_payload.get(personality_name)
        if raw_profile is None:
            resolved_profiles[personality_name] = default_parameters
            continue
        resolved_profiles[personality_name] = SamplingParameters.model_validate(raw_profile)

    return resolved_profiles
