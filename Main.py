# ============================================================
# MU Online Item Upgrade Cost Calculator
# 马尔可夫链装备强化策略优化计算器
# ============================================================
#
# Author:
# Razzer Lee
#
# GitHub Project:
# https://github.com/razzer1114/MuOnline_item_upgrade_cost_calculator
#
# Project Description:
# This project models MU Online item upgrading as an
# absorbing Markov chain and evaluates all possible
# item upgrade optimal strategies at various 
# upgrade success rates and Bless/Soul cost ratioes.
# Meanwhile providing analytical results
#
# The program can:
# - Find optimal upgrade strategies
# - Calculate expected upgrade cost
# - Generate 3D cost surfaces
# - Generate contour maps
# - Generate Bless-use boundary maps
#
# 本项目基于吸收型马尔可夫链，
# 对奇迹MU装备强化过程进行建模，
# 并自动搜索在不同灵魂强化成功率和
# 祝福/灵魂价格比值下的最优强化策略。
# 同时还提供了分析结果。
#
# 功能包括：
# - 搜索全局最优策略
# - 计算强化期望成本
# - 生成3D最优期望成本曲面图
# - 生成等高线图
# - 祝福使用边界图
#
# ============================================================
# License
# ============================================================
#
# MIT License
#
# Copyright (c) 2026 Razzer Lee
#
# Permission is hereby granted, free of charge,
# to any person obtaining a copy of this software
# and associated documentation files (the "Software"),
# to deal in the Software without restriction.
#
# ============================================================
# Disclaimer
# ============================================================
#
# This project is intended for research, educational,
# and strategy analysis purposes only.
#
# Actual in-game probabilities and economic conditions
# may differ from the user-defined parameters.
#
# Users may freely modify:
# - Soul success probability
# - Relative Bless cost
# - Parameter scanning range
#
# ============================================================




import itertools
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# ============================================================
# 1. Global Parameters / 全局参数设置
# ============================================================
# All important parameters are configured here.
# 后续计算、数据保存和绘图都会自动采用本处设置。

# ---------- Cost parameters / 成本参数 ----------
COST_SOUL = 1.0                         # Soul cost / 灵魂宝石成本，作为基准单位

# ---------- Scan range / 参数扫描范围 ----------
P_SOUL_MIN = 0.33                       # Minimum Soul success probability / 灵魂成功率最小值
P_SOUL_MAX = 0.95                       # Maximum Soul success probability / 灵魂成功率最大值
COST_BLESS_MIN = 0.5                    # Minimum relative Bless cost / 祝福相对价值最小值
COST_BLESS_MAX = 10                    # Maximum relative Bless cost / 祝福相对价值最大值

# ---------- Scan resolution / 参数扫描精度 ----------
P_POINTS = 500                           # Number of p_soul sampling points / 灵魂成功率采样点数
COST_POINTS = 500                        # Number of cost_bless sampling points / 祝福相对价值采样点数

# ---------- Output control / 输出控制 ----------
OUTPUT_DIR = "upgrade_figure_outputs"   # Output folder / 输出文件夹
SHOW_FIGURES = True                     # Whether to show figures / 是否显示图片窗口
SAVE_CSV = True                         # Whether to save CSV files / 是否保存CSV数据
SAVE_FIGURES = True                     # Whether to save figures / 是否保存图片
FIGURE_DPI = 300                        # Figure resolution / 图片分辨率

# ---------- Output file names / 输出文件名 ----------
OUTPUT_SURFACE_DATA_FILE = "surface_expected_total_cost.csv"
OUTPUT_BEST_STRATEGY_FILE = "surface_best_strategy.csv"
OUTPUT_3D_FIGURE_FILE = "expected_total_cost_surface.png"
OUTPUT_CONTOUR_FIGURE_FILE = "expected_total_cost_contour.png"
OUTPUT_BLESS_BOUNDARY_FILE = "bless_need_boundary_map.png"
OUTPUT_BLESS_NEED_MATRIX_FILE = "bless_need_matrix.csv"


# ============================================================
# 2. Basic Rules / 基本规则设置
# ============================================================

TRANSIENT_STATES = list(range(9))
ABSORBING_STATE = 9


def fail_state(i):
    """
    Return failure state after using Soul.
    返回使用灵魂失败后的状态。
    """
    if i == 0:
        return 0
    elif 1 <= i <= 6:
        return i - 1
    elif i in [7, 8]:
        return 0
    else:
        raise ValueError("Invalid state")


# ============================================================
# 3. Strategy Generation / 生成策略
# ============================================================


def generate_strategies():
    """
    Generate all 64 strategies.
    生成全部64种策略。

    For +0 to +5, each level can choose Bless or Soul.
    For +6 to +8, Soul is fixed.

    +0到+5每一级可选祝福或灵魂。
    +6到+8固定使用灵魂。
    """
    strategies = []
    for choices in itertools.product(["B", "S"], repeat=6):
        full_strategy = list(choices) + ["S", "S", "S"]
        strategies.append(full_strategy)
    return strategies


ALL_STRATEGIES = generate_strategies()


# ============================================================
# 4. Transition Matrix / 转移矩阵
# ============================================================


def build_transition_matrix(strategy, p_soul):
    """
    Build transient-state transition matrix Q.
    构建暂态转移矩阵Q。
    """
    q_soul = 1.0 - p_soul
    Q = np.zeros((9, 9))

    for i in TRANSIENT_STATES:
        action = strategy[i]

        if action == "B":
            next_state = i + 1
            if next_state < ABSORBING_STATE:
                Q[i, next_state] = 1.0

        elif action == "S":
            success_state = i + 1
            failure_state = fail_state(i)

            if success_state < ABSORBING_STATE:
                Q[i, success_state] += p_soul

            if failure_state < ABSORBING_STATE:
                Q[i, failure_state] += q_soul

        else:
            raise ValueError("Invalid action in strategy")

    return Q


# ============================================================
# 5. Cost Calculation / 成本计算
# ============================================================


def evaluate_strategy(strategy, p_soul, cost_bless):
    """
    Calculate expected total cost from +0 to +9 for one strategy.
    计算某一策略下从+0强化至+9的期望总成本。
    """
    Q = build_transition_matrix(strategy, p_soul)
    N = np.linalg.inv(np.eye(9) - Q)

    total_cost_vector = np.zeros(9)

    for i in TRANSIENT_STATES:
        if strategy[i] == "B":
            total_cost_vector[i] = cost_bless
        else:
            total_cost_vector[i] = COST_SOUL

    expected_total = (N @ total_cost_vector)[0]
    return expected_total



def find_min_cost_and_strategy(p_soul, cost_bless):
    """
    Find the optimal strategy and its expected total cost.
    寻找最优策略及其期望总成本。
    """
    best_cost = np.inf
    best_strategy = None

    for strategy in ALL_STRATEGIES:
        cost = evaluate_strategy(strategy, p_soul, cost_bless)
        if cost < best_cost:
            best_cost = cost
            best_strategy = "".join(strategy)

    return best_cost, best_strategy


# ============================================================
# 6. Parameter Scanning / 参数扫描
# ============================================================


def generate_surface_data():
    """
    Generate expected cost matrix and best strategy matrix.
    生成期望成本矩阵和最优策略矩阵。
    """
    p_values = np.linspace(P_SOUL_MIN, P_SOUL_MAX, P_POINTS)
    cost_values = np.linspace(COST_BLESS_MIN, COST_BLESS_MAX, COST_POINTS)

    X, Y = np.meshgrid(p_values, cost_values)
    Z = np.zeros_like(X)
    best_strategy_matrix = np.empty(X.shape, dtype=object)

    total_points = X.size
    current_point = 0

    for i in range(X.shape[0]):
        for j in range(X.shape[1]):
            current_point += 1
            p_soul = X[i, j]
            cost_bless = Y[i, j]

            best_cost, best_strategy = find_min_cost_and_strategy(
                p_soul,
                cost_bless
            )

            Z[i, j] = best_cost
            best_strategy_matrix[i, j] = best_strategy

        print(f"Scanning progress / 扫描进度: {current_point}/{total_points}")

    return p_values, cost_values, X, Y, Z, best_strategy_matrix


# ============================================================
# 7. Data Output / 数据输出
# ============================================================


def ensure_output_dir():
    """
    Create output folder if it does not exist.
    若输出文件夹不存在，则自动创建。
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)



def save_matrix_csv(values, index_values, column_values, filename):
    """
    Save matrix data as CSV.
    将矩阵数据保存为CSV。
    """
    filepath = os.path.join(OUTPUT_DIR, filename)
    df = pd.DataFrame(
        values,
        index=np.round(index_values, 6),
        columns=np.round(column_values, 6)
    )
    df.to_csv(filepath, encoding="utf-8-sig")
    print(f"CSV saved / CSV已保存: {filepath}")



def save_surface_outputs(p_values, cost_values, Z, best_strategy_matrix):
    """
    Save expected cost matrix and best strategy matrix.
    保存期望成本矩阵和最优策略矩阵。
    """
    if not SAVE_CSV:
        return

    save_matrix_csv(
        Z,
        cost_values,
        p_values,
        OUTPUT_SURFACE_DATA_FILE
    )

    save_matrix_csv(
        best_strategy_matrix,
        cost_values,
        p_values,
        OUTPUT_BEST_STRATEGY_FILE
    )


# ============================================================
# 8. Plotting: Expected Cost / 绘图：期望成本
# ============================================================


def finalize_figure(filename):
    """
    Save and/or show current figure.
    保存并/或显示当前图片。
    """
    if SAVE_FIGURES:
        filepath = os.path.join(OUTPUT_DIR, filename)
        plt.savefig(filepath, dpi=FIGURE_DPI, bbox_inches="tight")
        print(f"Figure saved / 图片已保存: {filepath}")

    if SHOW_FIGURES:
        plt.show()
    else:
        plt.close()



def plot_expected_cost_surface(X, Y, Z):
    """
    Plot 3D surface of expected total cost.
    绘制期望总成本3D曲面图。
    """
    fig = plt.figure(figsize=(12, 8))
    ax = fig.add_subplot(111, projection="3d")

    surface = ax.plot_surface(X, Y, Z, cmap="viridis")

    ax.set_xlim(P_SOUL_MIN, P_SOUL_MAX)
    ax.set_ylim(COST_BLESS_MIN, COST_BLESS_MAX)

    ax.set_xlabel("Soul Success Probability p_soul")
    ax.set_ylabel("Relative Bless Cost cost_bless")
    ax.set_zlabel("Expected Total Cost")
    ax.set_title("Best Expected Total Cost Surface")

    fig.colorbar(surface, ax=ax, shrink=0.65, pad=0.1)
    finalize_figure(OUTPUT_3D_FIGURE_FILE)



def plot_expected_cost_contour(X, Y, Z):
    """
    Plot contour map of expected total cost.
    绘制期望总成本等高线图。
    """
    plt.figure(figsize=(10, 7))

    contour = plt.contourf(X, Y, Z, levels=30, cmap="viridis")

    plt.xlim(P_SOUL_MIN, P_SOUL_MAX)
    plt.ylim(COST_BLESS_MIN, COST_BLESS_MAX)

    plt.xlabel("Soul Success Probability p_soul")
    plt.ylabel("Relative Bless Cost cost_bless")
    plt.title("Best Expected Total Cost Contour Map")

    plt.colorbar(contour, label="Expected Total Cost")
    finalize_figure(OUTPUT_CONTOUR_FIGURE_FILE)


# ============================================================
# 9. Bless Boundary Map / 祝福使用边界图
# ============================================================


def build_bless_need_matrix(strategy_matrix):
    """
    Build Bless-need matrix from best strategy matrix.
    根据最优策略矩阵生成是否需要祝福的矩阵。

    1 = Bless needed / 需要祝福
    0 = Soul only / 全灵魂
    """
    bless_need_matrix = np.zeros(strategy_matrix.shape, dtype=int)

    for i in range(strategy_matrix.shape[0]):
        for j in range(strategy_matrix.shape[1]):
            strategy = str(strategy_matrix[i, j])
            if "B" in strategy:
                bless_need_matrix[i, j] = 1
            else:
                bless_need_matrix[i, j] = 0

    return bless_need_matrix



def plot_bless_boundary_map(p_values, cost_values, bless_need_matrix):
    """
    Plot boundary map between Bless-needed and Soul-only strategies.
    绘制需要祝福与全灵魂策略之间的边界图。
    """
    X, Y = np.meshgrid(p_values, cost_values)

    plt.figure(figsize=(10, 7))

    contour_fill = plt.contourf(
        X,
        Y,
        bless_need_matrix,
        levels=[-0.5, 0.5, 1.5],
        alpha=0.75
    )

    boundary = plt.contour(
        X,
        Y,
        bless_need_matrix,
        levels=[0.5],
        colors="black",
        linewidths=2
    )

    plt.clabel(
        boundary,
        fmt={0.5: "Bless / Soul Boundary"},
        inline=True,
        fontsize=10
    )

    plt.xlabel("Soul Success Probability p_soul")
    plt.ylabel("Relative Bless Cost cost_bless")
    plt.title("Boundary Between Bless-Needed and Soul-Only Optimal Strategies")

    cbar = plt.colorbar(contour_fill, ticks=[0, 1])
    cbar.ax.set_yticklabels(["Soul only", "Bless needed"])

    plt.xlim(P_SOUL_MIN, P_SOUL_MAX)
    plt.ylim(COST_BLESS_MIN, COST_BLESS_MAX)

    finalize_figure(OUTPUT_BLESS_BOUNDARY_FILE)



def print_summary(p_values, cost_values, bless_need_matrix):
    """
    Print summary of parameter space.
    输出参数空间统计信息。
    """
    total_points = bless_need_matrix.size
    bless_points = np.sum(bless_need_matrix == 1)
    soul_only_points = np.sum(bless_need_matrix == 0)

    print("\nParameter range / 参数范围：")
    print(f"p_soul: {p_values.min():.4f} ~ {p_values.max():.4f}")
    print(f"cost_bless: {cost_values.min():.4f} ~ {cost_values.max():.4f}")

    print("\nRegion statistics / 区域统计：")
    print(f"Total points / 总参数点数量：{total_points}")
    print(f"Bless-needed points / 需要祝福区域点数：{bless_points}")
    print(f"Soul-only points / 不需要祝福区域点数：{soul_only_points}")
    print(f"Bless-needed ratio / 需要祝福区域占比：{bless_points / total_points:.2%}")
    print(f"Soul-only ratio / 不需要祝福区域占比：{soul_only_points / total_points:.2%}")


# ============================================================
# 10. Main Program / 主程序
# ============================================================


def main():
    """
    Run all calculations and generate all figures.
    执行全部计算并生成全部图像。
    """
    ensure_output_dir()

    p_values, cost_values, X, Y, Z, best_strategy_matrix = generate_surface_data()

    save_surface_outputs(
        p_values,
        cost_values,
        Z,
        best_strategy_matrix
    )

    plot_expected_cost_surface(X, Y, Z)
    plot_expected_cost_contour(X, Y, Z)

    bless_need_matrix = build_bless_need_matrix(best_strategy_matrix)

    if SAVE_CSV:
        save_matrix_csv(
            bless_need_matrix,
            cost_values,
            p_values,
            OUTPUT_BLESS_NEED_MATRIX_FILE
        )

    print_summary(p_values, cost_values, bless_need_matrix)
    plot_bless_boundary_map(p_values, cost_values, bless_need_matrix)

    print("\nAll tasks completed. / 全部计算与绘图已完成。")


if __name__ == "__main__":
    main()
