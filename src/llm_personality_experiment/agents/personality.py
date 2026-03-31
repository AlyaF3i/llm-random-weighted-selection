"""Personality loading helpers."""

from __future__ import annotations

from pathlib import Path

from llm_personality_experiment.agents.models import PersonalityDefinition


def load_personalities(directory: str | Path) -> list[PersonalityDefinition]:
    """Load all `*.md` personality prompts from a directory."""

    personalities_dir = Path(directory)
    if not personalities_dir.exists():
        raise FileNotFoundError(f"Personalities directory not found: {personalities_dir}")

    personalities: list[PersonalityDefinition] = []
    for path in sorted(personalities_dir.glob("*.md")):
        with path.open("r", encoding="utf-8") as handle:
            system_prompt = handle.read().strip()
        if not system_prompt:
            raise ValueError(f"Personality file is empty: {path}")
        personalities.append(
            PersonalityDefinition(
                name=path.stem,
                system_prompt=system_prompt,
                source_path=path.resolve(),
            )
        )
    if not personalities:
        raise ValueError(f"No personality files found in {personalities_dir}")
    return personalities
