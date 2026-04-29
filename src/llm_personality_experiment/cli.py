"""Command-line interface."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from llm_personality_experiment.analysis.comparison import compare_runs
from llm_personality_experiment.analysis.plots import generate_plots
from llm_personality_experiment.analysis.replay import launch_weight_replay
from llm_personality_experiment.analysis.summary import write_summary
from llm_personality_experiment.config import load_config
from llm_personality_experiment.experiment.runner import ExperimentRunner
from llm_personality_experiment.tasks.generator import TaskGenerator
from llm_personality_experiment.tasks.models import ScenarioType
from llm_personality_experiment.utils.io import read_jsonl


def main() -> None:
    """CLI entry point."""

    parser = argparse.ArgumentParser(prog="llm-personality-experiment")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run a full experiment")
    run_parser.add_argument("--config", required=True, help="Path to the YAML config file")

    analyze_parser = subparsers.add_parser("analyze", help="Analyze an existing run directory")
    analyze_parser.add_argument("--run-dir", required=True, help="Path to a previous run directory")
    analyze_parser.add_argument("--aggregate-every", type=int, default=10, help="Summary aggregation window")

    compare_parser = subparsers.add_parser("compare-runs", help="Compare multiple existing run directories")
    compare_parser.add_argument("--run-dir", action="append", required=True, help="Path to a run directory; pass twice or more")
    compare_parser.add_argument("--label", action="append", help="Optional label matching each run directory")
    compare_parser.add_argument("--output-dir", required=True, help="Directory where comparison plots will be written")

    replay_parser = subparsers.add_parser("replay", help="Replay one run live with animated weight updates")
    replay_parser.add_argument("--run-dir", required=True, help="Path to a previous run directory")
    replay_parser.add_argument("--interval-ms", type=int, default=1200, help="Animation interval in milliseconds")
    replay_parser.add_argument(
        "--family-view",
        action="store_true",
        help="Aggregate duplicate agents into base personality families",
    )

    sample_parser = subparsers.add_parser("generate-sample-tasks", help="Generate deterministic sample tasks")
    sample_parser.add_argument("--config", required=True, help="Path to the YAML config file")
    sample_parser.add_argument("--count", type=int, default=5, help="Number of tasks to generate")
    sample_parser.add_argument(
        "--scenario",
        choices=[scenario.value for scenario in ScenarioType],
        help="Optional fixed scenario type",
    )
    sample_parser.add_argument("--output", help="Optional output JSON file")

    args = parser.parse_args()
    if args.command == "run":
        config = load_config(args.config)
        run_paths = ExperimentRunner(config).run()
        print(json.dumps(run_paths.to_dict(), indent=2, sort_keys=True))
        return

    if args.command == "analyze":
        run_dir = Path(args.run_dir)
        log_path = run_dir / "experiment.jsonl"
        summary_path = run_dir / "summary.json"
        analysis_dir = run_dir / "analysis"
        run_metadata_path = run_dir / "run_metadata.json"
        run_metadata: dict[str, object] | None = None
        if run_metadata_path.exists():
            run_metadata = json.loads(run_metadata_path.read_text(encoding="utf-8"))
        else:
            records = read_jsonl(log_path)
            if records and isinstance(records[0].get("run_metadata"), dict):
                run_metadata = records[0]["run_metadata"]
        summary = write_summary(
            log_path=log_path,
            output_path=summary_path,
            aggregate_every=args.aggregate_every,
            run_metadata=run_metadata,
        )
        generated_plots = [str(path) for path in generate_plots(log_path=log_path, output_dir=analysis_dir)]
        print(json.dumps({"summary": summary, "plots": generated_plots}, indent=2, sort_keys=True))
        return

    if args.command == "compare-runs":
        comparison = compare_runs(run_dirs=args.run_dir, output_dir=args.output_dir, labels=args.label)
        print(json.dumps(comparison, indent=2, sort_keys=True))
        return

    if args.command == "generate-sample-tasks":
        config = load_config(args.config)
        generator = TaskGenerator(config)
        scenario = ScenarioType(args.scenario) if args.scenario else None
        tasks = [generator.generate(iteration=index + 1, scenario_type=scenario).to_dict() for index in range(args.count)]
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(json.dumps(tasks, indent=2, sort_keys=True), encoding="utf-8")
        else:
            print(json.dumps(tasks, indent=2, sort_keys=True))
        return

    if args.command == "replay":
        launch_weight_replay(run_dir=args.run_dir, interval_ms=args.interval_ms, family_view=args.family_view)
        return

    raise RuntimeError(f"Unhandled command: {args.command}")


if __name__ == "__main__":
    main()
