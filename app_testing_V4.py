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


def get_model_config(target_level):
    """
    Get model configuration according to target level.
    根据目标等级获取模型配置。

    target_level = 7: calculate +0 to +7
    target_level = 9: calculate +0 to +9
    """
    transient_states = list(range(target_level))
    absorbing_state = target_level

    # +0→+6 are the only free decision stages.
    # +0→+6 是可自由选择祝福/灵魂的阶段。
    decision_count = 6

    # Total upgrade stages = target_level
    # Example:
    # +0→+7 has 7 stages: 0,1,2,3,4,5,6
    # +0→+9 has 9 stages: 0,1,2,3,4,5,6,7,8
    total_stage_count = target_level

    forced_soul_count = total_stage_count - decision_count

    return {
        "transient_states": transient_states,
        "absorbing_state": absorbing_state,
        "decision_count": decision_count,
        "total_stage_count": total_stage_count,
        "forced_soul_count": forced_soul_count
    }


def generate_strategies(target_level):
    """
    Generate all 64 strategies.
    生成全部 64 种策略。

    +0 to +6: choose Bless or Soul.
    +0 到 +6：可选择祝福或灵魂。

    After +6: fixed as Soul.
    +6 之后：固定使用灵魂。
    """
    config = get_model_config(target_level)
    decision_count = config["decision_count"]
    forced_soul_count = config["forced_soul_count"]

    strategies = []

    for choices in itertools.product(["B", "S"], repeat=decision_count):
        strategy = list(choices) + ["S"] * forced_soul_count
        strategies.append(strategy)

    return strategies


def build_transition_matrix(strategy, soul_success_rate, target_level):
    """
    Build transient transition matrix Q.
    构建暂态转移矩阵 Q。
    """
    config = get_model_config(target_level)
    transient_states = config["transient_states"]
    absorbing_state = config["absorbing_state"]

    q_soul = 1 - soul_success_rate
    Q = np.zeros((target_level, target_level))

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

        else:
            raise ValueError("Unknown action / 未知动作")

    return Q


def evaluate_strategy(strategy, soul_success_rate, bless_relative_cost, target_level):
    """
    Evaluate one strategy.
    评估单个策略。

    Returns expected Bless consumption, expected Soul consumption,
    and expected total cost converted into Soul units.
    返回期望祝福消耗、期望灵魂消耗，以及折算为灵魂单位的期望总成本。
    """
    config = get_model_config(target_level)
    transient_states = config["transient_states"]

    Q = build_transition_matrix(strategy, soul_success_rate, target_level)
    N = np.linalg.inv(np.eye(target_level) - Q)

    bless_cost_vector = np.zeros(target_level)
    soul_cost_vector = np.zeros(target_level)
    total_cost_vector = np.zeros(target_level)

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


def find_optimal_strategy(soul_success_rate, bless_relative_cost, target_level):
    """
    Enumerate all strategies and rank them by expected total cost.
    枚举全部策略，并按期望总成本升序排序。
    """
    results = []

    for strategy in generate_strategies(target_level):
        result = evaluate_strategy(
            strategy,
            soul_success_rate,
            bless_relative_cost,
            target_level
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
    target_level
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
            target_level
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


def strategy_to_stage_table(strategy):
    """
    Convert strategy string into a stage-action table.
    将策略字符串转换为“强化阶段—宝石选择”表。
    """
    rows = []

    for i, action in enumerate(strategy):
        rows.append({
            "upgrade_stage / 强化阶段": f"+{i} → +{i + 1}",
            "action / 宝石选择": "Bless / 祝福" if action == "B" else "Soul / 灵魂",
            "symbol / 策略符号": action
        })

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
# 3.0 Purpose and Value / 用途和意义
# ============================================================

with st.expander("🎯 **这玩意有啥用？？**    **Why This Tool Exists？？**", expanded=False):

    st.markdown("""
### 这玩意有啥用？？

本工具并不是简单地估算“强化大概要花多少宝石”，而是用于在不同成功率、不同宝石价格条件下，生成最优的强化策略，以及进一步的分析。

适合：

- 经常、批量强化
- 不幸运装备、洞装
- 商人型玩家

---

在项目开发过程中，最常见一种观点：

> “掉落灵魂比祝福多，灵魂点装备不心疼。”

但这种看法忽略了两个**关键问题**：

- 灵魂与祝福本质上可以通过市场进行互换；
- 灵魂强化失败后带来大量重复消耗与长期累计成本；
- 区服市场状态的影响

最终导致累计消耗可能远高于直觉判断，没能用更少的资源得到同样的效果。

因此，真正重要的问题并不是简单的：

> “哪个宝石多？”“哪个宝石便宜”

而是：

> “达到目标等级，最少需要投入多少综合资源？”

除此之外，在不同服务器、不同阶段的市场环境下：

- 祝福与灵魂的价格比例可能非常接近；
- 某些新区甚至会出现价格倒挂；
- 玩家虽然知道“祝福更稳定”，却很难判断“到底什么时候该用祝福”。

类似地，当市场上同时存在 +0 与 +7 / +9 成品装备时：

玩家通常只能依赖经验、感觉或口口相传来判断：

> “到底是自己点装备更划算，还是直接买成品更划算？”

而本工具的核心意义之一，就是：

> 用可量化、可计算、可验证的理论模型，去客观描述大家长期积累的“经验”与“直觉”，并进一步形成辅助决策工具。

---

### 1. 生成最优强化策略，降低长期强化成本

玩家可以根据装备类型，或自行设定灵魂宝石成功率，计算从 +0 强化到目标等级（+7 或 +9）时：

- 每个阶段更适合使用祝福还是灵魂；
- 不同策略之间的长期成本差异；
- 当前参数下的最优强化路径。

对于经常或大量进行强化的玩家，该工具能够确保采用最经济的宝石利用策略。

---

### 2. 评估 +0 装备与高等级装备之间的理论价值差异

本工具可以根据市场中祝福与灵魂的相对价格，计算从 +0 强化到 +7 或 +9 的期望成本，从而为装备定价提供理论参考。

例如，一件 +9 装备的理论价值，至少应考虑：

- 基础装备价值；
- 强化过程中投入的期望资源成本。

但需要注意：

> +7 或 +9 与 +0 之间的实际市场差价，通常低于理论强化成本。

因为高阶装备往往在“抛售”，玩家此时希望快速换取现金或宝石，因此市场更偏向“买方市场”；而 +0 装备更有可能为新产出装备，为卖方“挂市场”日常操作，因此市场状态更接近对等交易。

---

### 3. 判断“自己强化”还是“直接购买”更划算

如果市场上的成品装备价格明显低于模型计算得到的强化期望成本，那么直接购买通常会更加稳定且经济。

反之，当：

- 高阶装备市场缺货(退坑人较少)；
- 版本更迭前期市场波动

自行强化可能更有优势。

---

### 4. 分析不同服务器经济环境下的策略变化

不同区服中：

- 祝福价格；
- 灵魂价格；
- 市场供需关系；

可能存在非常大的差异。

通过观察 **策略切换曲线（Strategy Switching Curve）**，玩家可以分析：

- 最优策略在何时发生变化；
- 何时祝福“值得使用”；
- 哪些强化阶段更适合使用祝福；
- 明确不同经济环境和强化风险的关系。

---

### 5. 为游戏商人的资源配置提供参考

对于商人型玩家，本工具还可以辅助分析：

- 宝石相对价值的合理性；
- 装备价格是否偏离理论成本；
- 是否存在低估、抛售、抄底机会。

例如：

如果某类宝石价格明显低于其实际强化价值，可能意味着市场低估；如果价格过高，则可能需要减少使用或等待市场回落。

对于长期玩家、商人而言，本工具可以辅助制定更加理性的资源配置方案。

---

### Why This Tool Exists？？

This tool is not simply designed to estimate “how many gems upgrading may cost.” Instead, it is intended to automatically identify better — or even optimal — upgrade strategies under different success rates and gem price conditions.

It is especially useful for:

- players who frequently upgrade equipment;
- players performing upgrades in bulk;
- players who want a more rational framework for evaluating item value;
- traders and economically-oriented players.

---

During development, one common player perspective repeatedly appeared:

> “Soul Gems drop more often, so using Soul Gems doesn’t feel expensive.”

However, this perspective often ignores two important facts:

- Soul Gems and Bless Gems are fundamentally interchangeable through the market;
- upgrade failures create large amounts of repeated consumption and long-term cumulative cost.

On the one hand, although Soul Gems may appear cheaper per attempt, failures can cause downgrades and repeated upgrading, leading to total resource consumption far higher than intuitive expectations.

As a result, one important practical question becomes:

> “Should Bless Gems actually be used?”

This tool is designed to provide a quantitative answer.

On the other hand, under certain market environments — especially on new servers or very old servers — the prices of Bless Gems and Soul Gems may become extremely close, or even inverted.

In such situations, most players intuitively understand that Bless Gems are “safer” or “more stable,” but still struggle to determine:

> “At which upgrade stages should Bless Gems actually be used?”

This tool is designed to provide a quantitative answer as well.

Similarly, when both +0 base items and +7 / +9 finished items coexist in the market, players often rely purely on experience, intuition, or community opinion to decide:

> “Is it more economical to upgrade manually or simply buy the finished item?”

This tool is designed to provide a quantitative answer too.

One of the core purposes of this project is therefore:

> to objectively describe long-standing player intuition and experience through a quantitative theoretical model, and further develop practical decision-support tools based on those models.

---

### 1. Generate optimal upgrade strategies and reduce long-term upgrade cost

Players can select an equipment type or manually define the Soul Gem success rate to calculate:

- whether Bless Gems or Soul Gems should be used at each stage;
- the long-term cost difference between strategies;
- the optimal upgrade path under current parameters.

For players who frequently upgrade equipment or perform upgrades in bulk, the tool can significantly reduce long-term average gem consumption.

---

### 2. Estimate the theoretical value gap between +0 items and high-level items

Using the relative market prices of Bless Gems and Soul Gems, the model can estimate the expected cost of upgrading from +0 to +7 or +9, providing a theoretical reference for item valuation.

For example, the theoretical value of a +9 item should include:

- the base item value;
- the expected resource cost consumed during upgrading.

However, the actual market price of high-level items is often lower than their theoretical upgrade cost.

This is because sellers of high-level items are usually attempting to quickly exchange them for cash or gems, creating a buyer-favored market. In contrast, +0 items are more commonly obtained through farming or monster drops, where sellers typically expect a more balanced return.

As a result:

> the actual market price difference between +0 and +7 / +9 items is often lower than the theoretical upgrade cost.

---

### 3. Decide whether manual upgrading or direct purchase is more economical

If the market price of a finished item is significantly lower than the expected upgrade cost calculated by the model, purchasing directly is usually the more stable and economical option.

On the other hand:

- when finished items are overpriced;
- when the market lacks supply;
- or when players have lower acquisition costs for resources;

manual upgrading may become more advantageous.

---

### 4. Analyze strategy changes under different server economies

Different servers may have dramatically different:

- Bless Gem prices;
- Soul Gem prices;
- supply-demand relationships.

By adjusting the Bless relative cost and observing the **Strategy Switching Curve**, players can analyze:

- when the optimal strategy changes;
- whether Bless Gems are worth using in the current server economy;
- which upgrade stages benefit most from Bless Gems;
- how upgrade risk changes under different market conditions.

---

### 5. Provide resource allocation references for in-game traders

For trader-oriented players, the model can also help analyze:

- whether gem prices are reasonable;
- whether item prices deviate from theoretical cost;
- potential opportunities for undervalued purchases, liquidation, hoarding, or market timing.

For example:

if a gem type appears significantly undervalued relative to its practical upgrade value, it may indicate a market opportunity; if overpriced, it may be preferable to reduce usage or wait for market correction.

For long-term players, traders, and guild resource managers, the tool can support more rational resource allocation decisions.
""")

st.markdown("---")
st.markdown("#### Developed by 作者： Razz ")
st.markdown("GitHub: https://github.com/razzer1114/MuOnline_item_upgrade_cost_calculator")
st.markdown("---")


# ============================================================
# 3.1 Sidebar Parameters / 左侧栏参数
# ============================================================

st.sidebar.header("参数设置 Parameter Settings")

target_mode = st.sidebar.selectbox(
    "目标等级 Target Level",
    [
        "+0 → +9 ",
        "+0 → +7 "
    ]
)

if target_mode == "+0 → +7 ":
    target_level = 7
else:
    target_level = 9

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
        f"Using preset / 使用预设："
        f"灵魂成功率 Soul Success Rate = {soul_success_rate}"
    )

bless_relative_cost = st.sidebar.number_input(
    "祝福相对价值 Bless Relative Cost",
    min_value=0.50,
    max_value=15.00,
    value=5.29,
    step=0.0001,
    format="%.4f"
)

st.sidebar.header("曲线设置 Curve Settings")

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

run_button = st.sidebar.button("运行优化 Run Optimization")


# ============================================================
# 4. Main Display / 主界面展示
# ============================================================

if run_button:

    result_df = find_optimal_strategy(
        soul_success_rate,
        bless_relative_cost,
        target_level
    )
    best = result_df.iloc[0]

    soul_only_strategy = list("S" * target_level)

    soul_only_result = evaluate_strategy(
        soul_only_strategy,
        soul_success_rate,
        bless_relative_cost,
        target_level
    )

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
        "64"
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
        "全灵魂成本 Soul-only Cost",
        f"{soul_only_result['expected_total_cost']:.4f}"
    )
    col4.metric(
        "节省成本 Cost Reduction",
        f"{soul_only_result['expected_total_cost'] - best['expected_total_cost']:.4f}"
    )

    st.subheader("最优策略 Optimal Strategy")

    best_df = pd.DataFrame([{
        "rank / 排名": best["rank"],
        "target_level / 目标等级": f"+0 → +{target_level}",
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

    st.subheader("最优策略展开 Optimal Strategy by Upgrade Stage")

    best_stage_df = strategy_to_stage_table(best["strategy"])
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
        file_name=f"strategy_results_64_plus0_to_plus{target_level}.csv",
        mime="text/csv"
    )

    st.subheader("策略切换曲线 Strategy Switching Curve")

    bless_cost_values, expected_costs, best_strategies = generate_switching_curve(
        soul_success_rate=soul_success_rate,
        bless_cost_min=bless_cost_min,
        bless_cost_max=bless_cost_max,
        num_points=num_points,
        target_level=target_level
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
    当前支持两种计算模式：  
    - `+0 → +7`：只计算从 +0 到 +7 的子模型，其中 +6→+7 固定使用灵魂。  
    - `+0 → +9`：完整模型，其中 +6→+7、+7→+8、+8→+9 固定使用灵魂。  

    **2. 祝福相对价值 Bless Relative Cost**  
    表示祝福宝石与灵魂宝石之间的价格比值，即：  
    祝福单价 / 灵魂单价。

    **3. 灵魂成功率 Soul Success Rate**  
    表示使用灵魂宝石进行强化时的成功概率，用于计算强化路径的期望成本。

    **4. 曲线 Curve**  
    表示在设定的祝福相对价值区间内，对所有最优策略进行采样得到的结果集合，用于分析策略变化趋势。

    **5. 策略 Strategy**  
    策略由字符序列组成，其中：  
    S 表示使用灵魂宝石（Soul）  
    B 表示使用祝福宝石（Bless）
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
