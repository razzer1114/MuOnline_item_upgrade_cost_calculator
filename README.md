# MuOnline_item_upgrade_cost_calculator
Probabilistic Modeling for Item Upgrade in Mu Online
  - My First Attempts with Results
    - [Excellent item w/o luck +0 to +9 costs 230 Sourls](Exemplary_Analysis&Calculation.md)
    - [Easy example](Easy_Start.md)
#
  - This example intends to encourage people to examine my results, to point out what to correct, and to collaborate for further development on this topic. 
# 
## Project Introduction
### Objective
This project leverages Markov chain theory to analyze the item upgrade system in the MMORPG **MU Online**. It provides a comprehensive probabilistic model to calculate the expected number of Gems, offering a framework for studying similar systems in other games.

### Background
- **MU Online**: A classic MMORPG where item upgrade nt is a key gameplay mechanic.
- **Upgrade System**:
  - Players attempt to increase equipment levels through repeated trials, facing both success and failure probabilities.
  - Failure can result in level downgrades or item explode, making the process stochastic and complex.
- **Markov Chain-Based Probabilistic Modeling**
  - xxx
- **Research Questions**:
  - How can we quantify the expected number of Gem to reach a specific enhancement level?
  - How can we optimize enhancement strategies?

### Key Contributions
- A Markov chain model for the equipment enhancement process.
- Recursive formulas for state transitions and higher-order cumulative terms.
- Extendable tools and methods for broader applications.

---

## Problem Modeling
### Item Upgrade Mechanism Modeling
- item levels are defined as states i :
  - State i corresponds to item level i-1, i.e., lvl 0 item is state i = 1.
  - State i transitions with probability p (success) to i + 1.
  - State i transitions with probability 1-p (failure) to 
      - state i = 1 for lvl 0 or 7 or 8 --- state i = 1 or 8 or 9
      - state i - 1 for lvl 1 to 6 --- state i = 2 to 7
      - state ( i_max + 1 ) as a special "explode" state.


        
%%%%%%%%%%%%%%%%%%%%%%%%%%% still need revision from here %%%%%%%%%%%%%%%%%%%%%%%%%%
%%%%%%%%%%%%%%%%%%%%%%%%%%% still need revision from here %%%%%%%%%%%%%%%%%%%%%%%%%%
%%%%%%%%%%%%%%%%%%%%%%%%%%% still need revision from here %%%%%%%%%%%%%%%%%%%%%%%%%%

# Transition Matrix (P)
  - Rows represent the current level, and columns represent the transition to the next level.
  - Elements represent the possibilities of transitions.
```python

P = [
    [0.5, 0.5, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],  # From Level 0
    [0.5, 0.0, 0.5, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],  # From Level 1
    [0.0, 0.5, 0.0, 0.5, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],  # From Level 2
    [0.0, 0.0, 0.5, 0.0, 0.5, 0.0, 0.0, 0.0, 0.0, 0.0],  # From Level 3
    [0.0, 0.0, 0.0, 0.5, 0.0, 0.5, 0.0, 0.0, 0.0, 0.0],  # From Level 4
    [0.0, 0.0, 0.0, 0.0, 0.5, 0.0, 0.5, 0.0, 0.0, 0.0],  # From Level 5
    [0.0, 0.0, 0.0, 0.0, 0.0, 0.5, 0.0, 0.5, 0.0, 0.0],  # From Level 6
    [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.5, 0.0, 0.5, 0.0],  # From Level 7
    [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.5, 0.0, 0.5],  # From Level 8
    [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.5],  # From Level 9 Absorbing State
]
```

### Transition Rules
- For state \( i \), the recursive formula is:
  \[
  E(i) = 1 + p \cdot E(i+1) + (1-p) \cdot E(i-1)
  \]
- Special cases:
  - \( E(0) \): Lowest level.
  - \( E(n) \): Highest level (absorbing state).

---

## Mathematical Derivations
### Recursive Formulas
- \( E(i) \) is derived as a recursive relationship for each state.
- General expressions are expanded step by step.

### Higher-Order Terms
- \( f(p) \): Represents cumulative higher-order terms from \( E(1) \).
  \[
  f(p) = \frac{7}{p} + \frac{6(1-p)}{p^2} + \frac{5(1-p)^2}{p^3} + \cdots
  \]
- \( g(p) \): Represents cumulative higher-order terms from \( E(8) \).
  \[
  g(p) = \frac{1}{p} + \frac{7(1-p)}{p^2} + \frac{6(1-p)^2}{p^3} + \cdots
  \]

---

## Numerical Verification
### Validation Process
- Implemented using MATLAB and Python.
- Calculated expected values for different probabilities \( p \).

### Example Results
- When \( p = 0.5 \):
  - \( f(p) = 56.0 \)
  - \( g(p) = 58.0 \)
  - \( E(9) = 116.0 \)

### Insights
- Results validate the consistency of the derived model with expected outcomes.

---

## Future Extensions
### Potential Research Directions
- Generalization to other games with similar mechanics.
- Incorporation of enhancement protection or increased probabilities.
- Optimization of resource costs in enhancement processes.

### Project Goals
- Expand this repository with community contributions:
  - Extend the model to other enhancement systems.
  - Explore new probabilistic models for related stochastic processes.

---

## How to Contribute
### Participation Opportunities
- Propose new enhancement models.
- Verify and refine recursive formulas.
- Share code implementations or real-world examples.

### Applications
- Analyze enhancement strategies for players.
- Assist developers in designing balanced game systems.

---

## Code Implementation
### Repository Contents
- MATLAB and Python scripts for recursive calculations.
- Tools for automating cumulative term expansions.
- Visualization of enhancement expectations under varying probabilities.

---

## License
This project is released under the [MIT License](https://opensource.org/licenses/MIT), encouraging open collaboration and research.

---

## Appendices
### Detailed Derivations
Step-by-step documentation of mathematical derivations.

### References
- *MU Online* game mechanics.
- Markov chain theory literature.
