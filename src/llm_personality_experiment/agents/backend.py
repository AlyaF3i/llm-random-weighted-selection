"""Backend abstraction for model calls."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Protocol
from urllib import error, request

from llm_personality_experiment.config import BackendConfig


class ModelBackend(Protocol):
    """Protocol implemented by concrete backend adapters."""

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """Generate a response from the model."""


@dataclass
class OllamaBackend:
    """Minimal Ollama chat backend with deterministic options."""

    config: BackendConfig

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        messages: list[dict[str, str]] = []
        if system_prompt.strip():
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_prompt})

        payload = json.dumps(
            {
                "model": self.config.model_name,
                "stream": False,
                "format": "json",
                "messages": messages,
                "options": {
                    "temperature": self.config.temperature,
                },
            }
        ).encode("utf-8")

        endpoint = f"{self.config.base_url.rstrip('/')}/api/chat"
        http_request = request.Request(
            endpoint,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with request.urlopen(http_request, timeout=self.config.timeout_seconds) as response:
                response_payload = json.loads(response.read().decode("utf-8"))
        except error.URLError as exc:
            raise RuntimeError(f"Failed to call Ollama backend at {endpoint}: {exc}") from exc

        message = response_payload.get("message", {})
        content = message.get("content")
        if not isinstance(content, str):
            raise RuntimeError("Ollama response missing message.content")
        return content.strip()


def create_backend(config: BackendConfig) -> ModelBackend:
    """Instantiate the configured backend."""

    if config.provider != "ollama":
        raise ValueError(f"Unsupported backend provider: {config.provider}")
    return OllamaBackend(config)
