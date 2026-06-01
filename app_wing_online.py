# app.py
# ============================================================
# MU Online Level 1 Wing Synthesis Expected Cost Calculator
# 奇迹MU 一代翅膀合成期望成本计算器
# ============================================================

import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st


# ============================================================
# 1. Helper Functions / 工具函数
# ============================================================

def gold_to_soul(gold: float, gold_per_soul: float) -> float:
    """
    Convert gold value into Soul-equivalent value.
    将金币价值换算为灵魂价值。
    """
    return gold / gold_per_soul


def expected_life_jewels_to_target(target_level: int, p: float = 0.5) -> float:
    """
    Expected Life Jewel consumption from no option to target option level.
    计算从无追加到目标追加等级的期望生命宝石消耗。

    Rule:
    Success +1, failure reset to 0.
    成功 +1，失败归零。

    target_level:
        0 = no option / 无追加
        1 = +4 / 追4
        2 = +8 / 追8
        3 = +12 / 追12
        4 = +16 / 追16
    """
    if target_level <= 0:
        return 0.0

    if not 0 < p < 1:
        raise ValueError("生命宝石成功率必须在 0 和 1 之间")

    return (1 - p ** target_level) / ((1 - p) * (p ** target_level))


def option_name(level: int) -> str:
    """
    Option level name.
    追加等级名称。
    """
    mapping = {
        0: "无追加 / No Option",
        1: "追4 / +4 Option",
        2: "追8 / +8 Option",
        3: "追12 / +12 Option",
        4: "追16 / +16 Option",
    }
    return mapping.get(level, f"追{level * 4} / +{level * 4} Option")


def wing_success_rate(
    stone_count: int,
    base_success_rate: float,
    magic_stone_bonus: float,
    max_success_rate: float
) -> float:
    """
    Calculate wing conversion success rate by magic stone count.
    根据魔晶石数量计算翅膀转化成功率。
    """
    return min(
        base_success_rate + stone_count * magic_stone_bonus,
        max_success_rate
    )


def calculate_wing_synthesis(
    gold_per_soul: float,
    bless_value: float,
    soul_value: float,
    life_value: float,
    chaos_gold: float,
    maya_weapon_plus4_no_option_gold: float,
    relic_synthesis_gold: float,
    wing_conversion_gold: float,
    life_success_rate: float,
    target_option_level: int,
    base_success_rate: float,
    max_success_rate: float,
    magic_stone_bonus: float,
    magic_stone_value: float,
    max_magic_stone_count: int
):
    """
    Main calculation function.
    主计算函数。
    """

    # Gold-based costs converted into Soul-equivalent units.
    # 金币类成本换算为灵魂单位。
    chaos_value = gold_to_soul(chaos_gold, gold_per_soul)
    maya_weapon_plus4_no_option_value = gold_to_soul(
        maya_weapon_plus4_no_option_gold,
        gold_per_soul
    )
    relic_synthesis_gold_value = gold_to_soul(
        relic_synthesis_gold,
        gold_per_soul
    )
    wing_conversion_gold_value = gold_to_soul(
        wing_conversion_gold,
        gold_per_soul
    )

    # Life Jewel option expected cost.
    # 生命宝石追加期望成本。
    expected_life_count = expected_life_jewels_to_target(
        target_option_level,
        life_success_rate
    )
    expected_option_cost = expected_life_count * life_value

    # Maya weapon with option cost.
    # +4 追属性玛雅武器成本。
    maya_weapon_plus4_with_option_cost = (
        maya_weapon_plus4_no_option_value
        + expected_option_cost
    )

    # 1st wing relic cost.
    # 一代翅膀圣物成本。
    relic_cost = (
        maya_weapon_plus4_with_option_cost
        + bless_value
        + soul_value
        + chaos_value
        + relic_synthesis_gold_value
    )

    records = []

    for n in range(max_magic_stone_count + 1):
        p = wing_success_rate(
            stone_count=n,
            base_success_rate=base_success_rate,
            magic_stone_bonus=magic_stone_bonus,
            max_success_rate=max_success_rate
        )

        single_attempt_cost = (
            relic_cost
            + wing_conversion_gold_value
            + n * magic_stone_value
        )

        expected_total_cost = single_attempt_cost / p

        records.append({
            "low_magic_stone_count / 低级魔晶石数量": n,
            "success_rate / 转化成功率": p,
            "single_attempt_cost_soul / 单次尝试成本_灵魂": single_attempt_cost,
            "expected_total_cost_soul / 期望总成本_灵魂": expected_total_cost,
        })

    df = pd.DataFrame(records)
    best_row = df.loc[df["expected_total_cost_soul / 期望总成本_灵魂"].idxmin()]

    summary = {
        "chaos_value": chaos_value,
        "maya_weapon_plus4_no_option_value": maya_weapon_plus4_no_option_value,
        "relic_synthesis_gold_value": relic_synthesis_gold_value,
        "wing_conversion_gold_value": wing_conversion_gold_value,
        "expected_life_count": expected_life_count,
        "expected_option_cost": expected_option_cost,
        "maya_weapon_plus4_with_option_cost": maya_weapon_plus4_with_option_cost,
        "relic_cost": relic_cost,
        "best_row": best_row
    }

    return df, summary


def plot_expected_cost_curve(df: pd.DataFrame):
    """
    Plot expected cost under different magic stone counts.
    绘制不同魔晶石数量下的期望成本曲线。
    """
    fig, ax = plt.subplots(figsize=(10, 5))

    x = df["low_magic_stone_count / 低级魔晶石数量"]
    y = df["expected_total_cost_soul / 期望总成本_灵魂"]

    ax.plot(x, y, marker="o", linewidth=2)
    ax.set_xlabel("Low Magic Stone Count / 低级魔晶石数量")
    ax.set_ylabel("Expected Total Cost (Soul) / 期望总成本（灵魂）")
    ax.set_title("Expected Cost under Different Magic Stone Counts")
    ax.grid(True, alpha=0.3)

    fig.tight_layout()
    return fig


def format_percentage(x):
    return f"{x:.2%}"


# ============================================================
# 2. Streamlit Page Config / 页面配置
# ============================================================

st.set_page_config(
    page_title="MU Online 1st Wing Synthesis Calculator",
    layout="wide"
)

st.title("奇迹MU 一代翅膀合成期望成本计算器")
st.title("MU Online 1st Wing Synthesis Expected Cost Calculator")

st.caption(
    "基于一代翅膀圣物合成与圣物转化规则，计算不同低级魔晶石数量下的合成期望成本，并自动给出当前参数下的最优方案。"
)

st.caption(
    "This tool calculates the expected cost of 1st wing synthesis under different Low Magic Stone counts and identifies the cost-minimizing strategy."
)


# ============================================================
# 3. Purpose / 用途说明
# ============================================================

with st.expander("🎯 用途和说明 Purpose & Notes", expanded=False):
    tab1, tab2, tab3 = st.tabs([
        "模型逻辑 / Model Logic",
        "成本构成 / Cost Components",
        "适用说明 / Applicability"
    ])

    with tab1:
        st.markdown("""
        ### 模型逻辑

        本工具针对**一代翅膀合成**过程进行期望成本计算，流程包括：

        1. 准备 `+4 玛雅武器`；
        2. 通过生命宝石追加属性，例如追4、追8、追12、追16；
        3. 消耗祝福、灵魂、玛雅宝石和金币，合成一代翅膀圣物；
        4. 将一代翅膀圣物转化为一代翅膀；
        5. 可使用低级魔晶石提高转化成功率；
        6. 枚举不同低级魔晶石数量，计算期望总成本；
        7. 自动寻找期望成本最低的方案。

        ### Model Logic

        This tool models the 1st wing synthesis process by:

        1. Preparing a +4 Maya weapon;
        2. Adding option levels using Life Jewels;
        3. Synthesizing a 1st wing relic;
        4. Converting the relic into a 1st wing;
        5. Using Low Magic Stones to increase conversion success rate;
        6. Enumerating all Magic Stone counts;
        7. Selecting the strategy with the minimum expected total cost.
        """)

    with tab2:
        st.markdown("""
        ### 成本构成

        当前模型将所有资源统一折算为**灵魂宝石价值**：

        - 金币；
        - 玛雅宝石；
        - 玛雅武器；
        - 生命宝石；
        - 祝福宝石；
        - 灵魂宝石；
        - 低级魔晶石；
        - 圣物合成金币；
        - 圣物转化金币。

        其中：

        - `金币 / 灵魂` 可自定义；
        - `祝福价值` 可按服务器市场价格调整；
        - `低级魔晶石价值` 默认可设置为 1 祝福；
        - 生命宝石追加采用“成功 +1，失败归零”的期望模型。
        """)

    with tab3:
        st.markdown("""
        ### 适用说明

        本工具适用于分析：

        - 一代翅膀圣物合成成本；
        - 一代翅膀转化期望成本；
        - 低级魔晶石是否值得使用；
        - 当前市场价格下的最低期望成本方案；
        - 不同区服金币、宝石价格变化对最优策略的影响。

        注意：  
        本工具只计算**一代翅膀和一代翅膀圣物**，二代、三代及其他合成规则暂不纳入。
        """)


# ============================================================
# 4. Sidebar Parameters / 左侧栏参数
# ============================================================

st.sidebar.header("执行操作 Run")
run_button = st.sidebar.button("运行计算 Run Calculation")

st.sidebar.markdown("---")
st.sidebar.header("基础价值换算 Basic Value Conversion")

gold_per_soul = st.sidebar.number_input(
    "金币换算 Gold per Soul",
    min_value=1.0,
    max_value=999999999.0,
    value=10_000_000.0,
    step=100_000.0,
    format="%.0f"
)

soul_value = 1.0

bless_value = st.sidebar.number_input(
    "祝福价值 Bless Value (Soul)",
    min_value=0.01,
    max_value=100.0,
    value=3.0,
    step=0.01,
    format="%.2f"
)

life_value = st.sidebar.number_input(
    "生命价值 Life Jewel Value (Soul)",
    min_value=0.01,
    max_value=100.0,
    value=1.0,
    step=0.01,
    format="%.2f"
)

chaos_gold = st.sidebar.number_input(
    "玛雅宝石金币价值 Chaos Value (Gold)",
    min_value=0.0,
    max_value=999999999.0,
    value=500_000.0,
    step=10_000.0,
    format="%.0f"
)

maya_weapon_plus4_no_option_gold = st.sidebar.number_input(
    "+4不追加玛雅武器价值 +4 Maya Weapon without Option (Gold)",
    min_value=0.0,
    max_value=999999999.0,
    value=5_000_000.0,
    step=100_000.0,
    format="%.0f"
)

st.sidebar.markdown("---")
st.sidebar.header("圣物合成与转化 Relic Synthesis & Conversion")

relic_synthesis_gold = st.sidebar.number_input(
    "圣物合成金币 Relic Synthesis Gold",
    min_value=0.0,
    max_value=999999999.0,
    value=10_000.0,
    step=1_000.0,
    format="%.0f"
)

wing_conversion_gold = st.sidebar.number_input(
    "圣物转化金币 Relic-to-Wing Conversion Gold",
    min_value=0.0,
    max_value=999999999.0,
    value=1_000_000.0,
    step=10_000.0,
    format="%.0f"
)

st.sidebar.markdown("---")
st.sidebar.header("生命宝石追加 Life Jewel Option")

target_option_level = st.sidebar.selectbox(
    "目标追加 Target Option",
    options=[0, 1, 2, 3, 4],
    format_func=lambda x: option_name(x),
    index=1
)

life_success_rate = st.sidebar.number_input(
    "生命宝石成功率 Life Success Rate",
    min_value=0.01,
    max_value=0.99,
    value=0.50,
    step=0.01,
    format="%.2f"
)

st.sidebar.markdown("---")
st.sidebar.header("一代翅膀转化 1st Wing Conversion")

base_success_rate = st.sidebar.number_input(
    "基础成功率 Base Success Rate",
    min_value=0.01,
    max_value=1.00,
    value=0.20,
    step=0.01,
    format="%.2f"
)

max_success_rate = st.sidebar.number_input(
    "成功率上限 Max Success Rate",
    min_value=0.01,
    max_value=1.00,
    value=1.00,
    step=0.01,
    format="%.2f"
)

magic_stone_bonus = st.sidebar.number_input(
    "每颗低级魔晶石成功率加成 Magic Stone Bonus",
    min_value=0.00,
    max_value=1.00,
    value=0.05,
    step=0.01,
    format="%.2f"
)

magic_stone_value_mode = st.sidebar.radio(
    "低级魔晶石价值设置 Magic Stone Value Setting",
    [
        "按祝福价值计算 Based on Bless Value",
        "手动输入 Manual Input"
    ]
)

if magic_stone_value_mode == "按祝福价值计算 Based on Bless Value":
    magic_stone_value = bless_value
    st.sidebar.info(f"当前低级魔晶石价值：{magic_stone_value:.4f} 灵魂")
else:
    magic_stone_value = st.sidebar.number_input(
        "低级魔晶石价值 Low Magic Stone Value (Soul)",
        min_value=0.0,
        max_value=100.0,
        value=bless_value,
        step=0.01,
        format="%.2f"
    )

max_magic_stone_count = st.sidebar.number_input(
    "最大低级魔晶石数量 Max Low Magic Stone Count",
    min_value=0,
    max_value=100,
    value=16,
    step=1
)


# ============================================================
# 5. Main Display / 主界面展示
# ============================================================

if run_button:

    df, summary = calculate_wing_synthesis(
        gold_per_soul=gold_per_soul,
        bless_value=bless_value,
        soul_value=soul_value,
        life_value=life_value,
        chaos_gold=chaos_gold,
        maya_weapon_plus4_no_option_gold=maya_weapon_plus4_no_option_gold,
        relic_synthesis_gold=relic_synthesis_gold,
        wing_conversion_gold=wing_conversion_gold,
        life_success_rate=life_success_rate,
        target_option_level=target_option_level,
        base_success_rate=base_success_rate,
        max_success_rate=max_success_rate,
        magic_stone_bonus=magic_stone_bonus,
        magic_stone_value=magic_stone_value,
        max_magic_stone_count=max_magic_stone_count
    )

    best_row = summary["best_row"]

    st.subheader("当前模型参数 Current Model Settings")

    setting_col1, setting_col2, setting_col3, setting_col4 = st.columns(4)

    setting_col1.metric(
        "金币换算 Gold per Soul",
        f"{gold_per_soul:,.0f}"
    )
    setting_col2.metric(
        "祝福价值 Bless Value",
        f"{bless_value:.4f} 灵魂"
    )
    setting_col3.metric(
        "目标追加 Target Option",
        option_name(target_option_level)
    )
    setting_col4.metric(
        "基础成功率 Base Success Rate",
        f"{base_success_rate:.2%}"
    )

    st.markdown("---")

    st.subheader("最优方案 Optimal Strategy")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "建议低级魔晶石数量",
        f"{int(best_row['low_magic_stone_count / 低级魔晶石数量'])} 颗"
    )
    col2.metric(
        "对应成功率",
        f"{best_row['success_rate / 转化成功率']:.2%}"
    )
    col3.metric(
        "单次尝试成本",
        f"{best_row['single_attempt_cost_soul / 单次尝试成本_灵魂']:.4f} 灵魂"
    )
    col4.metric(
        "期望总成本",
        f"{best_row['expected_total_cost_soul / 期望总成本_灵魂']:.4f} 灵魂"
    )

    st.markdown("---")

    st.subheader("成本拆解 Cost Breakdown")

    cost_col1, cost_col2, cost_col3, cost_col4 = st.columns(4)

    cost_col1.metric(
        "期望生命宝石消耗",
        f"{summary['expected_life_count']:.4f} 颗"
    )
    cost_col2.metric(
        "期望追加成本",
        f"{summary['expected_option_cost']:.4f} 灵魂"
    )
    cost_col3.metric(
        "+4追属性玛雅武器成本",
        f"{summary['maya_weapon_plus4_with_option_cost']:.4f} 灵魂"
    )
    cost_col4.metric(
        "一代翅膀圣物成本",
        f"{summary['relic_cost']:.4f} 灵魂"
    )

    breakdown_df = pd.DataFrame([
        {
            "item / 项目": "玛雅宝石 Chaos Jewel",
            "cost_soul / 成本_灵魂": summary["chaos_value"]
        },
        {
            "item / 项目": "+4不追加玛雅武器 +4 Maya Weapon without Option",
            "cost_soul / 成本_灵魂": summary["maya_weapon_plus4_no_option_value"]
        },
        {
            "item / 项目": "生命追加期望成本 Expected Life Option Cost",
            "cost_soul / 成本_灵魂": summary["expected_option_cost"]
        },
        {
            "item / 项目": "+4追属性玛雅武器 +4 Maya Weapon with Option",
            "cost_soul / 成本_灵魂": summary["maya_weapon_plus4_with_option_cost"]
        },
        {
            "item / 项目": "祝福宝石 Bless Jewel",
            "cost_soul / 成本_灵魂": bless_value
        },
        {
            "item / 项目": "灵魂宝石 Soul Jewel",
            "cost_soul / 成本_灵魂": soul_value
        },
        {
            "item / 项目": "圣物合成金币 Relic Synthesis Gold",
            "cost_soul / 成本_灵魂": summary["relic_synthesis_gold_value"]
        },
        {
            "item / 项目": "一代翅膀圣物总成本 1st Wing Relic Cost",
            "cost_soul / 成本_灵魂": summary["relic_cost"]
        },
        {
            "item / 项目": "圣物转化金币 Relic-to-Wing Conversion Gold",
            "cost_soul / 成本_灵魂": summary["wing_conversion_gold_value"]
        },
    ])

    st.dataframe(
        breakdown_df,
        use_container_width=True
    )

    st.download_button(
        label="下载成本拆解 CSV Download Cost Breakdown CSV",
        data=breakdown_df.to_csv(index=False, encoding="utf-8-sig"),
        file_name="wing_synthesis_cost_breakdown.csv",
        mime="text/csv"
    )

    st.markdown("---")

    st.subheader("不同低级魔晶石数量下的期望成本 Expected Cost by Low Magic Stone Count")

    display_df = df.copy()
    display_df["success_rate_display / 成功率显示"] = display_df[
        "success_rate / 转化成功率"
    ].apply(format_percentage)

    st.dataframe(
        display_df,
        use_container_width=True
    )

    st.download_button(
        label="下载枚举结果 CSV Download Enumeration Results CSV",
        data=df.to_csv(index=False, encoding="utf-8-sig"),
        file_name="wing_synthesis_magic_stone_enumeration.csv",
        mime="text/csv"
    )

    st.markdown("---")

    st.subheader("期望成本曲线 Expected Cost Curve")

    fig = plot_expected_cost_curve(df)
    st.pyplot(fig)

    st.markdown("---")

    st.subheader("结果解释 Result Interpretation")

    st.info(
        f"""
        在当前参数下，最低期望成本方案为使用 
        **{int(best_row['low_magic_stone_count / 低级魔晶石数量'])} 颗低级魔晶石**。

        此时圣物转化成功率为 
        **{best_row['success_rate / 转化成功率']:.2%}**，
        单次尝试成本为 
        **{best_row['single_attempt_cost_soul / 单次尝试成本_灵魂']:.4f} 灵魂**，
        合成一代翅膀的期望总成本为 
        **{best_row['expected_total_cost_soul / 期望总成本_灵魂']:.4f} 灵魂**。
        """
    )

else:
    st.info(
        "请在左侧设置参数，然后点击“运行计算”。"
    )
    st.info(
        "Set parameters on the left and click Run Calculation."
    )


# ============================================================
# 6. Guide / 使用说明
# ============================================================

with st.expander("📘 使用说明 Guide", expanded=False):
    st.markdown("""
    ### 1. 金币换算 Gold per Soul

    表示多少金币折算为 1 颗灵魂宝石。  
    例如：`10,000,000` 表示 1000 万金币 = 1 灵魂。

    ### 2. 祝福价值 Bless Value

    表示 1 颗祝福宝石折算为多少颗灵魂宝石。  
    例如：`3.0` 表示 1 祝福 = 3 灵魂。

    ### 3. 生命宝石追加 Life Jewel Option

    追加规则采用：

    - 成功：追加等级 +1；
    - 失败：追加等级归零。

    因此从无追加到追4、追8、追12、追16 的生命宝石消耗不是简单线性关系，而是连续成功问题的期望值。

    ### 4. 一代翅膀转化 1st Wing Conversion

    当前默认规则为：

    - 基础成功率：20%；
    - 每颗低级魔晶石增加 5%；
    - 一代翅膀成功率上限：100%；
    - 最多枚举 16 颗低级魔晶石。

    你可以在左侧参数栏中自行修改这些数值。

    ### 5. 期望总成本 Expected Total Cost

    模型采用：

    `期望总成本 = 单次尝试成本 / 成功率`

    当增加低级魔晶石时：

    - 成功率提高；
    - 单次尝试成本也提高；

    因此最优方案并不一定是“不放魔晶石”，也不一定是“放满魔晶石”，需要通过枚举比较得到。
    """)


# ============================================================
# 7. Disclaimer / 免责声明
# ============================================================

st.markdown("---")
st.markdown("### 免责声明 Disclaimer")

st.info(
    """
    本项目基于用户输入的成功率、金币换算比例与宝石相对价值进行计算，
    输出结果仅在所设定参数条件下成立。游戏内实际合成概率、市场价格、
    宝石价值和金币价值可能因区服、时间和交易环境而发生变化，
    因此计算结果不代表任何固定或真实环境下的唯一最优解。

    本工具提供的是一种期望成本计算方法与决策参考，
    而非对游戏实际机制、官方概率或市场价格的判定或保证。

    This project performs calculations based on user-defined success rates,
    gold conversion ratios, and relative item values. The results are valid
    only under the specified parameter settings. Actual in-game probabilities,
    market prices, jewel values, and gold values may vary across servers and time.
    Therefore, the computed results should be treated as a computational reference,
    not as a guarantee of actual game mechanics or market outcomes.
    """
)


# ============================================================
# 8. Footer / 页脚
# ============================================================

st.markdown("---")
st.markdown("#### Developed by 作者：Razz")
st.markdown("GitHub: https://github.com/razzer1114/MuOnline_item_upgrade_cost_calculator")


# ============================================================
# 9. Visit Counter / 访问统计
# ============================================================

st.sidebar.markdown("---")
st.sidebar.markdown("### 📊 Visits / 访问量")

st.sidebar.markdown(
    """
    <a href="https://www.hitwebcounter.com/" target="_blank">
        <img src="https://www.hitwebcounter.com/counter/counter.php?page=21499592&style=0030&nbdigits=5&type=page"
        style="border:0;" />
    </a>
    """,
    unsafe_allow_html=True
)
