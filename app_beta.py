# app.py
# MU Online Item Upgrade Optimizer with Streamlit
# MU Online 装备强化最优策略可视化工具

import itertools
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st


# ============================================================
# 1. Core Model / 核心模型
# ============================================================

cost_soul = 1  # Cost of Soul gem / 灵魂宝石成本

luck_success_bonus = 0.25  # Luck talisman fixed bonus / 幸运符固定增加25%成功率


def fail_state(i):
    """
    Failure rollback rule.
    强化失败后的回退规则。
    """
    if i == 0:
        return 0
    elif 1 <= i <= 6:
        return i - 1
    elif 7 <= i <= 8:
        return 0
    elif 9 <= i <= 14:
        return 0
    else:
        raise ValueError("Invalid state / 无效状态")


level_upgrade_info = {
    9:  [1, 1, 1, 0.60, 0.50, 0.40],
    10: [2, 2, 1, 0.60, 0.50, 0.40],
    11: [3, 3, 1, 0.55, 0.45, 0.35],
    12: [4, 4, 1, 0.55, 0.45, 0.35],
    13: [5, 5, 1, 0.50, 0.40, 0.30],
    14: [6, 6, 1, 0.50, 0.40, 0.30],
}


def get_model_config(target_level):
    """
    Get model configuration according to target level.
    根据目标等级获取模型配置。

    target_level = 1~15: calculate +0 to target level.
    target_level = 1~15：计算 +0 到指定目标等级。
    """
    transient_states = list(range(target_level))
    absorbing_state = target_level

    decision_count = min(6, target_level)
    total_stage_count = target_level
    forced_soul_count = total_stage_count - decision_count
    high_stage_count = max(0, target_level - 9)

    return {
        "transient_states": transient_states,
        "absorbing_state": absorbing_state,
        "decision_count": decision_count,
        "total_stage_count": total_stage_count,
        "forced_soul_count": forced_soul_count,
        "high_stage_count": high_stage_count
    }


def get_high_level_success_rate(i, high_item_type_index, use_luck):
    """
    Get success rate for high-level combination stage.
    获取+9以上合成强化阶段的成功率。
    """
    base_success = level_upgrade_info[i][high_item_type_index]

    if use_luck:
        return min(base_success + luck_success_bonus, 1.0)

    return base_success


def generate_strategies(target_level):
    """
    Generate all necessary strategies.
    生成全部必要策略。

    +0 to +6: choose Bless or Soul.
    +0 到 +6：可选择祝福或灵魂。

    +6 to +9: fixed as Soul.
    +6 到 +9：固定使用灵魂。

    +9 to target: enumerate protection and luck talismans.
    +9 到目标等级：枚举保护符和幸运符使用情况。
    """
    config = get_model_config(target_level)
    decision_count = config["decision_count"]
    forced_soul_count = config["forced_soul_count"]
    high_stage_count = config["high_stage_count"]

    strategies = []

    for choices in itertools.product(["B", "S"], repeat=decision_count):
        strategy = list(choices) + ["S"] * forced_soul_count

        if high_stage_count > 0:
            for protect_flags in itertools.product([False, True], repeat=high_stage_count):
                for luck_flags in itertools.product([False, True], repeat=high_stage_count):
                    strategies.append({
                        "strategy": strategy,
                        "protect_flags": list(protect_flags),
                        "luck_flags": list(luck_flags)
                    })
        else:
            strategies.append({
                "strategy": strategy,
                "protect_flags": [],
                "luck_flags": []
            })

    return strategies


def build_transition_matrix(
    strategy_info,
    soul_success_rate,
    target_level,
    high_item_type_index
):
    """
    Build transient transition matrix Q.
    构建暂态转移矩阵 Q。
    """
    config = get_model_config(target_level)
    transient_states = config["transient_states"]
    absorbing_state = config["absorbing_state"]

    strategy = strategy_info["strategy"]
    protect_flags = strategy_info["protect_flags"]
    luck_flags = strategy_info["luck_flags"]

    q_soul = 1 - soul_success_rate
    Q = np.zeros((target_level, target_level))

    for i in transient_states:
        action = strategy[i]

        if action == "B":
            next_state = i + 1

            if next_state < absorbing_state:
                Q[i, next_state] = 1.0

        elif action == "S":
            if i <= 8:
                success_state = i + 1
                failure_state = fail_state(i)

                if success_state < absorbing_state:
                    Q[i, success_state] += soul_success_rate

                if failure_state < absorbing_state:
                    Q[i, failure_state] += q_soul

            else:
                high_index = i - 9
                use_luck = luck_flags[high_index]

                success_rate = get_high_level_success_rate(
                    i,
                    high_item_type_index,
                    use_luck
                )

                success_state = i + 1
                failure_state = fail_state(i)

                if success_state < absorbing_state:
                    Q[i, success_state] += success_rate

                if failure_state < absorbing_state:
                    Q[i, failure_state] += 1 - success_rate

        else:
            raise ValueError("Unknown action / 未知动作")

    return Q


def build_cost_vectors(
    strategy_info,
    soul_success_rate,
    bless_relative_cost,
    target_level,
    high_item_type_index,
    item_0_cost,
    chaos_cost,
    talisman_protect_cost,
    talisman_luck_cost
):
    """
    Build resource cost vectors.
    构建资源成本向量。
    """
    config = get_model_config(target_level)
    transient_states = config["transient_states"]

    strategy = strategy_info["strategy"]
    protect_flags = strategy_info["protect_flags"]
    luck_flags = strategy_info["luck_flags"]

    bless_vec = np.zeros(target_level)
    soul_vec = np.zeros(target_level)
    chaos_vec = np.zeros(target_level)
    protect_vec = np.zeros(target_level)
    luck_vec = np.zeros(target_level)
    item_0_loss_count_vec = np.zeros(target_level)
    item_0_loss_cost_vec = np.zeros(target_level)
    total_vec = np.zeros(target_level)

    for i in transient_states:
        action = strategy[i]

        if i <= 8:
            if action == "B":
                bless_vec[i] = 1
                total_vec[i] = bless_relative_cost
            else:
                soul_vec[i] = 1
                total_vec[i] = cost_soul

        else:
            high_index = i - 9
            use_protect = protect_flags[high_index]
            use_luck = luck_flags[high_index]

            B, S, chaos = level_upgrade_info[i][:3]

            success_rate = get_high_level_success_rate(
                i,
                high_item_type_index,
                use_luck
            )
            failure_rate = 1 - success_rate

            bless_vec[i] = B
            soul_vec[i] = S
            chaos_vec[i] = chaos

            if use_protect:
                protect_vec[i] = 1

            if use_luck:
                luck_vec[i] = 1

            if not use_protect:
                item_0_loss_count_vec[i] = failure_rate
                item_0_loss_cost_vec[i] = failure_rate * item_0_cost

            total_vec[i] = (
                B * bless_relative_cost
                + S * cost_soul
                + chaos * chaos_cost
                + protect_vec[i] * talisman_protect_cost
                + luck_vec[i] * talisman_luck_cost
                + item_0_loss_cost_vec[i]
            )

    return (
        bless_vec,
        soul_vec,
        chaos_vec,
        protect_vec,
        luck_vec,
        item_0_loss_count_vec,
        item_0_loss_cost_vec,
        total_vec
    )


def evaluate_strategy(
    strategy_info,
    soul_success_rate,
    bless_relative_cost,
    target_level,
    high_item_type_index,
    item_0_cost,
    chaos_cost,
    talisman_protect_cost,
    talisman_luck_cost
):
    """
    Evaluate one strategy.
    评估单个策略。
    """
    Q = build_transition_matrix(
        strategy_info,
        soul_success_rate,
        target_level,
        high_item_type_index
    )

    N = np.linalg.inv(np.eye(target_level) - Q)

    (
        bless_vec,
        soul_vec,
        chaos_vec,
        protect_vec,
        luck_vec,
        item_0_loss_count_vec,
        item_0_loss_cost_vec,
        total_vec
    ) = build_cost_vectors(
        strategy_info,
        soul_success_rate,
        bless_relative_cost,
        target_level,
        high_item_type_index,
        item_0_cost,
        chaos_cost,
        talisman_protect_cost,
        talisman_luck_cost
    )

    expected_bless = (N @ bless_vec)[0]
    expected_soul = (N @ soul_vec)[0]
    expected_chaos = (N @ chaos_vec)[0]
    expected_protect = (N @ protect_vec)[0]
    expected_luck = (N @ luck_vec)[0]
    expected_item_0_loss_count = (N @ item_0_loss_count_vec)[0]
    expected_item_0_loss_cost = (N @ item_0_loss_cost_vec)[0]
    expected_total = (N @ total_vec)[0]

    protect_str = "".join(["1" if x else "0" for x in strategy_info["protect_flags"]])
    luck_str = "".join(["1" if x else "0" for x in strategy_info["luck_flags"]])

    return {
        "strategy": "".join(strategy_info["strategy"]),
        "protect_flags": protect_str,
        "luck_flags": luck_str,
        "expected_bless": expected_bless,
        "expected_soul": expected_soul,
        "expected_chaos": expected_chaos,
        "expected_protect": expected_protect,
        "expected_luck": expected_luck,
        "expected_item_0_loss_count": expected_item_0_loss_count,
        "expected_item_0_loss_cost": expected_item_0_loss_cost,
        "expected_total_cost": expected_total
    }


def find_optimal_strategy(
    soul_success_rate,
    bless_relative_cost,
    target_level,
    high_item_type_index,
    item_0_cost,
    chaos_cost,
    talisman_protect_cost,
    talisman_luck_cost
):
    """
    Enumerate all strategies and rank them by expected total cost.
    枚举全部策略，并按期望总成本升序排序。
    """
    results = []

    for strategy_info in generate_strategies(target_level):
        result = evaluate_strategy(
            strategy_info,
            soul_success_rate,
            bless_relative_cost,
            target_level,
            high_item_type_index,
            item_0_cost,
            chaos_cost,
            talisman_protect_cost,
            talisman_luck_cost
        )
        results.append(result)

    df = pd.DataFrame(results)
    df = df.sort_values(by="expected_total_cost").reset_index(drop=True)
    df.insert(0, "rank", range(1, len(df) + 1))

    return df


def generate_switching_curve(
    soul_success_rate,
    bless_cost_min,
    bless_cost_max,
    num_points,
    target_level,
    high_item_type_index,
    item_0_cost,
    chaos_cost,
    talisman_protect_cost,
    talisman_luck_cost
):
    """
    Generate optimal cost curve under fixed Soul success rate.
    在固定灵魂成功率下，生成最优期望成本曲线。
    """
    bless_cost_values = np.linspace(
        bless_cost_min,
        bless_cost_max,
        num_points
    )

    expected_costs = []
    best_strategies = []

    for bless_relative_cost in bless_cost_values:
        result_df = find_optimal_strategy(
            soul_success_rate,
            bless_relative_cost,
            target_level,
            high_item_type_index,
            item_0_cost,
            chaos_cost,
            talisman_protect_cost,
            talisman_luck_cost
        )
        best = result_df.iloc[0]

        expected_costs.append(best["expected_total_cost"])
        best_strategies.append(best["strategy"])

    return bless_cost_values, np.array(expected_costs), best_strategies


def find_switching_points(
    bless_cost_values,
    expected_costs,
    best_strategies
):
    """
    Detect points where the optimal strategy changes.
    检测最优策略发生切换的位置。
    """
    switch_points = []

    for i in range(1, len(best_strategies)):
        if best_strategies[i] != best_strategies[i - 1]:
            switch_points.append({
                "index": i,
                "bless_relative_cost": bless_cost_values[i],
                "expected_total_cost": expected_costs[i],
                "from_strategy": best_strategies[i - 1],
                "to_strategy": best_strategies[i]
            })

    return pd.DataFrame(switch_points)


def strategy_to_stage_table(strategy, protect_flags="", luck_flags=""):
    """
    Convert strategy string into a stage-action table.
    将策略字符串转换为“强化阶段—宝石选择”表。
    """
    rows = []

    for i, action in enumerate(strategy):
        row = {
            "upgrade_stage / 强化阶段": f"+{i} → +{i + 1}",
            "action / 宝石选择": "Bless / 祝福" if action == "B" else "Soul / 灵魂",
            "symbol / 策略符号": action
        }

        if i >= 9:
            high_index = i - 9
            row["protect / 保护符"] = (
                "Yes / 使用" if high_index < len(protect_flags) and protect_flags[high_index] == "1"
                else "No / 不使用"
            )
            row["luck / 幸运符"] = (
                "Yes / 使用" if high_index < len(luck_flags) and luck_flags[high_index] == "1"
                else "No / 不使用"
            )
        else:
            row["protect / 保护符"] = "-"
            row["luck / 幸运符"] = "-"

        rows.append(row)

    return pd.DataFrame(rows)


# ============================================================
# 2. Plot Functions / 绘图函数
# ============================================================

def plot_switching_curve(
    bless_cost_values,
    expected_costs,
    switch_df,
    soul_success_rate,
    target_level
):
    """
    Plot optimal expected cost curve and strategy switching points.
    绘制最优期望成本曲线与策略切换点。
    """
    fig, ax = plt.subplots(figsize=(10, 6))

    ax.plot(
        bless_cost_values,
        expected_costs,
        linewidth=2,
        label="Optimal expected cost / 最优期望成本"
    )

    for _, row in switch_df.iterrows():
        x = row["bless_relative_cost"]
        y = row["expected_total_cost"]

        ax.axvline(x=x, linestyle="--", linewidth=1, alpha=0.7)
        ax.scatter(x, y, s=60)

        label_text = (
            f'{row["from_strategy"]}\n'
            f'→ {row["to_strategy"]}\n'
            f'cost={x:.2f}'
        )

        ax.annotate(
            label_text,
            xy=(x, y),
            xytext=(30, 35),
            textcoords="offset points",
            fontsize=8,
            arrowprops=dict(arrowstyle="->", linewidth=0.8)
        )

    ax.set_xlabel("祝福相对价值 Bless Relative Cost")
    ax.set_ylabel("最小期望总成本 Minimum Expected Total Cost")
    ax.set_title(
        f"策略切换曲线 Strategy Switching Curve "
        f"(目标 Target = +{target_level}, "
        f"灵魂成功率 Soul Success Rate = {soul_success_rate})"
    )
    ax.grid(True, alpha=0.3)
    ax.legend()

    fig.tight_layout()
    return fig


# ============================================================
# 3. Streamlit App / Streamlit 应用界面
# ============================================================

st.set_page_config(
    page_title="MU Online Upgrade Optimizer",
    layout="wide"
)

st.title("奇迹MU装备强化最优策略生成器")
st.title("MU Online Item Upgrade Optimizer")

st.caption(
    "简介：基于吸收型马尔可夫链与Bellman最优决策思想的装备强化策略优化模型，用于在不确定成功率与多资源成本条件下求解最优强化路径"
)

st.caption(
    "Intro: A Markov chain and Bellman-based optimization framework for item upgrades, designed to identify optimal strategies under stochastic success rates and multi-resource cost conditions"
)


# ============================================================
# 3.0 Purpose and Value / 用途和意义（中文 + 英文 Tab）
# ============================================================

with st.expander("🎯 用途和意义 / Purpose & Value", expanded=False):

    tab_cn1, tab_cn2, tab_cn3 = st.tabs(["总述", "常见误区", "核心功能"])

    with tab_cn1:
        st.header("总述")
        st.markdown("""
        ### 这个工具可以用来做什么？

        本工具并不是简单地估算“强化大概要花多少宝石”，而是用于在不同成功率、不同宝石价格条件下，自动寻找更优甚至最优的强化策略。

        它尤其适合：

        - 经常强化装备的玩家
        - 批量强化装备的玩家
        - 希望更理性评估装备价值的玩家
        - 关注市场与资源配置的商人型玩家
        """)

    with tab_cn2:
        st.header("常见误区")
        st.markdown("""
        **在项目开发过程中，玩家经常会提到一种基于经验性观点：**

        “掉落灵魂比祝福多，灵魂点装备不心疼。”

        但这种看法往往忽略了几个关键问题：

        - 灵魂与祝福本质上可以通过市场进行互换；
        - 强化失败会带来大量重复消耗与长期累计成本。

        灵魂宝石虽然单次价格较低，但失败可能导致装备回退、重复强化，最终累计消耗往往远高于直觉判断。

        因此，真正重要的问题并不是：

        “一次强化用了什么宝石？”

        而是：

        “达到目标等级，平均需要投入多少资源？”
        """)

    with tab_cn3:
        st.header("核心功能")
        st.markdown("""
        本工具的核心意义之一，就是：

        用可量化、可计算、可验证的理论模型，去客观描述大家长期积累的“经验”与“直觉”，并进一步形成辅助决策工具。

        核心功能包括：

        1. 生成最优强化策略，降低长期强化成本；
        2. 评估 +0 装备与高等级装备之间的理论价值差异；
        3. 判断“自己强化”还是“直接购买”更划算；
        4. 分析不同服务器经济环境下的策略变化；
        5. 为游戏商人的资源配置提供参考。
        """)

    tab_en1, tab_en2, tab_en3 = st.tabs(["Overview", "Common Misconceptions", "Core Features"])

    with tab_en1:
        st.header("Overview")
        st.markdown("""
        This tool is designed to help players determine the optimal upgrade strategy under different success rates and gem price conditions.

        It is especially suitable for:

        - Players who frequently upgrade equipment
        - Players upgrading in bulk
        - Players who want a rational framework for evaluating item value
        - Traders and economically-oriented players
        """)

    with tab_en2:
        st.header("Common Misconceptions")
        st.markdown("""
        A common player misconception is:

        "Soul Gems drop more often, so using Soul Gems is cheap."

        However, this ignores key points:

        - Soul and Bless Gems are interchangeable via the market
        - Upgrade failures create repeated consumption and long-term cost

        The important question is not:

        "What gem was used in a single upgrade?"

        But:

        "How many resources are expected to reach the target level?"
        """)

    with tab_en3:
        st.header("Core Features")
        st.markdown("""
        Key features of this tool:

        1. Generate optimal upgrade strategies and reduce long-term cost
        2. Estimate theoretical value gap between +0 and high-level items
        3. Decide whether manual upgrade or direct purchase is more economical
        4. Analyze strategy changes under different server economies
        5. Provide resource allocation reference for traders
        """)


# ============================================================
# Visualization Gallery / 图表示例
# ============================================================

with st.expander("📊 可视化结果示例 Visualization Gallery", expanded=False):

    st.markdown("""
    本项目除当前交互式计算结果外，
    还提供了多种用于分析强化策略变化规律的可视化图表。

    In addition to the interactive optimizer,
    the project also provides several visualization maps
    for analyzing upgrade strategy behaviors.
    """)

    fig_tab1, fig_tab2, fig_tab3 = st.tabs([
        "Optimal Cost Surface",
        "Strategy Phase Boundary",
        "Multi-Curve Comparison"
    ])

    github_raw_base = (
        "https://raw.githubusercontent.com/"
        "razzer1114/MuOnline_item_upgrade_cost_calculator/master/"
    )

    with fig_tab1:
        st.markdown("""
        ### Optimal Cost Surface

        展示不同灵魂成功率与祝福相对价值下，
        最低期望强化成本的整体分布曲面。

        Shows the global minimum expected upgrade cost surface
        under different Soul success rates and Bless relative costs.
        """)

        st.image(
            github_raw_base + "bestcost_3d_mapping.png",
            use_container_width=True
        )

    with fig_tab2:
        st.markdown("""
        ### Strategy Phase Boundary

        展示不同参数条件下，
        最优策略何时开始需要使用祝福宝石。

        Shows when Bless Gems become necessary
        in the optimal strategy.
        """)

        st.image(
            github_raw_base + "bless_need_boundary_map.png",
            use_container_width=True
        )

    with fig_tab3:
        st.markdown("""
        ### Multi-Curve Comparison

        对比不同灵魂成功率下，
        最优成本曲线随祝福相对价值变化的趋势。

        Compares optimal cost curves
        under multiple Soul success rates.
        """)

        st.image(
            github_raw_base + "multi_p_soul_3d_cost_curves.png",
            use_container_width=True
        )


st.markdown("---")
st.markdown("#### Developed by 作者： Razz ")
st.markdown("GitHub: https://github.com/razzer1114/MuOnline_item_upgrade_cost_calculator")
st.markdown("---")


# ============================================================
# 3.1 Sidebar Parameters / 左侧栏参数
# ============================================================

st.sidebar.markdown("---")

st.sidebar.header("执行操作 Run")
run_button = st.sidebar.button("运行优化 Run Optimization")

st.sidebar.markdown("---")

st.sidebar.header("基础模型参数 Basic Model Settings")

target_mode = st.sidebar.selectbox(
    "目标等级 Target Level",
    [f"+0 → +{i} " for i in range(1, 16)],
    index=8
)

target_level = int(target_mode.split("+")[-1])

item_type = st.sidebar.selectbox(
    "成功率/装备类型 Success Rate/Item Type",
    [
        "自定义 / Custom",

        "镶宝 / Socket item, p = 0.40",
        "新版镶宝 / Socket item (New), p = 0.50",

        "卓越 / Excellent item, p = 0.50",
        "套装 / Set item, p = 0.50",

        "白装 / Normal item, p = 0.60",
        "卷轴 / Scroll, p = 0.60",
        "翅膀 / Wing, p = 0.60",

        "幸运镶宝 / Lucky socket item, p = 0.65",
        "新版幸运镶宝 / Lucky socket item (New), p = 0.75",

        "幸运卓越 / Lucky excellent item, p = 0.75",
        "幸运套装 / Lucky set item, p = 0.75",

        "幸运白装 / Lucky normal item, p = 0.85",
        "幸运翅膀 / Lucky wing, p = 0.85"
    ]
)

preset_map = {
    "镶宝 / Socket item, p = 0.40": 0.40,
    "新版镶宝 / Socket item (New), p = 0.50": 0.50,

    "卓越 / Excellent item, p = 0.50": 0.50,
    "套装 / Set item, p = 0.50": 0.50,

    "白装 / Normal item, p = 0.60": 0.60,
    "卷轴 / Scroll, p = 0.60": 0.60,
    "翅膀 / Wing, p = 0.60": 0.60,

    "幸运镶宝 / Lucky socket item, p = 0.65": 0.65,
    "新版幸运镶宝 / Lucky socket item (New), p = 0.75": 0.75,

    "幸运卓越 / Lucky excellent item, p = 0.75": 0.75,
    "幸运套装 / Lucky set item, p = 0.75": 0.75,

    "幸运白装 / Lucky normal item, p = 0.85": 0.85,
    "幸运翅膀 / Lucky wing, p = 0.85": 0.85
}

if item_type == "自定义 / Custom":
    soul_success_rate = st.sidebar.number_input(
        "灵魂成功率 Soul Success Rate",
        min_value=0.01,
        max_value=0.99,
        value=0.50,
        step=0.01,
        format="%.2f"
    )
else:
    soul_success_rate = preset_map[item_type]
    st.sidebar.info(
        f"使用预设 / Using preset："
        f"灵魂成功率 Soul Success Rate = {soul_success_rate}"
    )


st.sidebar.markdown("---")
st.sidebar.header("高阶合成参数 High-level Combination Settings")

high_item_type = st.sidebar.selectbox(
    "高阶装备类型 High-level Item Type",
    [
        "Normal item / 普通装备",
        "Excellent or set item / 卓越或套装",
        "Socket item / 镶宝装备"
    ]
)

high_item_type_index_map = {
    "Normal item / 普通装备": 3,
    "Excellent or set item / 卓越或套装": 4,
    "Socket item / 镶宝装备": 5
}

high_item_type_index = high_item_type_index_map[high_item_type]

item_0_cost = st.sidebar.number_input(
    "+0装备价值 Item +0 Cost",
    min_value=0.0,
    max_value=999999.0,
    value=10.0,
    step=0.1
)

chaos_cost = st.sidebar.number_input(
    "玛雅之石价值 Chaos Cost",
    min_value=0.0,
    max_value=999999.0,
    value=5.0,
    step=0.1
)

talisman_protect_cost = st.sidebar.number_input(
    "保护符价值 Protection Talisman Cost",
    min_value=0.0,
    max_value=999999.0,
    value=3.0,
    step=0.1
)

talisman_luck_cost = st.sidebar.number_input(
    "幸运符价值 Luck Talisman Cost",
    min_value=0.0,
    max_value=999999.0,
    value=2.0,
    step=0.1
)

st.sidebar.caption(
    "幸运符固定增加25%成功率 / Luck talisman fixed bonus: +25%"
)


st.sidebar.markdown("---")
st.sidebar.header("宝石价值参数 Gem Value Settings")

bless_cost_input_mode = st.sidebar.radio(
    "祝福相对价值输入 Bless Relative Cost Input",
    [
        "相对价值 Direct input",
        "宝石单价 Gem prices",
        "兑换比例 Exchange ratio"
    ]
)

if bless_cost_input_mode == "相对价值 Direct input":

    bless_relative_cost = st.sidebar.number_input(
        "祝福相对价值(颗/颗) Bless Relative Cost(gem/gem)",
        min_value=0.50,
        max_value=50.00,
        value=5.29,
        step=0.0001,
        format="%.4f"
    )

elif bless_cost_input_mode == "宝石单价 Gem prices":

    bless_unit_price = st.sidebar.number_input(
        "祝福单价(￥/颗) Bless Unit Price($/gem)",
        min_value=0.0001,
        max_value=999999.0,
        value=1 / 1.35,
        step=0.0001,
        format="%.4f"
    )

    soul_unit_price = st.sidebar.number_input(
        "灵魂单价 Soul Unit Price",
        min_value=0.0001,
        max_value=999999.0,
        value=1 / 7.14,
        step=0.0001,
        format="%.4f"
    )

    bless_relative_cost = bless_unit_price / soul_unit_price

    st.sidebar.info(
        f"换算结果 Conversion Result：1 Bless = {bless_relative_cost:.4f} Soul"
    )

elif bless_cost_input_mode == "兑换比例 Exchange ratio":

    bless_amount = st.sidebar.number_input(
        "祝福数量(颗) Bless Amount (gem)",
        min_value=1,
        max_value=999999,
        value=9,
        step=1,
    )

    soul_amount = st.sidebar.number_input(
        "等于多少灵魂 Equivalent Soul Amount",
        min_value=1,
        max_value=999999,
        value=50,
        step=1,
    )

    bless_relative_cost = soul_amount / bless_amount

    st.sidebar.info(
        f"换算结果 Conversion：1 Bless = {bless_relative_cost:.4f} Soul"
    )


st.sidebar.markdown("---")
st.sidebar.header("曲线设置 Curve Settings")
st.sidebar.caption("设置策略切换曲线的扫描范围 / Set the scan range for the strategy switching curve")

bless_cost_min = st.sidebar.number_input(
    "祝福相对价值最小值 Minimum Bless Relative Cost",
    min_value=0.1,
    max_value=50.0,
    value=2.0,
    step=0.1
)

bless_cost_max = st.sidebar.number_input(
    "祝福相对价值最大值 Maximum Bless Relative Cost",
    min_value=0.1,
    max_value=50.0,
    value=15.0,
    step=0.1
)

num_points = st.sidebar.slider(
    "曲线采样点数 Number of Curve Points",
    min_value=50,
    max_value=1000,
    value=50,
    step=50
)


# ============================================================
# 4. Main Display / 主界面展示
# ============================================================

if run_button:

    result_df = find_optimal_strategy(
        soul_success_rate,
        bless_relative_cost,
        target_level,
        high_item_type_index,
        item_0_cost,
        chaos_cost,
        talisman_protect_cost,
        talisman_luck_cost
    )

    best = result_df.iloc[0]

    st.subheader("当前模型参数 Current Model Settings")

    setting_col1, setting_col2, setting_col3, setting_col4 = st.columns(4)

    setting_col1.metric(
        "目标等级 Target Level",
        f"+0 → +{target_level}"
    )
    setting_col2.metric(
        "灵魂成功率 Soul Success Rate",
        f"{soul_success_rate:.2f}"
    )
    setting_col3.metric(
        "祝福相对价值 Bless Relative Cost",
        f"{bless_relative_cost:.4f}"
    )
    setting_col4.metric(
        "策略数量 Strategy Count",
        f"{len(result_df)}"
    )

    st.markdown("---")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "最优策略 Best Strategy",
        best["strategy"]
    )
    col2.metric(
        "最小成本期望 Minimum Expected Cost",
        f"{best['expected_total_cost']:.4f}"
    )
    col3.metric(
        "期望装备损失 Expected Item Loss",
        f"{best['expected_item_0_loss_count']:.4f}"
    )
    col4.metric(
        "期望损失价值 Expected Loss Cost",
        f"{best['expected_item_0_loss_cost']:.4f}"
    )

    st.subheader("最优策略 Optimal Strategy")

    best_df = pd.DataFrame([{
        "rank / 排名": best["rank"],
        "target_level / 目标等级": f"+0 → +{target_level}",
        "strategy / 策略": best["strategy"],
        "protect_flags / 保护符": best["protect_flags"],
        "luck_flags / 幸运符": best["luck_flags"],
        "expected_bless / 期望祝福": best["expected_bless"],
        "expected_soul / 期望灵魂": best["expected_soul"],
        "expected_chaos / 期望玛雅": best["expected_chaos"],
        "expected_protect / 期望保护符": best["expected_protect"],
        "expected_luck / 期望幸运符": best["expected_luck"],
        "expected_item_0_loss_count / 期望损失装备数量": best["expected_item_0_loss_count"],
        "expected_item_0_loss_cost / 期望损失装备价值": best["expected_item_0_loss_cost"],
        "expected_total_cost / 期望总成本": best["expected_total_cost"]
    }])

    st.dataframe(best_df, use_container_width=True)

    st.subheader("最优策略展开 Optimal Strategy by Upgrade Stage")

    best_stage_df = strategy_to_stage_table(
        best["strategy"],
        best["protect_flags"],
        best["luck_flags"]
    )
    st.dataframe(best_stage_df, use_container_width=True)

    st.subheader("成本最低的前10种策略 Top 10 Strategies")

    st.dataframe(
        result_df.head(10),
        use_container_width=True
    )

    csv_result = result_df.to_csv(index=False, encoding="utf-8-sig")

    st.download_button(
        label="下载策略结果 CSV Download Strategy Results CSV",
        data=csv_result,
        file_name=f"strategy_results_plus0_to_plus{target_level}.csv",
        mime="text/csv"
    )

    st.subheader("策略切换曲线 Strategy Switching Curve")

    if target_level <= 9:
        bless_cost_values, expected_costs, best_strategies = generate_switching_curve(
            soul_success_rate=soul_success_rate,
            bless_cost_min=bless_cost_min,
            bless_cost_max=bless_cost_max,
            num_points=num_points,
            target_level=target_level,
            high_item_type_index=high_item_type_index,
            item_0_cost=item_0_cost,
            chaos_cost=chaos_cost,
            talisman_protect_cost=talisman_protect_cost,
            talisman_luck_cost=talisman_luck_cost
        )

        switch_df = find_switching_points(
            bless_cost_values,
            expected_costs,
            best_strategies
        )

        fig = plot_switching_curve(
            bless_cost_values,
            expected_costs,
            switch_df,
            soul_success_rate,
            target_level
        )

        st.pyplot(fig)

        curve_df = pd.DataFrame({
            "bless_relative_cost / 祝福相对价值": bless_cost_values,
            "expected_total_cost / 期望总成本": expected_costs,
            "best_strategy / 最优策略": best_strategies
        })

        st.download_button(
            label="下载曲线数据 CSV Download Curve Data CSV",
            data=curve_df.to_csv(index=False, encoding="utf-8-sig"),
            file_name=f"strategy_switching_curve_plus0_to_plus{target_level}.csv",
            mime="text/csv"
        )

        st.subheader("策略切换点 Strategy Switching Points")

        if switch_df.empty:
            st.info(
                "No strategy switching point found in the selected range. / "
                "当前范围内未发现策略切换点。"
            )
        else:
            switch_df_display = switch_df.rename(columns={
                "index": "index / 序号",
                "bless_relative_cost": "bless_relative_cost / 祝福相对价值",
                "expected_total_cost": "expected_total_cost / 期望总成本",
                "from_strategy": "from_strategy / 原策略",
                "to_strategy": "to_strategy / 新策略"
            })

            st.dataframe(switch_df_display, use_container_width=True)

            st.download_button(
                label="下载策略切换点 CSV Download Switching Points CSV",
                data=switch_df_display.to_csv(index=False, encoding="utf-8-sig"),
                file_name=f"strategy_switching_points_plus0_to_plus{target_level}.csv",
                mime="text/csv"
            )
    else:
        st.info(
            "目标等级超过 +9 时，策略空间包含保护符和幸运符组合，曲线扫描计算量较大。当前版本保留单点最优策略计算，暂不自动生成曲线。"
        )
        st.info(
            "For targets above +9, the strategy space includes protection and luck talisman combinations. Curve scanning may be computationally heavy, so this version keeps single-point optimization only."
        )

else:
    st.info(
        "请在左侧设置参数，然后点击“运行优化”。使用前请阅读《使用说明》。"
    )
    st.info(
        "Set parameters on the left and click Run Optimization after reading the Guide."
    )


# ============================================================
# 5. Guide / 使用说明
# ============================================================

with st.expander("📘 使用说明 Guide", expanded=False):

    st.markdown("""
    **1. 目标等级 Target Level**  
    当前支持从 `+0 → +1` 到 `+0 → +15` 的全部目标等级。  

    **2. 祝福相对价值 Bless Relative Cost**  
    表示祝福宝石与灵魂宝石之间的价格比值，即：  
    祝福单价 / 灵魂单价。

    **3. 灵魂成功率 Soul Success Rate**  
    表示使用灵魂宝石进行强化时的成功概率，用于计算强化路径的期望成本。

    **4. +9以上高阶合成 High-level Combination Above +9**  
    当目标等级超过 +9 时，模型会自动纳入：  
    - 玛雅之石成本；  
    - 保护符成本；  
    - 幸运符成本；  
    - 未使用保护符失败时的装备损失成本。  

    **5. 幸运符 Luck Talisman**  
    幸运符固定增加 25% 成功率。  

    **6. 策略 Strategy**  
    策略由字符序列组成，其中：  
    S 表示使用灵魂宝石（Soul）  
    B 表示使用祝福宝石（Bless）

    **7. protect_flags / luck_flags**  
    仅对应 +9 以上的高阶强化阶段。  
    1 表示使用，0 表示不使用。
    """)


# ============================================================
# 6. Disclaimer / 免责声明
# ============================================================

st.markdown("---")
st.markdown("### 免责声明 Disclaimer")

st.info(
"""
本项目基于用户输入的成功率与宝石相对价值进行计算，输出结果仅在所设定参数条件下成立。游戏内实际强化概率可能与官方公示存在偏差，且不同区服不同时刻的市场情况存在波动，因此计算结果不代表任何固定或真实环境下的唯一最优解。为提高适用性与可验证性，本工具支持自定义成功率与宝石相对价值，用户可根据自身服务器环境或经验数据进行调整与复现。项目提供的是一种计算方法与决策参考，而非对游戏实际机制的判定或保证。

This project performs calculations based on user-defined success rates and relative gem values. The results are valid only under the specified parameter settings. Actual in-game upgrade probabilities may deviate from officially stated values, and market conditions may vary across servers and over time. Therefore, the computed results do not represent a unique optimal solution for any fixed or real-world environment. To improve applicability and reproducibility, this tool allows users to customize success rates and relative gem values according to their own server conditions or empirical observations. This project provides a computational framework and decision reference, rather than a definitive statement or guarantee of actual game mechanics.
"""
)
