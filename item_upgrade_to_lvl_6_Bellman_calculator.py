"""
MU Online +0 to +6 Upgrade Strategy Model

This script evaluates all 64 strategies for upgrading an item from +0 to +6.
Each stage can use either Bless Gem or Soul Gem.

Rules:
- Bless Gem: 100% success
- Soul Gem:
  +0 failure stays at +0
  +1~+5 failure downgrades by 1 level

Author: Razz
MIT
"""

import itertools
import numpy as np
import pandas as pd


# ============================================================
# 1. 参数设置 / Parameter Settings
# ============================================================

# 灵魂宝石成功概率，在这里修改
# Soul Gem success probability, modify it here
p_soul = 0.6

# 灵魂宝石失败概率
# Soul Gem failure probability
q_soul = 1 - p_soul

# 宝石相对价值
# Relative gem costs
cost_soul = 1
cost_bless = 5

# 输出文件名
# Output file name
output_file = "strategy_results_plus0_to_plus6.csv"


# ============================================================
# 2. 基本状态设置 / State Settings
# ============================================================

# 状态：+0 到 +6
# States: +0 to +6
# +6 为吸收态，+0 到 +5 为暂态
# +6 is the absorbing state; +0 to +5 are transient states
transient_states = list(range(6))  # 0~5
absorbing_state = 6

# 六个强化阶段：
# Six upgrade stages:
# +0→+1, +1→+2, ..., +5→+6
decision_states = list(range(6))


def fail_state(i):
    """
    灵魂宝石失败后的回退等级。
    Return fallback state after a failed Soul upgrade.

    +0 失败仍为 +0；
    Failure at +0 stays at +0.

    +1~+5 失败回退 1 级。
    Failure from +1 to +5 downgrades by one level.
    """
    if i == 0:
        return 0
    elif 1 <= i <= 5:
        return i - 1
    else:
        raise ValueError("Invalid state / 无效状态")


# ============================================================
# 3. 生成全部 64 种策略 / Generate All 64 Strategies
# ============================================================

def generate_strategies():
    """
    生成 64 种固定策略。
    Generate all 64 fixed strategies.

    B = Bless Gem / 祝福宝石
    S = Soul Gem / 灵魂宝石
    """
    strategies = []

    for choices in itertools.product(["B", "S"], repeat=6):
        strategies.append(list(choices))

    return strategies


# ============================================================
# 4. 构建转移矩阵 Q / Build Transition Matrix Q
# ============================================================

def build_transition_matrix(strategy):
    """
    构建暂态转移矩阵 Q，维度为 6×6。
    Build transient transition matrix Q with dimension 6×6.

    Q[i, j] 表示从状态 i 转移到状态 j 的概率。
    Q[i, j] denotes probability of moving from state i to state j.
    """
    Q = np.zeros((6, 6))

    for i in transient_states:
        action = strategy[i]

        if action == "B":
            # 祝福宝石：100% 成功到下一级
            # Bless Gem: 100% success to next level
            next_state = i + 1

            # 如果到达 +6，则进入吸收态，不写入 Q
            # If reaching +6, it is absorbing and not included in Q
            if next_state < absorbing_state:
                Q[i, next_state] = 1.0

        elif action == "S":
            # 灵魂宝石：概率成功，失败回退
            # Soul Gem: probabilistic success, failure rollback
            success_state = i + 1
            failure_state = fail_state(i)

            # 成功转移
            # Successful transition
            if success_state < absorbing_state:
                Q[i, success_state] += p_soul

            # 失败转移
            # Failed transition
            if failure_state < absorbing_state:
                Q[i, failure_state] += q_soul

        else:
            raise ValueError("Unknown action / 未知动作")

    return Q


# ============================================================
# 5. 构建成本向量 / Build Cost Vectors
# ============================================================

def build_cost_vectors(strategy):
    """
    构建祝福、灵魂和总成本向量。
    Build Bless, Soul, and total cost vectors.
    """
    bless_cost_vector = np.zeros(6)
    soul_cost_vector = np.zeros(6)
    total_cost_vector = np.zeros(6)

    for i in transient_states:
        action = strategy[i]

        if action == "B":
            bless_cost_vector[i] = 1
            total_cost_vector[i] = cost_bless

        elif action == "S":
            soul_cost_vector[i] = 1
            total_cost_vector[i] = cost_soul

    return bless_cost_vector, soul_cost_vector, total_cost_vector


# ============================================================
# 6. 评估单个策略 / Evaluate a Single Strategy
# ============================================================

def evaluate_strategy(strategy):
    """
    计算单个策略从 +0 到 +6 的期望消耗。
    Evaluate expected consumption from +0 to +6 for one strategy.
    """
    Q = build_transition_matrix(strategy)

    I = np.eye(6)

    # 基本矩阵 N = (I - Q)^(-1)
    # Fundamental matrix N = (I - Q)^(-1)
    N = np.linalg.inv(I - Q)

    bless_cost_vector, soul_cost_vector, total_cost_vector = build_cost_vectors(strategy)

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

def find_optimal_strategy():
    """
    枚举全部 64 种策略，并按期望总成本排序。
    Enumerate all 64 strategies and rank by expected total cost.
    """
    strategies = generate_strategies()

    results = []
    for strategy in strategies:
        results.append(evaluate_strategy(strategy))

    df = pd.DataFrame(results)
    df = df.sort_values(by="expected_total_cost").reset_index(drop=True)
    df.insert(0, "rank", range(1, len(df) + 1))

    return df


# ============================================================
# 8. 主程序 / Main Program
# ============================================================

if __name__ == "__main__":
    result_df = find_optimal_strategy()

    print("Top 10 strategies with the lowest expected total cost:")
    print(result_df.head(10))

    print("\nOptimal strategy:")
    print(result_df.iloc[0])

    # 导出全部 64 种策略结果
    # Export all 64 strategy results
    result_df.to_csv(output_file, index=False, encoding="utf-8-sig")

    print(f"\nResults exported to: {output_file}")
