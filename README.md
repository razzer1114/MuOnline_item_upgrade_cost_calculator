# MU Online Item Upgrade Cost Calculator [中文](README_CN.md)

---
**Probabilistic Modeling for MU Online Item Upgrades using Absorbing Markov Chains**

- [**Results: All**](Results_Collection.md)

- [Theory: +0 to +9 Upgrade Markov Model (Soul Gems Only, Any Success Rate)](Calculator_MK1.md)

- [Theory: +0 to +9 Upgrade Bellman + Markov Model (Soul & Bless Gems, Any Success Rate, Any Strategy, Any Relative Cost)](Calculator_MK2.md)

- [Code: +0 to +9 Upgrade – Enumerate All Strategies, Compute Expected Cost, and Rank Optimal (Soul & Bless Gems, Any Success Rate, Any Strategy, Any Relative Cost)](item_upgrade_to_lvl_9_Bellman_calculator.py)

- [Code: +0 to +9 Upgrade – Expected Cost Calculation (Soul Gems Only, Any Success Rate)](item_upgrade_to_lvl_9_markov_chain_calculator.py)

- [Code: +0 to +7 Upgrade – Expected Cost Calculation (Soul Gems Only, Any Success Rate)](item_upgrade_to_lvl_7_markov_chain_calculator.py)

- [Code: +0 to +6 Upgrade – Expected Cost Calculation (Soul & Bless Gems, Any Success Rate, Any Strategy, Any Relative Cost)](item_upgrade_to_lvl_6_Bellman_calculator.py)

- [Code: +0 to +9 Upgrade – Optimal Strategy Cost Curve with Switching Points (Soul & Bless Gems, Fixed Success Rate, Any Strategy, Any Relative Cost)](strategy_switching_cost_curve.py)

- [Code: +0 to +9 Upgrade – Multi-Curve 3D Optimal Strategy Visualization (Multiple Typical Success Rates, Soul & Bless Gems)](Multi_p_cure.py)

- [Simple Case: Quick Intuition and Basic Understanding](Simple_Case.md)

---

## 📌 Project Overview

This project develops a **probabilistic framework** to analyze item upgrade systems in games such as MU Online.  
By modeling the upgrade process as an **absorbing Markov chain**, we compute the **expected number of resources (e.g., Gems)** required to reach a target enhancement level.

The project is intended as a small, transparent, and extensible tool to analyze stochastic item enhancement systems in online games.

---

## 🧭 Markov Chain

A Markov chain is a stochastic process used to describe how a system evolves between different states over time. Its key property is:

> The next state depends only on the current state, and not on the past history.

Formally, if the system is currently in state `i`, the probability of transitioning to state `j` is denoted by `P_ij`. All such probabilities form a **transition matrix**, which fully characterizes the dynamics of the system.

In an item upgrade system:

- each item level can be treated as a state;
- each upgrade attempt corresponds to a state transition;
- success or failure determines the transition probabilities.

In this project, the upgrade process is modeled as an **absorbing Markov chain**, which consists of:

- **transient states**: e.g., +0 to +8, where the system continues to move between states;
- an **absorbing state**: e.g., +9, which, once reached, cannot be left and terminates the process.

A key result from absorbing Markov chain theory is that the expected number of steps (or resource consumption) required to reach the absorbing state can be computed as:

$$
E = (I - Q)^{-1} \mathbf{1}
$$

where:

- `Q` is the transition matrix between transient states;
- `I` is the identity matrix;
- `1` represents the unit cost incurred at each step.

This approach provides an exact and systematic way to compute the expected resource cost (e.g., Soul Gems) under complex upgrade rules.

---

## 🧭 MU Online

**MU Online** is a classic MMORPG in which equipment enhancement plays a central role in gameplay progression.  

### Upgrade System Characteristics

- Players attempt to increase item levels through repeated enhancement trials  
- Each attempt consumes a resource (e.g., Soul Gem)  
- Each attempt has:
  - a **success probability**  
  - a **failure probability**
- Failure may lead to:
  - level downgrade  
  - reset to base level  
  - item destruction  

These mechanisms introduce **strong stochasticity**, making the total resource cost highly uncertain.

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
- adding new upgrade systems, like wings using the wing thing;
- improving mathematical derivations;
- adding tests and examples;
- implementing visualization or a web calculator.

If you find that the game mechanics differ from this model, please open an issue and provide the relevant rule description or evidence.

---

## License

This project is released under the MIT License.

---

## References

- MU Online.com.
- Absorbing Markov chain theory.
- Expected hitting time for finite Markov chains.
