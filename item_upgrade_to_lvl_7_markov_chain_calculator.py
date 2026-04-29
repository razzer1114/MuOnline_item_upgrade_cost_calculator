"""
MU Online Item Upgrade Cost Calculator

This script calculates the expected number of Soul Gems required to upgrade
an item from +0 to +7 using an absorbing Markov chain model.

Model:
- State 1 -> item level +0
- State 2 -> item level +1
- ...
- State 8 -> item level +7, absorbing state

Transition rules:
- State 1: failure stays at state 1
- States 2 to 7: failure downgrades to state i - 1
- State 8: absorbing state

Author: Razz
License: MIT
"""

import numpy as np


def build_absorbing_markov_chain(p: float):
    """
    Build the absorbing Markov chain transition matrix.

    Parameters
    ----------
    p : float
        Success probability of each upgrade attempt. Must satisfy 0 < p <= 1.

    Returns
    -------
    P : np.ndarray
        Full transition matrix, shape (8, 8).
    Q : np.ndarray
        Transient-state transition matrix, shape (7, 7).
    R : np.ndarray
        Transition matrix from transient states to absorbing state, shape (7, 1).
    """

    if not (0 < p <= 1):
        raise ValueError("Success probability p must satisfy 0 < p <= 1.")

    n_states = 8
    P = np.zeros((n_states, n_states))

    # State 1: failure stays at state 1, success moves to state 2
    P[0, 0] = 1 - p
    P[0, 1] = p

    # States 2 to 7: failure downgrades by one state, success upgrades by one state
    # State 7 success moves to state 8, the absorbing target state
    for i in range(1, 7):
        P[i, i - 1] = 1 - p
        P[i, i + 1] = p

    # State 8: absorbing state
    P[7, 7] = 1.0

    Q = P[:7, :7]
    R = P[:7, 7:]

    return P, Q, R


def expected_gems(p: float):
    """
    Calculate the expected number of gems required to reach +7 from each level.

    Parameters
    ----------
    p : float
        Success probability of each upgrade attempt.

    Returns
    -------
    E : np.ndarray
        Expected gem consumption from levels +0 to +7.
        E[0] corresponds to +0 -> +7.
        E[7] is 0 because +7 is the absorbing target state.
    P : np.ndarray
        Full transition matrix.
    Q : np.ndarray
        Transient-state transition matrix.
    R : np.ndarray
        Absorbing transition matrix.
    N : np.ndarray
        Fundamental matrix, N = (I - Q)^(-1).
    """

    P, Q, R = build_absorbing_markov_chain(p)

    I = np.eye(Q.shape[0])
    one = np.ones(Q.shape[0])

    # Fundamental matrix:
    # N = (I - Q)^(-1)
    N = np.linalg.inv(I - Q)

    # Expected hitting time:
    # E = N * 1
    E_transient = N @ one

    # Add absorbing state expectation E_8 = 0
    E = np.append(E_transient, 0.0)

    return E, P, Q, R, N


def print_results(p: float):
    """
    Print matrices and expected gem consumption results.
    """

    E, P, Q, R, N = expected_gems(p)

    np.set_printoptions(precision=4, suppress=True)

    print("=" * 60)
    print("MU Online Item Upgrade Cost Calculator")
    print("=" * 60)
    print(f"Target level: +7")
    print(f"Success probability: p = {p}")
    print(f"Failure probability: 1 - p = {1 - p}")
    print()

    print("Full transition matrix P:")
    print(P)
    print()

    print("Transient-state transition matrix Q:")
    print(Q)
    print()

    print("Absorbing transition matrix R:")
    print(R)
    print()

    print("Fundamental matrix N = (I - Q)^(-1):")
    print(N)
    print()

    print("Expected Soul Gem consumption:")
    for level, value in enumerate(E):
        print(f"+{level} -> +7: {value:.6f}")

    print()
    print(f"Expected Soul Gems from +0 to +7: {E[0]:.6f}")


if __name__ == "__main__":
    print_results(p=0.75)
