# Combined Mapping:
# 1. Best Expected Cost vs p_soul and cost_bless
# 2. Bless Use Boundary Map
#
# 合并版：
# 1. 最佳期望成本 vs 灵魂成功率与祝福宝石相对价值
# 2. 是否需要使用祝福宝石的策略分界图

import itertools
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# ============================================================
# 1. 参数设置 Initialization
# ============================================================

cost_soul = 1

# 参数扫描范围 / Parameter scanning range
p_min = 0.35
p_max = 0.87
cost_min = 3.1
cost_max = 8.5
p_points = 300
cost_points = 100

# 输出文件 / Output files
output_surface_data_file = "surface_expected_total_cost.csv"
output_best_strategy_file = "surface_best_strategy.csv"

output_3d_figure_file = "expected_total_cost_surface.png"
output_contour_figure_file = "expected_total_cost_contour.png"
output_phase_map_file = "bless_need_boundary_map.png"


# ============================================================
# 2. 基本规则设置 Basic Rules
# ============================================================

transient_states = list(range(9))
absorbing_state = 9


def fail_state(i):
    """
    灵魂宝石失败后的回退规则
    Failure rollback rule after Soul gem failure
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
# 3. 生成策略 Generating Strategies
# ============================================================

def generate_strategies():
    """
    生成 64 种策略：
    +0 到 +6 可选择 B 或 S；
    +6 到 +9 固定为 S。

    Generate 64 strategies:
    +0 to +6 can choose B or S;
    +6 to +9 are fixed as S.
    """
    strategies = []

    for choices in itertools.product(["B", "S"], repeat=6):
        full_strategy = list(choices) + ["S", "S", "S"]
        strategies.append(full_strategy)

    return strategies


# ============================================================
# 4. 转移矩阵 Transition Matrix
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
# 5. 成本计算 Cost Calculation
# ============================================================

def evaluate_strategy(strategy, p_soul, cost_bless):
    """
    计算单个策略的期望总成本
    Evaluate expected total cost for one strategy
    """
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
    """
    在给定 p_soul 和 cost_bless 下寻找最优策略
    Find the optimal strategy under given p_soul and cost_bless
    """
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
# 6. 参数扫描 Parameter Scanning
# ============================================================

def generate_surface_data(
    p_min,
    p_max,
    cost_min,
    cost_max,
    p_points,
    cost_points
    
    # p_min = 0.35
    # p_max = 0.86
    # cost_min = 4
    # cost_max = 8.5
    # p_points = 80
    # cost_points = 80
    
    
    
    
    
    
):
    """
    生成三维曲面数据：
    X: p_soul
    Y: cost_bless
    Z: expected_total_cost

    Generate surface data:
    X: p_soul
    Y: cost_bless
    Z: expected_total_cost
    """
    p_values = np.linspace(p_min, p_max, p_points)
    cost_values = np.linspace(cost_min, cost_max, cost_points)

    X, Y = np.meshgrid(p_values, cost_values)
    Z = np.zeros_like(X, dtype=float)
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
# 7. 导出数据 Export Data
# ============================================================

def export_surface_data(X, Y, Z, best_strategy_matrix):
    """
    导出：
    1. 扁平化曲面数据 surface_expected_total_cost.csv
    2. 最优策略矩阵 surface_best_strategy.csv

    Export:
    1. flattened surface data
    2. best strategy matrix
    """
    surface_df = pd.DataFrame({
        "p_soul": X.ravel(),
        "cost_bless": Y.ravel(),
        "expected_total_cost": Z.ravel(),
        "best_strategy": best_strategy_matrix.ravel()
    })

    surface_df.to_csv(
        output_surface_data_file,
        index=False,
        encoding="utf-8-sig"
    )

    strategy_df = pd.DataFrame(
        best_strategy_matrix,
        index=np.round(Y[:, 0], 4),
        columns=np.round(X[0, :], 4)
    )

    strategy_df.index.name = "cost_bless"
    strategy_df.columns.name = "p_soul"

    strategy_df.to_csv(
        output_best_strategy_file,
        encoding="utf-8-sig"
    )

    print("\nCSV 导出完成 / CSV files exported:")
    print(output_surface_data_file)
    print(output_best_strategy_file)


# ============================================================
# 8. 绘制最优成本三维图 Plot 3D Cost Surface
# ============================================================

def plot_expected_cost_surface(X, Y, Z):
    """
    绘制最优期望成本三维曲面图
    Plot 3D surface of optimal expected cost
    """
    fig = plt.figure(figsize=(12, 8))
    ax = fig.add_subplot(111, projection="3d")

    surface = ax.plot_surface(
        X,
        Y,
        Z,
        cmap="viridis",
        linewidth=0,
        antialiased=True
    )

    ax.set_xlim(p_min, p_max)
    ax.set_ylim(cost_min, cost_max)

    ax.set_xlabel("p_soul")
    ax.set_ylabel("cost_bless")
    ax.set_zlabel("expected_total_cost")

    ax.set_title("Best Expected Cost vs p_soul and cost_bless")

    fig.colorbar(
        surface,
        ax=ax,
        shrink=0.6,
        aspect=12,
        label="expected_total_cost"
    )

    plt.tight_layout()
    plt.savefig(output_3d_figure_file, dpi=300)
    plt.show()

    print(f"3D 图已保存 / 3D figure saved: {output_3d_figure_file}")


# ============================================================
# 9. 绘制最优成本等高线图 Plot Cost Contour Map
# ============================================================

def plot_expected_cost_contour(X, Y, Z):
    """
    绘制最优期望成本等高线图
    Plot contour map of optimal expected cost
    """
    plt.figure(figsize=(10, 7))

    contour = plt.contourf(
        X,
        Y,
        Z,
        levels=30,
        cmap="viridis"
    )

    plt.xlim(p_min, p_max)
    plt.ylim(cost_min, cost_max)

    plt.xlabel("p_soul")
    plt.ylabel("cost_bless")
    plt.title("Best Expected Cost Contour Map")

    cbar = plt.colorbar(contour)
    cbar.set_label("expected_total_cost")

    plt.tight_layout()
    plt.savefig(output_contour_figure_file, dpi=300)
    plt.show()

    print(f"等高线图已保存 / Contour figure saved: {output_contour_figure_file}")


# ============================================================
# 10. 构建祝福使用矩阵 Build Bless-Need Matrix
# ============================================================

def build_bless_need_matrix(strategy_matrix):
    """
    若最优策略中包含 B，则认为该参数点需要使用祝福。
    若最优策略全为 S，则认为不需要使用祝福。

    If the optimal strategy contains B, Bless is needed.
    If the optimal strategy is all S, Soul-only is optimal.
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


# ============================================================
# 11. 输出祝福使用区域统计 Print Bless-Need Summary
# ============================================================

def print_bless_summary(X, Y, bless_need_matrix):
    """
    输出祝福使用区域统计
    Print summary of Bless-needed and Soul-only regions
    """
    p_values = X[0, :]
    cost_values = Y[:, 0]

    total_points = bless_need_matrix.size
    bless_points = np.sum(bless_need_matrix == 1)
    soul_only_points = np.sum(bless_need_matrix == 0)

    print("\n参数范围 / Parameter range:")
    print(f"p_soul: {p_values.min():.4f} ~ {p_values.max():.4f}")
    print(f"cost_bless: {cost_values.min():.4f} ~ {cost_values.max():.4f}")

    print("\n区域统计 / Region summary:")
    print(f"总参数点数量 / Total points: {total_points}")
    print(f"需要祝福区域点数 / Bless-needed points: {bless_points}")
    print(f"不需要祝福区域点数 / Soul-only points: {soul_only_points}")
    print(f"需要祝福区域占比 / Bless-needed ratio: {bless_points / total_points:.2%}")
    print(f"不需要祝福区域占比 / Soul-only ratio: {soul_only_points / total_points:.2%}")


# ============================================================
# 12. 绘制祝福使用分界图 Plot Bless Boundary Map
# ============================================================

def plot_bless_boundary_map(X, Y, bless_need_matrix):
    """
    绘制祝福使用分界图：
    横轴：p_soul
    纵轴：cost_bless
    颜色：是否需要祝福
    黑色线：祝福 / 全灵魂策略边界

    Plot Bless usage boundary map:
    X-axis: p_soul
    Y-axis: cost_bless
    Color: whether Bless is needed
    Black line: boundary between Bless-needed and Soul-only regions
    """
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

    plt.title(
        "Boundary Between Bless-Needed and Soul-Only Optimal Strategies"
    )

    cbar = plt.colorbar(contour_fill, ticks=[0, 1])
    cbar.ax.set_yticklabels([
        "Soul only",
        "Bless needed"
    ])

    plt.xlim(p_min, p_max)
    plt.ylim(cost_min, cost_max)

    plt.tight_layout()
    plt.savefig(output_phase_map_file, dpi=300)
    plt.show()

    print(f"祝福使用分界图已保存 / Bless boundary map saved: {output_phase_map_file}")


# ============================================================
# 13. 主程序 Main
# ============================================================

if __name__ == "__main__":

    X, Y, Z, best_strategy_matrix = generate_surface_data(
        p_min=p_min,
        p_max=p_max,
        cost_min=cost_min,
        cost_max=cost_max,
        p_points=p_points,
        cost_points=cost_points
    )

    export_surface_data(X, Y, Z, best_strategy_matrix)

    plot_expected_cost_surface(X, Y, Z)

    plot_expected_cost_contour(X, Y, Z)

    bless_need_matrix = build_bless_need_matrix(best_strategy_matrix)

    print_bless_summary(X, Y, bless_need_matrix)

    plot_bless_boundary_map(X, Y, bless_need_matrix)

    print("\n全部任务完成 / All tasks completed.")