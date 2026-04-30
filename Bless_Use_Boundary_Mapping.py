# 使用祝福策略与全灵魂策论的边界图
# Bless Use boundary 

# 要在主3D图代码同文件夹下紧随其后运行 即 Graph_LowestCost_vs_p_and_cob.py
# use this code after 3D mapping code and in the same folder, which is Graph_LowestCost_vs_p_and_cob


import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# ============================================================
# 1. 输入文件
# ============================================================

input_best_strategy_file = "surface_best_strategy.csv"

output_phase_map_file = "bless_need_boundary_map.png"


# ============================================================
# 2. 读取最佳策略矩阵
# ============================================================

def load_best_strategy_matrix(filename):
    """
    读取 surface_best_strategy.csv。

    行索引：cost_bless
    列索引：p_soul
    单元格：best_strategy，例如 SSBBBBSSS
    """

    df = pd.read_csv(filename, index_col=0)

    cost_values = df.index.astype(float).to_numpy()
    p_values = df.columns.astype(float).to_numpy()

    strategy_matrix = df.to_numpy()

    return p_values, cost_values, strategy_matrix


# ============================================================
# 3. 判断是否需要祝福
# ============================================================

def build_bless_need_matrix(strategy_matrix):
    """
    若最佳策略中包含 B，则认为该参数点“需要使用祝福”。
    若最佳策略全为 S，则认为“不需要使用祝福”。

    输出：
    bless_need_matrix:
        1 = 需要祝福
        0 = 不需要祝福
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
# 4. 绘制祝福使用分界图
# ============================================================

def plot_bless_boundary_map(
    p_values,
    cost_values,
    bless_need_matrix,
    strategy_matrix
):
    """
    绘制分区图：
    横轴：p_soul
    纵轴：cost_bless
    颜色：是否需要祝福
    黑色线：祝福 / 不祝福 的分界线
    """

    X, Y = np.meshgrid(p_values, cost_values)

    plt.figure(figsize=(10, 7))

    # 分区填色
    contour_fill = plt.contourf(
        X,
        Y,
        bless_need_matrix,
        levels=[-0.5, 0.5, 1.5],
        alpha=0.75
    )

    # 绘制分界线
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

    # 坐标轴
    plt.xlabel("Soul Success Probability p_soul")
    plt.ylabel("Relative Bless Cost cost_bless")

    plt.title(
        "Boundary Between Bless-Needed and Soul-Only Optimal Strategies"
    )

    # 色条
    cbar = plt.colorbar(contour_fill, ticks=[0, 1])
    cbar.ax.set_yticklabels([
        "Soul only",
        "Bless needed"
    ])

    # 边界范围自动匹配表格
    plt.xlim(p_values.min(), p_values.max())
    plt.ylim(cost_values.min(), cost_values.max())

    plt.tight_layout()
    plt.savefig(output_phase_map_file, dpi=300)
    plt.show()

    print(f"图像已保存：{output_phase_map_file}")


# ============================================================
# 5. 输出统计信息
# ============================================================

def print_summary(p_values, cost_values, bless_need_matrix):
    total_points = bless_need_matrix.size
    bless_points = np.sum(bless_need_matrix == 1)
    soul_only_points = np.sum(bless_need_matrix == 0)

    print("\n参数范围：")
    print(f"p_soul: {p_values.min():.4f} ~ {p_values.max():.4f}")
    print(f"cost_bless: {cost_values.min():.4f} ~ {cost_values.max():.4f}")

    print("\n区域统计：")
    print(f"总参数点数量：{total_points}")
    print(f"需要祝福区域点数：{bless_points}")
    print(f"不需要祝福区域点数：{soul_only_points}")
    print(f"需要祝福区域占比：{bless_points / total_points:.2%}")
    print(f"不需要祝福区域占比：{soul_only_points / total_points:.2%}")


# ============================================================
# 6. 主程序
# ============================================================

if __name__ == "__main__":

    p_values, cost_values, strategy_matrix = load_best_strategy_matrix(
        input_best_strategy_file
    )

    bless_need_matrix = build_bless_need_matrix(strategy_matrix)

    print_summary(
        p_values,
        cost_values,
        bless_need_matrix
    )

    plot_bless_boundary_map(
        p_values,
        cost_values,
        bless_need_matrix,
        strategy_matrix
    )