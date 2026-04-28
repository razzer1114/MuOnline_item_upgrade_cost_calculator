# MU Online Item Upgrade Cost Calculator [中文](README_CN.md)

**Probabilistic modeling for item upgrades in MU Online using absorbing Markov chains**
- [**Current Results**](Results_Collection.md)
- [Explain: +0 to +9 Upgrade (Soul Gems, Any Success Rate)](Calculator_MK1.md)
- [Code: +0 to +9 Upgrade (Soul Gems, Any Success Rate)](item_upgrade_to_lvl_9_markov_chain_calculator.py)
- [Code: +0 to +7 Upgrade (Soul Gems, Any Success Rate)](item_upgrade_to_lvl_7_markov_chain_calculator.py)
- [Simple Case: to get a basic understanding](Simple_Case.md)

---

## 📌 Project Overview

This project develops a **probabilistic framework** to analyze item upgrade systems in games such as MU Online.  
By modeling the upgrade process as an **absorbing Markov chain**, we compute the **expected number of resources (e.g., Gems)** required to reach a target enhancement level.

The project is intended as a small, transparent, and extensible tool to analyze stochastic item enhancement systems in online games.

---
## 🧭 Background

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

## Current Work Walkthrough 
- [Explain: +0 to +9 Upgrade (Soul Gems, Any Success Rate)](Calculator_MK1.md)
- [Code: +0 to +9 Upgrade (Soul Gems, Any Success Rate)](item_upgrade_to_lvl_9_markov_chain_calculator.py)
- [Code: +0 to +7 Upgrade (Soul Gems, Any Success Rate)](item_upgrade_to_lvl_7_markov_chain_calculator.py)
- [Simple Case: to get a basic understanding](Simple_Case.md)
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
