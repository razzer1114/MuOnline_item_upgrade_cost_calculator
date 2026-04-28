# MU Online Item Upgrade Cost Calculator

**Probabilistic modeling for item upgrades in MU Online using absorbing Markov chains**

This project calculates the expected number of gems required to upgrade an item in **MU Online**. The current example focuses on upgrading an excellent item **without luck** from **+0 to +9**, assuming a constant success probability and one Soul Gem consumed per upgrade attempt.

The project is intended as a small, transparent, and extensible tool to analyze stochastic item enhancement systems in online games.

---

## Example Result

For an excellent item without luck, assuming:

- Success probability: `p = 0.5`
- Failure probability: `1 - p = 0.5`
- Cost per attempt: `1 Soul Gem`
- Target level: `+9`

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

## Repository Structure

A recommended repository structure is:

```text
mu-online-upgrade-cost-calculator/
│
├── README.md
├── LICENSE
├── requirements.txt
│
├── src/
│   ├── upgrade_model.py
│   └── run_example.py
│
├── examples/
│   └── excellent_item_no_luck_p05.py
│
├── docs/
│   ├── model_derivation.md
│   └── transition_rules.md
│
├── results/
│   └── p05_expected_gems.csv
│
└── tests/
    └── test_model.py
```

For a minimal first release, `README.md`, `requirements.txt`, and `src/upgrade_model.py` are sufficient.

---

## Installation

Clone the repository:

```bash
git clone https://github.com/your-username/mu-online-upgrade-cost-calculator.git
cd mu-online-upgrade-cost-calculator
```

Install dependencies:

```bash
pip install -r requirements.txt
```

The current version only requires NumPy:

```text
numpy>=1.24
```

---

## Python Implementation

Create the following file:

```text
src/upgrade_model.py
```

```python
import numpy as np


def build_transition_matrix(p: float) -> np.ndarray:
    """
    Build the full transition matrix P for the MU Online +0 to +9 upgrade model.

    State definition:
        State 1  -> item level +0
        State 2  -> item level +1
        ...
        State 10 -> item level +9, absorbing state

    Transition rules:
        State 1: failure stays at state 1.
        States 2 to 7: failure downgrades to state i-1.
        States 8 to 9: failure returns to state 1.
        State 10: absorbing state.

    Parameters
    ----------
    p : float
        Success probability of each upgrade attempt. Must satisfy 0 < p <= 1.

    Returns
    -------
    np.ndarray
        A 10 x 10 transition matrix P.
    """
    if not (0 < p <= 1):
        raise ValueError("Success probability p must satisfy 0 < p <= 1.")

    n_states = 10
    P = np.zeros((n_states, n_states), dtype=float)

    # State 1: +0
    # Failure stays at +0; success goes to +1.
    P[0, 0] = 1 - p
    P[0, 1] = p

    # States 2 to 7: +1 to +6
    # Failure downgrades by one state; success upgrades by one state.
    for idx in range(1, 7):
        P[idx, idx - 1] = 1 - p
        P[idx, idx + 1] = p

    # State 8: +7
    # Failure returns to +0; success goes to +8.
    P[7, 0] = 1 - p
    P[7, 8] = p

    # State 9: +8
    # Failure returns to +0; success goes to +9.
    P[8, 0] = 1 - p
    P[8, 9] = p

    # State 10: +9, absorbing state.
    P[9, 9] = 1.0

    return P


def split_absorbing_chain(P: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """
    Split the full transition matrix P into Q and R.

    Q contains transient-to-transient transitions.
    R contains transient-to-absorbing transitions.
    """
    Q = P[:9, :9]
    R = P[:9, 9:]
    return Q, R


def expected_gems(p: float) -> np.ndarray:
    """
    Calculate the expected number of gems required to reach +9 from each level.

    The returned array has length 10:
        result[0] -> expected gems from +0 to +9
        result[1] -> expected gems from +1 to +9
        ...
        result[9] -> expected gems from +9 to +9, which is 0

    Parameters
    ----------
    p : float
        Success probability of each upgrade attempt.

    Returns
    -------
    np.ndarray
        Expected gem consumption from each item level +0 to +9.
    """
    P = build_transition_matrix(p)
    Q, _ = split_absorbing_chain(P)

    I = np.eye(Q.shape[0])
    ones = np.ones(Q.shape[0])

    # Solve (I - Q)E = 1.
    # This is numerically preferable to computing inv(I - Q) explicitly.
    E_transient = np.linalg.solve(I - Q, ones)

    # Add E_10 = 0 for the absorbing target level +9.
    return np.append(E_transient, 0.0)


def expected_gems_table(p: float) -> list[tuple[str, float]]:
    """
    Return expected gem consumption as a readable table.
    """
    E = expected_gems(p)
    return [(f"+{level}", float(value)) for level, value in enumerate(E)]
```

---

## Example Script

Create the following file:

```text
src/run_example.py
```

```python
from upgrade_model import expected_gems, expected_gems_table


def main() -> None:
    p = 0.5
    E = expected_gems(p)

    print(f"Success probability: {p}")
    print("Expected Soul Gem consumption:")

    for level, value in expected_gems_table(p):
        print(f"{level} -> +9: {value:.6f}")

    print()
    print(f"Expected Soul Gems from +0 to +9: {E[0]:.6f}")


if __name__ == "__main__":
    main()
```

Run the example:

```bash
python src/run_example.py
```

Expected output:

```text
Success probability: 0.5
Expected Soul Gem consumption:
+0 -> +9: 230.000000
+1 -> +9: 228.000000
+2 -> +9: 224.000000
+3 -> +9: 218.000000
+4 -> +9: 210.000000
+5 -> +9: 200.000000
+6 -> +9: 188.000000
+7 -> +9: 174.000000
+8 -> +9: 116.000000
+9 -> +9: 0.000000

Expected Soul Gems from +0 to +9: 230.000000
```

---

## Minimal Example

A short standalone example is:

```python
from src.upgrade_model import expected_gems

p = 0.5
E = expected_gems(p)

print(E)
print(f"Expected Soul Gems from +0 to +9: {E[0]:.0f}")
```

---

## Test

Create the following file:

```text
tests/test_model.py
```

```python
import numpy as np

from src.upgrade_model import expected_gems


def test_expected_gems_p05() -> None:
    E = expected_gems(0.5)

    expected = np.array([
        230,
        228,
        224,
        218,
        210,
        200,
        188,
        174,
        116,
        0,
    ], dtype=float)

    assert np.allclose(E, expected)
```

Run tests with:

```bash
pytest
```

If `pytest` is used, add it to the development dependencies or install it separately:

```bash
pip install pytest
```

---

## Notes on Model Scope

The current version assumes:

- constant success probability across all levels;
- no Talisman of Luck;
- no additional protection item;
- no item destruction state;
- exactly one Soul Gem consumed per attempt;
- target level is `+9`.

These assumptions are intentionally simple so that the Markov chain structure remains transparent and easy to verify.

---

## Future Work

Possible extensions include:

- different success rates for different item levels;
- support for Talisman of Luck or other success-rate modifiers;
- protection items that prevent downgrade or reset;
- item destruction or explosion as an additional absorbing state;
- multiple gem types and weighted resource costs;
- Monte Carlo simulation for validation;
- visualization of expected gem cost under different probabilities;
- web-based calculator;
- extension to other MMORPG enhancement systems.

---

## Contributing

Contributions are welcome. Possible ways to contribute include:

- verifying game mechanics;
- correcting transition rules;
- adding new upgrade systems;
- improving mathematical derivations;
- adding tests and examples;
- implementing visualization or a web calculator.

If you find that the game mechanics differ from this model, please open an issue and provide the relevant rule description or evidence.

---

## License

This project is released under the MIT License.

---

## References

- MU Online item enhancement mechanics.
- Absorbing Markov chain theory.
- Expected hitting time for finite Markov chains.
