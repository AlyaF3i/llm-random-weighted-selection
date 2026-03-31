# Ahmed Run Guide

This file explains exactly how to install the project and run it on a fresh machine.

## Required Versions

- Python: `3.11`
- Conda: any recent Miniconda or Anaconda
- Ollama: required for the local model backend
- Model used by the project: `qwen3.5:9b`

## 1. Clone The Repository

Open a terminal in the directory where you want the project:

```powershell
git clone <repo-url>
cd project
```

## 2. Create The Conda Environment

The repo already includes an environment file:

- [environment.yml](C:/Users/user/Desktop/study/Algorithms/project/environment.yml)

Create the environment:

```powershell
conda env create -f environment.yml
```

Activate it:

```powershell
conda activate llm-personality-exp
```

## 3. Install Ollama

Install Ollama from:

- [https://ollama.com/download](https://ollama.com/download)

After installing, verify it:

```powershell
ollama --version
```

## 4. Pull The Model

Pull the exact model used by the configs:

```powershell
ollama pull qwen3.5:9b
```

Verify it exists:

```powershell
ollama list
```

## 5. Check The Project Install

Run the tests:

```powershell
pytest -q
```

Expected result: all tests should pass.

## 6. Recommended Config

Use this easier config first:

- [configs/easy_qwen.yaml](C:/Users/user/Desktop/study/Algorithms/project/configs/easy_qwen.yaml)

Why this config:

- smaller position range
- fewer move types
- more solvable tasks
- fewer trap and constraint-heavy tasks
- same model: `qwen3.5:9b`

## 7. Run The Experiment

Run:

```powershell
python -m llm_personality_experiment.cli run --config configs\easy_qwen.yaml
```

The command prints a JSON object with the output paths.

## 8. Where Results Are Stored

Each run creates a directory under:

```text
artifacts\runs\<run_id>\
```

Inside that folder:

- `experiment.jsonl` = one full record per iteration
- `summary.json` = aggregate results
- `config_snapshot.yaml` = exact config used for that run
- `analysis\` = generated plots

Important output files:

- `artifacts\runs\<run_id>\experiment.jsonl`
- `artifacts\runs\<run_id>\summary.json`
- `artifacts\runs\<run_id>\analysis\metrics_over_time.png`
- `artifacts\runs\<run_id>\analysis\weights_over_time.png`
- `artifacts\runs\<run_id>\analysis\failure_rates.png`
- `artifacts\runs\<run_id>\analysis\scenario_performance.png`

## 9. Generate Sample Tasks Only

If you want to inspect tasks without running the full experiment:

```powershell
python -m llm_personality_experiment.cli generate-sample-tasks --config configs\easy_qwen.yaml --count 10
```

To save them:

```powershell
python -m llm_personality_experiment.cli generate-sample-tasks --config configs\easy_qwen.yaml --count 10 --output artifacts\tasks\sample_tasks.json
```

## 10. Re-Analyze An Existing Run

If a run already exists, generate the summary and plots again:

```powershell
python -m llm_personality_experiment.cli analyze --run-dir artifacts\runs\<run_id> --aggregate-every 4
```

## 11. Common Problems

### Model not found

Fix:

```powershell
ollama pull qwen3.5:9b
```

### Ollama not running

Try:

```powershell
ollama list
```

If that fails, start Ollama and retry.

### Too many `invalid_json` failures

This can still happen with local models.
Use the easier config first:

- `configs/easy_qwen.yaml`

If needed, increase backend timeout in the config.

### Slow first run

The first request can be slower because the model is loading into memory.

## 12. Minimal Run Checklist

Run these commands in order:

```powershell
conda env create -f environment.yml
conda activate llm-personality-exp
ollama pull qwen3.5:4b
pytest -q
python -m llm_personality_experiment.cli run --config configs\easy_qwen.yaml
```
