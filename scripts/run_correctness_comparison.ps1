conda activate llm-personality-exp

python -m llm_personality_experiment.cli run --config configs\correctness_only_metric_average.yaml

python -m llm_personality_experiment.cli run --config configs\correctness_only_exponential.yaml

python -m llm_personality_experiment.cli compare-runs --run-dir artifacts\runs\correctness_only_metric_average_20260429T054415Z --run-dir artifacts\runs\correctness_only_exponential_20260429T064925Z --label metric_average --label exponential --output-dir artifacts\comparisons\correctness_only_comparison

