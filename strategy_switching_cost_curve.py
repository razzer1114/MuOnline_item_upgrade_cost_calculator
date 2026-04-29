import itertools
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# ============================================================
# 1. 基本参数 / Basic Parameters
# ============================================================

cost_soul = 1

# 固定灵魂成功率，可修改
# Fixed Soul success probability (can be modified)
p_soul_fixed = 0.5

# 祝福相对价值扫描范围，可修改
# Range of relative Bless cost to scan (modifiable)
cost_min = 0.5
cost_max = 15
num_points = 500

output_curve_file = "strategy_switching_cost_curve.png"
output_switch_table_file = "strategy_switching_points.csv"


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
    枚举所有策略（+0~+6可选，后3步固定S）
    Enumerate all strategies (first 6 stages configurable)
    """
    strategies = []

    for choices in itertools.product(["B", "S"], repeat=6):
        strategy = list(choices) + ["S", "S", "S"]
        strategies.append(strategy)

    return strategies


# ============================================================
# 4. 构建转移矩阵 / Build transition matrix
# ============================================================

def build_transition_matrix(strategy, p_soul):
    """
    构建马尔可夫链暂态转移矩阵 Q
    Build transient transition matrix Q of Markov chain
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
# 5. 评估单个策略 / Evaluate a strategy
# ============================================================

def evaluate_strategy(strategy, p_soul, cost_bless):
    """
    计算期望总成本（折算为灵魂）
    Compute expected total cost (converted to Soul units)
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
# 6. 寻找最优策略 / Find optimal strategy
# ============================================================

def find_optimal_strategy(p_soul, cost_bless):
    """
    在给定参数下寻找最优策略
    Find optimal strategy under given parameters
    """
    strategies = generate_strategies()

    best_cost = np.inf
    best_strategy = None

    for strategy in strategies:
        expected_cost = evaluate_strategy(
            strategy,
            p_soul,
            cost_bless
        )

        if expected_cost < best_cost:
            best_cost = expected_cost
            best_strategy = "".join(strategy)

    return best_cost, best_strategy


# ============================================================
# 7. 生成曲线 / Generate cost curve
# ============================================================

def generate_strategy_switching_curve(
    p_soul,
    cost_min,
    cost_max,
    num_points
):
    """
    生成：
    - 成本曲线
    - 最优策略序列
    Generate:
    - cost curve
    - optimal strategy sequence
    """
    cost_values = np.linspace(cost_min, cost_max, num_points)

    expected_costs = []
    best_strategies = []

    for cost_bless in cost_values:
        best_cost, best_strategy = find_optimal_strategy(
            p_soul,
            cost_bless
        )

        expected_costs.append(best_cost)
        best_strategies.append(best_strategy)

    return cost_values, np.array(expected_costs), best_strategies


# ============================================================
# 8. 提取策略切换点 / Detect switching points
# ============================================================

def find_switching_points(cost_values, expected_costs, best_strategies):
    """
    找到策略发生变化的点
    Detect where optimal strategy changes
    """
    switch_points = []

    for i in range(1, len(best_strategies)):
        if best_strategies[i] != best_strategies[i - 1]:
            switch_points.append({
                "index": i,
                "cost_bless": cost_values[i],
                "expected_total_cost": expected_costs[i],
                "from_strategy": best_strategies[i - 1],
                "to_strategy": best_strategies[i]
            })

    return switch_points


# ============================================================
# 9. 绘制策略切换图 / Plot switching diagram
# ============================================================

def plot_strategy_switching_curve(
    cost_values,
    expected_costs,
    best_strategies,
    switch_points,
    p_soul
):
    plt.figure(figsize=(13, 8))

    plt.plot(
        cost_values,
        expected_costs,
        linewidth=2,
        label="Optimal expected cost"
    )

    # 标注切换点 / Mark switching points
    for k, sp in enumerate(switch_points):
        x = sp["cost_bless"]
        y = sp["expected_total_cost"]

        plt.axvline(x=x, linestyle="--", linewidth=1, alpha=0.7)

        plt.scatter(x, y, s=60, zorder=5)

        label_text = (
            f'{sp["from_strategy"]}\n→ {sp["to_strategy"]}\n'
            f'cost={x:.2f}'
        )

        # 增大注释偏移，并采用上下交替，避免文字重叠
        # Increase annotation offset and alternate positions to avoid overlap
        offset_list = [
            (25, 30),
            (25, -55),
            (40, 50),
            (40, -75),
            (55, 70),
            (55, -95)
        ]
        xy_offset = offset_list[k % len(offset_list)]

        plt.annotate(
            label_text,
            xy=(x, y),
            xytext=xy_offset,
            textcoords="offset points",
            fontsize=8,
            arrowprops=dict(arrowstyle="->", linewidth=0.8)
        )

    plt.xlabel("Relative Bless Cost cost_bless")
    plt.ylabel("Minimum Expected Total Cost (Soul units)")
    plt.title(
        f"Strategy Switching Points (p_soul = {p_soul})"
    )

    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()

    plt.savefig(output_curve_file, dpi=300)
    plt.show()

    print(f"Saved figure: {output_curve_file}")


# ============================================================
# 10. 导出切换点 / Export switching points
# ============================================================

def export_switching_points(switch_points):
    df = pd.DataFrame(switch_points)

    if df.empty:
        print("No switching points found.")
    else:
        df.to_csv(output_switch_table_file, index=False, encoding="utf-8-sig")
        print(f"Saved table: {output_switch_table_file}")
        print(df)


# ============================================================
# 11. 主程序 / Main
# ============================================================

if __name__ == "__main__":

    cost_values, expected_costs, best_strategies = generate_strategy_switching_curve(
        p_soul=p_soul_fixed,
        cost_min=cost_min,
        cost_max=cost_max,
        num_points=num_points
    )

    switch_points = find_switching_points(
        cost_values,
        expected_costs,
        best_strategies
    )

    export_switching_points(switch_points)

    plot_strategy_switching_curve(
        cost_values,
        expected_costs,
        best_strategies,
        switch_points,
        p_soul_fixed
    )

    print("\nParameters:")
    print(f"p_soul = {p_soul_fixed}")
    print(f"cost_bless range = [{cost_min}, {cost_max}]")
    print(f"num_points = {num_points}")
