# Chart Guide For The Showcase Run

This document explains the charts for the run:

`artifacts/runs/weight_showcase_qwen_9b_20260426T160942Z`

The analysis images are in:

`artifacts/runs/weight_showcase_qwen_9b_20260426T160942Z/analysis`

## What This Run Is Testing

This run is intentionally a simple weight-update showcase, not a hard reasoning benchmark.

- Model: `qwen3.5:9b`
- Total tasks: `30`
- Agents selected per task: `3`
- Personality families: `always_correct`, `sometimes_correct`, `always_nice_teacher`
- Duplicate agents per family: `2`
- Task type: one-question elementary addition exam
- Operand range: `1..4`
- Questions per task: exactly `1`
- Reference answers: included in the task payload

That means the experiment is mainly testing whether the adaptive weighting logic can separate:

- a family that should almost always be correct
- a family that should be mixed
- a family that should stay kind but academically wrong

## The Most Important Clarification

In this codebase, `failure` does not mean "wrong answer."

It means a format or validation problem such as:

- invalid JSON
- schema validation failure
- duplicate question IDs
- unknown question IDs
- missing required feedback

So in this run:

- `always_correct` had the only true failure: `1` `invalid_json`
- `always_nice_teacher` was usually wrong academically, but not failing structurally
- `sometimes_correct` was structurally valid and academically mixed

This is why failure plots and correctness plots are telling different stories.

## Why Only Correctness Follows The Expected Pattern

For this showcase task, `correctness` is the real signal. The other metrics are mostly saturated or measuring something else.

### Correctness

Meaning:

- academic accuracy on the exam
- in this run, because each task has one question worth one point, correctness is effectively "did the agent give the right answer or not?"

Why it is informative here:

- `always_correct` full-credit rate: `30 / 31 = 96.8%`
- `sometimes_correct` full-credit rate: `16 / 34 = 47.1%`
- `always_nice_teacher` full-credit rate: `0 / 25 = 0%`

This is the metric that should drive the story, and it does.

### Completeness

Meaning:

- fraction of questions answered

Why it is weak here:

- every task has only one question
- when an agent returns valid JSON, it almost always answers that one question
- so completeness is close to `1.0` for almost everybody

Interpretation:

- completeness is technically correct
- it is not very discriminative for this particular setup

### Reliability

Meaning:

- whether the response was structurally valid enough to parse and validate

Why it is weak here:

- almost every output was valid JSON and schema-valid
- only one attempt failed structurally
- therefore reliability stays high for almost everyone

Interpretation:

- reliability is useful for catching formatting collapses
- it is not the main signal in this run because formatting was mostly stable

### Supportiveness

Meaning:

- whether the feedback text sounds encouraging and contains the configured coaching language

Why it does not match correctness:

- supportiveness measures tone, not academic accuracy
- `always_nice_teacher` can be very supportive while still giving wrong answers
- the verifier intentionally allows those to separate

Interpretation:

- supportiveness is behaving correctly
- it is just measuring a different axis than the one your showcase is trying to highlight

## Why `sometimes_correct` Was Selected More Than `always_correct`

Short answer: yes, partly randomness, then reinforcement.

The selection counts by family were:

- `sometimes_correct`: `34`
- `always_correct`: `31`
- `always_nice_teacher`: `25`

Why this happened:

- selection uses weighted random sampling, not greedy argmax
- `epsilon = 0.1`, so some exploration is guaranteed
- each family has two duplicates, and duplicates can drift apart
- `sometimes_correct__02` happened to realize a stronger trajectory than `sometimes_correct__01`
- once one duplicate gets a slightly better path early, adaptive reweighting can amplify that lead

Important nuance:

- the final weights still ended in the expected order by family average
- `always_correct`: `0.747`
- `sometimes_correct`: `0.610`
- `always_nice_teacher`: `0.421`

So the system still learned the right ranking overall, even though selections were not strictly ordered at every step.

## Which Old Charts Are Weak For This Run

These charts are not wrong. They are just low-value for this exact configuration.

### `scenario_scores.png`

Why weak:

- all tasks are `addition`
- there is only one scenario in the run

Result:

- this chart collapses to one bar group and does not compare anything meaningful

### `exam_scores_over_time.png`

Why weak:

- it averages the same metrics that are already shown elsewhere
- with one-question tasks, it mostly mirrors correctness plus a near-flat completeness line

Result:

- it is redundant for presentation purposes

### `question_volume_over_time.png`

Why weak:

- every task has exactly one question and one point

Result:

- it is basically flat and adds no story

## Recommended Charts For Presentation

These are the charts that best fit the current showcase.

### `family_weights_over_time.png`

What it shows:

- average weight per personality family over iterations
- duplicates are merged, which makes the story cleaner

How to read it:

- if the framework is working, `always_correct` should rise to the top
- `sometimes_correct` should settle in the middle
- `always_nice_teacher` should stay at the bottom

Why it matters:

- this is the cleanest chart for the main thesis: better measured behavior gets more weight

### `family_correctness_over_time.png`

What it shows:

- family-average correctness metric over time

How to read it:

- this explains why `family_weights_over_time.png` moves the way it does
- weight changes should broadly follow this chart because correctness has the largest metric coefficient

Why it matters:

- this is the causal companion to the weight chart

### `outcome_breakdown_by_family.png`

What it shows:

- stacked shares of:
  - full-credit attempts
  - wrong-answer attempts
  - format failures

How to read it:

- `always_correct` should be almost entirely full-credit with a tiny failure slice
- `sometimes_correct` should be split between full-credit and wrong-answer
- `always_nice_teacher` should be entirely wrong-answer and not format-failure

Why it matters:

- this directly resolves the confusion between "wrong" and "failure"

### `task_outcome_mix_over_time.png`

What it shows:

- for each iteration, among the selected agents, how many were:
  - full-credit
  - wrong-answer
  - format-failure

How to read it:

- later iterations should contain more green share if the weighting system is concentrating on better agents

Why it matters:

- it turns the experiment into a visible per-task story instead of only a final summary

### `family_scorecard.png`

What it shows:

- full-credit rate by family
- average final weight by family
- normalized selection share by family

How to read it:

- if full-credit rate and final weight align, the adaptive weighting behaved coherently

Why it matters:

- this is the best single summary slide for the final conclusion

### `json_validity_over_time.png`

What it shows:

- cumulative JSON-valid and schema-valid rates across all attempts

How to read it:

- this should stay high in the showcase run
- if it crashes, then the weight story is contaminated by formatting noise

Why it matters:

- it is the control chart showing that the run was not dominated by parser failures

## Secondary Charts

These are still useful, but they are not the first charts to show.

### `weights_over_time.png`

- Useful if you want to show duplicate-agent drift.
- Less clean than the family-level version because it has six lines instead of three.

### `selection_counts.png`

- Useful for showing that selection changes over time.
- Less clean than the family-level version because duplicates fragment the story.

### `family_selection_counts.png`

- Good supporting evidence after the weight chart.
- Shows that lower-performing families are selected less often overall.

### `metrics_over_time.png`

- Useful only if you explicitly explain that three of the four metrics are low-signal here.
- Do not present it without commentary, or the audience may wrongly assume the other metrics are broken.

### `failure_rates.png`

- Useful as a control slide.
- In this run it mainly says "the experiment did not collapse structurally."

## What Each Main Result Means In Plain Language

The family-level result is:

- `always_correct` performed best and ended with the highest weight
- `sometimes_correct` performed in the middle and ended with a middle weight
- `always_nice_teacher` was polite but wrong and ended with the lowest weight

That is exactly the expected adaptive-selection behavior.

The only caveat is:

- selection counts are still stochastic because the algorithm is sampling with exploration

That is not a bug. It is part of the design.

## Suggested Slide Order For The Charts

Use this order if you want the cleanest narrative:

1. `family_weights_over_time.png`
2. `family_correctness_over_time.png`
3. `outcome_breakdown_by_family.png`
4. `task_outcome_mix_over_time.png`
5. `family_scorecard.png`
6. `json_validity_over_time.png`

Optional backup slides:

1. `weights_over_time.png`
2. `selection_counts.png`
3. `metrics_over_time.png`
4. `failure_rates.png`

## Nikpah Prompt For A Fancy Summary Chart

Use this prompt if you want a polished infographic-style chart from the same story:

```text
Create a clean, presentation-quality infographic chart for an AI experiment comparing three agent personalities: always_correct, sometimes_correct, and always_nice_teacher. The experiment uses adaptive weighted selection, so better-performing agents should gain higher selection weight over time. Use a modern academic style with a white background, dark charcoal text, muted grid lines, emerald green for strong performance, amber for mixed performance, and deep red for poor performance. The chart should combine three pieces of information for each personality family: full-credit answer rate, average final selection weight, and total selection count. Show always_correct as the top performer with full-credit rate about 96.8%, average final weight about 0.747, and 31 selections. Show sometimes_correct as the middle performer with full-credit rate about 47.1%, average final weight about 0.610, and 34 selections. Show always_nice_teacher as the lowest academic performer with full-credit rate 0%, average final weight about 0.421, and 25 selections. Visually emphasize that adaptive weighting follows measured correctness, not politeness. Add a subtitle: "Better measured task performance leads to higher selection weight." Include small annotations that format failure happened only once and only for always_correct, while always_nice_teacher was usually wrong but structurally valid. Make the result look polished enough for a university presentation slide.
```

## Bottom Line

For this specific run, the correct interpretation is:

- `correctness` is the main signal
- `completeness`, `reliability`, and `supportiveness` are behaving as defined, but they are weak separators in this showcase
- `failure` means format or validation error, not wrong math
- the family-level charts are the most faithful way to present the experiment
