[中文](Calculator_MK1_CN.md)
## 🎯 Problem Statement

> What is the expected number of Soul Gems required to upgrade an item from +0 to +9?

---

## 🧠 Modeling Approach

We model the upgrade process as an **absorbing Markov chain**, where:

- Each item level corresponds to a **state**
- The target level (+9) is an **absorbing state**
- Each upgrade attempt is a **state transition**

---


## Example Result

For an excellent item without luck, assuming:

- Cost per attempt: `1 Soul Gem`
- Target level: `+9`
- Success probability: `p = 0.5`
- Failure probability: `1 - p = 0.5`
- Failure at lvl 2~6 causes item lvl to drop 1, failure at lvl 1,7,8 returns to lvl 1.


The expected Soul Gem consumption from `+0` to `+9` is:

```text
230 Soul Gems
```

Expected consumption from each starting level:

| Starting Level | Expected Soul Gems to +9 |
|---:|---:|
| +0 | 230 |
| +1 | 228 |
| +2 | 224 |
| +3 | 218 |
| +4 | 210 |
| +5 | 200 |
| +6 | 188 |
| +7 | 174 |
| +8 | 116 |
| +9 | 0 |

---

## Project Objective

The objective of this project is to provide a reproducible probabilistic model for calculating the expected gem cost of item upgrades.

The current model answers the following question:

> How many Soul Gems are expected to be consumed, on average, to upgrade an item from a given level to +9?

This project may also serve as a basis for further analysis, including:

- different success probabilities at different levels;
- protection items;
- item destruction or reset states;
- multiple gem types and weighted costs;
- strategy optimization for enhancement systems.

---

## Model Assumptions

The current version models the Soul Gem upgrade process from `+0` to `+9`.

### State Definition

The item level is represented as a Markov chain state:

| State | Item Level |
|---:|---:|
| 1 | +0 |
| 2 | +1 |
| 3 | +2 |
| 4 | +3 |
| 5 | +4 |
| 6 | +5 |
| 7 | +6 |
| 8 | +7 |
| 9 | +8 |
| 10 | +9 |

State `10`, corresponding to item level `+9`, is the absorbing state.

Once the item reaches `+9`, the upgrade process ends.

---

## Transition Rules

Let:

- `p` be the success probability;
- `1 - p` be the failure probability;
- each attempt consume one Soul Gem.

The transition rules are:

| Current State | Item Level | Success Result | Failure Result |
|---:|---:|---:|---:|
| 1 | +0 | State 2 | State 1 |
| 2 | +1 | State 3 | State 1 |
| 3 | +2 | State 4 | State 2 |
| 4 | +3 | State 5 | State 3 |
| 5 | +4 | State 6 | State 4 |
| 6 | +5 | State 7 | State 5 |
| 7 | +6 | State 8 | State 6 |
| 8 | +7 | State 9 | State 1 |
| 9 | +8 | State 10 | State 1 |
| 10 | +9 | State 10 | State 10 |

In compact form:

- For state `i = 1`, failure remains at state `1`.
- For states `i = 2, ..., 7`, failure downgrades to state `i - 1`.
- For states `i = 8, 9`, failure returns to state `1`.
- State `i = 10` is absorbing.

---

## Absorbing Markov Chain Formulation

The transition matrix can be written in the standard absorbing Markov chain form:

$$
P =
\begin{bmatrix}
Q & R \\
0 & I
\end{bmatrix}
$$

where:

- `Q` is the transient-to-transient transition matrix;
- `R` is the transient-to-absorbing transition matrix;
- `I` is the identity matrix for absorbing states.

For this model, states `1` to `9` are transient states, and state `10` is the absorbing state.

---

## Full Transition Matrix

Using the state order:

$$
(1,2,3,4,5,6,7,8,9,10)
$$

The full transition matrix is:

$$
P=
\begin{bmatrix}
1-p & p & 0 & 0 & 0 & 0 & 0 & 0 & 0 & 0\\
1-p & 0 & p & 0 & 0 & 0 & 0 & 0 & 0 & 0\\
0 & 1-p & 0 & p & 0 & 0 & 0 & 0 & 0 & 0\\
0 & 0 & 1-p & 0 & p & 0 & 0 & 0 & 0 & 0\\
0 & 0 & 0 & 1-p & 0 & p & 0 & 0 & 0 & 0\\
0 & 0 & 0 & 0 & 1-p & 0 & p & 0 & 0 & 0\\
0 & 0 & 0 & 0 & 0 & 1-p & 0 & p & 0 & 0\\
1-p & 0 & 0 & 0 & 0 & 0 & 0 & 0 & p & 0\\
1-p & 0 & 0 & 0 & 0 & 0 & 0 & 0 & 0 & p\\
0 & 0 & 0 & 0 & 0 & 0 & 0 & 0 & 0 & 1
\end{bmatrix}
$$

The transient matrix `Q` is the upper-left `9 x 9` block of `P`:

$$
Q=
\begin{bmatrix}
1-p & p & 0 & 0 & 0 & 0 & 0 & 0 & 0\\
1-p & 0 & p & 0 & 0 & 0 & 0 & 0 & 0\\
0 & 1-p & 0 & p & 0 & 0 & 0 & 0 & 0\\
0 & 0 & 1-p & 0 & p & 0 & 0 & 0 & 0\\
0 & 0 & 0 & 1-p & 0 & p & 0 & 0 & 0\\
0 & 0 & 0 & 0 & 1-p & 0 & p & 0 & 0\\
0 & 0 & 0 & 0 & 0 & 1-p & 0 & p & 0\\
1-p & 0 & 0 & 0 & 0 & 0 & 0 & 0 & p\\
1-p & 0 & 0 & 0 & 0 & 0 & 0 & 0 & 0
\end{bmatrix}
$$

The absorbing transition matrix `R` is:

$$
R=
\begin{bmatrix}
0\\
0\\
0\\
0\\
0\\
0\\
0\\
0\\
p
\end{bmatrix}
$$

Only state `9`, corresponding to item level `+8`, can directly move to the absorbing state `10`, corresponding to `+9`.

---

## Expected Gem Consumption

Let:

$$
E_i
$$

be the expected number of Soul Gems required to reach state `10` from state `i`.

Define:

$$
E=
\begin{bmatrix}
E_1\\
E_2\\
\vdots\\
E_9
\end{bmatrix}
$$

For transient states, the expectation equation is:

$$
E = \mathbf{1} + Q E
$$

where:

$$
\mathbf{1}=
\begin{bmatrix}
1\\
1\\
\vdots\\
1
\end{bmatrix}
$$

Each component of `1` represents the one Soul Gem consumed in the current attempt.

Rearranging gives:

$$
(I-Q)E=\mathbf{1}
$$

Therefore:

$$
E=(I-Q)^{-1}\mathbf{1}
$$

For numerical computation, it is better to solve the linear system directly instead of explicitly computing the inverse:

$$
(I-Q)E=\mathbf{1}
$$

---

## Recursive Form

The same model can also be written as recursive expectation equations.

For state `1`:

$$
E_1 = 1 + pE_2 + (1-p)E_1
$$

For states `2` to `7`:

$$
E_i = 1 + pE_{i+1} + (1-p)E_{i-1}, \quad i=2,3,\dots,7
$$

For state `8`:

$$
E_8 = 1 + pE_9 + (1-p)E_1
$$

For state `9`:

$$
E_9 = 1 + pE_{10} + (1-p)E_1
$$

Since state `10` is absorbing:

$$
E_{10}=0
$$

The recursive equations are equivalent to the matrix equation:

$$
(I-Q)E=\mathbf{1}
$$

---
## Example Result (with Luck)

For an excellent item **with luck**, assuming:

- Cost per attempt: `1 Soul Gem`
- Target level: `+9`
- Success probability: `p = 0.75`
- Failure probability: `1 - p = 0.25`
- Failure at lvl 2~6 causes item lvl to drop 1, failure at lvl 1,7,8 returns to lvl 1.


The expected Soul Gem consumption from `+0` to `+9` is:

```text
26.223035 Soul Gems
```

Expected consumption from each starting level:

| Starting Level | Expected Soul Gems to +9 |
|---:|---:|
| +0 | 26.223035 |
| +1 | 24.889702 |
| +2 | 23.111924 |
| +3 | 21.185998 |
| +4 | 19.210689 |
| +5 | 17.218920 |
| +6 | 15.221663 |
| +7 | 13.222578 |
| +8 | 7.555759 |
| +9 | 0.000000 |

---

