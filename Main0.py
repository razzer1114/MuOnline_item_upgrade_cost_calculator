# ============================================================
# MU Online Item Upgrade Cost Calculator
# for optimal strategy 
# to upgrade +7 +9 at GIVEN soul success rate 
# and Bless/Soul cost ratio
#
# 马尔可夫链装备强化策略优化计算器
# 计算给定灵魂强化成功率和祝福灵魂价格比的
# 最优强化策略
#
# ============================================================
#
# Author:
# Razz
#
# GitHub Project:
# https://github.com/razzer1114/MuOnline_item_upgrade_cost_calculator
#
# Project Description:
# This project models MU Online item upgrading as an
# absorbing Markov chain and evaluates all possible
# Bless/Soul upgrade strategies using exhaustive search.
#
# The program can:
# - Calculate expected upgrade cost
# - Find globally optimal upgrade strategies
# - Compare +0 to +7 and +0 to +9 upgrade results
# - Export ranked strategy results
#
# 本项目基于吸收型马尔可夫链，
# 对奇迹MU装备强化过程进行建模，
# 并通过穷举法自动搜索最优强化策略。
#
# 功能包括：
# - 计算强化期望成本
# - 搜索全局最优策略
# - 生成 +0 到 +7 与 +0 到 +9 的强化结果
# - 导出策略排序结果
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
# - Target upgrade levels
#
# ============================================================


import itertools
import os
import numpy as np
import pandas as pd


# ============================================================
# 1. 参数设置 / Parameter Settings
# ============================================================

# 灵魂宝石成功概率
# Soul Gem success probability
P_SOUL = 0.50

# 灵魂宝石相对成本，通常设为 1
# Relative Soul Gem cost, usually set as 1
COST_SOUL = 1.0

# 祝福宝石相对成本
# Relative Bless Gem cost
COST_BLESS = 5.29 / 1

# 需要计算的目标强化等级
# Target upgrade levels to calculate
TARGET_LEVELS = [7, 9]

# 输出前 N 个最优策略
# Number of top-ranked strategies to print
TOP_N = 10

# 是否导出 CSV 文件
# Whether to export CSV files
EXPORT_CSV = True

# 输出文件夹
# Output folder
OUTPUT_FOLDER = "given_parameter_results"


# ============================================================
# 2. 基本规则设置 / Basic Rule Settings
# ============================================================

def fail_state(i):
    """
    灵魂宝石失败后的状态转移规则。
    Return fallback state after a failed Soul upgrade.

    +0:
        失败仍停留在 +0
        Failure stays at +0

    +1 ~ +6:
        失败回退 1 级
        Failure downgrades by one level

    +7 ~ +8:
        失败回到 +0
        Failure returns to +0
    """
    if i == 0:
        return 0
    elif 1 <= i <= 6:
        return i - 1
    elif i in [7, 8]:
        return 0
    else:
        raise ValueError("Invalid state / 无效状态")


def get_stage_columns(target_level):
    """
    生成策略阶段列名。
    Generate stage column names.
    """
    return [f"L{i}_to_{i + 1}" for i in range(target_level)]


# ============================================================
# 3. 策略生成 / Strategy Generation
# ============================================================

def generate_strategies(target_level):
    """
    生成固定策略集合。
    Generate all fixed strategies.

    对于 +0 到 +7：
    - +0→+1 到 +5→+6 可选择 Bless 或 Soul，共 6 个决策阶段
    - +6→+7 固定使用 Soul

    For +0 to +7:
    - +0→+1 to +5→+6 are decision stages, Bless or Soul
    - +6→+7 is fixed as Soul

    对于 +0 到 +9：
    - +0→+1 到 +5→+6 可选择 Bless 或 Soul，共 6 个决策阶段
    - +6→+7、+7→+8、+8→+9 固定使用 Soul

    For +0 to +9:
    - +0→+1 to +5→+6 are decision stages, Bless or Soul
    - +6→+7, +7→+8, +8→+9 are fixed as Soul
    """
    if target_level < 1:
        raise ValueError("target_level must be at least 1 / 目标等级必须至少为 1")

    # 当前模型中，最多只允许 +0→+1 到 +5→+6 这 6 个阶段选择 Bless/Soul。
    # In the current model, only the first six stages can choose Bless/Soul.
    decision_count = min(6, target_level)

    strategies = []
    for choices in itertools.product(["B", "S"], repeat=decision_count):
        forced_soul_count = target_level - decision_count
        full_strategy = list(choices) + ["S"] * forced_soul_count
        strategies.append(full_strategy)

    return strategies


# ============================================================
# 4. 转移矩阵构建 / Transition Matrix Construction
# ============================================================

def build_transition_matrix(strategy, target_level, p_soul):
    """
    构建暂态转移矩阵 Q。
    Build transient transition matrix Q.

    target_level = 7:
        暂态为 +0 到 +6，吸收态为 +7，Q 维度为 7×7。

    target_level = 9:
        暂态为 +0 到 +8，吸收态为 +9，Q 维度为 9×9。
    """
    q_soul = 1 - p_soul
    transient_states = list(range(target_level))
    absorbing_state = target_level

    Q = np.zeros((target_level, target_level))

    for i in transient_states:
        action = strategy[i]

        if action == "B":
            # Bless Gem: 100% success to next level
            # 祝福宝石：100% 成功到下一级
            next_state = i + 1

            if next_state < absorbing_state:
                Q[i, next_state] = 1.0

        elif action == "S":
            # Soul Gem: probabilistic success, failure rollback
            # 灵魂宝石：概率成功，失败回退
            success_state = i + 1
            failure_state = fail_state(i)

            if success_state < absorbing_state:
                Q[i, success_state] += p_soul

            if failure_state < absorbing_state:
                Q[i, failure_state] += q_soul

        else:
            raise ValueError("Unknown action / 未知动作")

    return Q


# ============================================================
# 5. 成本向量构建 / Cost Vector Construction
# ============================================================

def build_cost_vectors(strategy, target_level, cost_soul, cost_bless):
    """
    构建祝福、灵魂和总成本向量。
    Build Bless, Soul, and total cost vectors.

    每进入一个暂态状态并尝试强化一次，就消耗对应宝石。
    Each upgrade attempt consumes the gem selected for that state.
    """
    bless_cost_vector = np.zeros(target_level)
    soul_cost_vector = np.zeros(target_level)
    total_cost_vector = np.zeros(target_level)

    for i in range(target_level):
        action = strategy[i]

        if action == "B":
            bless_cost_vector[i] = 1
            total_cost_vector[i] = cost_bless

        elif action == "S":
            soul_cost_vector[i] = 1
            total_cost_vector[i] = cost_soul

        else:
            raise ValueError("Unknown action / 未知动作")

    return bless_cost_vector, soul_cost_vector, total_cost_vector


# ============================================================
# 6. 单策略评估 / Single Strategy Evaluation
# ============================================================

def evaluate_strategy(strategy, target_level, p_soul, cost_soul, cost_bless):
    """
    计算单个策略的期望消耗。
    Evaluate expected consumption for one strategy.
    """
    Q = build_transition_matrix(strategy, target_level, p_soul)

    I = np.eye(target_level)

    # Fundamental matrix: N = (I - Q)^(-1)
    # 吸收型马尔可夫链基本矩阵：N = (I - Q)^(-1)
    N = np.linalg.inv(I - Q)

    bless_cost_vector, soul_cost_vector, total_cost_vector = build_cost_vectors(
        strategy=strategy,
        target_level=target_level,
        cost_soul=cost_soul,
        cost_bless=cost_bless
    )

    expected_bless = (N @ bless_cost_vector)[0]
    expected_soul = (N @ soul_cost_vector)[0]
    expected_total_cost = (N @ total_cost_vector)[0]

    return {
        "strategy": "".join(strategy),
        "expected_bless": expected_bless,
        "expected_soul": expected_soul,
        "expected_total_cost": expected_total_cost
    }


# ============================================================
# 7. 枚举全部策略并排序 / Enumerate and Rank Strategies
# ============================================================

def find_optimal_strategy(target_level, p_soul, cost_soul, cost_bless):
    """
    枚举全部策略，并按期望总成本排序。
    Enumerate all strategies and rank by expected total cost.
    """
    strategies = generate_strategies(target_level)

    results = []
    for strategy in strategies:
        result = evaluate_strategy(
            strategy=strategy,
            target_level=target_level,
            p_soul=p_soul,
            cost_soul=cost_soul,
            cost_bless=cost_bless
        )
        results.append(result)

    df = pd.DataFrame(results)
    df = df.sort_values(by="expected_total_cost").reset_index(drop=True)
    df.insert(0, "rank", range(1, len(df) + 1))
    df.insert(1, "target_level", f"+0_to_+{target_level}")

    return df


def build_strategy_matrix(target_level):
    """
    生成策略矩阵。
    Generate strategy matrix.
    """
    strategies = generate_strategies(target_level)
    columns = get_stage_columns(target_level)

    matrix = []
    strategy_strings = []

    for strategy in strategies:
        matrix.append(strategy)
        strategy_strings.append("".join(strategy))

    df_matrix = pd.DataFrame(matrix, columns=columns)
    df_matrix.insert(0, "strategy", strategy_strings)
    df_matrix.insert(0, "target_level", f"+0_to_+{target_level}")

    return df_matrix


# ============================================================
# 8. 结果输出 / Result Output
# ============================================================

def print_result_summary(result_df, target_level, p_soul, cost_soul, cost_bless, top_n):
    """
    打印结果摘要。
    Print result summary.
    """
    optimal = result_df.iloc[0]

    print("\n" + "=" * 70)
    print(f"MU Online +0 to +{target_level} Upgrade Strategy Result")
    print("=" * 70)

    print("\nParameter Settings:")
    print(f"Soul success probability (p_soul): {p_soul:.4f}")
    print(f"Soul failure probability         : {1 - p_soul:.4f}")
    print(f"Soul relative cost               : {cost_soul:.4f}")
    print(f"Bless relative cost              : {cost_bless:.4f}")

    print(f"\nTotal strategies evaluated       : {len(result_df)}")

    print("\nOptimal Strategy:")
    print(f"Strategy                         : {optimal['strategy']}")
    print(f"Expected Bless Gems              : {optimal['expected_bless']:.6f}")
    print(f"Expected Soul Gems               : {optimal['expected_soul']:.6f}")
    print(f"Expected Total Cost              : {optimal['expected_total_cost']:.6f}")

    print(f"\nTop {top_n} Strategies:")
    print(result_df.head(top_n).to_string(index=False))


def export_results(result_df, strategy_matrix_df, target_level, output_folder):
    """
    导出结果文件。
    Export result files.
    """
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    result_file = os.path.join(
        output_folder,
        f"strategy_results_plus0_to_plus{target_level}.csv"
    )

    matrix_file = os.path.join(
        output_folder,
        f"strategy_matrix_plus0_to_plus{target_level}.csv"
    )

    result_df.to_csv(result_file, index=False, encoding="utf-8-sig")
    strategy_matrix_df.to_csv(matrix_file, index=False, encoding="utf-8-sig")

    print(f"\nResults exported to        : {result_file}")
    print(f"Strategy matrix exported to: {matrix_file}")


# ============================================================
# 9. 主程序 / Main Program
# ============================================================

if __name__ == "__main__":

    all_best_rows = []

    for target_level in TARGET_LEVELS:
        result_df = find_optimal_strategy(
            target_level=target_level,
            p_soul=P_SOUL,
            cost_soul=COST_SOUL,
            cost_bless=COST_BLESS
        )

        strategy_matrix_df = build_strategy_matrix(target_level)

        print_result_summary(
            result_df=result_df,
            target_level=target_level,
            p_soul=P_SOUL,
            cost_soul=COST_SOUL,
            cost_bless=COST_BLESS,
            top_n=TOP_N
        )

        best_row = result_df.iloc[[0]].copy()
        all_best_rows.append(best_row)

        if EXPORT_CSV:
            export_results(
                result_df=result_df,
                strategy_matrix_df=strategy_matrix_df,
                target_level=target_level,
                output_folder=OUTPUT_FOLDER
            )

    # 导出 +7 与 +9 的最优结果汇总
    # Export summary of optimal results for +7 and +9
    if EXPORT_CSV and all_best_rows:
        summary_df = pd.concat(all_best_rows, ignore_index=True)
        summary_file = os.path.join(
            OUTPUT_FOLDER,
            "optimal_strategy_summary_plus7_plus9.csv"
        )
        summary_df.to_csv(summary_file, index=False, encoding="utf-8-sig")
        print(f"\nOptimal summary exported to: {summary_file}")
