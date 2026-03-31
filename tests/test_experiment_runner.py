from __future__ import annotations

from pathlib import Path

from llm_personality_experiment.config import ExperimentConfig
from llm_personality_experiment.experiment.runner import ExperimentRunner


class _StubBackend:
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        return '{"answer":{"status":"NOT_SOLVABLE","moves":[]}}'


def test_experiment_runner_writes_artifacts(config, monkeypatch, tmp_path) -> None:
    config_payload = config.model_dump(mode="python")
    config_payload["iterations"] = 2
    config_payload["paths"]["output_root"] = str(tmp_path / "artifacts")
    config_payload["analysis"]["generate_after_run"] = True
    runtime_config = ExperimentConfig.model_validate(config_payload)

    monkeypatch.setattr("llm_personality_experiment.experiment.runner.create_backend", lambda _: _StubBackend())

    run_paths = ExperimentRunner(runtime_config).run()

    assert Path(run_paths.log_path).exists()
    assert Path(run_paths.summary_path).exists()
    assert (Path(run_paths.analysis_dir) / "metrics_over_time.png").exists()
