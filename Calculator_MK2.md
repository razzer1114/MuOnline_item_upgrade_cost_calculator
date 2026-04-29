## Principle Overview [中文](Calculator_MK2_CN.md)

### 1. Problem Statement

This project focuses on the optimization of resource allocation in the equipment enhancement process. The objective is to determine an optimal strategy that minimizes the expected total cost under given enhancement rules and market conditions.

In the enhancement system, players choose between different materials (Soul and Bless) at each attempt. These materials differ in success probabilities and cost structures. Additionally, failure introduces rollback or resource loss, making the process stochastic and path-dependent.

Key challenges include:

- Multi-stage decision process (+0 → +9)
- Each decision affects future expected costs
- Market price fluctuations (Soul vs Bless)
- Different equipment success rates (e.g., with/without luck)

The model is designed to:

- Support arbitrary success probabilities
- Support dynamic market price inputs
- Enumerate and evaluate all strategies
- Output the globally optimal strategy and expected resource consumption

---

### 2. Modeling Approach

The enhancement process spans 9 stages (+0 → +9):

- +0 to +5: two choices (Soul or Bless)
- +6 to +9: fixed strategy (typically one material)

Thus, the total strategy space is:

> 2⁶ = 64 strategies

The solution approach:

1. Enumerate all 64 strategies (e.g., `SSBBBBSSS`)
2. Compute expected Soul and Bless consumption
3. Convert all costs into a unified metric (Soul equivalent)
4. Rank all strategies to find the optimal one

This approach ensures:

- Global optimality
- Low computational cost
- High reproducibility

---

### 3. Markov Model Structure

The enhancement process is modeled as an absorbing Markov chain.

**States:**
- Transient: +0 to +8
- Absorbing: +9 (success)

**Transitions:**
- Success → next level
- Failure → rollback or stay

**Strategy embedding:**
- Each strategy defines material choice at each stage
- Each choice determines transition probabilities

**Outputs:**
- `expected_soul`
- `expected_bless`
- `expected_total_cost`

---

### 4. Example Result

#### (1) Market Price Reference

Date: April 28, 2026  
Source: Official trading platform (China server, reference XIAO CE ZI)

| Item | Value |
|------|------|
| 1 RMB = Soul | 7.14 |
| 1 RMB = Bless | 1.35 |
| 1 Bless (in Soul) | 7.14 / 1.35 ≈ 5.29 |

---

#### (2) Baseline Scenario  
*(Excellent Set, No Luck)*

Parameters:
- `p_soul = 0.5`
- Bless priced by market conversion

**Top strategies:**

| rank | strategy     | expected_bless | expected_soul | expected_total_cost |
|------|--------------|----------------|----------------|---------------------|
| 1    | SSBBBBSSS    | 20.0           | 38.0           | 143.777778          |
| 2    | SSSBBBSSS    | 16.0           | 62.0           | 146.622222          |
| 3    | SBBBBBSSS    | 24.0           | 22.0           | 148.933333          |
| 4    | SSBSBBSSS    | 20.0           | 46.0           | 151.777778          |
| ...  | ...          | ...            | ...            | ...                 |
| 12   | BBBBBBSSS    | 28             | 14             | 162.088889          |
| ...  | ...          | ...            | ...            | ...                 |
| 58   | SSSSSSSSS    | 0              | 230            | 230                 |
| 64   | BSSSSSSSS    | 28             | 174            | 322.088889          |

---

### 5. Solution Workflow

For each of the 64 strategies:

1. Fix strategy sequence (e.g., `SSBBBBSSS`)
2. Simulate Markov transitions
3. Compute expected resource consumption
4. Convert to unified cost (Soul)
5. Rank all strategies

This pipeline is fully reproducible and parameterizable.

---

### 6. Sensitivity Analysis

#### (3.1) `p_soul = 0.5`, `1 Bless = 5 Soul`

| Item | Value |
|------|------|
| Optimal strategy | SSBBBBSSS |
| expected_bless | 20.0 |
| expected_soul | 38.0 |
| Total cost (Soul) | ≈ 138 |

Comparison:
- All Soul: 230  
- Optimized strategy significantly reduces cost

---

#### (3.2) `p_soul = 0.6`, `1 Bless = 5 Soul`

| rank | strategy     | expected_bless | expected_soul | expected_total_cost |
|------|--------------|----------------|----------------|---------------------|
| 1    | SSSSSSSSS    | 0.000000       | 75.514657      | 75.514657           |
| 2    | SSSSSBSSS    | 4.629630       | 54.398720      | 77.546868           |
| 3    | SSSSBSSSS    | 5.864198       | 50.054870      | 79.375857           |
| 4    | SSSSBBSSS    | 7.407407       | 42.338820      | 79.375857           |

---

#### (3.3) `p_soul = 0.6`, `1 Bless = 4 Soul`

| rank | strategy     | expected_bless | expected_soul | expected_total_cost |
|------|--------------|----------------|----------------|---------------------|
| 1    | SSSBBBSSS    | 10.185185      | 31.193416      | 71.934156           |
| 2    | SSSSBBSSS    | 7.407407       | 42.338820      | 71.968450           |
| 3    | SSSBSBSSS    | 9.259259       | 35.823045      | 72.860082           |
| 4    | SSSSSBSSS    | 4.629630       | 54.398720      | 72.917238           |
| ...  | ...          | ...            | ...            | ...                 |
| 12   | SSSSSSSSS    | 0              | 75.514657      | 75.514657           |

---

### 7. Key Insights

- **High-level stages amplify failure cost** → Bless becomes more valuable  
- **Higher Soul success rate (p_soul)** → strategy shifts toward full Soul  
- **Market price sensitivity** → optimal strategy highly dependent on Bless/Soul ratio  

---

### 8. Summary (For Users)

This model provides a reproducible framework for enhancement optimization:

- **Input:** success rates + market prices  
- **Output:** optimal strategy + expected cost  
- **Method:** brute-force enumeration + Markov expectation  

Applicable to:

- Strategy optimization
- Economic analysis
- Cross-server comparison

Potential extensions:

- Real-time price API integration  
- Equipment-specific success rate database  
- Automated strategy recommendation system  
