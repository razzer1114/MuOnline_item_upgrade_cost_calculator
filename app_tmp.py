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

cost_soul = 1


def fail_state(i):
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


def get_high_level_success_rate(i, high_item_type_index, use_luck, luck_success_bonus):
    base_success = level_upgrade_info[i][high_item_type_index]

    if use_luck:
        return min(base_success + luck_success_bonus, 1.0)

    return base_success


def generate_strategies(target_level):
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
    high_item_type_index,
    luck_success_bonus
):
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
                use_protect = protect_flags[high_index]
                use_luck = luck_flags[high_index]

                success_rate = get_high_level_success_rate(
                    i,
                    high_item_type_index,
                    use_luck,
                    luck_success_bonus
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
    talisman_luck_cost,
    luck_success_bonus
):
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
                use_luck,
                luck_success_bonus
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
    talisman_luck_cost,
    luck_success_bonus
):
    Q = build_transition_matrix(
        strategy_info,
        soul_success_rate,
        target_level,
        high_item_type_index,
        luck_success_bonus
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
        talisman_luck_cost,
        luck_success_bonus
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
    talisman_luck_cost,
    luck_success_bonus
):
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
            talisman_luck_cost,
            luck_success_bonus
        )
        results.append(result)

    df = pd.DataFrame(results)
    df = df.sort_values(by="expected_total_cost").reset_index(drop=True)
    df.insert(0, "rank", range(1, len(df) + 1))

    return df


def strategy_to_stage_table(strategy, protect_flags="", luck_flags=""):
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
# 2. Streamlit App / Streamlit 应用界面
# ============================================================

st.set_page_config(
    page_title="MU Online Upgrade Optimizer",
    layout="wide"
)

st.title("奇迹MU装备强化最优策略生成器")
st.title("MU Online Item Upgrade Optimizer")

st.caption(
    "简介：基于吸收型马尔可夫链与Bellman最优决策思想的装备强化策略优化模型"
)

st.caption(
    "Intro: A Markov chain and Bellman-based optimization framework for item upgrades"
)

st.markdown("---")
st.markdown("#### Developed by 作者： Razz ")
st.markdown("GitHub: https://github.com/razzer1114/MuOnline_item_upgrade_cost_calculator")
st.markdown("---")


# ============================================================
# 3. Sidebar Parameters / 左侧栏参数
# ============================================================

st.sidebar.markdown("---")
st.sidebar.header("执行操作 Run")
run_button = st.sidebar.button("运行优化 Run Optimization")
st.sidebar.markdown("---")

st.sidebar.header("基础模型参数 Basic Model Settings")

target_mode = st.sidebar.selectbox(
    "目标等级 Target Level",
    [f"+0 → +{i}" for i in range(1, 16)],
    index=8
)

target_level = int(target_mode.split("+")[-1])

item_type = st.sidebar.selectbox(
    "灵魂成功率预设 Soul Success Rate Preset",
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
        f"Using preset / 使用预设：Soul Success Rate = {soul_success_rate}"
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

# 幸运符固定增加25%成功率
# Luck talisman always provides +25% success rate
luck_success_bonus = 0.25


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
        "祝福相对价值 Bless Relative Cost",
        min_value=0.50,
        max_value=50.00,
        value=5.29,
        step=0.0001,
        format="%.4f"
    )

elif bless_cost_input_mode == "宝石单价 Gem prices":
    bless_unit_price = st.sidebar.number_input(
        "祝福单价 Bless Unit Price",
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
        f"Conversion Result：1 Bless = {bless_relative_cost:.4f} Soul"
    )

else:
    bless_amount = st.sidebar.number_input(
        "祝福数量 Bless Amount",
        min_value=0.0001,
        max_value=999999.0,
        value=1.0,
        step=0.0001,
        format="%.4f"
    )

    soul_amount = st.sidebar.number_input(
        "等于多少灵魂 Equivalent Soul Amount",
        min_value=0.0001,
        max_value=999999.0,
        value=5.29,
        step=0.0001,
        format="%.4f"
    )

    bless_relative_cost = soul_amount / bless_amount

    st.sidebar.info(
        f"Conversion Result：1 Bless = {bless_relative_cost:.4f} Soul"
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
        talisman_luck_cost,
        luck_success_bonus
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

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "最优策略 Best Strategy",
        best["strategy"]
    )
    col2.metric(
        "最小成本期望 Minimum Expected Cost",
        f"{best['expected_total_cost']:.4f}"
    )
    col3.metric(
        "排名 Rank",
        int(best["rank"])
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

else:
    st.info(
        "请在左侧设置参数，然后点击“运行优化”。"
    )
    st.info(
        "Set parameters on the left and click Run Optimization."
    )


# ============================================================
# 5. Guide / 使用说明
# ============================================================

with st.expander("📘 使用说明 Guide", expanded=False):

    st.markdown("""
    **1. 目标等级 Target Level**  
    当前支持从 `+0 → +1` 到 `+0 → +15` 的全部目标等级。  

    **2. +0 → +6 阶段**  
    系统枚举 Bless / Soul 的所有组合。  

    **3. +6 → +9 阶段**  
    固定使用 Soul。  

    **4. +9 → +15 阶段**  
    系统枚举是否使用保护符和幸运符，并计算玛雅、符咒、装备损失等成本。  

    **5. 策略 Strategy**  
    S 表示 Soul / 灵魂。  
    B 表示 Bless / 祝福。  

    **6. protect_flags / luck_flags**  
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
本项目基于用户输入的成功率与宝石相对价值进行计算，输出结果仅在所设定参数条件下成立。
游戏内实际强化概率可能与官方公示存在偏差，且不同区服不同时刻的市场情况存在波动，
因此计算结果不代表任何固定或真实环境下的唯一最优解。

This project performs calculations based on user-defined success rates and relative gem values.
The results are valid only under the specified parameter settings.
Actual in-game upgrade probabilities and market conditions may vary.
"""
)
