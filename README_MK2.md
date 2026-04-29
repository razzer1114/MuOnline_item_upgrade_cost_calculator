[中文](Calculator_MK2_CN.md)

## 🎯 Problem Statement

> What is the optimal upgrade strategy and expected cost to upgrade an item from +0 to +9, when both Bless Gems and Soul Gems are available?

---

## 🧠 Modeling Approach

We model the upgrade process as an **absorbing Markov decision system**, where:

- Each item level corresponds to a **state**
- The target level (+9) is an **absorbing state**
- Each upgrade attempt is a **state transition**
- At certain levels, players can choose between **different resources (actions)**

---

## ⚙️ Strategy Design

### Decision Scope

- Levels `+0 → +6`:  
  Player can choose between:
  - Bless Gem (100% success, higher cost)
  - Soul Gem (probabilistic success, lower cost)

- Levels `+6 → +9`:  
  Must use Soul Gems (no choice)

---

### Strategy Space

Each decision point has 2 choices:

```
Bless / Soul
```

Total number of strategies:

```
2^6 = 64 strategies
```

Each strategy can be represented as a string:

```
e.g. BBBSSSSSS
```

---

## 📊 Example Result

Assuming:

- Bless cost: `5`
- Soul cost: `1`
- Success probability: `p = 0.6`
- Failure probability: `1 - p = 0.4`

The model evaluates all 64 strategies and outputs:

```
Optimal Strategy:
SSSSSSSSS
```

Expected total cost from `+0` to `+9`:

```
≈ 7.96 (example from simplified model)
```

*(Actual value depends on full +9 model parameters)*

---

## 🎯 Project Objective

The objective of this project is to:

> Identify the optimal upgrade strategy under multi-resource conditions.

Specifically:

- Compare all possible strategies
- Compute expected resource consumption
- Minimize total expected cost

---

## 📌 Model Assumptions

### State Definition

| State | Item Level |
|---:|---:|
| 0 | +0 |
| 1 | +1 |
| 2 | +2 |
| 3 | +3 |
| 4 | +4 |
| 5 | +5 |
| 6 | +6 |
| 7 | +7 |
| 8 | +8 |
| 9 | +9 |

State `9` is the absorbing state.

---

## 🔁 Transition Rules

Let:

- `p` be the success probability of Soul Gem
- `1 - p` be the failure probability

### Bless Gem

```
Success probability = 1
Always upgrade to next level
```

---

### Soul Gem

| Current Level | Success | Failure |
|---|---|---|
| +0 | +1 | +0 |
| +1~+6 | +i+1 | i-1 |
| +7, +8 | +i+1 | +0 |
| +9 | +9 | +9 |

---

## 🧮 Absorbing Markov Chain Formulation

For a fixed strategy, the system becomes a standard absorbing Markov chain:

$$
P =
\begin{bmatrix}
Q & R \\
0 & I
\end{bmatrix}
$$

where:

- `Q`: transient-to-transient matrix  
- `R`: transient-to-absorbing matrix  

---

## 💰 Expected Cost Calculation

Define cost vector:

$$
c_i =
\begin{cases}
c_b, & \text{if Bless is used}\\
c_s, & \text{if Soul is used}
\end{cases}
$$

Expected total cost:

$$
E = (I - Q)^{-1} c
$$

---

## 🔍 Strategy Evaluation

For each of the 64 strategies:

1. Build transition matrix `Q`
2. Build cost vector `c`
3. Compute:

$$
E = (I - Q)^{-1} c
$$

4. Extract:

```
E_0 = expected cost from +0
```

---

## 📁 Output

### 1. Strategy Ranking

```
strategy_results_64.csv
```

Contains:

- strategy string
- expected Bless consumption
- expected Soul consumption
- expected total cost

---

### 2. Strategy Matrix

```
strategy_matrix_64.csv
```

- 64 × 9 binary matrix  
- 0 = Bless, 1 = Soul  

---

### 3. Transition Matrices

```
strategy_transition_matrices.npz
```

- One transition matrix per strategy  

---

## 🧩 Interpretation

This model reveals:

```
Optimal strategy depends on:
- relative gem cost
- success probability
- failure penalty structure
```

Key insight:

> Bless Gems are most valuable at levels where failure causes significant rollback.

---

## 🚀 Future Extensions

This framework can be extended to:

- level-dependent success probability  
- protection items (no downgrade)  
- destruction probability  
- hybrid cost models  
- dynamic strategies (MDP / Bellman)  

---

## 🧾 Summary

This project upgrades the classic Markov chain model into:

```
Multi-resource strategy optimization problem
```

Instead of asking:

> "How many gems are needed?"

We now answer:

> "What is the best way to spend gems?"
