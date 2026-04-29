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
import itertools
import os
import numpy as np
import pandas as pd


# ============================================================
# 1. 参数设置 / Parameter Settings
# ============================================================

# 灵魂宝石成功概率，在这里修改
# Soul gem success probability, modify it here
p_soul = 0.6

# 灵魂宝石失败概率
# Soul gem failure probability
q_soul = 1 - p_soul

# 宝石相对价值
# Relative gem costs
cost_soul = 1
cost_bless = 5

# 输出文件名
# Output file names
output_result_file = "strategy_results_64.csv"
output_strategy_matrix_file = "strategy_matrix_64.csv"
output_transition_npz_file = "strategy_transition_matrices.npz"
output_transition_csv_folder = "transition_matrices_csv"


# ============================================================
# 2. 基本规则设置 / Basic Rule Settings
# ============================================================

# 状态：+0 到 +9
# States: +0 to +9
# +9 为吸收态，+0 到 +8 为暂态
# +9 is the absorbing state; +0 to +8 are transient states
transient_states = list(range(9))
absorbing_state = 9

# 可自由选择祝福/灵魂的阶段：
# Decision stages where Bless or Soul can be selected:
# +0→+1, +1→+2, ..., +5→+6
decision_states = list(range(6))

# +6→+7, +7→+8, +8→+9 必须使用灵魂
# +6→+7, +7→+8, and +8→+9 must use Soul
forced_soul_states = [6, 7, 8]


def fail_state(i):
    """
    灵魂宝石失败后的回退等级。
    Return the fallback state after a failed Soul upgrade.

    +0 失败仍为 +0；
    Failure at +0 stays at +0.

    +1~+6 失败回退 1 级；
    Failure from +1 to +6 rolls back by one level.

    +7、+8 失败回到 +0。
    Failure at +7 and +8 returns to +0.
    """
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
    """
    生成 64 种固定策略。
    Generate 64 fixed strategies.

    B = Bless gem / 祝福宝石
    S = Soul gem / 灵魂宝石

    仅枚举 +0→+6 的 6 个可决策阶段；
    Only enumerate the six decision stages from +0 to +6.

    后续 +6→+9 自动补充为 SSS。
    The remaining stages from +6 to +9 are automatically fixed as SSS.
    """
    strategies = []

    for choices in itertools.product(["B", "S"], repeat=6):
        full_strategy = list(choices) + ["S", "S", "S"]
        strategies.append(full_strategy)

    return strategies


# ============================================================
# 4. 生成策略矩阵 / Generate Strategy Matrix
# ============================================================

def generate_strategy_matrix():
    """
    生成 64×9 的策略矩阵。
    Generate a 64×9 strategy matrix.

    行：64 种策略
    Rows: 64 strategies

    列：9 个强化阶段（+0→+1 ... +8→+9）
    Columns: 9 upgrade stages (+0→+1 ... +8→+9)

    编码规则：
    Encoding:
    B = 0（Bless / 祝福）
    S = 1（Soul / 灵魂）
    """
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
    """
    构建暂态转移矩阵 Q，维度为 9×9。
    Build the transient transition matrix Q with dimension 9×9.

    Q[i, j] 表示从状态 i 转移到状态 j 的概率。
    Q[i, j] denotes the probability of moving from state i to state j.
    """
    Q = np.zeros((9, 9))

    for i in transient_states:
        action = strategy[i]

        if action == "B":
            # 使用祝福宝石，100% 成功到下一级
            # Use Bless gem: 100% success to the next level
            next_state = i + 1

            # 如果到达 +9，则为吸收态，不写入 Q
            # If the next state is +9, it is absorbing and not included in Q
            if next_state < absorbing_state:
                Q[i, next_state] = 1.0

        elif action == "S":
            # 使用灵魂宝石
            # Use Soul gem
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
# 6. 构建成本向量 / Build Cost Vectors
# ============================================================

def build_cost_vectors(strategy):
    """
    为每个暂态状态建立成本向量。
    Build cost vectors for each transient state.

    每进入一个状态并尝试强化一次，就消耗对应宝石。
    Each upgrade attempt consumes the gem selected for that state.
    """
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
    """
    对单个策略进行评估。
    Evaluate a single strategy.

    计算内容：
    Metrics calculated:
    1. 期望祝福宝石消耗 / Expected Bless gem consumption
    2. 期望灵魂宝石消耗 / Expected Soul gem consumption
    3. 期望综合成本 / Expected total cost
    """
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
    """
    枚举全部 64 种策略，并按期望综合成本升序排序。
    Enumerate all 64 strategies and sort them by expected total cost.
    """
    strategies = generate_strategies()

    results = []
    for strategy in strategies:
        result = evaluate_strategy(strategy)
        results.append(result)

    df = pd.DataFrame(results)

    # 按期望综合成本升序排序
    # Sort by expected total cost in ascending order
    df = df.sort_values(by="expected_total_cost").reset_index(drop=True)

    # 添加排名列
    # Add ranking column
    df.insert(0, "rank", range(1, len(df) + 1))

    return df


# ============================================================
# 9. 生成所有策略的转移矩阵 / Generate Transition Matrices
# ============================================================

def generate_all_transition_matrices():
    """
    为 64 种策略生成对应的转移矩阵 Q。
    Generate transition matrices Q for all 64 strategies.

    返回：
    Return:
        dict: {"strategy_string": Q_matrix}
    """
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
    """
    导出 64 种策略的完整评估结果。
    Export the complete evaluation results of all 64 strategies.
    """
    df.to_csv(filename, index=False, encoding="utf-8-sig")
    print(f"结果已导出 / Results exported to: {filename}")


def export_strategy_matrix(df_matrix, filename=output_strategy_matrix_file):
    """
    导出 64×9 策略矩阵。
    Export the 64×9 strategy matrix.
    """
    df_matrix.to_csv(filename, index=False, encoding="utf-8-sig")
    print(f"策略矩阵已导出 / Strategy matrix exported to: {filename}")


def export_transition_matrices_npz(
    transition_dict,
    filename=output_transition_npz_file
):
    """
    将所有策略的转移矩阵导出为单个 NPZ 文件。
    Export all transition matrices into a single NPZ file.
    """
    np.savez(filename, **transition_dict)
    print(f"转移矩阵 NPZ 已导出 / Transition matrices NPZ exported to: {filename}")


def export_transition_matrices_csv(
    transition_dict,
    folder=output_transition_csv_folder
):
    """
    将每个策略的转移矩阵单独导出为 CSV 文件。
    Export each transition matrix as an individual CSV file.
    """
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
    """
    从 NPZ 文件中读取某一种策略的转移矩阵。
    Load the transition matrix of a given strategy from the NPZ file.

    示例 / Example:
        Q = load_transition_matrix_from_npz("BBBBBBSSS")
    """
    data = np.load(filename)
    return data[strategy_string]


# ============================================================
# 12. 主程序 / Main Program
# ============================================================

if __name__ == "__main__":
    # 计算并排序 64 种策略
    # Evaluate and rank all 64 strategies
    result_df = find_optimal_strategy()

    print("\n全部策略中成本最低的前 10 种：")
    print("Top 10 strategies with the lowest expected total cost:")
    print(result_df.head(10))

    print("\n最优策略：")
    print("Optimal strategy:")
    best = result_df.iloc[0]
    print(best)

    # 导出 64 种策略的评估结果
    # Export evaluation results of all 64 strategies
    export_results(result_df)

    # 生成并导出策略矩阵
    # Generate and export strategy matrix
    strategy_matrix_df = generate_strategy_matrix()
    export_strategy_matrix(strategy_matrix_df)

    # 生成并导出所有策略的转移矩阵
    # Generate and export transition matrices for all strategies
    transition_dict = generate_all_transition_matrices()

    # 推荐：导出为单个 NPZ 文件
    # Recommended: export as a single NPZ file
    export_transition_matrices_npz(transition_dict)

    # 可选：导出为 64 个 CSV 文件
    # Optional: export as 64 individual CSV files
    export_transition_matrices_csv(transition_dict)

