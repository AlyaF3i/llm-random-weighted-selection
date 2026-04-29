from __future__ import annotations

from pathlib import Path

from llm_personality_experiment.analysis.comparison import compare_runs
from llm_personality_experiment.config import ExperimentConfig
from llm_personality_experiment.experiment.runner import ExperimentRunner


class _StubBackend:
    def generate(self, system_prompt: str, user_prompt: str, sampling_parameters=None) -> str:
        return '{"submission":{"answers":[{"question_id":"q1","answer":"5"},{"question_id":"q2","answer":"6"},{"question_id":"q3","answer":"9"}],"feedback":"Great work, keep practicing and check carefully."}}'


def test_compare_runs_generates_plots(config, monkeypatch, tmp_path) -> None:
    monkeypatch.setattr("llm_personality_experiment.experiment.runner.create_backend", lambda _: _StubBackend())

    metric_average_payload = config.model_dump(mode="python")
    metric_average_payload["paths"]["output_root"] = str(tmp_path / "artifacts_metric")
    metric_average_payload["analysis"]["generate_after_run"] = False
    metric_average_payload["selection"]["metric_weights"] = {
        "correctness": 1.0,
        "completeness": 0.0,
        "supportiveness": 0.0,
        "reliability": 0.0,
    }
    metric_average_payload["selection"]["weight_update_rule"] = "metric_average"
    metric_average_payload["experiment_name"] = "metric_average_correctness_only"

    exponential_payload = config.model_dump(mode="python")
    exponential_payload["paths"]["output_root"] = str(tmp_path / "artifacts_exponential")
    exponential_payload["analysis"]["generate_after_run"] = False
    exponential_payload["selection"]["metric_weights"] = {
        "correctness": 1.0,
        "completeness": 0.0,
        "supportiveness": 0.0,
        "reliability": 0.0,
    }
    exponential_payload["selection"]["weight_update_rule"] = "exponential"
    exponential_payload["selection"]["exponential_eta"] = 1.25
    exponential_payload["experiment_name"] = "exponential_correctness_only"

    metric_average_run = ExperimentRunner(ExperimentConfig.model_validate(metric_average_payload)).run()
    exponential_run = ExperimentRunner(ExperimentConfig.model_validate(exponential_payload)).run()

    comparison_dir = tmp_path / "comparison"
    comparison = compare_runs(
        run_dirs=[metric_average_run.run_dir, exponential_run.run_dir],
        output_dir=comparison_dir,
        labels=["metric_average", "exponential"],
    )

    assert (comparison_dir / "comparison_summary.json").exists()
    assert (comparison_dir / "family_final_weights_comparison.png").exists()
    assert (comparison_dir / "family_weight_trajectories_comparison.png").exists()
    assert len(comparison["runs"]) == 2
