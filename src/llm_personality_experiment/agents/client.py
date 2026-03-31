"""Prompt construction and agent execution."""

from __future__ import annotations

import json

from llm_personality_experiment.agents.backend import ModelBackend
from llm_personality_experiment.agents.models import PersonalityDefinition
from llm_personality_experiment.tasks.models import NavigationTask


JSON_CONTRACT = {
    "answer": {
        "status": "SOLVED",
        "moves": ["+1", "+2"],
    }
}


class AgentRunner:
    """Run a personality-backed agent against a task."""

    def __init__(self, backend: ModelBackend) -> None:
        self._backend = backend

    def run(self, personality: PersonalityDefinition, task: NavigationTask) -> str:
        """Execute one task with one personality."""

        system_prompt = (
            f"{personality.system_prompt}\n\n"
            "You must output JSON only. No markdown, no explanations, no extra text.\n"
            'Return exactly one object with the schema {"answer":{"status":"SOLVED|NOT_SOLVABLE","moves":[...]}}.\n'
            "If the task is unsolvable, return status NOT_SOLVABLE with an empty moves array.\n"
            "Do not output reasoning, thinking, analysis, XML tags, or any text before or after the JSON.\n"
            "Your response must start with { and end with }."
        )
        user_prompt = (
            "Solve this 1D navigation task and return JSON only.\n"
            f"Task:\n{json.dumps(task.to_dict(), sort_keys=True)}\n"
            f"Example schema:\n{json.dumps(JSON_CONTRACT, sort_keys=True)}"
        )
        return self._backend.generate(system_prompt=system_prompt, user_prompt=user_prompt)
