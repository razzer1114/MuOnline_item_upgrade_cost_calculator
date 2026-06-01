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
    return gold / gold_per_soul


def bless_to_soul(bless_count: float, bless_value: float) -> float:
    return bless_count * bless_value


def material_value_ratio_input(
    label_cn: str,
    label_en: str,
    default_item_count: float,
    default_soul_equivalent: float,
    gold_per_soul: float,
    bless_value: float,
    key: str
):
    """
    Universal material value input by ratio.
    通用材料价值比例输入。

    Supported modes:
    1. X material = Y Soul
    2. X material = Y Gold
    3. X material = Y Bless
    """

    st.sidebar.markdown(f"#### {label_cn} / {label_en}")

    mode = st.sidebar.radio(
        "设置方式 Input Mode",
        [
            "灵魂换算：X材料 = Y灵魂",
            "金币换算：X材料 = Y金币",
            "祝福换算：X材料 = Y祝福"
        ],
        key=f"{key}_mode"
    )

    item_count = st.sidebar.number_input(
        f"{label_cn}数量 X / {label_en} Count X",
        min_value=0.0001,
        max_value=999999999.0,
        value=float(default_item_count),
        step=1.0,
        format="%.4f",
        key=f"{key}_item_count"
    )

    if mode == "灵魂换算：X材料 = Y灵魂":
        soul_equivalent = st.sidebar.number_input(
            f"等于多少灵魂 Y / Equivalent Soul Y",
            min_value=0.0,
            max_value=999999999.0,
            value=float(default_soul_equivalent),
            step=0.01,
            format="%.4f",
            key=f"{key}_soul_equivalent"
        )

        value_soul = soul_equivalent / item_count
        original_text = f"{item_count:g} {label_cn} = {soul_equivalent:g} 灵魂"

    elif mode == "金币换算：X材料 = Y金币":
        default_gold_equivalent = default_soul_equivalent * gold_per_soul

        gold_equivalent = st.sidebar.number_input(
            f"等于多少金币 Y / Equivalent Gold Y",
            min_value=0.0,
            max_value=999999999999.0,
            value=float(default_gold_equivalent),
            step=1000.0,
            format="%.0f",
            key=f"{key}_gold_equivalent"
        )

        value_soul = gold_to_soul(gold_equivalent, gold_per_soul) / item_count
        original_text = f"{item_count:g} {label_cn} = {gold_equivalent:,.0f} 金币"

    else:
        default_bless_equivalent = (
            default_soul_equivalent / bless_value
            if bless_value > 0
            else 0.0
        )

        bless_equivalent = st.sidebar.number_input(
            f"等于多少祝福 Y / Equivalent Bless Y",
            min_value=0.0,
            max_value=999999999.0,
            value=float(default_bless_equivalent),
            step=0.01,
            format="%.4f",
            key=f"{key}_bless_equivalent"
        )

        value_soul = bless_to_soul(bless_equivalent, bless_value) / item_count
        original_text = f"{item_count:g} {label_cn} = {bless_equivalent:g} 祝福"

    st.sidebar.info(
        f"""
    1 {label_cn}
    ≈ {value_soul:.6f} 灵魂
    """
    )

    return value_soul, original_text


def expected_life_jewels_to_target(target_level: int, p: float = 0.5) -> float:
    """
    Expected trials for consecutive successes.
    生命宝石追加：成功+1，失败归零。
    """
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

    best_row = df.loc[
        df["expected_total_cost_soul / 期望总成本_灵魂"].idxmin()
    ]

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
    page_title="MU Online Level 1 Wing Synthesis Calculator",
    layout="wide"
)

st.title("奇迹MU 一代翅膀合成期望成本计算器")
st.title("MU Online Level one Wing Synthesis Expected Cost Calculator")


st.caption(
    "基于一代翅膀圣物合成与圣物转化规则，计算不同低级魔晶石数量下的合成期望成本，并自动给出当前参数下的最优方案。"
)

st.caption(
    "Material values are set by exchange ratios and converted into Soul-equivalent cost."
)


# ============================================================
# 3. Purpose / 用途说明
# ============================================================

with st.expander("🎯 用途和说明 Purpose & Notes", expanded=False):

    purpose_tab_cn, purpose_tab_en = st.tabs([
        "中文版",
        "English Version"
    ])

    with purpose_tab_cn:
        st.markdown("""
        ## 工具用途

        本工具针对**奇迹MU一代翅膀合成**过程进行期望成本计算。

        在游戏中，翅膀合成涉及多种材料、成功率以及不同服务器经济环境下的市场价格差异。单纯依靠经验判断往往难以准确评估真实成本。

        本工具通过统一价值换算体系，将所有材料最终折算为灵魂宝石价值，并自动计算不同魔晶石使用策略下的期望成本，从而帮助玩家寻找更优甚至最优方案。

        ---

        ## 当前版本支持

        - 金币可按：
          - 金币 = 灵魂
          - 金币 = 祝福
          两种方式设置；

        - 祝福可按：
          - 祝福 = 灵魂
          - 祝福 = 金币
          两种方式设置；

        - 以下材料支持三种价值输入方式：
          - X材料 = Y灵魂
          - X材料 = Y金币
          - X材料 = Y祝福

          包括：

          - 生命宝石
          - 玛雅宝石
          - +4不追加玛雅武器
          - 低级魔晶石

        - 圣物合成费用与圣物转化费用采用固定金币输入；

        - 所有成本最终统一折算为灵魂价值进行计算。

        ---

        ## 注意事项

        金币和祝福不能同时仅通过彼此进行换算，否则无法唯一确定灵魂价值基准。

        因此：

        - 金币或祝福至少有一个需要直接与灵魂建立换算关系；
        - 系统会自动根据输入关系计算完整的价值换算体系。

        ---

        ## 适用场景

        本工具特别适用于：

        - 经常合成翅膀的玩家；
        - 希望评估翅膀真实价值的玩家；
        - 对不同服务器经济环境进行比较分析的玩家；
        - 关注材料配置效率与长期成本的商人型玩家。
        """)

    with purpose_tab_en:
        st.markdown("""
        ## Purpose

        This calculator evaluates the expected synthesis cost of **Level 1 Wings in MU Online**.

        Wing synthesis involves multiple materials, success rates, and market-dependent values. Relying solely on experience often makes it difficult to estimate the true expected cost.

        This tool converts all materials into Soul-equivalent value and automatically evaluates different Magic Stone strategies to identify more efficient or even optimal solutions.

        ---

        ## Current Features

        - Gold can be valued through:
          - Gold ↔ Soul
          - Gold ↔ Bless

        - Bless can be valued through:
          - Bless ↔ Soul
          - Bless ↔ Gold

        - The following materials support three valuation methods:

          - X Material = Y Soul
          - X Material = Y Gold
          - X Material = Y Bless

          Including:

          - Life Jewel
          - Chaos Jewel
          - +4 Maya Weapon without Option
          - Low Magic Stone

        - Relic synthesis fee and relic-to-wing conversion fee are fixed Gold costs;

        - All values are ultimately converted into Soul-equivalent cost for calculation.

        ---

        ## Important Notes

        Gold and Bless cannot both be defined solely through each other.

        Therefore:

        - At least one of them must be directly linked to Soul value;
        - The calculator will automatically derive the complete exchange system based on user inputs.

        ---

        ## Recommended Use Cases

        This calculator is particularly useful for:

        - Players who frequently synthesize wings;
        - Players evaluating the real value of wings;
        - Comparing different server economies;
        - Traders interested in long-term cost optimization and resource allocation.
        """)


# ============================================================
# 4. Sidebar Parameters / 左侧栏参数
# ============================================================

st.sidebar.header("执行操作 Run")
run_button = st.sidebar.button("运行计算 Run Calculation")


# ============================================================
# 4.1 Basic Exchange Rates / 基础换算比例
# ============================================================

st.sidebar.markdown("---")
st.sidebar.header("基础换算比例 Basic Exchange Rates")

# ---------- Gold Conversion / 金币换算 ----------

st.sidebar.markdown("#### 金币 / Gold")

gold_mode = st.sidebar.radio(
    "金币价值设置方式 Gold Value Setting", 
    [
        "金币与灵魂换算：X金币 = Y灵魂",
        "金币与祝福换算：X金币 = Y祝福"
    ],
    key="gold_mode"
)

gold_x = st.sidebar.number_input(
    "金币数量 X / Gold Count X",
    min_value=0.0001,
    max_value=999999999999.0,
    value=10_000_000.0,
    step=100_000.0,
    format="%.0f",
    key="gold_x"
)

if gold_mode == "金币与灵魂换算：X金币 = Y灵魂":
    gold_y_soul = st.sidebar.number_input(
        "等于多少灵魂 Y / Equivalent Soul Y",
        min_value=0.0001,
        max_value=999999999.0,
        value=1.0,
        step=1.0,
        format="%.4f",
        key="gold_y_soul"
    )
    gold_y_bless = None
    gold_original_text = f"{gold_x:,.0f} 金币 = {gold_y_soul:g} 灵魂"
else:
    gold_y_bless = st.sidebar.number_input(
        "等于多少祝福 Y / Equivalent Bless Y",
        min_value=0.0001,
        max_value=999999999.0,
        value=1.0 / 3.0,
        step=0.01,
        format="%.4f",
        key="gold_y_bless"
    )
    gold_y_soul = None
    gold_original_text = f"{gold_x:,.0f} 金币 = {gold_y_bless:g} 祝福"


# ---------- Bless Conversion / 祝福换算 ----------

st.sidebar.markdown("#### 祝福 / Bless")

bless_mode = st.sidebar.radio(
    "祝福价值设置方式 Bless Value Setting",
    [
        "祝福与灵魂换算：X祝福 = Y灵魂",
        "祝福与金币换算：X祝福 = Y金币"
    ],
    key="bless_mode"
)

bless_x = st.sidebar.number_input(
    "祝福数量 X / Bless Count X",
    min_value=0.0001,
    max_value=999999999.0,
    value=1.0,
    step=1.0,
    format="%.4f",
    key="bless_x"
)

if bless_mode == "祝福与灵魂换算：X祝福 = Y灵魂":
    bless_y_soul = st.sidebar.number_input(
        "等于多少灵魂 Y / Equivalent Soul Y",
        min_value=0.0001,
        max_value=999999999.0,
        value=3.0,
        step=0.01,
        format="%.4f",
        key="bless_y_soul"
    )
    bless_y_gold = None
    bless_original_text = f"{bless_x:g} 祝福 = {bless_y_soul:g} 灵魂"
else:
    bless_y_gold = st.sidebar.number_input(
        "等于多少金币 Y / Equivalent Gold Y",
        min_value=0.0001,
        max_value=999999999999.0,
        value=30_000_000.0,
        step=100_000.0,
        format="%.0f",
        key="bless_y_gold"
    )
    bless_y_soul = None
    bless_original_text = f"{bless_x:g} 祝福 = {bless_y_gold:,.0f} 金币"


# ---------- Solve Exchange System / 求解基础换算 ----------

gold_direct_to_soul = gold_mode == "金币与灵魂换算：X金币 = Y灵魂"
bless_direct_to_soul = bless_mode == "祝福与灵魂换算：X祝福 = Y灵魂"

if not gold_direct_to_soul and not bless_direct_to_soul:
    st.sidebar.error(
        "当前设置无法唯一确定灵魂基准：金币按祝福换算，祝福又按金币换算。"
        "请至少让金币或祝福中的一个直接与灵魂换算。"
    )
    st.error(
        "基础换算比例设置错误：金币和祝福不能同时只通过彼此换算。"
        "请在左侧将金币或祝福至少一个设置为与灵魂换算。"
    )
    st.stop()

# Case 1: Bless directly defines Soul value.
# 情况1：祝福直接与灵魂换算，先求祝福价值。
if bless_direct_to_soul:
    bless_value = bless_y_soul / bless_x

    if gold_direct_to_soul:
        gold_per_soul = gold_x / gold_y_soul
    else:
        gold_per_soul = gold_x / (gold_y_bless * bless_value)

# Case 2: Gold directly defines Soul value, Bless depends on Gold.
# 情况2：金币直接与灵魂换算，祝福可由金币推导。
else:
    gold_per_soul = gold_x / gold_y_soul

    if bless_direct_to_soul:
        bless_value = bless_y_soul / bless_x
    else:
        bless_value = gold_to_soul(bless_y_gold, gold_per_soul) / bless_x

# If Gold is direct and Bless is Gold-based, calculate Bless value here.
# 如果金币直接与灵魂换算，祝福按金币换算，则由金币推导祝福价值。
if gold_direct_to_soul and not bless_direct_to_soul:
    bless_value = gold_to_soul(bless_y_gold, gold_per_soul) / bless_x

# If Bless is direct and Gold is Bless-based, calculate Gold-per-Soul here.
# 如果祝福直接与灵魂换算，金币按祝福换算，则由祝福推导金币价值。
if bless_direct_to_soul and not gold_direct_to_soul:
    gold_per_soul = gold_x / (gold_y_bless * bless_value)

soul_value = 1.0

st.sidebar.info(
    f"""

1 灵魂
≈ {gold_per_soul:,.0f} 金币

1 祝福
≈ {bless_value:.4f} 灵魂
≈ {bless_value * gold_per_soul:,.0f} 金币
"""
)


# ============================================================
# 4.2 Material Values / 材料价值
# ============================================================

st.sidebar.markdown("---")
st.sidebar.header("材料价值设置 Material Value Settings")

life_value, life_original_text = material_value_ratio_input(
    "生命宝石",
    "Life Jewel",
    default_item_count=1.0,
    default_soul_equivalent=1.0,
    gold_per_soul=gold_per_soul,
    bless_value=bless_value,
    key="life"
)

chaos_value, chaos_original_text = material_value_ratio_input(
    "玛雅宝石",
    "Chaos Jewel",
    default_item_count=1.0,
    default_soul_equivalent=0.05,
    gold_per_soul=gold_per_soul,
    bless_value=bless_value,
    key="chaos"
)

maya_weapon_plus4_no_option_value, maya_weapon_original_text = material_value_ratio_input(
    "+4不追加玛雅武器",
    "+4 Maya Weapon without Option",
    default_item_count=1.0,
    default_soul_equivalent=0.5,
    gold_per_soul=gold_per_soul,
    bless_value=bless_value,
    key="maya_weapon"
)

magic_stone_value, magic_stone_original_text = material_value_ratio_input(
    "低级魔晶石",
    "Low Magic Stone",
    default_item_count=1.0,
    default_soul_equivalent=bless_value,
    gold_per_soul=gold_per_soul,
    bless_value=bless_value,
    key="magic_stone"
)



# ============================================================
# 4.3 Synthesis System Gold Fees / 合成系统金币费用
# ============================================================

st.sidebar.markdown("---")
st.sidebar.header("合成系统金币费用 Synthesis System Gold Fees")

relic_synthesis_gold = st.sidebar.number_input(
    "圣物合成费用（金币） Relic Synthesis Fee (Gold)",
    min_value=0.0,
    max_value=999999999999.0,
    value=10_000.0,
    step=1_000.0,
    format="%.0f",
    key="relic_synthesis_gold"
)

wing_conversion_gold = st.sidebar.number_input(
    "圣物转化费用（金币） Relic-to-Wing Conversion Fee (Gold)",
    min_value=0.0,
    max_value=999999999999.0,
    value=1_000_000.0,
    step=10_000.0,
    format="%.0f",
    key="wing_conversion_gold"
)

relic_synthesis_gold_value = gold_to_soul(
    relic_synthesis_gold,
    gold_per_soul
)

wing_conversion_gold_value = gold_to_soul(
    wing_conversion_gold,
    gold_per_soul
)

st.sidebar.info(
    f"""
圣物合成费用：
{relic_synthesis_gold:,.0f} 金币
≈ {relic_synthesis_gold_value:.6f} 灵魂

圣物转化费用：
{wing_conversion_gold:,.0f} 金币
≈ {wing_conversion_gold_value:.6f} 灵魂
"""
)


# ============================================================
# 4.4 Life Option / 生命宝石追加
# ============================================================

st.sidebar.markdown("---")
st.sidebar.header("生命宝石追加 Life Jewel Option")

target_option_level = st.sidebar.selectbox(
    "目标追加 Target Option",
    options=[0, 1, 2, 3, 4],
    format_func=lambda x: option_name(x),
    index=1,
    key="target_option_level"
)

life_success_rate = st.sidebar.number_input(
    "生命宝石成功率 Life Success Rate",
    min_value=0.01,
    max_value=0.99,
    value=0.50,
    step=0.01,
    format="%.2f",
    key="life_success_rate"
)


# ============================================================
# 4.5 Wing Conversion / 翅膀转化
# ============================================================

st.sidebar.markdown("---")
st.sidebar.header("一代翅膀转化 Level 1 Wing Conversion")

base_success_rate_pct = st.sidebar.number_input(
    "基础成功率 Base Success Rate (%)",
    min_value=0.00,
    max_value=100.00,
    value=20.00,
    step=0.01,
    format="%.2f",
    key="base_success_rate_pct"
)

base_success_rate = base_success_rate_pct / 100

max_success_rate_pct = st.sidebar.number_input(
    "成功率上限 Max Success Rate (%)",
    min_value=0.00,
    max_value=100.00,
    value=100.00,
    step=0.01,
    format="%.2f",
    key="max_success_rate_pct"
)

max_success_rate = max_success_rate_pct / 100

magic_stone_bonus_pct = st.sidebar.number_input(
    "每颗低级魔晶石成功率加成 Magic Stone Bonus (%)",
    min_value=0.00,
    max_value=100.00,
    value=5.00,
    step=0.01,
    format="%.2f",
    key="magic_stone_bonus_pct"
)

magic_stone_bonus = magic_stone_bonus_pct / 100

import math

if magic_stone_bonus > 0:

    max_magic_stone_count = math.ceil(
        (max_success_rate - base_success_rate)
        / magic_stone_bonus
    )

    max_magic_stone_count = max(
        0,
        max_magic_stone_count
    )

else:
    max_magic_stone_count = 0

st.sidebar.info(
    f"""

基础成功率：{base_success_rate_pct:.2f}%

每颗魔晶石加成：{magic_stone_bonus_pct:.2f}%

成功率上限：{max_success_rate_pct:.2f}%

最大需要枚举：
{max_magic_stone_count} 颗低级魔晶石
"""
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
        {
            "item / 项目": "金币 Gold",
            "original_value / 原始值": gold_original_text,
            "value_soul / 折算灵魂": f"1 金币 = {1 / gold_per_soul:.10f} 灵魂"
        },
        {
            "item / 项目": "灵魂宝石 Soul Jewel",
            "original_value / 原始值": "1 灵魂 = 1 灵魂",
            "value_soul / 折算灵魂": soul_value
        },
        {
            "item / 项目": "祝福宝石 Bless Jewel",
            "original_value / 原始值": bless_original_text,
            "value_soul / 折算灵魂": bless_value
        },
        {
            "item / 项目": "生命宝石 Life Jewel",
            "original_value / 原始值": life_original_text,
            "value_soul / 折算灵魂": life_value
        },
        {
            "item / 项目": "玛雅宝石 Chaos Jewel",
            "original_value / 原始值": chaos_original_text,
            "value_soul / 折算灵魂": chaos_value
        },
        {
            "item / 项目": "+4不追加玛雅武器 +4 Maya Weapon without Option",
            "original_value / 原始值": maya_weapon_original_text,
            "value_soul / 折算灵魂": maya_weapon_plus4_no_option_value
        },
        {
            "item / 项目": "低级魔晶石 Low Magic Stone",
            "original_value / 原始值": magic_stone_original_text,
            "value_soul / 折算灵魂": magic_stone_value
        },
        {
            "item / 项目": "圣物合成费用 Relic Synthesis Fee",
            "original_value / 原始值": f"{relic_synthesis_gold:,.0f} 金币",
            "value_soul / 折算灵魂": relic_synthesis_gold_value
        },
        {
            "item / 项目": "圣物转化费用 Relic-to-Wing Conversion Fee",
            "original_value / 原始值": f"{wing_conversion_gold:,.0f} 金币",
            "value_soul / 折算灵魂": wing_conversion_gold_value
        },
    ])

    st.dataframe(value_df, use_container_width=True)

    st.download_button(
        label="下载材料价值换算 CSV Download Material Value CSV",
        data=value_df.to_csv(index=False, encoding="utf-8-sig"),
        file_name="wing_synthesis_material_value_conversion.csv",
        mime="text/csv"
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
            "item / 项目": "一代翅膀圣物总成本 Lvl 1 Wing Relic Cost",
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

with st.expander("📘 使用说明 User Guide", expanded=False):

    guide_tab_cn, guide_tab_en = st.tabs([
        "中文版",
        "English Version"
    ])

    with guide_tab_cn:
        st.markdown("""
        # 使用说明

        ## 1. 工具用途

        本工具用于计算《奇迹MU》中一代翅膀从材料准备到最终转化成功的期望成本，并自动寻找当前参数条件下的最优魔晶石使用方案。

        所有成本最终统一折算为“灵魂宝石价值”进行计算，以便比较不同材料、不同服务器经济环境下的真实成本。

        ---

        ## 2. 基础换算比例

        本工具采用“灵魂”作为统一价值单位。

        您需要首先设置市场基准价格：

        - 金币与灵魂之间的换算关系；
        - 祝福与灵魂之间的换算关系；
        - 或通过祝福与金币的关系间接建立换算。

        例如：

        - 10,000,000金币 = 1灵魂
        - 1祝福 = 3灵魂

        系统将自动计算：

        - 1灵魂 ≈ 10,000,000金币
        - 1祝福 ≈ 30,000,000金币

        ---

        ## 3. 材料价值设置

        以下材料均支持三种设置方式：

        - 灵魂换算：X材料 = Y灵魂
        - 金币换算：X材料 = Y金币
        - 祝福换算：X材料 = Y祝福

        支持的材料包括：

        - 生命宝石
        - 玛雅宝石
        - +4不追加玛雅武器
        - 低级魔晶石

        例如：

        - 1生命 = 1灵魂
        - 1玛雅 = 500,000金币
        - 1低级魔晶石 = 1祝福

        系统会自动换算为：

        - 1生命 = ?灵魂
        - 1玛雅 = ?灵魂
        - 1魔晶石 = ?灵魂

        ---

        ## 4. 圣物合成与转化费用

        圣物相关费用属于系统固定金币消耗：

        - 圣物合成费用
        - 圣物转化费用

        输入金币后，系统会自动折算为灵魂价值。

        ---

        ## 5. 生命宝石追加

        用于计算：

        - 追4
        - 追8
        - 追12
        - 追16

        所需的生命宝石期望消耗量。

        模型假设：

        - 成功则追加等级 +1；
        - 失败则归零重新开始。

        系统采用连续成功期望模型自动计算平均消耗。

        ---

        ## 6. 翅膀转化

        设置：

        - 基础成功率
        - 成功率上限
        - 每颗低级魔晶石成功率加成

        例如：

        - 基础成功率：20%
        - 每颗魔晶石：+5%
        - 成功率上限：100%

        系统将自动计算：

        - 最大需要使用的魔晶石数量；
        - 枚举所有可能方案；
        - 自动寻找最低期望成本方案。

        ---

        ## 7. 结果解读

        程序会输出：

        - 推荐魔晶石数量
        - 最终成功率
        - 单次尝试成本
        - 合成期望总成本

        同时提供：

        - 材料价值换算表
        - 成本拆解表
        - 全部枚举结果
        - 期望成本曲线

        用于分析不同策略之间的差异。

        ---

        ## 8. 免责声明

        本工具基于用户输入参数进行计算。

        实际游戏中的：

        - 合成成功率
        - 市场价格
        - 宝石价值
        - 金币价值

        可能随服务器、时间及市场环境发生变化。

        因此本工具仅提供理论计算结果与决策参考，不保证与实际游戏环境完全一致。
        """)

    with guide_tab_en:
        st.markdown("""
        # User Guide

        ## 1. Purpose

        This calculator estimates the expected cost of synthesizing a Level 1 Wing in MU Online and automatically identifies the optimal Magic Stone strategy under the current assumptions.

        All costs are converted into Soul-equivalent value for comparison across different market environments.

        ---

        ## 2. Base Exchange Rates

        Soul is used as the universal value unit.

        You must first define:

        - Gold ↔ Soul relationship;
        - Bless ↔ Soul relationship;
        - or Bless ↔ Gold relationship.

        Example:

        - 10,000,000 Gold = 1 Soul
        - 1 Bless = 3 Soul

        The calculator will automatically derive:

        - 1 Soul ≈ 10,000,000 Gold
        - 1 Bless ≈ 30,000,000 Gold

        ---

        ## 3. Material Value Settings

        Each material supports three valuation methods:

        - X Material = Y Soul
        - X Material = Y Gold
        - X Material = Y Bless

        Supported materials:

        - Life Jewel
        - Chaos Jewel
        - +4 Maya Weapon without Option
        - Low Magic Stone

        Examples:

        - 1 Life Jewel = 1 Soul
        - 1 Chaos Jewel = 500,000 Gold
        - 1 Low Magic Stone = 1 Bless

        The calculator automatically converts all values into Soul-equivalent cost.

        ---

        ## 4. Relic Costs

        The following are fixed system Gold costs:

        - Relic Synthesis Fee
        - Relic-to-Wing Conversion Fee

        Gold costs are automatically converted into Soul-equivalent value.

        ---

        ## 5. Life Jewel Option Enhancement

        The calculator estimates the expected Life Jewel consumption required for:

        - +4 Option
        - +8 Option
        - +12 Option
        - +16 Option

        Model assumptions:

        - Success increases option level by one step;
        - Failure resets progress to zero.

        Expected consumption is calculated using a consecutive-success expectation model.

        ---

        ## 6. Wing Conversion

        Configure:

        - Base Success Rate
        - Maximum Success Rate
        - Success Rate Bonus per Magic Stone

        Example:

        - Base Success Rate: 20%
        - Magic Stone Bonus: +5%
        - Maximum Success Rate: 100%

        The calculator automatically:

        - Determines the maximum required Magic Stone count;
        - Enumerates all feasible strategies;
        - Finds the minimum expected-cost solution.

        ---

        ## 7. Results

        The program provides:

        - Recommended Magic Stone count;
        - Final Success Rate;
        - Cost per Attempt;
        - Expected Total Cost.

        Additional outputs include:

        - Material Value Conversion Table;
        - Cost Breakdown Table;
        - Full Enumeration Results;
        - Expected Cost Curve.

        ---

        ## 8. Disclaimer

        All results are calculated using user-defined assumptions.

        Actual in-game:

        - Success rates;
        - Market prices;
        - Jewel values;
        - Gold values;

        may vary across servers and over time.

        Therefore, this tool should be regarded as a decision-support calculator rather than a guarantee of actual game outcomes.
        """)
   
# ============================================================
# 7. author / 作者
# ============================================================

st.markdown("---")
#st.markdown("#### Developed by 作者：Razz")
#st.markdown("GitHub: https://github.com/razzer1114/MuOnline_item_upgrade_cost_calculator")
#st.markdown("💬 如果有问题、意见或建议，请移步贴吧讨论：")
#st.markdown("https://tieba.baidu.com/p/10761263145")

# ============================================================
# 8. Disclaimer / 免责声明
# ============================================================

st.markdown("---")
st.markdown("### 免责声明 Disclaimer")

st.info(
    """
本项目基于用户输入的成功率、金币换算比例与宝石相对价值进行计算，
输出结果仅在所设定参数条件下成立。

游戏内实际合成概率、市场价格、宝石价值和金币价值可能因区服、
时间和交易环境而发生变化，因此计算结果不代表任何固定或真实环境下的唯一最优解。

本工具提供的是一种期望成本计算方法与决策参考，
而非对游戏实际机制、官方概率或市场价格的判定或保证。

--------------------------------------------------

This project calculates expected synthesis cost based on
user-defined success rates, exchange ratios and market values.

Results are only valid under the specified assumptions.

Actual in-game probabilities, market prices and exchange rates
may vary across servers and over time.

The calculator provides a decision-support framework and
expected-cost model only.

It does not guarantee actual game mechanics,
official probabilities or real market values.
    """
)





# ============================================================
# 9. Visit Counter / 访问统计
# ============================================================

st.sidebar.markdown("---")
st.sidebar.markdown("### 📊 Visits / 访问量")

st.sidebar.markdown(
    """
    <a href="https://www.hitwebcounter.com/" target="_blank" rel="noopener">
        <img src="https://www.hitwebcounter.com/counter/counter.php?page=21501228&style=0032&nbdigits=5&type=page"
        alt="Visit Counter"
        decoding="async"
        style="border:0;max-width:100%;height:auto;" />
    </a>
    """,
    unsafe_allow_html=True
)
