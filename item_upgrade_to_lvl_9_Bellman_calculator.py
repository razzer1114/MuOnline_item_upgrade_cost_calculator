"""
MU Online 强化策略与成本分析模型
MU Online Item Upgrade Strategy & Cost Analyzer

本脚本将 MU Online 装备强化（+0 → +9）过程建模为
带多资源决策的吸收型马尔可夫链模型。
This script models the MU Online item upgrade process (+0 → +9)
as an absorbing Markov chain with multi-resource decision strategies.

核心特性 / Key Features:
- 两类强化资源 / Two upgrade resources:
  • 祝福宝石（Bless）：100% 成功，成本较高
    Bless Gem: 100% success, higher cost
  • 灵魂宝石（Soul）：概率成功，成本较低
    Soul Gem: probabilistic success, lower cost

- 决策范围 / Decision scope:
  • +0 → +6：可选择祝福或灵魂
    Levels +0 → +6: choose Bless or Soul
  • +6 → +9：固定使用灵魂
    Levels +6 → +9: Soul only (fixed)

- 策略空间 / Strategy space:
  • 共 2^6 = 64 种强化策略
    Total of 2^6 = 64 possible strategies

- 每种策略计算 / For each strategy, compute:
  • 期望祝福宝石消耗
    Expected Bless gem consumption
  • 期望灵魂宝石消耗
    Expected Soul gem consumption
  • 期望综合成本（加权）
    Expected total cost (weighted)

- 数学方法 / Method:
  • 吸收型马尔可夫链基本矩阵
    Fundamental matrix of absorbing Markov chain
    N = (I - Q)^(-1)

- 输出结果 / Outputs:
  • 策略成本排序结果
    Ranked strategy list (by expected cost)
  • 策略矩阵（64×9）
    Strategy matrix (64×9)
  • 各策略转移矩阵
    Transition matrices for each strategy

状态转移规则 / Transition Rules:
- 状态 0（+0）：
    失败仍停留在 0
    Failure stays at 0

- 状态 1 至 6：
    失败回退 1 级
    Failure downgrades by one level

- 状态 7 与 8：
    失败回到 0
    Failure returns to 0

- 状态 9（+9）：
    吸收态（终止）
    Absorbing state (terminal)

Author: Razz
License: MIT
"""
"""
MU Online 强化策略与成本分析模型
MU Online Item Upgrade Strategy & Cost Analyzer
"""

import itertools
import os
import numpy as np
import pandas as pd


# ============================================================
# 1. 参数设置 / Parameter Settings
# ============================================================

p_soul = 0.4
q_soul = 1 - p_soul

cost_soul = 1
cost_bless = 7.14 / 1.35

output_result_file = "strategy_results_64.csv"
output_strategy_matrix_file = "strategy_matrix_64.csv"
output_transition_npz_file = "strategy_transition_matrices.npz"
output_transition_csv_folder = "transition_matrices_csv"


# ============================================================
# 2. 基本规则设置 / Basic Rule Settings
# ============================================================

transient_states = list(range(9))
absorbing_state = 9

decision_states = list(range(6))
forced_soul_states = [6, 7, 8]


def fail_state(i):
    if i == 0:
        return 0
    elif 1 <= i <= 6:
        return i - 1
    elif i in [7, 8]:
        return 0
    else:
        raise ValueError("Invalid state / 无效状态")


# ============================================================
# 3. 生成全部 64 种策略 / Generate All 64 Strategies
# ============================================================

def generate_strategies():
    strategies = []

    for choices in itertools.product(["B", "S"], repeat=6):
        full_strategy = list(choices) + ["S", "S", "S"]
        strategies.append(full_strategy)

    return strategies


# ============================================================
# 4. 生成策略矩阵 / Generate Strategy Matrix
# ============================================================

def generate_strategy_matrix():
    strategies = generate_strategies()

    matrix = []
    strategy_strings = []

    for strategy in strategies:
        row = []

        for action in strategy:
            if action == "B":
                row.append(0)
            elif action == "S":
                row.append(1)
            else:
                raise ValueError("Unknown action / 未知动作")

        matrix.append(row)
        strategy_strings.append("".join(strategy))

    columns = [f"L{i}_to_{i+1}" for i in range(9)]
    df_matrix = pd.DataFrame(matrix, columns=columns)
    df_matrix.insert(0, "strategy", strategy_strings)

    return df_matrix


# ============================================================
# 5. 构建转移矩阵 Q / Build Transition Matrix Q
# ============================================================

def build_transition_matrix(strategy):
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

        else:
            raise ValueError("Unknown action / 未知动作")

    return Q


# ============================================================
# 6. 构建成本向量 / Build Cost Vectors
# ============================================================

def build_cost_vectors(strategy):
    bless_cost_vector = np.zeros(9)
    soul_cost_vector = np.zeros(9)
    total_cost_vector = np.zeros(9)

    for i in transient_states:
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
# 7. 评估单个策略 / Evaluate a Single Strategy
# ============================================================

def evaluate_strategy(strategy):
    Q = build_transition_matrix(strategy)

    I = np.eye(9)
    N = np.linalg.inv(I - Q)

    bless_cost_vector, soul_cost_vector, total_cost_vector = build_cost_vectors(strategy)

    expected_bless = (N @ bless_cost_vector)[0]
    expected_soul = (N @ soul_cost_vector)[0]
    expected_total = (N @ total_cost_vector)[0]

    return {
        "strategy": "".join(strategy),
        "expected_bless": expected_bless,
        "expected_soul": expected_soul,
        "expected_total_cost": expected_total
    }


# ============================================================
# 8. 枚举全部策略并排序 / Enumerate and Rank All Strategies
# ============================================================

def find_optimal_strategy():
    strategies = generate_strategies()

    results = []

    for strategy in strategies:
        result = evaluate_strategy(strategy)
        results.append(result)

    df = pd.DataFrame(results)
    df = df.sort_values(by="expected_total_cost").reset_index(drop=True)
    df.insert(0, "rank", range(1, len(df) + 1))

    return df


# ============================================================
# 9. 生成所有策略的转移矩阵 / Generate Transition Matrices
# ============================================================

def generate_all_transition_matrices():
    strategies = generate_strategies()

    transition_dict = {}

    for strategy in strategies:
        strategy_str = "".join(strategy)
        Q = build_transition_matrix(strategy)
        transition_dict[strategy_str] = Q

    return transition_dict


# ============================================================
# 10. 导出结果 / Export Results
# ============================================================

def export_results(df, filename=output_result_file):
    df.to_csv(filename, index=False, encoding="utf-8-sig")
    print(f"结果已导出 / Results exported to: {filename}")


def export_strategy_matrix(df_matrix, filename=output_strategy_matrix_file):
    df_matrix.to_csv(filename, index=False, encoding="utf-8-sig")
    print(f"策略矩阵已导出 / Strategy matrix exported to: {filename}")


def export_transition_matrices_npz(
    transition_dict,
    filename=output_transition_npz_file
):
    np.savez(filename, **transition_dict)
    print(f"转移矩阵 NPZ 已导出 / Transition matrices NPZ exported to: {filename}")


def export_transition_matrices_csv(
    transition_dict,
    folder=output_transition_csv_folder
):
    if not os.path.exists(folder):
        os.makedirs(folder)

    row_labels = [f"+{i}" for i in range(9)]
    col_labels = [f"+{i}" for i in range(9)]

    for strategy, Q in transition_dict.items():
        filename = os.path.join(folder, f"{strategy}.csv")

        df_Q = pd.DataFrame(Q, index=row_labels, columns=col_labels)
        df_Q.to_csv(filename, encoding="utf-8-sig")

    print(f"CSV 转移矩阵已导出 / CSV matrices exported to folder: {folder}")


# ============================================================
# 11. 读取 NPZ 示例 / Example: Load Transition Matrix from NPZ
# ============================================================

def load_transition_matrix_from_npz(
    strategy_string,
    filename=output_transition_npz_file
):
    data = np.load(filename)
    return data[strategy_string]


# ============================================================
# 12. 主程序 / Main Program
# ============================================================

if __name__ == "__main__":

    result_df = find_optimal_strategy()
    print("\n当前参数：")
    print("Current parameters:")
    print(f"p_soul = {p_soul}")
    print(f"cost_bless = {cost_bless:.6f}")


    print("\n全部策略成本：")
    print(" lowest expected total cost of ALL strategies:")
    print(result_df.head(64))



    print("\n最优策略：")
    print("Optimal strategy:")
    best = result_df.iloc[0]
    print(best)

    soul_only_strategy = list("SSSSSSSSS")
    soul_only_result = evaluate_strategy(soul_only_strategy)

    print("\n全部使用灵魂宝石策略：")
    print("Soul-only strategy:")
    print(f"strategy               {soul_only_result['strategy']}")
    print(f"expected_bless         {soul_only_result['expected_bless']:.6f}")
    print(f"expected_soul          {soul_only_result['expected_soul']:.6f}")
    print(f"expected_total_cost    {soul_only_result['expected_total_cost']:.6f}")

    export_results(result_df)

    strategy_matrix_df = generate_strategy_matrix()
    export_strategy_matrix(strategy_matrix_df)

    transition_dict = generate_all_transition_matrices()

    export_transition_matrices_npz(transition_dict)

    export_transition_matrices_csv(transition_dict)
