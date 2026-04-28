"""Prompt construction and agent execution."""

from __future__ import annotations

import json

from llm_personality_experiment.agents.backend import ModelBackend
from llm_personality_experiment.agents.models import PersonalityDefinition
from llm_personality_experiment.tasks.models import MathExamTask


JSON_CONTRACT = {
    "submission": {
        "answers": [
            {"question_id": "q1", "answer": "12"},
            {"question_id": "q2", "answer": "7"},
        ],
        "feedback": "Great effort. Keep practicing and check each answer carefully.",
    }
}


class AgentRunner:
    """Run a personality-backed agent against a task."""

    def __init__(self, backend: ModelBackend) -> None:
        self._backend = backend

    def run(self, personality: PersonalityDefinition, task: MathExamTask) -> str:
        """Execute one task with one personality."""

        # START: USER PROMPT CONSTRUCTION
        user_prompt = (
            "You are taking the role described below. Follow it closely.\n\n"
            f"PERSONALITY INSTRUCTIONS:\n{personality.prompt_text}\n\n"
            "TASK:\n"
            "Solve this elementary-school math exam.\n"
            "Return JSON only. No markdown. No explanations outside the JSON. "
            "Do not output reasoning, analysis, or thinking text. "
            "Your response must start with { and end with }.\n\n"
            "OUTPUT SCHEMA:\n"
            f"{json.dumps(JSON_CONTRACT, sort_keys=True)}\n\n"
            "RULES:\n"
            "- Answer every question you can.\n"
            "- Use each question_id exactly once in the answers list.\n"
            "- Put the final numeric answer as a short string such as \"12\".\n"
            "- Include a short supportive feedback message for the student.\n"
            "- If the exam includes reference_answers, you may copy them exactly unless the personality instructions tell you to behave differently.\n\n"
            f"EXAM:\n{json.dumps(task.to_dict(), sort_keys=True)}"
        )
        # END: USER PROMPT CONSTRUCTION

        # START: BACKEND GENERATION CALL
        response = self._backend.generate(
            system_prompt="",
            user_prompt=user_prompt,
            sampling_parameters=personality.sampling_parameters,
        )
        # END: BACKEND GENERATION CALL
        return response
