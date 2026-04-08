# Ahmed Run Guide

This file explains how to install and run the project on a fresh machine.

## Required Versions

- Python: `3.11`
- Conda: recent Miniconda or Anaconda
- Ollama: required for local model runs
- Recommended model in this repo: `qwen3.5:9b`

The conda environment file already pins Python:

- [environment.yml](C:/Users/user/Desktop/study/Algorithms/project/environment.yml)

## 1. Clone The Repository

```powershell
git clone <repo-url>
cd project
```

## 2. Create The Conda Environment

```powershell
conda env create -f environment.yml
conda activate llm-personality-exp
```

## 3. Install Ollama

Download it from:

- [Ollama Download](https://ollama.com/download)

Verify:

```powershell
ollama --version
```

## 4. Pull The Model

```powershell
ollama pull qwen3.5:9b
```

Optional check:

```powershell
ollama list
```

## 5. Validate The Setup

Run the tests:

```powershell
pytest -q
```

Expected result: all tests pass.

## 6. Recommended First Config

Start with:

- [configs/easy_qwen.yaml](C:/Users/user/Desktop/study/Algorithms/project/configs/easy_qwen.yaml)

Why:

- easier elementary-school exams
- smaller operand ranges
- shorter runs than the default config
- `agents_per_task: 2`, so two agents answer the same exam each iteration
- duplicated personalities already configured for comparison
- uses `qwen3.5:9b`

## 7. Run The Experiment

```powershell
python -m llm_personality_experiment.cli run --config configs\easy_qwen.yaml
```

The command prints a JSON object with the output paths for the run directory, log file, metadata file, summary file, config snapshot, and analysis folder.

## 8. Where Results Are Stored

Each run creates a folder under:

```text
artifacts\runs\<run_id>\
```

Important files inside it:

- `experiment.jsonl` = one record per task iteration, with all invited agents inside `agent_attempts`
- `tasks.jsonl` = one record per asked exam
- `run_metadata.json` = model name and key run settings
- `summary.json` = aggregate run metrics
- `config_snapshot.yaml` = exact validated config used
- `analysis\` = generated plots

Main result files:

- `artifacts\runs\<run_id>\experiment.jsonl`
- `artifacts\runs\<run_id>\tasks.jsonl`
- `artifacts\runs\<run_id>\run_metadata.json`
- `artifacts\runs\<run_id>\summary.json`
- `artifacts\runs\<run_id>\config_snapshot.yaml`

Main plots:

- `artifacts\runs\<run_id>\analysis\metrics_over_time.png`
- `artifacts\runs\<run_id>\analysis\weights_over_time.png`
- `artifacts\runs\<run_id>\analysis\failure_rates.png`
- `artifacts\runs\<run_id>\analysis\scenario_scores.png`
- `artifacts\runs\<run_id>\analysis\selection_counts.png`
- `artifacts\runs\<run_id>\analysis\exam_scores_over_time.png`
- `artifacts\runs\<run_id>\analysis\json_validity_over_time.png`
- `artifacts\runs\<run_id>\analysis\agent_failure_counts.png`
- `artifacts\runs\<run_id>\analysis\agent_success_rates.png`
- `artifacts\runs\<run_id>\analysis\question_volume_over_time.png`
- `artifacts\runs\<run_id>\analysis\failure_type_heatmap.png`
- `artifacts\runs\<run_id>\analysis\final_metric_snapshot.png`

Several plots use thresholds or reference lines:

- metric plots use configured baselines
- some bar plots are colored by above/below average
- validity plots show a target threshold band

## 9. What Gets Stored About The Run

This matters if you compare different models later.

Stored automatically:

- the backend model name
- provider, base URL, timeout, and temperature
- `agents_per_task`
- selection epsilon and metric weights
- full task-generation settings
- personality duplication settings
- the full validated config snapshot

You can inspect those in:

- `run_metadata.json`
- `summary.json` under `run_metadata`
- each `experiment.jsonl` line under `run_metadata`
- `config_snapshot.yaml`

## 10. Generate Sample Exams Only

If you want to inspect generated tasks without running the model:

```powershell
python -m llm_personality_experiment.cli generate-sample-tasks --config configs\easy_qwen.yaml --count 10
```

To save them:

```powershell
python -m llm_personality_experiment.cli generate-sample-tasks --config configs\easy_qwen.yaml --count 10 --output artifacts\tasks\sample_tasks.json
```

## 11. Re-Analyze An Existing Run

```powershell
python -m llm_personality_experiment.cli analyze --run-dir artifacts\runs\<run_id> --aggregate-every 6
```

This regenerates:

- `summary.json`
- all plots in `analysis\`

## 12. Common Problems

### Model not found

```powershell
ollama pull qwen3.5:9b
```

### Ollama not running

```powershell
ollama list
```

If that fails, start Ollama and retry.

### Many `invalid_json` or `schema_validation_failed` records

This can still happen with local models.

Try:

- `configs/easy_qwen.yaml`
- a longer timeout
- fewer questions per exam
- fewer invited agents if your machine is slow

### Slow first run

The first request is often slower because the model is loading into memory.

## 13. Minimal Checklist

Run these commands in order:

```powershell
conda env create -f environment.yml
conda activate llm-personality-exp
ollama pull qwen3.5:9b
pytest -q
python -m llm_personality_experiment.cli run --config configs\easy_qwen.yaml
```
