

# 3D Mapping of Best cost vs p_soul and cost of bless
# 最佳期望vs强化概率与宝石相对价值 3D曲面图


import itertools
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# ============================================================
# 1. 参数设置 Initialization
# ============================================================

cost_soul = 1

output_result_file = "strategy_results_64.csv"
output_strategy_matrix_file = "strategy_matrix_64.csv"
output_surface_data_file = "surface_expected_total_cost.csv"
output_best_strategy_file = "surface_best_strategy.csv"

output_3d_figure_file = "expected_total_cost_surface.png"
output_contour_figure_file = "expected_total_cost_contour.png"


# ============================================================
# 2. 基本规则设置 Basic Rules
# ============================================================

transient_states = list(range(9))
absorbing_state = 9

def fail_state(i):
    if i == 0:
        return 0
    elif 1 <= i <= 6:
        return i - 1
    elif i in [7, 8]:
        return 0
    else:
        raise ValueError("Invalid state")


# ============================================================
# 3. 生成策略 Generating Stratigies
# ============================================================

def generate_strategies():
    strategies = []
    for choices in itertools.product(["B", "S"], repeat=6):
        full_strategy = list(choices) + ["S", "S", "S"]
        strategies.append(full_strategy)
    return strategies


# ============================================================
# 4. 转移矩阵 Trans Matrix
# ============================================================

def build_transition_matrix(strategy, p_soul):
    q_soul = 1 - p_soul
    Q = np.zeros((9, 9))

    for i in transient_states:
        action = strategy[i]

        if action == "B":
            next_state = i + 1
            if next_state < absorbing_state:
                Q[i, next_state] = 1.0

        elif action == "S":
            success_state = i + 1
            failure_state = fail_state(i)

            if success_state < absorbing_state:
                Q[i, success_state] += p_soul

            if failure_state < absorbing_state:
                Q[i, failure_state] += q_soul

    return Q


# ============================================================
# 5. 成本计算 Cost Calculation
# ============================================================

def evaluate_strategy(strategy, p_soul, cost_bless):
    Q = build_transition_matrix(strategy, p_soul)

    N = np.linalg.inv(np.eye(9) - Q)

    total_cost_vector = np.zeros(9)

    for i in transient_states:
        if strategy[i] == "B":
            total_cost_vector[i] = cost_bless
        else:
            total_cost_vector[i] = cost_soul

    expected_total = (N @ total_cost_vector)[0]

    return expected_total


def find_min_cost_and_strategy(p_soul, cost_bless):
    strategies = generate_strategies()

    best_cost = np.inf
    best_strategy = None

    for strategy in strategies:
        cost = evaluate_strategy(strategy, p_soul, cost_bless)
        if cost < best_cost:
            best_cost = cost
            best_strategy = "".join(strategy)

    return best_cost, best_strategy


# ============================================================
# 6. 参数扫描 Scaning 
# ============================================================

def generate_surface_data(
    p_min=0.35,
    p_max=0.86,
    cost_min=4,
    cost_max=8.5,
    p_points=80,
    cost_points=80
):
    p_values = np.linspace(p_min, p_max, p_points)
    cost_values = np.linspace(cost_min, cost_max, cost_points)

    X, Y = np.meshgrid(p_values, cost_values)
    Z = np.zeros_like(X)
    best_strategy_matrix = np.empty(X.shape, dtype=object)

    for i in range(X.shape[0]):
        for j in range(X.shape[1]):
            p_soul = X[i, j]
            cost_bless = Y[i, j]

            best_cost, best_strategy = find_min_cost_and_strategy(
                p_soul,
                cost_bless
            )

            Z[i, j] = best_cost
            best_strategy_matrix[i, j] = best_strategy

    return X, Y, Z, best_strategy_matrix


# ============================================================
# 7. 绘图 Graphing
# ============================================================

def plot_expected_cost_surface(X, Y, Z):
    fig = plt.figure(figsize=(12, 8))
    ax = fig.add_subplot(111, projection="3d")

    surface = ax.plot_surface(X, Y, Z, cmap="viridis")

    ax.set_xlim(0.35, 0.86)
    ax.set_ylim(4, 8.5)

    ax.set_xlabel("p_soul")
    ax.set_ylabel("cost_bless")
    ax.set_zlabel("expected_total_cost")

    fig.colorbar(surface, ax=ax)

    plt.savefig("surface.png", dpi=300)
    plt.show()


def plot_expected_cost_contour(X, Y, Z):
    plt.figure(figsize=(10, 7))

    contour = plt.contourf(X, Y, Z, levels=30, cmap="viridis")

    plt.xlim(0.35, 0.86)
    plt.ylim(4, 8.5)

    plt.xlabel("p_soul")
    plt.ylabel("cost_bless")

    plt.colorbar(contour)

    plt.savefig("contour.png", dpi=300)
    plt.show()


# ============================================================
# 8. 主程序 Main
# ============================================================

if __name__ == "__main__":

    X, Y, Z, best_strategy_matrix = generate_surface_data(
        p_min=0.35,
        p_max=0.86,
        cost_min=4,
        cost_max=8.5,
        p_points=80,
        cost_points=80
    )

    plot_expected_cost_surface(X, Y, Z)
    plot_expected_cost_contour(X, Y, Z)
