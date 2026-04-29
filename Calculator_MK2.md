[中文](Calculator_MK2_CN.md)

## 🎯 Problem Statement

> What is the optimal upgrade strategy and expected cost to upgrade an item from +0 to +9, when both Bless Gems and Soul Gems are available?

---

## 🧠 Modeling Approach

We model the upgrade process as an **absorbing Markov decision system (MDP)**:

- Each item level is a **state**
- +9 is an **absorbing state**
- Each upgrade attempt is a **state transition**
- At some levels, the player chooses an **action** (Bless or Soul)

---

## ⚙️ Strategy Design

### Decision Scope
- `+0 → +6`: choose **Bless** or **Soul**
- `+6 → +9`: **Soul only**

### Strategy Space
```
2^6 = 64 strategies
```
Example: `BBBSSSSSS`

---

## 🧮 Bellman Dynamic Programming

Besides full enumeration, the problem can be formulated via **Bellman optimality**:

Let `V(i)` be the minimal expected cost from level `i` to `+9`. Then:

$$
V(i) = \min_{a \in A_i} \left[ c(i,a) + \sum_j P(j|i,a) V(j) \right]
$$

- `a` ∈ {Bless, Soul}
- `c(i,a)` is the immediate cost
- `P(j|i,a)` is the transition probability

This defines a **dynamic programming recursion** that yields the optimal policy.

> In this project, we use enumeration (64 strategies) for clarity and verification, but the Bellman formulation provides a scalable general solution.

---

## 🔁 Transition Rules

- Bless: success = 1
- Soul:
  - +0: fail → +0
  - +1~+6: fail → i-1
  - +7,+8: fail → +0
  - +9: absorbing

---

## 💰 Expected Cost

For a fixed strategy:

$$
E = (I - Q)^{-1} c
$$

---

## 📁 Outputs

- `strategy_results_64.csv`
- `strategy_matrix_64.csv`
- `strategy_transition_matrices.npz`

---

## 🚀 Extensions

- Level-dependent probabilities
- Protection items
- Dynamic policy optimization (Bellman / Value Iteration)

---

## 🧾 Summary

From:

> "How many gems are needed?"

To:

> "What is the optimal way to use gems?"
