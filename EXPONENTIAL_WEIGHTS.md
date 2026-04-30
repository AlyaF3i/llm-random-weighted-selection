# Exponential Weights: Theory And Why We Use It

This note explains the theory behind the exponential-weight update used in the project, the exact equation implemented in the code, and why it can be preferable to the simpler metric-average weighting rule.

Relevant implementation:

- `src/llm_personality_experiment/scoring/selection.py`
- `src/llm_personality_experiment/experiment/runner.py`
- `configs/correctness_only_exponential.yaml`

## 1. The Main Idea

Exponential weights come from the online learning literature, especially the **Multiplicative Weights Update** method and the closely related **Hedge** algorithm.

The idea is simple:

- each agent has a current weight
- after observing performance, we multiply the weight by an exponential factor
- better reward causes larger multiplicative growth
- worse reward causes relatively weaker growth
- then all weights are normalized back into probabilities

This creates an adaptive selection rule that concentrates probability mass on better-performing agents over time.

## 2. The Theorem Behind It

The classic result is the **Multiplicative Weights / Hedge regret bound**.

### Informal Theorem

Suppose there are `N` experts or agents.

At each round `t = 1, 2, ..., T`:

- each agent receives a reward `r_i,t` in `[0,1]`
- the algorithm maintains a distribution over agents
- weights are updated multiplicatively

Then the cumulative performance of the exponential-weights algorithm is close to the cumulative performance of the best fixed agent in hindsight.

In other words:

- the algorithm does not need to know in advance which agent is best
- it gradually shifts probability toward better agents
- its regret grows sublinearly in `T`

So as the number of rounds increases, the average regret per round goes to zero.

### Standard Regret Statement

For rewards in `[0,1]`, one common form is:

```text
Regret(T) <= (ln N)/eta + (eta T)/8
```

where:

- `N` = number of agents
- `T` = number of rounds
- `eta > 0` = learning-rate parameter

If we choose:

```text
eta = sqrt((8 ln N) / T)
```

then:

```text
Regret(T) = O(sqrt(T ln N))
```

This is the main theoretical reason exponential weights are attractive: they come with a strong online-learning guarantee.

## 3. The Equation Used In General

Let:

- `w_i^(t)` be the unnormalized weight of agent `i` at round `t`
- `r_i^(t)` be the reward of agent `i` at round `t`
- `eta` be the exponential update strength

The multiplicative update is:

```text
w_i^(t+1) = w_i^(t) * exp(eta * r_i^(t))
```

Then normalize:

```text
p_i^(t+1) = w_i^(t+1) / sum_j w_j^(t+1)
```

where `p_i^(t+1)` is the probability of selecting agent `i` at the next round.

## 4. The Exact Equation Used In This Project

In this repository, the exponential update is implemented in:

- `src/llm_personality_experiment/scoring/selection.py`

The code computes a reward from the observed normalized scores:

```text
reward_i^(t) = weighted_average(observation_i^(t), metric_weights)
```

That weighted average is:

```text
reward_i^(t) =
(
  a * correctness_i^(t)
  + b * completeness_i^(t)
  + c * supportiveness_i^(t)
  + d * reliability_i^(t)
) / (a + b + c + d)
```

where:

- `a` = correctness coefficient
- `b` = completeness coefficient
- `c` = supportiveness coefficient
- `d` = reliability coefficient

Then the direct selection weight is updated as:

```text
w_i^(t+1) = w_i^(t) * exp(eta * reward_i^(t))
```

After that, the code renormalizes all weights:

```text
p_i^(t+1) = w_i^(t+1) / sum_j w_j^(t+1)
```

### Important Implementation Detail

In the current implementation:

- selected agents get their observed reward from the current task
- unselected agents are treated as having reward `0` for that round
- all weights are then renormalized

So practically the update is:

```text
if agent i was selected:
    w_i <- w_i * exp(eta * reward_i)
else:
    w_i <- w_i * exp(eta * 0) = w_i
```

then normalize all weights.

## 5. The Equation Used In The Correctness-Only Experiment

For the new comparison experiment, the metric weights are:

```text
correctness = 1
completeness = 0
supportiveness = 0
reliability = 0
```

So the reward simplifies to:

```text
reward_i^(t) = correctness_i^(t)
```

and the update becomes:

```text
w_i^(t+1) = w_i^(t) * exp(eta * correctness_i^(t))
```

After normalization:

```text
p_i^(t+1) = w_i^(t+1) / sum_j w_j^(t+1)
```

This makes the experiment especially clean:

- agents with correct answers grow faster
- agents with wrong answers grow more slowly
- the selection probabilities separate over time

## 6. What The Metric-Average Rule Does

The older rule in the project is:

```text
weight_i^(t) =
(
  a * metric_correctness_i^(t)
  + b * metric_completeness_i^(t)
  + c * metric_supportiveness_i^(t)
  + d * metric_reliability_i^(t)
) / (a + b + c + d)
```

This is not a multiplicative online-learning rule.

It is simply a direct weighted average of the current metric state.

That means:

- there is no explicit multiplicative amplification
- there is no classical regret guarantee attached to the selection rule itself
- weight separation is smoother and often weaker
- the effect of one strong round is moderated by the current metric state

## 7. Why Exponential Weights Can Be Better

This needs one important clarification:

**Exponential weights are not universally better in every setting.**

But for adaptive agent selection, they often have stronger theoretical and practical advantages.

### 7.1 Better Theoretical Foundation

The biggest advantage is that exponential weights come from a standard online-learning algorithm with regret guarantees.

The metric-average rule is intuitive, but it is heuristic.

So if a professor asks:

- "What is the theory behind your adaptive choice?"

the exponential version has a cleaner answer.

### 7.2 Faster Separation Between Good And Bad Agents

Because the update is multiplicative:

```text
w <- w * exp(eta * reward)
```

good agents compound their advantage over time.

This often makes the difference between:

- consistently correct agents
- mixed agents
- consistently wrong agents

more visible in the selection probabilities.

That is useful in your experiment because the whole point is to show that better-performing agents should gradually receive higher weight.

### 7.3 Better Match To Repeated Selection Problems

This project is essentially an online repeated-decision problem:

- at each round, choose agents
- observe reward
- adapt future probabilities

That structure matches exponential weights very naturally.

### 7.4 Clearer Interpretation Of `eta`

The parameter `eta` directly controls how aggressively the algorithm reacts to reward.

- small `eta`: slower adaptation, more conservative updates
- large `eta`: faster separation, stronger concentration on winners

This is often easier to explain than a more indirect state-based averaging effect.

## 8. Why The Metric-Average Rule Still Has Value

The metric-average rule is still useful.

Its advantages are:

- simple to explain
- stable
- less aggressive
- directly tied to interpretable metric state

So if someone asks:

- "Why not always use exponential weights?"

the honest answer is:

- metric-average weights are smoother and easier to reason about
- exponential weights are more principled for online selection, but more sensitive to the learning-rate choice

## 9. Main Tradeoff

The tradeoff is:

### Metric-Average

- simpler
- smoother
- more heuristic
- weaker theoretical story

### Exponential Weights

- stronger theory
- sharper adaptation
- better for repeated online selection
- more sensitive to tuning, especially `eta`

## 10. What To Say In The Presentation

A concise presentation version is:

> We tested a second selection strategy based on multiplicative or exponential weights. This comes from the Hedge or Multiplicative Weights framework in online learning. After each round, an agent’s probability weight is multiplied by `exp(eta * reward)` and then renormalized. In our correctness-only experiment, the reward is just the correctness score. This method has a standard regret guarantee, adapts more sharply to repeated success or failure, and is theoretically stronger than simply recomputing a linear weighted average of the metrics at each round.

## 11. Final Equation Summary

### Metric-Average Rule

```text
weight_i =
(
  a * correctness_i
  + b * completeness_i
  + c * supportiveness_i
  + d * reliability_i
) / (a + b + c + d)
```

### Exponential Rule In General

```text
reward_i =
(
  a * correctness_i
  + b * completeness_i
  + c * supportiveness_i
  + d * reliability_i
) / (a + b + c + d)
```

```text
w_i^(t+1) = w_i^(t) * exp(eta * reward_i^(t))
```

```text
p_i^(t+1) = w_i^(t+1) / sum_j w_j^(t+1)
```

### Exponential Rule In The Correctness-Only Experiment

```text
reward_i^(t) = correctness_i^(t)
```

```text
w_i^(t+1) = w_i^(t) * exp(eta * correctness_i^(t))
```

```text
p_i^(t+1) = w_i^(t+1) / sum_j w_j^(t+1)
```

## 12. Bottom Line

If the goal is only to have an interpretable heuristic score, the metric-average rule is fine.

If the goal is to justify adaptive repeated selection with a stronger theorem and a more standard online-learning method, the exponential-weight rule is the better choice.
