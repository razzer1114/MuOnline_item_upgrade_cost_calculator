"""
Plot expected Soul Gem consumption versus success probability.

This script uses the absorbing Markov chain model to calculate the expected
Soul Gem consumption from +0 to +9 under different success probabilities.
"""

import numpy as np
import matplotlib.pyplot as plt

from item_upgrade_to_lvl_9_markov_chain_calculator import expected_gems


def plot_expected_cost_vs_p(
    p_min: float = 0.3,
    p_max: float = 0.95,
    num_points: int = 200,
    output_file: str = "expected_cost_vs_p.png",
):
    """
    Plot expected Soul Gem consumption from +0 to +9
    as a function of success probability p.
    """

    p_values = np.linspace(p_min, p_max, num_points)
    expected_costs = []

    for p in p_values:
        E, _, _, _, _ = expected_gems(p)
        expected_costs.append(E[0])

    plt.figure(figsize=(8, 5))
    plt.plot(p_values, expected_costs, linewidth=2)

    plt.xlabel("Success Probability p")
    plt.ylabel("Expected Soul Gems from +0 to +9")
    plt.title("Expected Soul Gem Consumption vs Success Probability")
    plt.grid(True)

    plt.savefig(output_file, dpi=300, bbox_inches="tight")
    plt.show()


if __name__ == "__main__":
    plot_expected_cost_vs_p()
