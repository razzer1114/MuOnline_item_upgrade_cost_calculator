[中文](Calculator_MK2_CN.md)

## 🎯 Problem Statement

> What is the optimal upgrade strategy and expected cost to upgrade an item from +0 to +9 under arbitrary success probabilities and gem prices?

This project aims to build a **generalizable optimization model** that:

- Adapts to **any Soul success rate**
- Adapts to **any relative gem price**
- Applies to **different servers and economies**
- Outputs **optimal strategies automatically**

---

## 🧠 Modeling Approach

### Bellman Dynamic Programming

We formulate the upgrade process as a decision problem:

$$
V(i) = \min_{a \in A_i} \left[ c(i,a) + \sum_j P(j|i,a) V(j) \right]
$$

This describes:

- Current decision cost
- Future expected optimal cost

It defines the **optimal policy structure**.

---

### Absorbing Markov Chain

For any fixed strategy:

- States = item levels
- +9 = absorbing state
- Transitions = upgrade success/failure

Expected cost:

$$
E = (I - Q)^{-1} c
$$

---

### Practical Solution

Total strategies:

```
2^6 = 64
```

Therefore:

```
Enumerate all strategies + evaluate using Markov
```

---

## 📊 Example Result（Real Market Data）

**Key insight: Using real market prices, the model directly produces actionable optimal strategies.**

Based on April 28, 2026 China server data:

- 1 RMB = 7.14 Soul
- 1 RMB = 1.35 Bless
- Therefore:

```
1 Bless ≈ 5.29 Soul
```

Under:

```
p_soul = 0.5
```

Optimal strategy:

| Level | Action |
|---|---|
| +0→+1 | Soul |
| +1→+2 | Soul |
| +2→+3 | Bless |
| +3→+4 | Bless |
| +4→+5 | Bless |
| +5→+6 | Bless |
| +6→+7 | Soul |
| +7→+8 | Soul |
| +8→+9 | Soul |

Strategy string:

```
SSBBBBSSS
```

---

## 🔁 Transition Rules

- Bless: success = 1
- Soul:
  - +0: stay
  - +1~+6: -1
  - +7,+8: → +0

---

## 📈 Sensitivity Analysis

### Case 1
p = 0.5, 1B = 5S

- Optimal: SSBBBBSSS
- Cost ≈ 138
- Full Soul: 230

---

### Case 2
p = 0.6, 1B = 5S

- Optimal: SSSSSSSSS

---

### Case 3
p = 0.6, 1B = 4S

- Optimal: SSSBBBSSS

---

## 🧾 Summary

This project transforms:

"How many gems?"

into:

"What is the optimal strategy?"
