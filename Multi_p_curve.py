import itertools
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# ============================================================
# 1. 基本参数 / Basic Parameters
# ============================================================

cost_soul = 1

# 典型装备类型及灵魂成功率 / Typical item types and Soul success rates
p_soul_cases = {
    "Socket item": 0.40,
    "Excellent set": 0.50,
    "Normal item": 0.60,
    "Lucky socket item": 0.65,
    "Lucky excellent set": 0.75,
    "Lucky normal item": 0.85
}

# 祝福宝石相对价值扫描范围 / Range of relative Bless cost
cost_min = 0.5
cost_max = 15
num_points = 500

output_3d_curve_file = "multi_p_soul_3d_cost_curves.png"
output_curve_data_file = "multi_p_soul_cost_curve_data.csv"


# ============================================================
# 2. 状态规则 / State Transition Rules
# ============================================================

transient_states = list(range(9))
absorbing_state = 9


def fail_state(i):
    """
    失败后的回退规则
    Failure rollback rule
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
# 3. 生成 64 种策略 / Generate 64 strategies
# ============================================================

def generate_strategies():
    """
    枚举所有策略：
    +0→+6 可选 B 或 S；
    +6→+9 固定为 S。
    
    Enumerate all strategies:
    +0 to +6 can choose B or S;
    +6 to +9 are fixed as S.
    """
    strategies = []

    for choices in itertools.product(["B", "S"], repeat=6):
        strategy = list(choices) + ["S", "S", "S"]
        strategies.append(strategy)

    return strategies


# ============================================================
# 4. 构建转移矩阵 / Build Transition Matrix
# ============================================================

def build_transition_matrix(strategy, p_soul):
    """
    构建暂态转移矩阵 Q
    Build transient transition matrix Q
    """
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

        else:
            raise ValueError("Unknown action")

    return Q


# ============================================================
# 5. 评估单个策略 / Evaluate a Strategy
# ============================================================

def evaluate_strategy(strategy, p_soul, cost_bless):
    """
    计算某一策略下的期望总成本，折算为灵魂宝石数量。
    Compute expected total cost under a strategy, converted to Soul units.
    """
    Q = build_transition_matrix(strategy, p_soul)
    N = np.linalg.inv(np.eye(9) - Q)

    total_cost_vector = np.zeros(9)

    for i in transient_states:
        if strategy[i] == "B":
            total_cost_vector[i] = cost_bless
        elif strategy[i] == "S":
            total_cost_vector[i] = cost_soul
        else:
            raise ValueError("Unknown action")

    expected_total_cost = (N @ total_cost_vector)[0]

    return expected_total_cost


# ============================================================
# 6. 寻找最优策略 / Find Optimal Strategy
# ============================================================

def find_optimal_strategy(p_soul, cost_bless):
    """
    在给定 p_soul 和 cost_bless 下，寻找最低期望成本策略。
    Find the minimum-cost strategy for given p_soul and cost_bless.
    """
    strategies = generate_strategies()

    best_cost = np.inf
    best_strategy = None

    for strategy in strategies:
        expected_cost = evaluate_strategy(strategy, p_soul, cost_bless)

        if expected_cost < best_cost:
            best_cost = expected_cost
            best_strategy = "".join(strategy)

    return best_cost, best_strategy


# ============================================================
# 7. 生成单条曲线 / Generate One Curve
# ============================================================

def generate_cost_curve_for_p(
    item_name,
    p_soul,
    cost_min,
    cost_max,
    num_points
):
    """
    对固定 p_soul，生成 cost_bless - expected cost 曲线。
    Generate the cost curve for a fixed p_soul.
    """
    cost_values = np.linspace(cost_min, cost_max, num_points)

    records = []

    for cost_bless in cost_values:
        best_cost, best_strategy = find_optimal_strategy(
            p_soul=p_soul,
            cost_bless=cost_bless
        )

        records.append({
            "item_type": item_name,
            "p_soul": p_soul,
            "cost_bless": cost_bless,
            "expected_total_cost": best_cost,
            "best_strategy": best_strategy
        })

    return pd.DataFrame(records)


# ============================================================
# 8. 生成全部曲线数据 / Generate All Curve Data
# ============================================================

def generate_all_curve_data():
    """
    生成全部典型成功率下的曲线数据。
    Generate curve data for all typical success rates.
    """
    all_dfs = []

    for item_name, p_soul in p_soul_cases.items():
        df = generate_cost_curve_for_p(
            item_name=item_name,
            p_soul=p_soul,
            cost_min=cost_min,
            cost_max=cost_max,
            num_points=num_points
        )
        all_dfs.append(df)

    result_df = pd.concat(all_dfs, ignore_index=True)

    return result_df


# ============================================================
# 9. 绘制 3D 曲线图 / Plot 3D Curves
# ============================================================

def plot_multi_p_soul_3d_curves(result_df):
    """
    在同一个 3D 图中绘制多条 p_soul 曲线。
    
    X-axis: cost_bless
    Y-axis: p_soul
    Z-axis: minimum expected total cost
    """
    fig = plt.figure(figsize=(13, 9))
    ax = fig.add_subplot(111, projection="3d")

    for item_name, p_soul in p_soul_cases.items():
        df_case = result_df[result_df["item_type"] == item_name]

        x = df_case["cost_bless"].to_numpy()
        y = df_case["p_soul"].to_numpy()
        z = df_case["expected_total_cost"].to_numpy()

        label_text = f"{item_name} (p={p_soul})"

        ax.plot(
            x,
            y,
            z,
            linewidth=2.2,
            label=label_text
        )

    ax.set_xlabel("Relative Bless Cost cost_bless", labelpad=12)
    ax.set_ylabel("Soul Success Probability p_soul", labelpad=12)
    ax.set_zlabel("Minimum Expected Total Cost (Soul units)", labelpad=12)

    ax.set_title(
        "Optimal Expected Cost Curves under Typical Soul Success Rates",
        pad=20
    )

    ax.set_xlim(cost_min, cost_max)
    ax.set_ylim(0.35, 0.90)

    ax.view_init(elev=25, azim=-55)

    ax.legend(loc="upper right", fontsize=8)

    plt.tight_layout()
    plt.savefig(output_3d_curve_file, dpi=300)
    plt.show()

    print(f"3D curve figure saved: {output_3d_curve_file}")


# ============================================================
# 10. 主程序 / Main
# ============================================================

if __name__ == "__main__":

    result_df = generate_all_curve_data()

    result_df.to_csv(
        output_curve_data_file,
        index=False,
        encoding="utf-8-sig"
    )

    print(f"Curve data saved: {output_curve_data_file}")

    plot_multi_p_soul_3d_curves(result_df)

    print("\nTypical Soul success rates:")
    for item_name, p_soul in p_soul_cases.items():
        print(f"{item_name}: p_soul = {p_soul}")
