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
transient_states = list(range(9))  # Transient states +0 to +8 / 暂态 +0 至 +8
absorbing_state = 9  # Absorbing state +9 / 吸收态 +9


def fail_state(i):
    """
    Failure rollback rule.
    灵魂宝石强化失败后的回退规则。
    """
    if i == 0:
        return 0
    elif 1 <= i <= 6:
        return i - 1
    elif i in [7, 8]:
        return 0
    else:
        raise ValueError("Invalid state / 无效状态")


def generate_strategies():
    """
    Generate all 64 strategies.
    生成全部 64 种策略。

    +0 to +6: choose Bless or Soul.
    +0 到 +6：可选择祝福或灵魂。

    +6 to +9: fixed as Soul.
    +6 到 +9：固定使用灵魂。
    """
    strategies = []
    for choices in itertools.product(["B", "S"], repeat=6):
        strategy = list(choices) + ["S", "S", "S"]
        strategies.append(strategy)
    return strategies


def build_transition_matrix(strategy, soul_success_rate):
    """
    Build transient transition matrix Q.
    构建暂态转移矩阵 Q。
    """
    q_soul = 1 - soul_success_rate
    Q = np.zeros((9, 9))

    for i in transient_states:
        action = strategy[i]

        if action == "B":
            # Bless gem: deterministic success.
            # 祝福宝石：必定成功。
            next_state = i + 1
            if next_state < absorbing_state:
                Q[i, next_state] = 1.0

        elif action == "S":
            # Soul gem: probabilistic success/failure.
            # 灵魂宝石：概率成功/失败。
            success_state = i + 1
            failure_state = fail_state(i)

            if success_state < absorbing_state:
                Q[i, success_state] += soul_success_rate

            if failure_state < absorbing_state:
                Q[i, failure_state] += q_soul

    return Q


def evaluate_strategy(strategy, soul_success_rate, bless_relative_cost):
    """
    Evaluate one strategy.
    评估单个策略。

    Returns expected Bless consumption, expected Soul consumption,
    and expected total cost converted into Soul units.
    返回期望祝福消耗、期望灵魂消耗，以及折算为灵魂单位的期望总成本。
    """
    Q = build_transition_matrix(strategy, soul_success_rate)
    N = np.linalg.inv(np.eye(9) - Q)

    bless_cost_vector = np.zeros(9)
    soul_cost_vector = np.zeros(9)
    total_cost_vector = np.zeros(9)

    for i in transient_states:
        if strategy[i] == "B":
            bless_cost_vector[i] = 1
            total_cost_vector[i] = bless_relative_cost
        else:
            soul_cost_vector[i] = 1
            total_cost_vector[i] = cost_soul

    expected_bless = (N @ bless_cost_vector)[0]
    expected_soul = (N @ soul_cost_vector)[0]
    expected_total = (N @ total_cost_vector)[0]

    return {
        "strategy": "".join(strategy),
        "expected_bless": expected_bless,
        "expected_soul": expected_soul,
        "expected_total_cost": expected_total
    }


def find_optimal_strategy(soul_success_rate, bless_relative_cost):
    """
    Enumerate all strategies and rank them by expected total cost.
    枚举全部策略，并按期望总成本升序排序。
    """
    results = []

    for strategy in generate_strategies():
        result = evaluate_strategy(
            strategy,
            soul_success_rate,
            bless_relative_cost
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
    num_points
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
            bless_relative_cost
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


# ============================================================
# 2. Plot Functions / 绘图函数
# ============================================================

def plot_switching_curve(
    bless_cost_values,
    expected_costs,
    switch_df,
    soul_success_rate
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
        f"(灵魂成功率 Soul Success Rate = {soul_success_rate})"
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

st.markdown("---")
st.markdown("#### By Razz")
st.markdown("---")

st.markdown("#### 📘 使用说明 Guide")


st.markdown("""
**1. 祝福相对价值**  
表示祝福宝石与灵魂宝石之间的价格比值，即：  
祝福单价 / 灵魂单价。

**Bless Relative Cost** represents the price ratio between Bless and Soul gems, defined as:  
price of Bless / price of Soul.

**2. 灵魂成功率**  
表示使用灵魂宝石进行强化时的成功概率，用于计算强化路径的期望成本。

**Soul Success Rate** refers to the probability of a successful upgrade when using a Soul gem, which directly affects the expected cost.

**3. 曲线**  
表示在设定的祝福相对价值区间内，对所有最优策略进行采样得到的结果集合，用于分析策略变化趋势。

**Curve** represents the sampled set of optimal strategies across a range of Bless relative costs, used to analyze how strategies change under different economic conditions.

**4. 策略**  
策略由字符序列组成，其中：  
S 表示使用灵魂宝石（Soul）  
B 表示使用祝福宝石（Bless）

**Strategy** is represented as a sequence of characters:  
S = use Soul gem  
B = use Bless gem
""")

st.markdown("---")

st.sidebar.header("参数设置 Parameter Settings")

item_type = st.sidebar.selectbox(
    "装备类型 Item Type",
    [
        "Custom / 自定义",
        "Socket item / 镶宝装备, p = 0.40",
        "Excellent set / 卓越或套装, p = 0.50",
        "Normal item / 白装或卷轴, p = 0.60",
        "Lucky socket item / 幸运镶宝装备, p = 0.65",
        "Lucky excellent set / 幸运卓越套装, p = 0.75",
        "Lucky normal item / 幸运普通装备, p = 0.85"
    ]
)

preset_map = {
    "Socket item / 镶宝装备, p = 0.40": 0.40,
    "Excellent set / 卓越或套装, p = 0.50": 0.50,
    "Normal item / 白装或卷轴, p = 0.60": 0.60,
    "Lucky socket item / 幸运镶宝装备, p = 0.65": 0.65,
    "Lucky excellent set / 幸运卓越套装, p = 0.75": 0.75,
    "Lucky normal item / 幸运普通装备, p = 0.85": 0.85
}

if item_type == "Custom / 自定义":
    soul_success_rate = st.sidebar.slider(
        "灵魂成功率 Soul Success Rate",
        min_value=0.01,
        max_value=0.99,
        value=0.50,
        step=0.01
    )
else:
    soul_success_rate = preset_map[item_type]
    st.sidebar.info(
        f"Using preset / 使用预设："
        f"灵魂成功率 Soul Success Rate = {soul_success_rate}"
    )

bless_relative_cost = st.sidebar.slider(
    "祝福相对价值 Bless Relative Cost",
    min_value=0.50,
    max_value=15.00,
    value=5.29,
    step=0.01
)

st.sidebar.header("曲线设置 Curve Settings")

bless_cost_min = st.sidebar.number_input(
    "祝福相对价值最小值 Minimum Bless Relative Cost",
    min_value=0.1,
    max_value=50.0,
    value=0.5,
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
    value=300,
    step=50
)

run_button = st.sidebar.button("运行优化 Run Optimization")


# ============================================================
# 4. Main Display / 主界面展示
# ============================================================

if run_button:

    result_df = find_optimal_strategy(
        soul_success_rate,
        bless_relative_cost
    )
    best = result_df.iloc[0]

    soul_only_result = evaluate_strategy(
        list("SSSSSSSSS"),
        soul_success_rate,
        bless_relative_cost
    )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "灵魂成功率 Soul Success Rate",
        f"{soul_success_rate:.2f}"
    )
    col2.metric(
        "祝福相对价值 Bless Relative Cost",
        f"{bless_relative_cost:.4f}"
    )
    col3.metric(
        "最优策略 Best Strategy",
        best["strategy"]
    )
    col4.metric(
        "最小成本 Minimum Cost",
        f"{best['expected_total_cost']:.4f}"
    )

    st.subheader("最优策略 Optimal Strategy")

    best_df = pd.DataFrame([{
        "rank / 排名": best["rank"],
        "strategy / 策略": best["strategy"],
        "expected_bless / 期望祝福消耗": best["expected_bless"],
        "expected_soul / 期望灵魂消耗": best["expected_soul"],
        "expected_total_cost / 期望总成本": best["expected_total_cost"],
        "soul_only_expected_total_cost / 全灵魂期望总成本": soul_only_result["expected_total_cost"],
        "cost_reduction_vs_soul_only / 相对全灵魂节省成本": (
            soul_only_result["expected_total_cost"]
            - best["expected_total_cost"]
        )
    }])

    st.dataframe(best_df, use_container_width=True)

    st.subheader("成本最低的前10种策略 Top 10 Strategies")

    st.dataframe(
        result_df.head(10),
        use_container_width=True
    )

    csv_result = result_df.to_csv(index=False, encoding="utf-8-sig")

    st.download_button(
        label="下载策略结果 CSV Download Strategy Results CSV",
        data=csv_result,
        file_name="strategy_results_64.csv",
        mime="text/csv"
    )

    st.subheader("策略切换曲线 Strategy Switching Curve")

    bless_cost_values, expected_costs, best_strategies = generate_switching_curve(
        soul_success_rate=soul_success_rate,
        bless_cost_min=bless_cost_min,
        bless_cost_max=bless_cost_max,
        num_points=num_points
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
        soul_success_rate
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
        file_name="strategy_switching_curve.csv",
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
            file_name="strategy_switching_points.csv",
            mime="text/csv"
        )

else:
    st.info(
        "请在左侧设置参数，然后点击“运行优化”"
    )
    st.info(
        "Set parameters on the left and click Run Optimization"
    )
    st.markdown("---")

st.markdown("### 免责声明 Disclaimer")

st.info(
"""
本项目基于用户输入的成功率与宝石相对价值进行计算，输出结果仅在所设定参数条件下成立。游戏内实际强化概率可能与官方公示存在偏差，且不同区服不同时刻的市场情况存在波动，因此计算结果不代表任何固定或真实环境下的唯一最优解。为提高适用性与可验证性，本工具支持自定义成功率与宝石相对价值，用户可根据自身服务器环境或经验数据进行调整与复现。项目提供的是一种计算方法与决策参考，而非对游戏实际机制的判定或保证。

This project performs calculations based on user-defined success rates and relative gem values. The results are valid only under the specified parameter settings. Actual in-game upgrade probabilities may deviate from officially stated values, and market conditions may vary across servers and over time. Therefore, the computed results do not represent a unique optimal solution for any fixed or real-world environment. To improve applicability and reproducibility, this tool allows users to customize success rates and relative gem values according to their own server conditions or empirical observations. This project provides a computational framework and decision reference, rather than a definitive statement or guarantee of actual game mechanics.
"""
)
