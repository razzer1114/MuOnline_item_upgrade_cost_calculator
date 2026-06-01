# app.py
# ============================================================
# MU Online 1st Wing Synthesis Expected Cost Calculator
# 奇迹MU 一代翅膀合成期望成本计算器
# ============================================================

import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st


# ============================================================
# 1. Helper Functions / 工具函数
# ============================================================

def gold_to_soul(gold: float, gold_per_soul: float) -> float:
    return gold / gold_per_soul


def bless_to_soul(bless_count: float, bless_value: float) -> float:
    return bless_count * bless_value


def material_value_input(
    label_cn: str,
    label_en: str,
    default_soul: float,
    gold_per_soul: float,
    bless_value: float,
    key: str
) -> float:
    """
    Universal material value input.
    通用材料价值输入：支持按灵魂、祝福、金币设置，最终统一换算为灵魂。
    """

    mode = st.sidebar.radio(
        f"{label_cn} / {label_en}",
        [
            "按灵魂输入 Soul",
            "按祝福输入 Bless",
            "按金币输入 Gold"
        ],
        key=f"{key}_mode",
        horizontal=True
    )

    if mode == "按灵魂输入 Soul":
        value = st.sidebar.number_input(
            f"{label_cn}价值（灵魂） / {label_en} Value (Soul)",
            min_value=0.0,
            max_value=999999999.0,
            value=float(default_soul),
            step=0.01,
            format="%.4f",
            key=f"{key}_soul"
        )
        return value

    elif mode == "按祝福输入 Bless":
        value = st.sidebar.number_input(
            f"{label_cn}价值（祝福） / {label_en} Value (Bless)",
            min_value=0.0,
            max_value=999999999.0,
            value=float(default_soul / bless_value if bless_value > 0 else 0),
            step=0.01,
            format="%.4f",
            key=f"{key}_bless"
        )
        return bless_to_soul(value, bless_value)

    else:
        value = st.sidebar.number_input(
            f"{label_cn}价值（金币） / {label_en} Value (Gold)",
            min_value=0.0,
            max_value=999999999999.0,
            value=float(default_soul * gold_per_soul),
            step=1000.0,
            format="%.0f",
            key=f"{key}_gold"
        )
        return gold_to_soul(value, gold_per_soul)


def expected_life_jewels_to_target(target_level: int, p: float = 0.5) -> float:
    if target_level <= 0:
        return 0.0

    if not 0 < p < 1:
        raise ValueError("生命宝石成功率必须在 0 和 1 之间")

    return (1 - p ** target_level) / ((1 - p) * (p ** target_level))


def option_name(level: int) -> str:
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
    return min(
        base_success_rate + stone_count * magic_stone_bonus,
        max_success_rate
    )


def calculate_wing_synthesis(
    bless_value: float,
    soul_value: float,
    life_value: float,
    chaos_value: float,
    maya_weapon_plus4_no_option_value: float,
    relic_synthesis_gold_value: float,
    wing_conversion_gold_value: float,
    life_success_rate: float,
    target_option_level: int,
    base_success_rate: float,
    max_success_rate: float,
    magic_stone_bonus: float,
    magic_stone_value: float,
    max_magic_stone_count: int
):

    expected_life_count = expected_life_jewels_to_target(
        target_option_level,
        life_success_rate
    )

    expected_option_cost = expected_life_count * life_value

    maya_weapon_plus4_with_option_cost = (
        maya_weapon_plus4_no_option_value
        + expected_option_cost
    )

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
        "expected_life_count": expected_life_count,
        "expected_option_cost": expected_option_cost,
        "maya_weapon_plus4_with_option_cost": maya_weapon_plus4_with_option_cost,
        "relic_cost": relic_cost,
        "best_row": best_row
    }

    return df, summary


def plot_expected_cost_curve(df: pd.DataFrame):
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

st.title("奇迹MU 一代翅膀合成期望成本计算器 尝鲜版")
st.title("MU Online 1st Wing Synthesis Expected Cost Calculator Beta")

st.caption(
    "基于一代翅膀圣物合成与圣物转化规则，计算不同低级魔晶石数量下的合成期望成本，并自动给出当前参数下的最优方案。"
)

st.caption(
    "All material values can be entered as Soul, Bless, or Gold and will be converted into Soul-equivalent cost."
)


# ============================================================
# 3. Purpose / 用途说明
# ============================================================

with st.expander("🎯 用途和说明 Purpose & Notes", expanded=False):
    st.markdown("""
    本工具针对**一代翅膀合成**过程进行期望成本计算。

    当前版本支持将所有材料价值按以下三种方式输入：

    1. 按灵魂数量输入；
    2. 按祝福数量输入；
    3. 按金币数量输入。

    系统会根据“金币/灵魂”和“祝福/灵魂”的换算比例，自动将所有材料折算为灵魂单位，并用于期望成本计算。
    """)


# ============================================================
# 4. Sidebar Parameters / 左侧栏参数
# ============================================================

st.sidebar.header("执行操作 Run")
run_button = st.sidebar.button("运行计算 Run Calculation")

st.sidebar.markdown("---")
st.sidebar.header("基础换算比例 Basic Exchange Rates")

gold_per_soul = st.sidebar.number_input(
    "金币换算 Gold per Soul",
    min_value=1.0,
    max_value=999999999999.0,
    value=10_000_000.0,
    step=100_000.0,
    format="%.0f"
)

bless_value = st.sidebar.number_input(
    "祝福价值 Bless Value：1祝福 = ? 灵魂",
    min_value=0.0001,
    max_value=10000.0,
    value=3.0,
    step=0.01,
    format="%.4f"
)

soul_value = 1.0

st.sidebar.info(
    f"当前换算：1 灵魂 = {gold_per_soul:,.0f} 金币；1 祝福 = {bless_value:.4f} 灵魂"
)

st.sidebar.markdown("---")
st.sidebar.header("材料价值设置 Material Value Settings")

life_value = material_value_input(
    "生命宝石",
    "Life Jewel",
    default_soul=1.0,
    gold_per_soul=gold_per_soul,
    bless_value=bless_value,
    key="life"
)

chaos_value = material_value_input(
    "玛雅宝石",
    "Chaos Jewel",
    default_soul=0.05,
    gold_per_soul=gold_per_soul,
    bless_value=bless_value,
    key="chaos"
)

maya_weapon_plus4_no_option_value = material_value_input(
    "+4不追加玛雅武器",
    "+4 Maya Weapon without Option",
    default_soul=0.5,
    gold_per_soul=gold_per_soul,
    bless_value=bless_value,
    key="maya_weapon"
)

relic_synthesis_gold_value = material_value_input(
    "圣物合成费用",
    "Relic Synthesis Fee",
    default_soul=0.001,
    gold_per_soul=gold_per_soul,
    bless_value=bless_value,
    key="relic_fee"
)

wing_conversion_gold_value = material_value_input(
    "圣物转化费用",
    "Relic-to-Wing Conversion Fee",
    default_soul=0.1,
    gold_per_soul=gold_per_soul,
    bless_value=bless_value,
    key="conversion_fee"
)

magic_stone_value = material_value_input(
    "低级魔晶石",
    "Low Magic Stone",
    default_soul=bless_value,
    gold_per_soul=gold_per_soul,
    bless_value=bless_value,
    key="magic_stone"
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
        bless_value=bless_value,
        soul_value=soul_value,
        life_value=life_value,
        chaos_value=chaos_value,
        maya_weapon_plus4_no_option_value=maya_weapon_plus4_no_option_value,
        relic_synthesis_gold_value=relic_synthesis_gold_value,
        wing_conversion_gold_value=wing_conversion_gold_value,
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
        "低级魔晶石价值",
        f"{magic_stone_value:.4f} 灵魂"
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

    st.subheader("材料价值换算结果 Material Value Conversion")

    value_df = pd.DataFrame([
        {"item / 项目": "灵魂宝石 Soul Jewel", "value_soul / 灵魂价值": soul_value},
        {"item / 项目": "祝福宝石 Bless Jewel", "value_soul / 灵魂价值": bless_value},
        {"item / 项目": "生命宝石 Life Jewel", "value_soul / 灵魂价值": life_value},
        {"item / 项目": "玛雅宝石 Chaos Jewel", "value_soul / 灵魂价值": chaos_value},
        {"item / 项目": "+4不追加玛雅武器 +4 Maya Weapon without Option", "value_soul / 灵魂价值": maya_weapon_plus4_no_option_value},
        {"item / 项目": "圣物合成费用 Relic Synthesis Fee", "value_soul / 灵魂价值": relic_synthesis_gold_value},
        {"item / 项目": "圣物转化费用 Relic-to-Wing Conversion Fee", "value_soul / 灵魂价值": wing_conversion_gold_value},
        {"item / 项目": "低级魔晶石 Low Magic Stone", "value_soul / 灵魂价值": magic_stone_value},
    ])

    st.dataframe(value_df, use_container_width=True)

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
            "cost_soul / 成本_灵魂": chaos_value
        },
        {
            "item / 项目": "+4不追加玛雅武器 +4 Maya Weapon without Option",
            "cost_soul / 成本_灵魂": maya_weapon_plus4_no_option_value
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
            "item / 项目": "圣物合成费用 Relic Synthesis Fee",
            "cost_soul / 成本_灵魂": relic_synthesis_gold_value
        },
        {
            "item / 项目": "一代翅膀圣物总成本 1st Wing Relic Cost",
            "cost_soul / 成本_灵魂": summary["relic_cost"]
        },
        {
            "item / 项目": "圣物转化费用 Relic-to-Wing Conversion Fee",
            "cost_soul / 成本_灵魂": wing_conversion_gold_value
        },
    ])

    st.dataframe(breakdown_df, use_container_width=True)

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

    st.dataframe(display_df, use_container_width=True)

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
    st.info("请在左侧设置参数，然后点击“运行计算”。")
    st.info("Set parameters on the left and click Run Calculation.")


# ============================================================
# 6. Guide / 使用说明
# ============================================================

with st.expander("📘 使用说明 Guide", expanded=False):
    st.markdown("""
    ### 1. 基础换算比例

    需要先设置两个基础比例：

    - `1 灵魂 = 多少金币`
    - `1 祝福 = 多少灵魂`

    所有材料都会通过这两个比例统一换算为灵魂单位。

    ### 2. 材料价值输入方式

    每一种材料都可以选择三种输入方式：

    - 按灵魂输入；
    - 按祝福输入；
    - 按金币输入。

    例如：

    - 如果你知道 1 颗玛雅约等于 50 万金币，就选择“按金币输入”；
    - 如果你知道 1 颗低级魔晶石约等于 1 祝福，就选择“按祝福输入”；
    - 如果你已经知道某材料约等于多少灵魂，就选择“按灵魂输入”。

    ### 3. 计算逻辑

    系统最终会将所有材料统一折算为灵魂价值，再进入一代翅膀合成期望成本模型。

    ### 4. 期望总成本

    模型采用：

    `期望总成本 = 单次尝试成本 / 成功率`

    增加低级魔晶石会提高成功率，但也会增加单次尝试成本，因此最优方案需要枚举比较。
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
    <a href="https://www.hitwebcounter.com/" target="_blank" rel="noopener">
        <img src="https://www.hitwebcounter.com/counter/counter.php?page=21501229&style=0032&nbdigits=5&type=page"
             alt="Visit Counter"
             decoding="async"
             style="border:0;max-width:100%;height:auto;">
    </a>
    """,
    unsafe_allow_html=True
)
