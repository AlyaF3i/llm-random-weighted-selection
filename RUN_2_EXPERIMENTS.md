# Run 2 Experiments

Copy and run these commands:

```powershell
conda activate llm-personality-exp
python -m llm_personality_experiment.cli run --config configs\correctness_only_metric_average.yaml
python -m llm_personality_experiment.cli run --config configs\correctness_only_exponential.yaml
```

After both runs finish, copy the two `run_dir` values printed by the CLI and run:

```powershell
python -m llm_personality_experiment.cli compare-runs --run-dir artifacts\runs\<metric_average_run_id> --run-dir artifacts\runs\<exponential_run_id> --label metric_average --label exponential --output-dir artifacts\comparisons\correctness_only_comparison
```
