# Presentation Plan

This is a 30-minute presentation plan.

It is written to be presentation-ready, not just as a short outline. It includes:

- which run to present
- relative paths to the result artifacts
- what to say on each slide
- which image, chart, or table to add
- what happened in earlier failed versions
- why the final showcase setup makes more sense

## Primary Run To Present

Use this run as the main experiment:

- `artifacts/runs/weight_showcase_qwen_9b_20260426T160942Z/`

Main files from that run:

- `artifacts/runs/weight_showcase_qwen_9b_20260426T160942Z/summary.json`
- `artifacts/runs/weight_showcase_qwen_9b_20260426T160942Z/tasks.jsonl`
- `artifacts/runs/weight_showcase_qwen_9b_20260426T160942Z/experiment.jsonl`
- `artifacts/runs/weight_showcase_qwen_9b_20260426T160942Z/run_metadata.json`

Main charts from that run:

- `artifacts/runs/weight_showcase_qwen_9b_20260426T160942Z/analysis/weights_over_time.png`
- `artifacts/runs/weight_showcase_qwen_9b_20260426T160942Z/analysis/metrics_over_time.png`
- `artifacts/runs/weight_showcase_qwen_9b_20260426T160942Z/analysis/selection_counts.png`
- `artifacts/runs/weight_showcase_qwen_9b_20260426T160942Z/analysis/final_metric_snapshot.png`
- `artifacts/runs/weight_showcase_qwen_9b_20260426T160942Z/analysis/json_validity_over_time.png`
- `artifacts/runs/weight_showcase_qwen_9b_20260426T160942Z/analysis/agent_success_rates.png`
- `artifacts/runs/weight_showcase_qwen_9b_20260426T160942Z/analysis/failure_rates.png`

## Comparison Run To Mention As A Failure Case

Use this older run to explain what did not work:

- `artifacts/runs/easy_qwen_9b_20260425T022806Z/`

Important failure artifact:

- `artifacts/runs/easy_qwen_9b_20260425T022806Z/summary.json`

Why it matters:

- all attempts failed with `invalid_json`
- all scenario scores were `0.0`
- weights mostly collapsed for everyone
- it showed the penalty mechanism, but not the reward mechanism

## High-Level Story For The Whole Talk

The talk should tell this story:

1. We wanted to show adaptive weighted selection among prompt personalities.
2. The early task setups were too hard or too strict for the chosen local model.
3. That made the model fail formatting or task completion, so the experiment only showed penalties.
4. We then simplified the task deliberately to isolate prompt behavior from reasoning difficulty.
5. In the final run, the ranking became meaningful:
   - `always_correct` ended highest
   - `sometimes_correct` ended in the middle
   - `always_nice_teacher` ended lowest
6. Therefore, the framework does demonstrate the intended effect when the task is controlled enough.

## Slide 1: Title

Title:
- Adaptive Weighted Selection of LLM Personalities

Content:
- course/project title if needed
- your name and teammate names
- one-line claim:
  - better measured behavior should produce higher selection weights over time

Add:
- small crop from `artifacts/runs/weight_showcase_qwen_9b_20260426T160942Z/analysis/weights_over_time.png`

Speaker notes:
- start with the end goal, not implementation details
- tell the audience the whole project is about dynamic preference among prompt personalities

Suggested time:
- 2 minutes

## Slide 2: Motivation

Title:
- Why This Experiment Matters

Content:
- many personalities can share the same base LLM
- prompts change behavior even when the model stays fixed
- we want a deterministic way to compare those behaviors
- we want the system to prefer stronger performers automatically

Add:
- simple conceptual diagram:
  - one model
  - multiple personalities
  - repeated tasks
  - adaptive reweighting

Speaker notes:
- emphasize that the base model stays fixed
- only prompt personality and measured outcomes differ

Suggested time:
- 2 minutes

## Slide 3: Research Question

Title:
- What Exactly Are We Testing?

Content:
- if multiple prompt personalities answer the same tasks,
- and we score them deterministically,
- will the selection weights move upward for better behavior
- and downward for worse behavior?

Add:
- one short bullet list or one text box

Speaker notes:
- make this slide crisp
- this is the question the rest of the deck should answer

Suggested time:
- 1.5 minutes

## Slide 4: System Architecture

Title:
- Experiment Pipeline

Content:
- generate deterministic task
- select `k` agents using weighted random sampling with epsilon exploration
- collect outputs
- verify outputs without another LLM
- update metrics
- recompute weights
- log everything for replay and analysis

Add:
- flowchart

Suggested flow:
- task generator
- selected personalities
- model outputs
- verifier
- metric update
- new weights

Speaker notes:
- mention that all runs are fully logged
- mention that task verification is deterministic

Suggested time:
- 2.5 minutes

## Slide 5: Metrics And Weight Formula

Title:
- How The System Decides Who Is Better

Content:
- four tracked metrics:
  - correctness
  - completeness
  - supportiveness
  - reliability
- weights are computed as a weighted average of these metrics
- correctness has the highest coefficient in the current config

Add:
- formula block

Suggested formula:

```text
weight_i =
(0.45 * correctness_i
 + 0.20 * completeness_i
 + 0.15 * supportiveness_i
 + 0.20 * reliability_i)
/ 1.00
```

Speaker notes:
- this is important for interpreting the final results
- explain that valid JSON helps, but correctness dominates

Suggested time:
- 2.5 minutes

## Slide 6: Update Logic

Title:
- Why Weights Can Move Up Or Down

Content:
- each metric is updated after observation
- if an agent performs well, its metrics move up
- if it performs poorly, its metrics move down
- the rates are baseline-aware

Add:
- small equations or one pseudo-code box

Suggested pseudo-code:

```text
if observed >= current:
    move upward
else:
    move downward
```

Speaker notes:
- no need to overload the audience with all constants
- focus on the directional logic

Suggested time:
- 2 minutes

## Slide 7: Early Version Of The Project

Title:
- Earlier Task Designs We Tried

Content:
- the project originally started with a harder deterministic task family
- earlier versions included more complex structured reasoning tasks
- later math-exam versions still used multi-question tasks and strict JSON
- these setups were valid technically, but not good for the final demonstration

Add:
- one timeline slide

Suggested timeline:
- structured reasoning / path-style task
- multi-question arithmetic task
- final showcase task with visible reference answers

Speaker notes:
- be honest that the project evolved
- say this evolution improved the clarity of the experiment

Suggested time:
- 2 minutes

## Slide 8: What Failed In The Earlier Run

Title:
- Why The Earlier Math Run Did Not Support The Story

Content:
- use `artifacts/runs/easy_qwen_9b_20260425T022806Z/summary.json`
- 42 logged tasks
- 126 total attempts
- 126 `invalid_json` failures
- all scenario scores were `0.0`
- every agent’s failure rate was `1.0`

Add:
- one table and one chart

Suggested table:

| Metric | Earlier run |
|---|---:|
| Logged tasks | 42 |
| Attempts | 126 |
| Format failures | 126 |
| Correctness | 0.0 |
| Reliability | 0.0 |

Suggested chart:
- `artifacts/runs/easy_qwen_9b_20260425T022806Z/analysis/failure_rates.png`

Speaker notes:
- this run only demonstrated punishment
- it did not demonstrate reward
- therefore it was not enough for the final presentation claim

Suggested time:
- 3 minutes

## Slide 9: Why The Earlier Run Failed

Title:
- Why Those Results Were Not Good Enough

Content:
- the model struggled with strict JSON-only output
- the tasks were still too demanding for a clean showcase
- the experiment mixed reasoning difficulty with prompt behavior
- because almost everyone failed, the weights mostly reflected repeated penalties

Add:
- short bullet slide

Speaker notes:
- say “the model was not bad in a general sense”
- say “the setup was bad for the demonstration goal”
- the important point is mismatch between task difficulty and presentation objective

Suggested time:
- 2 minutes

## Slide 10: Final Showcase Redesign

Title:
- How We Redesigned The Task To Isolate Behavior

Content:
- final run used a one-question addition task
- every task exposed `reference_answers`
- the task became almost trivial
- now differences should come from prompt behavior, not arithmetic difficulty

Use config:
- `configs/easy_qwen.yaml`

Important config choices:
- `iterations: 30`
- `agents_per_task: 3`
- `include_reference_answers: true`
- addition only
- one question only
- `qwen3.5:9b`

Add:
- screenshot or text snippet from `configs/easy_qwen.yaml`
- one example task from `artifacts/runs/weight_showcase_qwen_9b_20260426T160942Z/tasks.jsonl`

Speaker notes:
- explicitly say this was a deliberate showcase design
- the task is simplified on purpose

Suggested time:
- 3 minutes

## Slide 11: Personality Definitions In The Final Run

Title:
- How We Forced Behavioral Separation

Content:
- `always_correct`:
  - copy `reference_answers`
- `sometimes_correct`:
  - odd iterations correct
  - even iterations intentionally wrong on the first answer
- `always_nice_teacher`:
  - valid JSON
  - kind feedback
  - wrong answer `"0"`

Add:
- one 3-row table

Suggested table:

| Personality | Rule | Expected rank |
|---|---|---|
| `always_correct` | always copy answer key | highest |
| `sometimes_correct` | alternate correct and wrong | middle |
| `always_nice_teacher` | valid but wrong | lowest |

Speaker notes:
- this slide is critical
- it explains why the final run should be interpretable

Suggested time:
- 3 minutes

## Slide 12: Main Result

Title:
- Final Weight Curves Show Separation

Content:
- the three families separated as intended
- `always_correct` rose the highest
- `sometimes_correct` stayed in the middle
- `always_nice_teacher` stayed lowest

Add:
- `artifacts/runs/weight_showcase_qwen_9b_20260426T160942Z/analysis/weights_over_time.png`

Speaker notes:
- this is the central evidence slide
- spend time here
- explain the ordering clearly

Suggested time:
- 3.5 minutes

## Slide 13: Quantitative Family-Level Summary

Title:
- Aggregated Family Results

Content:
- collapse the duplicate agents into base personality families

Add:
- one table with the family-level summary

Suggested table:

| Family | Attempts | Successes | Failures | Success rate | Avg correctness metric | Avg final weight |
|---|---:|---:|---:|---:|---:|---:|
| `always_correct` | 31 | 30 | 1 | 96.8% | 0.627 | 0.747 |
| `sometimes_correct` | 34 | 34 | 0 | 100.0% | 0.421 | 0.610 |
| `always_nice_teacher` | 25 | 25 | 0 | 100.0% | 0.191 | 0.421 |

Speaker notes:
- define success rate carefully:
  - success here means a valid attempt, not necessarily a correct answer
- correctness and final weight are the more important columns

Suggested time:
- 3 minutes

## Slide 14: Correctness Versus Reliability

Title:
- Valid JSON Is Not The Same As Correctness

Content:
- almost all final-run outputs were valid JSON
- `always_nice_teacher` still ranked low because correctness was weak
- this is desirable behavior
- the framework is not fooled by formatting alone

Add:
- `artifacts/runs/weight_showcase_qwen_9b_20260426T160942Z/analysis/json_validity_over_time.png`
- `artifacts/runs/weight_showcase_qwen_9b_20260426T160942Z/analysis/final_metric_snapshot.png`

Speaker notes:
- emphasize that this is one of the strongest design points of the experiment

Suggested time:
- 2 minutes

## Slide 15: Selection Pressure

Title:
- Higher Weights Influence Future Selection

Content:
- once weights diverged, stronger agents became more competitive in selection
- duplicates can still differ because of stochastic exposure and epsilon exploration
- this is expected in weighted random selection

Add:
- `artifacts/runs/weight_showcase_qwen_9b_20260426T160942Z/analysis/selection_counts.png`

Speaker notes:
- explain why the duplicate agents are not perfectly identical in counts
- mention exploration and random sampling

Suggested time:
- 1.5 minutes

## Slide 16: One Remaining Noise Source

Title:
- Imperfections That Still Appeared

Content:
- one `always_correct` copy had one `invalid_json` failure
- one `sometimes_correct` copy accumulated stronger correctness than its twin
- this does not break the overall story
- it shows that even a controlled setup still contains stochastic effects

Add:
- `artifacts/runs/weight_showcase_qwen_9b_20260426T160942Z/analysis/agent_success_rates.png`

Speaker notes:
- this slide helps you sound rigorous and honest

Suggested time:
- 1.5 minutes

## Slide 17: Final Takeaway

Title:
- Did The Framework Demonstrate The Intended Effect?

Content:
- yes
- the final showcase run demonstrated both sides of the mechanism:
  - stronger behavior received higher weights
  - weaker behavior stayed lower
- the earlier failed run showed why task design matters
- the final redesign isolated the intended behavior clearly

Add:
- one takeaway box

Suggested takeaway:

```text
When the task is controlled enough to separate prompt behavior from reasoning difficulty,
the adaptive weighting mechanism behaves as intended.
```

Suggested time:
- 2 minutes

## Slide 18: Limitations And Future Work

Title:
- What We Would Improve Next

Content:
- add family-level plots directly in the code
- run longer experiments
- compare more models
- test slightly harder tasks after this showcase baseline
- tune prompts and sampling systematically
- add confidence intervals over multiple repeated runs

Add:
- no chart required

Suggested time:
- 1.5 minutes

## Backup Material

If you have extra time or get questions, keep these ready:

- one sample task from:
  - `artifacts/runs/weight_showcase_qwen_9b_20260426T160942Z/tasks.jsonl`
- one successful `always_correct` attempt from:
  - `artifacts/runs/weight_showcase_qwen_9b_20260426T160942Z/experiment.jsonl`
- one wrong-but-valid `always_nice_teacher` attempt from:
  - `artifacts/runs/weight_showcase_qwen_9b_20260426T160942Z/experiment.jsonl`
- one comparison screenshot from the failed run:
  - `artifacts/runs/easy_qwen_9b_20260425T022806Z/analysis/failure_rates.png`

## Presenter Notes

Points to emphasize:

- the model stayed fixed; the prompt personalities changed
- the verifier was deterministic and did not use another LLM
- the final task was intentionally simplified to isolate the weighting behavior
- the final claim is about the framework’s mechanism, not about permanent human-like traits

Points not to overclaim:

- do not say the experiment proves true “personalities”
- do not say valid JSON alone means good performance
- do not say the failed earlier run was useless
  - it was useful because it revealed why the task had to be simplified

Recommended speaking rhythm:

- first 10 minutes:
  - motivation, architecture, metrics, history
- middle 10 minutes:
  - failed run, redesign, final setup
- last 10 minutes:
  - final results, interpretation, limitations, Q&A setup
