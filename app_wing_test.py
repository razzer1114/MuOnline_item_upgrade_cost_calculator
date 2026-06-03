# app.py
# ============================================================
# MU Online Level 1 & Level 2 Wing Synthesis Expected Cost Calculator
# 奇迹MU 一代/二代翅膀合成期望成本计算器
# ============================================================

import math
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

# ============================================================
# note: 玛雅武器 is translated as Chaos Weapon.
# note: All costs are internally converted into Soul-equivalent value.
# 说明：所有成本最终统一折算为灵魂价值。
# ============================================================

# ============================================================
# 1. Helper Functions / 工具函数
# ============================================================

def gold_to_soul(gold: float, gold_per_soul: float) -> float:
    return gold / gold_per_soul if gold_per_soul > 0 else 0.0


def bless_to_soul(bless_count: float, bless_value: float) -> float:
    return bless_count * bless_value


def format_percentage(x: float) -> str:
    return f"{x:.2%}"


def option_name(level: int) -> str:
    mapping = {
        0: "无追加 / No Option",
        1: "追4 / +4 Option",
        2: "追8 / +8 Option",
        3: "追12 / +12 Option",
        4: "追16 / +16 Option",
    }
    return mapping.get(level, f"追{level * 4} / +{level * 4} Option")


def expected_life_jewels_to_target(target_level: int, p: float = 0.5) -> float:
    """
    Expected trials to get target_level consecutive successes.
    生命宝石追加：成功+1档，失败归零；目标为连续成功 target_level 次。
    """
    if target_level <= 0:
        return 0.0
    if not 0 < p < 1:
        raise ValueError("生命宝石成功率必须在 0 和 1 之间")
    return (1 - p ** target_level) / ((1 - p) * (p ** target_level))


def material_value_ratio_input(
    label_cn: str,
    label_en: str,
    default_item_count: float,
    default_soul_equivalent: float,
    gold_per_soul: float,
    bless_value: float,
    key: str,
    show_title: bool = True,
    parent=st.sidebar,
):
    """
    Universal material value input by ratio.
    通用材料价值比例输入。

    Supported modes:
    1. X material = Y Soul
    2. X material = Y Gold
    3. X material = Y Bless
    """
    if show_title:
        parent.markdown(f"#### {label_cn} / {label_en}")

    mode = parent.radio(
        "设置方式 Input Mode",
        [
            "灵魂换算：X材料 = Y灵魂",
            "金币换算：X材料 = Y金币",
            "祝福换算：X材料 = Y祝福",
        ],
        key=f"{key}_mode",
    )

    item_count = parent.number_input(
        f"{label_cn}数量 X / {label_en} Count X",
        min_value=0.0001,
        max_value=999999999.0,
        value=float(default_item_count),
        step=1.0,
        format="%.4f",
        key=f"{key}_item_count",
    )

    if mode == "灵魂换算：X材料 = Y灵魂":
        soul_equivalent = parent.number_input(
            f"等于多少灵魂 Y / Equivalent Soul Y",
            min_value=0.0,
            max_value=999999999.0,
            value=float(default_soul_equivalent),
            step=0.01,
            format="%.4f",
            key=f"{key}_soul_equivalent",
        )
        value_soul = soul_equivalent / item_count
        original_text = f"{item_count:g} {label_cn} = {soul_equivalent:g} 灵魂"

    elif mode == "金币换算：X材料 = Y金币":
        default_gold_equivalent = default_soul_equivalent * gold_per_soul
        gold_equivalent = parent.number_input(
            f"等于多少金币 Y / Equivalent Gold Y",
            min_value=0.0,
            max_value=999999999999.0,
            value=float(default_gold_equivalent),
            step=1000.0,
            format="%.0f",
            key=f"{key}_gold_equivalent",
        )
        value_soul = gold_to_soul(gold_equivalent, gold_per_soul) / item_count
        original_text = f"{item_count:g} {label_cn} = {gold_equivalent:,.0f} 金币"

    else:
        default_bless_equivalent = default_soul_equivalent / bless_value if bless_value > 0 else 0.0
        bless_equivalent = parent.number_input(
            f"等于多少祝福 Y / Equivalent Bless Y",
            min_value=0.0,
            max_value=999999999.0,
            value=float(default_bless_equivalent),
            step=0.01,
            format="%.4f",
            key=f"{key}_bless_equivalent",
        )
        value_soul = bless_to_soul(bless_equivalent, bless_value) / item_count
        original_text = f"{item_count:g} {label_cn} = {bless_equivalent:g} 祝福"

    parent.info(
        f"""
1 {label_cn}
≈ {value_soul:.6f} 灵魂

1 {label_en}
≈ {value_soul:.6f} Soul
"""
    )
    return value_soul, original_text


def soul_cost_input(label_cn: str, label_en: str, default_soul: float, gold_per_soul: float, bless_value: float, key: str, parent=st.sidebar):
    """
    Direct value input with three in-game valuation modes.
    直接价值输入：灵魂、祝福、金币三种方式。
    """
    return material_value_ratio_input(
        label_cn=label_cn,
        label_en=label_en,
        default_item_count=1.0,
        default_soul_equivalent=default_soul,
        gold_per_soul=gold_per_soul,
        bless_value=bless_value,
        key=key,
        show_title=False,
        parent=parent,
    )


def wing_success_rate(stone_count: int, base_success_rate: float, magic_stone_bonus: float, max_success_rate: float) -> float:
    return min(base_success_rate + stone_count * magic_stone_bonus, max_success_rate)


def calculate_level1_wing_synthesis(
    bless_value: float,
    soul_value: float,
    chaos_value: float,
    chaos_weapon_plus4_with_option_cost: float,
    relic_synthesis_gold_value: float,
    wing_conversion_gold_value: float,
    base_success_rate: float,
    max_success_rate: float,
    magic_stone_bonus: float,
    magic_stone_value: float,
    max_magic_stone_count: int,
):
    relic_cost = (
        chaos_weapon_plus4_with_option_cost
        + bless_value
        + soul_value
        + chaos_value
        + relic_synthesis_gold_value
    )

    records = []
    for n in range(max_magic_stone_count + 1):
        p = wing_success_rate(n, base_success_rate, magic_stone_bonus, max_success_rate)
        if p <= 0:
            expected_total_cost = float("inf")
        else:
            single_attempt_cost = relic_cost + wing_conversion_gold_value + n * magic_stone_value
            expected_total_cost = single_attempt_cost / p
        records.append({
            "low_magic_stone_count / 低级魔晶石数量": n,
            "success_rate / 转化成功率": p,
            "single_attempt_cost_soul / 单次尝试成本_灵魂": single_attempt_cost,
            "expected_total_cost_soul / 期望总成本_灵魂": expected_total_cost,
        })

    df = pd.DataFrame(records)
    best_row = df.loc[df["expected_total_cost_soul / 期望总成本_灵魂"].idxmin()]
    return df, {"relic_cost": relic_cost, "best_row": best_row}


def calculate_low_magic_stone_auto_value(
    shop_plus9_option12_value: float,
    life_value: float,
    life_success_rate: float,
    synthesis_gold_value: float,
    output_count: int = 3,
):
    """
    Low Magic Stone automatic calculation.
    低级魔晶石自动计算：+9追16普通装备，50,000金币，100%成功，产出3颗。
    """
    if output_count <= 0:
        raise ValueError("产出数量必须大于0")
    if not 0 < life_success_rate < 1:
        raise ValueError("生命成功率必须在0和1之间")

    p = life_success_rate
    expected_life_count_from_0_to_16 = expected_life_jewels_to_target(4, p)
    cost_from_0_to_16 = expected_life_count_from_0_to_16 * life_value

    # From +12 to +16 means one more option success, but failure resets to +0.
    # 从追12冲追16，需要1次成功；失败则归零。
    cost_12_to_16_continue = life_value + (1 - p) * cost_from_0_to_16
    cost_12_to_16_rebuy = (life_value + (1 - p) * shop_plus9_option12_value) / p
    cost_12_to_16 = min(cost_12_to_16_continue, cost_12_to_16_rebuy)
    failure_strategy = (
        "失败后继续追加 / Continue after Failure"
        if cost_12_to_16_continue <= cost_12_to_16_rebuy
        else "失败后重新购买商店装 / Rebuy Shop Equipment after Failure"
    )

    total_synthesis_cost = shop_plus9_option12_value + cost_12_to_16 + synthesis_gold_value
    low_magic_stone_value = total_synthesis_cost / output_count

    breakdown = {
        "shop_plus9_option12_value": shop_plus9_option12_value,
        "expected_life_count_from_0_to_16": expected_life_count_from_0_to_16,
        "cost_from_0_to_16": cost_from_0_to_16,
        "cost_12_to_16_continue": cost_12_to_16_continue,
        "cost_12_to_16_rebuy": cost_12_to_16_rebuy,
        "cost_12_to_16": cost_12_to_16,
        "failure_strategy": failure_strategy,
        "synthesis_gold_value": synthesis_gold_value,
        "total_synthesis_cost": total_synthesis_cost,
        "output_count": output_count,
        "low_magic_stone_value": low_magic_stone_value,
    }
    return low_magic_stone_value, breakdown


def enhancement_cost_to_plus9_input(label_cn: str, label_en: str, gold_per_soul: float, bless_value: float, key: str, parent=st.sidebar):
    """
    Placeholder-compatible enhancement module for +0 to +9.
    强化至+9成本模块：当前支持直接输入或分段输入；后续可替换为强化App的马尔科夫/枚举核心函数。
    """
    mode = parent.radio(
        f"{label_cn}强化至+9成本设置 / {label_en} Upgrade-to-+9 Cost Mode",
        [
            "直接输入：手动设置强化至+9期望成本",
            "分段输入：+0至+6、+6至+7、+7至+8、+8至+9成本",
        ],
        key=f"{key}_enhance_mode",
    )

    if mode == "直接输入：手动设置强化至+9期望成本":
        cost, text = soul_cost_input(
            f"{label_cn}强化至+9期望成本",
            f"{label_en} Expected Upgrade Cost to +9",
            default_soul=5.0,
            gold_per_soul=gold_per_soul,
            bless_value=bless_value,
            key=f"{key}_enhance_direct",
            parent=parent,
        )
        detail = pd.DataFrame([{"item / 项目": f"{label_cn}强化至+9", "cost_soul / 成本_灵魂": cost}])
        return cost, text, detail

    c06, t06 = soul_cost_input(f"{label_cn}+0至+6成本", f"{label_en} +0 to +6 Cost", 1.0, gold_per_soul, bless_value, f"{key}_0_6", parent)
    c67, t67 = soul_cost_input(f"{label_cn}+6至+7成本", f"{label_en} +6 to +7 Cost", 1.0, gold_per_soul, bless_value, f"{key}_6_7", parent)
    c78, t78 = soul_cost_input(f"{label_cn}+7至+8成本", f"{label_en} +7 to +8 Cost", 1.0, gold_per_soul, bless_value, f"{key}_7_8", parent)
    c89, t89 = soul_cost_input(f"{label_cn}+8至+9成本", f"{label_en} +8 to +9 Cost", 1.0, gold_per_soul, bless_value, f"{key}_8_9", parent)
    total = c06 + c67 + c78 + c89
    detail = pd.DataFrame([
        {"item / 项目": f"{label_cn}+0至+6", "cost_soul / 成本_灵魂": c06},
        {"item / 项目": f"{label_cn}+6至+7", "cost_soul / 成本_灵魂": c67},
        {"item / 项目": f"{label_cn}+7至+8", "cost_soul / 成本_灵魂": c78},
        {"item / 项目": f"{label_cn}+8至+9", "cost_soul / 成本_灵魂": c89},
        {"item / 项目": f"{label_cn}强化至+9合计", "cost_soul / 成本_灵魂": total},
    ])
    return total, "分段输入：强化至+9成本", detail


def calculate_medium_magic_stone_value(
    excellent_plus9_option16_value: float,
    synthesis_gold_value: float,
    output_count: int,
):
    if output_count <= 0:
        raise ValueError("中级魔晶石产出数量必须大于0")
    total = excellent_plus9_option16_value + synthesis_gold_value
    return total / output_count, {
        "excellent_plus9_option16_value": excellent_plus9_option16_value,
        "synthesis_gold_value": synthesis_gold_value,
        "output_count": output_count,
        "total_synthesis_cost": total,
        "medium_magic_stone_value": total / output_count,
    }


def calculate_level2_wing_synthesis(
    level1_plus9_option4_wing_value: float,
    feather_value: float,
    chaos_value: float,
    relic_synthesis_gold_value: float,
    medium_magic_stone_value: float,
    lucky_charm_value: float,
    wing_conversion_gold_value: float,
    base_success_rate: float,
    medium_magic_stone_bonus: float,
    lucky_charm_bonus: float,
    max_success_rate: float,
    min_medium_stone_count: int,
    max_medium_stone_count: int,
    max_lucky_charm_count: int,
):
    relic_cost = level1_plus9_option4_wing_value + feather_value + chaos_value + relic_synthesis_gold_value
    records = []

    for n in range(min_medium_stone_count, max_medium_stone_count + 1):
        for m in range(0, max_lucky_charm_count + 1):
            p = min(base_success_rate + n * medium_magic_stone_bonus + m * lucky_charm_bonus, max_success_rate)
            single_attempt_cost = relic_cost + wing_conversion_gold_value + n * medium_magic_stone_value + m * lucky_charm_value
            expected_total_cost = single_attempt_cost / p if p > 0 else float("inf")
            records.append({
                "medium_magic_stone_count / 中级魔晶石数量": n,
                "lucky_charm_count / 幸运符数量": m,
                "success_rate / 转化成功率": p,
                "single_attempt_cost_soul / 单次尝试成本_灵魂": single_attempt_cost,
                "expected_total_cost_soul / 期望总成本_灵魂": expected_total_cost,
            })

    df = pd.DataFrame(records)
    best_row = df.loc[df["expected_total_cost_soul / 期望总成本_灵魂"].idxmin()]
    return df, {"relic_cost": relic_cost, "best_row": best_row}


def plot_expected_cost_curve_l1(df: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(10, 5))
    x = df["low_magic_stone_count / 低级魔晶石数量"]
    y = df["expected_total_cost_soul / 期望总成本_灵魂"]
    ax.plot(x, y, marker="o", linewidth=2)
    ax.set_xlabel("Low Magic Stone Count / 低级魔晶石数量")
    ax.set_ylabel("Expected Total Cost (Soul) / 期望总成本（灵魂）")
    ax.set_title("Level 1 Wing Expected Cost under Different Magic Stone Counts")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    return fig


def plot_expected_cost_curve_l2(best_by_stone: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(10, 5))
    x = best_by_stone["medium_magic_stone_count / 中级魔晶石数量"]
    y = best_by_stone["expected_total_cost_soul / 期望总成本_灵魂"]
    ax.plot(x, y, marker="o", linewidth=2)
    ax.set_xlabel("Medium Magic Stone Count / 中级魔晶石数量")
    ax.set_ylabel("Best Expected Total Cost (Soul) / 最优期望成本（灵魂）")
    ax.set_title("Level 2 Wing Best Expected Cost by Medium Magic Stone Count")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    return fig


# ============================================================
# 2. Streamlit Page Config / 页面配置
# ============================================================

st.set_page_config(
    page_title="MU Online Wing Synthesis Calculator",
    layout="wide",
)

st.title("奇迹MU 一代/二代翅膀合成期望成本计算器")
st.title("MU Online Level 1 & Level 2 Wing Synthesis Expected Cost Calculator")
st.title("尝鲜版-最新功能 Beta Version")
st.title("https://muwingbeta.streamlit.app/")

st.caption("基于一代、二代翅膀圣物合成与圣物转化规则，统一折算为灵魂价值，计算不同材料策略下的合成期望成本。")
st.caption("Material values are set by exchange ratios and converted into Soul-equivalent cost.")

# ============================================================
# 3. Purpose / 用途说明
# ============================================================

with st.expander("🎯 用途和说明 Purpose & Notes", expanded=False):
    purpose_tab_cn, purpose_tab_en = st.tabs(["中文版", "English Version"])
    with purpose_tab_cn:
        st.markdown("""
## 工具用途

本工具针对**奇迹MU一代与二代翅膀合成**过程进行期望成本计算。

在游戏中，翅膀合成涉及多种材料、成功率以及不同服务器经济环境下的市场价格差异。单纯依靠经验判断往往难以准确评估真实成本。

本工具通过统一价值换算体系，将所有材料最终折算为灵魂宝石价值，并自动计算不同魔晶石与幸运符使用策略下的期望成本，从而帮助玩家寻找更优甚至最优方案。

---

## 当前版本支持

- 一代翅膀可单独计算；
- 二代翅膀可调用或输入 +9追4 一代翅膀价值；
- 金币、祝福和各类材料均可按灵魂、祝福、金币三类方式换算；
- 生命宝石、玛雅宝石、洛克之羽、幸运符、低级/中级魔晶石等均可设置；
- 中级魔晶石支持直接输入或按合成规则自动计算；
- 圣物合成费用与圣物转化费用采用固定金币输入；
- 所有成本最终统一折算为灵魂价值进行计算。

---

## 注意事项

金币和祝福不能同时仅通过彼此进行换算，否则无法唯一确定灵魂价值基准。

因此：

- 金币或祝福至少有一个需要直接与灵魂建立换算关系；
- 系统会自动根据输入关系计算完整的价值换算体系。
""")
    with purpose_tab_en:
        st.markdown("""
## Purpose

This calculator evaluates the expected synthesis cost of **Level 1 and Level 2 Wings in MU Online**.

Wing synthesis involves multiple materials, success rates, and market-dependent values. This tool converts all materials into Soul-equivalent value and evaluates different Magic Stone and Lucky Charm strategies.

---

## Current Features

- Standalone Level 1 Wing calculation;
- Level 2 Wing calculation with direct or calculated +9+4 Level 1 Wing value;
- Gold, Bless, and material values can be converted into Soul-equivalent value;
- Life Jewel, Chaos Jewel, Loch's Feather, Lucky Charm, Low/Medium Magic Stone are configurable;
- Medium Magic Stone supports direct input or synthesis-based calculation;
- Relic synthesis and conversion fees are fixed Gold costs;
- All costs are ultimately converted into Soul-equivalent value.
""")

# ============================================================
# 4. Sidebar: Entry / 左侧栏入口
# ============================================================

st.sidebar.header("功能入口 Function Entry")
if "app_mode" not in st.session_state:
    st.session_state.app_mode = "一代翅膀 / Level 1 Wing"

col_btn1, col_btn2 = st.sidebar.columns(2)
if col_btn1.button("一代翅膀"):
    st.session_state.app_mode = "一代翅膀 / Level 1 Wing"
if col_btn2.button("二代翅膀"):
    st.session_state.app_mode = "二代翅膀 / Level 2 Wing"

app_mode = st.sidebar.radio(
    "当前模块 Current Module",
    ["一代翅膀 / Level 1 Wing", "二代翅膀 / Level 2 Wing"],
    index=0 if st.session_state.app_mode == "一代翅膀 / Level 1 Wing" else 1,
    key="app_mode_radio",
)
st.session_state.app_mode = app_mode

run_button = st.sidebar.button("运行计算 Run Calculation")

# ============================================================
# 5. Common Exchange System / 通用换算体系
# ============================================================

st.sidebar.markdown("---")
st.sidebar.header("基础换算 Base Exchange")

# Gold / 金币
gold_section = st.sidebar.container()
with gold_section:
    st.markdown("#### 金币 / Gold")
    gold_mode = st.radio(
        "金币价值设置方式 Gold Value Setting",
        ["金币与灵魂换算：X金币 = Y灵魂", "金币与祝福换算：X金币 = Y祝福"],
        key="gold_mode",
    )
    gold_x = st.number_input("金币数量 X / Gold Count X", min_value=0.0001, max_value=999999999999.0, value=10_000_000.0, step=100_000.0, format="%.0f", key="gold_x")
    if gold_mode == "金币与灵魂换算：X金币 = Y灵魂":
        gold_y_soul = st.number_input("等于多少灵魂 Y / Equivalent Soul Y", min_value=0.0001, max_value=999999999.0, value=1.0, step=1.0, format="%.4f", key="gold_y_soul")
        gold_y_bless = None
        gold_original_text = f"{gold_x:,.0f} 金币 = {gold_y_soul:g} 灵魂"
    else:
        gold_y_bless = st.number_input("等于多少祝福 Y / Equivalent Bless Y", min_value=0.0001, max_value=999999999.0, value=1.0 / 3.0, step=0.01, format="%.4f", key="gold_y_bless")
        gold_y_soul = None
        gold_original_text = f"{gold_x:,.0f} 金币 = {gold_y_bless:g} 祝福"
    gold_result_box = st.empty()

# Bless / 祝福
bless_section = st.sidebar.container()
with bless_section:
    st.markdown("#### 祝福 / Bless")
    bless_mode = st.radio(
        "祝福价值设置方式 Bless Value Setting",
        ["祝福与灵魂换算：X祝福 = Y灵魂", "祝福与金币换算：X祝福 = Y金币"],
        key="bless_mode",
    )
    bless_x = st.number_input("祝福数量 X / Bless Count X", min_value=0.0001, max_value=999999999.0, value=1.0, step=1.0, format="%.4f", key="bless_x")
    if bless_mode == "祝福与灵魂换算：X祝福 = Y灵魂":
        bless_y_soul = st.number_input("等于多少灵魂 Y / Equivalent Soul Y", min_value=0.0001, max_value=999999999.0, value=3.0, step=0.01, format="%.4f", key="bless_y_soul")
        bless_y_gold = None
        bless_original_text = f"{bless_x:g} 祝福 = {bless_y_soul:g} 灵魂"
    else:
        bless_y_gold = st.number_input("等于多少金币 Y / Equivalent Gold Y", min_value=0.0001, max_value=999999999999.0, value=30_000_000.0, step=100_000.0, format="%.0f", key="bless_y_gold")
        bless_y_soul = None
        bless_original_text = f"{bless_x:g} 祝福 = {bless_y_gold:,.0f} 金币"
    bless_result_box = st.empty()

# Solve exchange system / 求解基础换算
gold_direct_to_soul = gold_mode == "金币与灵魂换算：X金币 = Y灵魂"
bless_direct_to_soul = bless_mode == "祝福与灵魂换算：X祝福 = Y灵魂"

if not gold_direct_to_soul and not bless_direct_to_soul:
    st.sidebar.error("当前设置无法唯一确定灵魂基准：金币按祝福换算，祝福又按金币换算。请至少让金币或祝福中的一个直接与灵魂换算。")
    st.error("基础换算比例设置错误：金币和祝福不能同时只通过彼此换算。")
    st.stop()

if bless_direct_to_soul:
    bless_value = bless_y_soul / bless_x
    gold_per_soul = gold_x / gold_y_soul if gold_direct_to_soul else gold_x / (gold_y_bless * bless_value)
else:
    gold_per_soul = gold_x / gold_y_soul
    bless_value = gold_to_soul(bless_y_gold, gold_per_soul) / bless_x

soul_value = 1.0

gold_result_box.info(f"""
金币设置 / Gold Setting:
{gold_original_text}

1 灵魂 / 1 Soul
≈ {gold_per_soul:,.0f} 金币 / Gold
""")
bless_result_box.info(f"""
祝福设置 / Bless Setting:
{bless_original_text}

1 祝福 / 1 Bless
≈ {bless_value:.6f} 灵魂 / Soul
≈ {bless_value * gold_per_soul:,.0f} 金币 / Gold
""")

# ============================================================
# 6. Common Materials / 通用材料
# ============================================================

st.sidebar.markdown("---")
st.sidebar.header("通用材料 Common Materials")

life_value, life_original_text = material_value_ratio_input("生命宝石", "Life Jewel", 1.0, 1.0, gold_per_soul, bless_value, "life", show_title=True, parent=st.sidebar)
chaos_value, chaos_original_text = material_value_ratio_input("玛雅宝石", "Chaos Jewel", 1.0, 0.05, gold_per_soul, bless_value, "chaos", show_title=True, parent=st.sidebar)

# ============================================================
# 7. Level 1 Wing Parameter Function / 一代参数模块
# ============================================================

def level1_parameter_sidebar(prefix: str):
    """Collect Level 1 wing parameters and return calculated values."""
    st.sidebar.markdown("---")
    st.sidebar.header("一代翅膀参数 Level 1 Wing Parameters")

    base_success_rate_pct = st.sidebar.number_input("一代基础成功率 Base Success Rate (%)", 0.0, 100.0, 20.0, 0.01, format="%.2f", key=f"{prefix}_base_success_rate_pct")
    max_success_rate_pct = st.sidebar.number_input("一代成功率上限 Max Success Rate (%)", 0.0, 100.0, 100.0, 0.01, format="%.2f", key=f"{prefix}_max_success_rate_pct")
    magic_stone_bonus_pct = st.sidebar.number_input("每颗低级魔晶石成功率加成 Low Magic Stone Bonus (%)", 0.0, 100.0, 5.0, 0.01, format="%.2f", key=f"{prefix}_magic_stone_bonus_pct")

    base_success_rate = base_success_rate_pct / 100
    max_success_rate = max_success_rate_pct / 100
    magic_stone_bonus = magic_stone_bonus_pct / 100
    max_magic_stone_count = math.ceil((max_success_rate - base_success_rate) / magic_stone_bonus) if magic_stone_bonus > 0 else 0
    max_magic_stone_count = max(0, int(max_magic_stone_count))

    st.sidebar.info(f"""
一代基础成功率：{base_success_rate_pct:.2f}%

每颗低级魔晶石加成：{magic_stone_bonus_pct:.2f}%

一代成功率上限：{max_success_rate_pct:.2f}%

最大枚举数量：{max_magic_stone_count} 颗低级魔晶石
""")

    st.sidebar.markdown("#### +4追4玛雅武器 / +4+4 Chaos Weapon")
    chaos_weapon_mode = st.sidebar.radio(
        "+4追4玛雅武器成本设置 / +4+4 Chaos Weapon Cost Mode",
        ["自动计算：+4不追加玛雅武器 + 生命追加期望成本", "直接输入：手动设置+4追4玛雅武器价值"],
        key=f"{prefix}_chaos_weapon_mode",
    )

    target_option_level = 1
    life_success_rate = 0.50
    expected_option_cost = 0.0
    chaos_weapon_plus4_no_option_value = 0.0
    chaos_weapon_detail = []

    if chaos_weapon_mode == "自动计算：+4不追加玛雅武器 + 生命追加期望成本":
        life_success_rate = st.sidebar.number_input("生命宝石成功率 Life Success Rate", 0.01, 0.99, 0.50, 0.01, format="%.2f", key=f"{prefix}_life_success_rate")
        expected_life_count = expected_life_jewels_to_target(target_option_level, life_success_rate)
        expected_option_cost = expected_life_count * life_value
        chaos_weapon_plus4_no_option_value, chaos_weapon_original_text = material_value_ratio_input(
            "+4不追加玛雅武器", "+4 Chaos Weapon without Option", 1.0, 0.5, gold_per_soul, bless_value, f"{prefix}_chaos_weapon_no_option", show_title=False, parent=st.sidebar
        )
        chaos_weapon_plus4_with_option_value = chaos_weapon_plus4_no_option_value + expected_option_cost
        chaos_weapon_value_text = "自动计算：+4不追加玛雅武器 + 生命追加期望成本"
        chaos_weapon_detail.extend([
            {"item / 项目": "+4不追加玛雅武器", "cost_soul / 成本_灵魂": chaos_weapon_plus4_no_option_value},
            {"item / 项目": "生命追加至追4期望成本", "cost_soul / 成本_灵魂": expected_option_cost},
        ])
        st.sidebar.info(f"+4追4玛雅武器 ≈ {chaos_weapon_plus4_with_option_value:.6f} 灵魂")
    else:
        chaos_weapon_plus4_with_option_value, chaos_weapon_value_text = soul_cost_input(
            "+4追4玛雅武器", "+4+4 Chaos Weapon", 1.5, gold_per_soul, bless_value, f"{prefix}_chaos_weapon_direct", st.sidebar
        )
        expected_life_count = 0.0

    st.sidebar.markdown("#### 低级魔晶石 / Low Magic Stone")
    low_magic_stone_mode = st.sidebar.radio(
        "低级魔晶石价值设置 / Low Magic Stone Cost Mode",
        ["直接输入：手动设置低级魔晶石价值", "自动计算：按低级魔晶石合成规则"],
        key=f"{prefix}_low_magic_stone_mode",
    )
    low_magic_breakdown = None
    if low_magic_stone_mode == "直接输入：手动设置低级魔晶石价值":
        low_magic_stone_value, low_magic_stone_text = soul_cost_input("低级魔晶石", "Low Magic Stone", bless_value, gold_per_soul, bless_value, f"{prefix}_low_magic_direct", st.sidebar)
    else:
        shop_plus9_option12_value, shop_text = soul_cost_input("+9追12商店普通装备", "+9+12 Normal Shop Equipment", 0.3, gold_per_soul, bless_value, f"{prefix}_shop_p9_o12", st.sidebar)
        low_magic_life_success_rate = st.sidebar.number_input("低级魔晶石材料追加生命成功率 Life Success Rate", 0.01, 0.99, float(life_success_rate), 0.01, format="%.2f", key=f"{prefix}_low_magic_life_rate")
        low_magic_gold = st.sidebar.number_input("低级魔晶石合成金币费用 Low Magic Stone Fee (Gold)", 0.0, 999999999999.0, 50_000.0, 1_000.0, format="%.0f", key=f"{prefix}_low_magic_gold")
        low_magic_output = st.sidebar.number_input("低级魔晶石每次产出 Output Count", 1, 999, 3, 1, key=f"{prefix}_low_magic_output")
        low_magic_gold_value = gold_to_soul(low_magic_gold, gold_per_soul)
        low_magic_stone_value, low_magic_breakdown = calculate_low_magic_stone_auto_value(shop_plus9_option12_value, life_value, low_magic_life_success_rate, low_magic_gold_value, int(low_magic_output))
        low_magic_stone_text = "自动计算：+9追16普通装备，50,000金币，成功率100%，产出3颗"
        st.sidebar.info(f"1 低级魔晶石 ≈ {low_magic_stone_value:.6f} 灵魂")

    st.sidebar.markdown("#### 一代合成系统金币费用 Level 1 System Gold Fees")
    relic_synthesis_gold = st.sidebar.number_input("一代圣物合成费用 Relic Synthesis Fee (Gold)", 0.0, 999999999999.0, 10_000.0, 1_000.0, format="%.0f", key=f"{prefix}_relic_synthesis_gold")
    wing_conversion_gold = st.sidebar.number_input("一代圣物转化费用 Relic Conversion Fee (Gold)", 0.0, 999999999999.0, 1_000_000.0, 10_000.0, format="%.0f", key=f"{prefix}_wing_conversion_gold")

    return {
        "base_success_rate": base_success_rate,
        "max_success_rate": max_success_rate,
        "magic_stone_bonus": magic_stone_bonus,
        "max_magic_stone_count": max_magic_stone_count,
        "chaos_weapon_plus4_with_option_value": chaos_weapon_plus4_with_option_value,
        "chaos_weapon_value_text": chaos_weapon_value_text,
        "expected_life_count": expected_life_count,
        "expected_option_cost": expected_option_cost,
        "chaos_weapon_detail": chaos_weapon_detail,
        "low_magic_stone_value": low_magic_stone_value,
        "low_magic_stone_text": low_magic_stone_text,
        "low_magic_breakdown": low_magic_breakdown,
        "relic_synthesis_gold": relic_synthesis_gold,
        "wing_conversion_gold": wing_conversion_gold,
        "relic_synthesis_gold_value": gold_to_soul(relic_synthesis_gold, gold_per_soul),
        "wing_conversion_gold_value": gold_to_soul(wing_conversion_gold, gold_per_soul),
    }

# ============================================================
# 8. Mode-specific Sidebar / 分模块参数
# ============================================================

if app_mode == "一代翅膀 / Level 1 Wing":
    l1_params = level1_parameter_sidebar("l1")
else:
    st.sidebar.markdown("---")
    st.sidebar.header("二代翅膀参数 Level 2 Wing Parameters")

    st.sidebar.markdown("#### +9追4一代翅膀/披风 / +9+4 Level 1 Wing or Cloak")
    l1_wing_source_mode = st.sidebar.radio(
        "+9追4一代翅膀价值来源 / Value Source",
        [
            "直接输入：手动设置+9追4一代翅膀价值",
            "自动计算：一代翅膀合成成本 + 强化至+9 + 追加至追4",
        ],
        key="l2_l1_wing_source_mode",
    )

    l2_nested_l1_params = None
    l1_upgrade_detail = pd.DataFrame()
    l1_option_detail = pd.DataFrame()

    if l1_wing_source_mode == "直接输入：手动设置+9追4一代翅膀价值":
        level1_plus9_option4_wing_value, level1_plus9_option4_text = soul_cost_input(
            "+9追4一代翅膀/披风", "+9+4 Level 1 Wing/Cloak", 30.0, gold_per_soul, bless_value, "l2_l1_plus9_option4_direct", st.sidebar
        )
        l1_base_wing_cost = level1_plus9_option4_wing_value
    else:
        st.sidebar.info("下面将先计算+0一代翅膀，再叠加强化至+9与追加至追4成本。")
        l2_nested_l1_params = level1_parameter_sidebar("l2_nested_l1")
        df_l1_auto, summary_l1_auto = calculate_level1_wing_synthesis(
            bless_value=bless_value,
            soul_value=soul_value,
            chaos_value=chaos_value,
            chaos_weapon_plus4_with_option_cost=l2_nested_l1_params["chaos_weapon_plus4_with_option_value"],
            relic_synthesis_gold_value=l2_nested_l1_params["relic_synthesis_gold_value"],
            wing_conversion_gold_value=l2_nested_l1_params["wing_conversion_gold_value"],
            base_success_rate=l2_nested_l1_params["base_success_rate"],
            max_success_rate=l2_nested_l1_params["max_success_rate"],
            magic_stone_bonus=l2_nested_l1_params["magic_stone_bonus"],
            magic_stone_value=l2_nested_l1_params["low_magic_stone_value"],
            max_magic_stone_count=l2_nested_l1_params["max_magic_stone_count"],
        )
        l1_base_wing_cost = float(summary_l1_auto["best_row"]["expected_total_cost_soul / 期望总成本_灵魂"])
        l1_upgrade_cost, l1_upgrade_text, l1_upgrade_detail = enhancement_cost_to_plus9_input("一代翅膀/披风", "Level 1 Wing/Cloak", gold_per_soul, bless_value, "l2_l1_wing", st.sidebar)
        l1_life_success_rate_for_option = st.sidebar.number_input("一代翅膀追加至追4生命成功率 Life Success Rate for +4 Option", 0.01, 0.99, 0.50, 0.01, format="%.2f", key="l2_l1_option4_life_rate")
        l1_option4_cost = expected_life_jewels_to_target(1, l1_life_success_rate_for_option) * life_value
        l1_option_detail = pd.DataFrame([
            {"item / 项目": "+0一代翅膀期望成本", "cost_soul / 成本_灵魂": l1_base_wing_cost},
            {"item / 项目": "一代翅膀强化至+9成本", "cost_soul / 成本_灵魂": l1_upgrade_cost},
            {"item / 项目": "一代翅膀追加至追4成本", "cost_soul / 成本_灵魂": l1_option4_cost},
        ])
        level1_plus9_option4_wing_value = l1_base_wing_cost + l1_upgrade_cost + l1_option4_cost
        level1_plus9_option4_text = "自动计算：一代合成 + 强化至+9 + 追加至追4"
        st.sidebar.success(f"+9追4一代翅膀/披风 ≈ {level1_plus9_option4_wing_value:.6f} 灵魂")

    st.sidebar.markdown("#### 洛克之羽 / Loch's Feather")
    feather_value, feather_text = soul_cost_input("洛克之羽", "Loch's Feather", 10.0, gold_per_soul, bless_value, "l2_feather", st.sidebar)

    st.sidebar.markdown("#### 幸运符咒 / Lucky Charm")
    lucky_charm_value, lucky_charm_text = soul_cost_input("幸运符咒", "Lucky Charm", 1.0, gold_per_soul, bless_value, "l2_lucky_charm", st.sidebar)

    st.sidebar.markdown("#### 中级魔晶石 / Medium Magic Stone")
    medium_magic_mode = st.sidebar.radio(
        "中级魔晶石价值设置 / Medium Magic Stone Cost Mode",
        ["直接输入：手动设置中级魔晶石价值", "自动计算：按中级魔晶石合成规则"],
        key="l2_medium_magic_mode",
    )
    medium_breakdown = None
    medium_material_detail = pd.DataFrame()

    if medium_magic_mode == "直接输入：手动设置中级魔晶石价值":
        medium_magic_stone_value, medium_magic_text = soul_cost_input("中级魔晶石", "Medium Magic Stone", 3.0, gold_per_soul, bless_value, "l2_medium_direct", st.sidebar)
    else:
        material_mode = st.sidebar.radio(
            "+9追16卓越材料价值来源 / +9+16 Excellent Material Source",
            ["直接输入：手动设置+9追16卓越材料价值", "自动计算：卓越基础装备 + 强化至+9 + 追加至追16"],
            key="l2_medium_material_mode",
        )
        if material_mode == "直接输入：手动设置+9追16卓越材料价值":
            excellent_plus9_option16_value, excellent_text = soul_cost_input("+9追16卓越品质武器/防具", "+9+16 Excellent Weapon/Armor", 9.0, gold_per_soul, bless_value, "l2_excellent_p9_o16_direct", st.sidebar)
        else:
            excellent_base_value, excellent_base_text = soul_cost_input("卓越品质武器/防具基础价值", "Base Excellent Weapon/Armor", 1.0, gold_per_soul, bless_value, "l2_excellent_base", st.sidebar)
            excellent_upgrade_cost, excellent_upgrade_text, excellent_upgrade_detail = enhancement_cost_to_plus9_input("卓越装备", "Excellent Equipment", gold_per_soul, bless_value, "l2_excellent", st.sidebar)
            excellent_life_rate = st.sidebar.number_input("卓越装备追加至追16生命成功率 Life Success Rate for +16 Option", 0.01, 0.99, 0.50, 0.01, format="%.2f", key="l2_excellent_option16_life_rate")
            excellent_option16_cost = expected_life_jewels_to_target(4, excellent_life_rate) * life_value
            excellent_plus9_option16_value = excellent_base_value + excellent_upgrade_cost + excellent_option16_cost
            medium_material_detail = pd.DataFrame([
                {"item / 项目": "卓越装备基础价值", "cost_soul / 成本_灵魂": excellent_base_value},
                {"item / 项目": "卓越装备强化至+9成本", "cost_soul / 成本_灵魂": excellent_upgrade_cost},
                {"item / 项目": "卓越装备追加至追16成本", "cost_soul / 成本_灵魂": excellent_option16_cost},
                {"item / 项目": "+9追16卓越装备合计", "cost_soul / 成本_灵魂": excellent_plus9_option16_value},
            ])
            st.sidebar.success(f"+9追16卓越装备 ≈ {excellent_plus9_option16_value:.6f} 灵魂")

        medium_magic_gold = st.sidebar.number_input("中级魔晶石合成金币费用 Medium Magic Stone Fee (Gold)", 0.0, 999999999999.0, 50_000.0, 1_000.0, format="%.0f", key="l2_medium_gold")
        medium_magic_output = st.sidebar.number_input("中级魔晶石每次产出 Output Count", 1, 999, 3, 1, key="l2_medium_output")
        medium_magic_stone_value, medium_breakdown = calculate_medium_magic_stone_value(excellent_plus9_option16_value, gold_to_soul(medium_magic_gold, gold_per_soul), int(medium_magic_output))
        medium_magic_text = "自动计算：+9追16卓越装备，50,000金币，成功率100%，产出3颗"
        st.sidebar.info(f"1 中级魔晶石 ≈ {medium_magic_stone_value:.6f} 灵魂")

    st.sidebar.markdown("#### 二代成功率与费用 Level 2 Success Rates & Fees")
    l2_base_success_pct = st.sidebar.number_input("二代基础成功率 Base Success Rate (%)", 0.0, 100.0, 53.0, 0.01, format="%.2f", key="l2_base_success_pct")
    l2_medium_bonus_pct = st.sidebar.number_input("每颗中级魔晶石成功率加成 Medium Magic Stone Bonus (%)", 0.0, 100.0, 5.0, 0.01, format="%.2f", key="l2_medium_bonus_pct")
    l2_lucky_bonus_pct = st.sidebar.number_input("每张幸运符成功率加成 Lucky Charm Bonus (%)", 0.0, 100.0, 10.0, 0.01, format="%.2f", key="l2_lucky_bonus_pct")
    l2_max_success_pct = st.sidebar.number_input("二代成功率上限 Max Success Rate (%)", 0.0, 100.0, 100.0, 0.01, format="%.2f", key="l2_max_success_pct")

    min_medium_count = st.sidebar.number_input("最少中级魔晶石数量 Min Medium Magic Stone Count", 0, 99, 1, 1, key="l2_min_medium_count")
    max_medium_count_default = max(int(min_medium_count), int(math.ceil(max(0.0, (l2_max_success_pct - l2_base_success_pct) / max(l2_medium_bonus_pct, 0.0001)))) + int(min_medium_count))
    max_medium_count = st.sidebar.number_input("最大枚举中级魔晶石数量 Max Medium Magic Stone Count", int(min_medium_count), 99, min(20, max_medium_count_default), 1, key="l2_max_medium_count")
    max_lucky_count = st.sidebar.number_input("最大枚举幸运符数量 Max Lucky Charm Count", 0, 99, 10, 1, key="l2_max_lucky_count")

    l2_relic_synthesis_gold = st.sidebar.number_input("二代圣物合成费用 Level 2 Relic Synthesis Fee (Gold)", 0.0, 999999999999.0, 5_000_000.0, 100_000.0, format="%.0f", key="l2_relic_synthesis_gold")
    l2_wing_conversion_gold = st.sidebar.number_input("二代翅膀转化费用 Level 2 Wing Conversion Fee (Gold)", 0.0, 999999999999.0, 10_000_000.0, 100_000.0, format="%.0f", key="l2_wing_conversion_gold")

# ============================================================
# 9. Main Display / 主界面展示
# ============================================================

if run_button:
    if app_mode == "一代翅膀 / Level 1 Wing":
        df, summary = calculate_level1_wing_synthesis(
            bless_value=bless_value,
            soul_value=soul_value,
            chaos_value=chaos_value,
            chaos_weapon_plus4_with_option_cost=l1_params["chaos_weapon_plus4_with_option_value"],
            relic_synthesis_gold_value=l1_params["relic_synthesis_gold_value"],
            wing_conversion_gold_value=l1_params["wing_conversion_gold_value"],
            base_success_rate=l1_params["base_success_rate"],
            max_success_rate=l1_params["max_success_rate"],
            magic_stone_bonus=l1_params["magic_stone_bonus"],
            magic_stone_value=l1_params["low_magic_stone_value"],
            max_magic_stone_count=l1_params["max_magic_stone_count"],
        )
        best_row = summary["best_row"]

        st.subheader("一代翅膀计算结果 Level 1 Wing Results")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("建议低级魔晶石数量", f"{int(best_row['low_magic_stone_count / 低级魔晶石数量'])} 颗")
        col2.metric("对应成功率", f"{best_row['success_rate / 转化成功率']:.2%}")
        col3.metric("单次尝试成本", f"{best_row['single_attempt_cost_soul / 单次尝试成本_灵魂']:.4f} 灵魂")
        col4.metric("期望总成本", f"{best_row['expected_total_cost_soul / 期望总成本_灵魂']:.4f} 灵魂")

        st.markdown("---")
        st.subheader("一代成本拆解 Level 1 Cost Breakdown")
        breakdown_rows = [
            {"item / 项目": "金币 Gold", "cost_soul / 成本_灵魂": f"1金币 = {1 / gold_per_soul:.10f} 灵魂"},
            {"item / 项目": "祝福宝石 Bless Jewel", "cost_soul / 成本_灵魂": bless_value},
            {"item / 项目": "灵魂宝石 Soul Jewel", "cost_soul / 成本_灵魂": soul_value},
            {"item / 项目": "生命宝石 Life Jewel", "cost_soul / 成本_灵魂": life_value},
            {"item / 项目": "玛雅宝石 Chaos Jewel", "cost_soul / 成本_灵魂": chaos_value},
            *l1_params["chaos_weapon_detail"],
            {"item / 项目": "+4追4玛雅武器 +4+4 Chaos Weapon", "cost_soul / 成本_灵魂": l1_params["chaos_weapon_plus4_with_option_value"]},
            {"item / 项目": "低级魔晶石 Low Magic Stone", "cost_soul / 成本_灵魂": l1_params["low_magic_stone_value"]},
            {"item / 项目": "一代圣物合成费用", "cost_soul / 成本_灵魂": l1_params["relic_synthesis_gold_value"]},
            {"item / 项目": "一代翅膀圣物成本", "cost_soul / 成本_灵魂": summary["relic_cost"]},
            {"item / 项目": "一代翅膀转化费用", "cost_soul / 成本_灵魂": l1_params["wing_conversion_gold_value"]},
        ]
        breakdown_df = pd.DataFrame(breakdown_rows)
        st.dataframe(breakdown_df, use_container_width=True)
        st.download_button("下载一代成本拆解 CSV", breakdown_df.to_csv(index=False, encoding="utf-8-sig"), "level1_wing_cost_breakdown.csv", "text/csv")

        st.markdown("---")
        st.subheader("不同低级魔晶石数量下的期望成本 Expected Cost by Low Magic Stone Count")
        display_df = df.copy()
        display_df["success_rate_display / 成功率显示"] = display_df["success_rate / 转化成功率"].apply(format_percentage)
        st.dataframe(display_df, use_container_width=True)
        st.download_button("下载一代枚举结果 CSV", df.to_csv(index=False, encoding="utf-8-sig"), "level1_wing_enumeration.csv", "text/csv")

        st.markdown("---")
        st.subheader("期望成本曲线 Expected Cost Curve")
        st.pyplot(plot_expected_cost_curve_l1(df))

        st.info(f"在当前参数下，一代翅膀最低期望成本方案为使用 **{int(best_row['low_magic_stone_count / 低级魔晶石数量'])} 颗低级魔晶石**，期望总成本为 **{best_row['expected_total_cost_soul / 期望总成本_灵魂']:.4f} 灵魂**。")

    else:
        df2, summary2 = calculate_level2_wing_synthesis(
            level1_plus9_option4_wing_value=level1_plus9_option4_wing_value,
            feather_value=feather_value,
            chaos_value=chaos_value,
            relic_synthesis_gold_value=gold_to_soul(l2_relic_synthesis_gold, gold_per_soul),
            medium_magic_stone_value=medium_magic_stone_value,
            lucky_charm_value=lucky_charm_value,
            wing_conversion_gold_value=gold_to_soul(l2_wing_conversion_gold, gold_per_soul),
            base_success_rate=l2_base_success_pct / 100,
            medium_magic_stone_bonus=l2_medium_bonus_pct / 100,
            lucky_charm_bonus=l2_lucky_bonus_pct / 100,
            max_success_rate=l2_max_success_pct / 100,
            min_medium_stone_count=int(min_medium_count),
            max_medium_stone_count=int(max_medium_count),
            max_lucky_charm_count=int(max_lucky_count),
        )
        best_row = summary2["best_row"]

        st.subheader("二代翅膀计算结果 Level 2 Wing Results")
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("建议中级魔晶石", f"{int(best_row['medium_magic_stone_count / 中级魔晶石数量'])} 颗")
        col2.metric("建议幸运符", f"{int(best_row['lucky_charm_count / 幸运符数量'])} 张")
        col3.metric("对应成功率", f"{best_row['success_rate / 转化成功率']:.2%}")
        col4.metric("单次尝试成本", f"{best_row['single_attempt_cost_soul / 单次尝试成本_灵魂']:.4f} 灵魂")
        col5.metric("期望总成本", f"{best_row['expected_total_cost_soul / 期望总成本_灵魂']:.4f} 灵魂")

        st.markdown("---")
        st.subheader("二代成本拆解 Level 2 Cost Breakdown")
        breakdown_rows = [
            {"item / 项目": "+9追4一代翅膀/披风", "cost_soul / 成本_灵魂": level1_plus9_option4_wing_value},
            {"item / 项目": "洛克之羽 Loch's Feather", "cost_soul / 成本_灵魂": feather_value},
            {"item / 项目": "玛雅宝石 Chaos Jewel", "cost_soul / 成本_灵魂": chaos_value},
            {"item / 项目": "二代圣物合成费用", "cost_soul / 成本_灵魂": gold_to_soul(l2_relic_synthesis_gold, gold_per_soul)},
            {"item / 项目": "二代翅膀圣物成本", "cost_soul / 成本_灵魂": summary2["relic_cost"]},
            {"item / 项目": "中级魔晶石 Medium Magic Stone", "cost_soul / 成本_灵魂": medium_magic_stone_value},
            {"item / 项目": "幸运符咒 Lucky Charm", "cost_soul / 成本_灵魂": lucky_charm_value},
            {"item / 项目": "二代翅膀转化费用", "cost_soul / 成本_灵魂": gold_to_soul(l2_wing_conversion_gold, gold_per_soul)},
        ]
        breakdown_df = pd.DataFrame(breakdown_rows)
        st.dataframe(breakdown_df, use_container_width=True)
        st.download_button("下载二代成本拆解 CSV", breakdown_df.to_csv(index=False, encoding="utf-8-sig"), "level2_wing_cost_breakdown.csv", "text/csv")

        if not l1_upgrade_detail.empty or not l1_option_detail.empty:
            st.markdown("---")
            st.subheader("+9追4一代翅膀上游成本 Upper-Level Cost for +9+4 Level 1 Wing")
            upstream_l1_df = pd.concat([l1_option_detail, l1_upgrade_detail], ignore_index=True) if not l1_upgrade_detail.empty else l1_option_detail
            st.dataframe(upstream_l1_df, use_container_width=True)

        if not medium_material_detail.empty:
            st.markdown("---")
            st.subheader("中级魔晶石材料成本 Medium Magic Stone Material Cost")
            st.dataframe(medium_material_detail, use_container_width=True)

        st.markdown("---")
        st.subheader("二代枚举结果 Level 2 Enumeration Results")
        display_df = df2.copy()
        display_df["success_rate_display / 成功率显示"] = display_df["success_rate / 转化成功率"].apply(format_percentage)
        st.dataframe(display_df, use_container_width=True)
        st.download_button("下载二代枚举结果 CSV", df2.to_csv(index=False, encoding="utf-8-sig"), "level2_wing_enumeration.csv", "text/csv")

        st.markdown("---")
        best_by_stone = df2.sort_values("expected_total_cost_soul / 期望总成本_灵魂").groupby("medium_magic_stone_count / 中级魔晶石数量", as_index=False).first()
        st.subheader("每个中级魔晶石数量下的最佳方案 Best Strategy by Medium Magic Stone Count")
        st.dataframe(best_by_stone, use_container_width=True)
        st.pyplot(plot_expected_cost_curve_l2(best_by_stone))

        st.info(f"在当前参数下，二代翅膀最低期望成本方案为使用 **{int(best_row['medium_magic_stone_count / 中级魔晶石数量'])} 颗中级魔晶石**、**{int(best_row['lucky_charm_count / 幸运符数量'])} 张幸运符**，期望总成本为 **{best_row['expected_total_cost_soul / 期望总成本_灵魂']:.4f} 灵魂**。")

else:
    st.info("请在左侧选择一代或二代翅膀模块，设置参数，然后点击“运行计算”。")
    st.info("Select Level 1 or Level 2 Wing module on the left, set parameters, and click Run Calculation.")

# ============================================================
# 10. User Guide / 使用说明
# ============================================================

with st.expander("📘 使用说明 User Guide", expanded=False):
    guide_tab_cn, guide_tab_en = st.tabs(["中文版", "English Version"])
    with guide_tab_cn:
        st.markdown("""
# 使用说明

## 1. 工具用途

本工具用于计算《奇迹MU》中一代、二代翅膀从材料准备到最终转化成功的期望成本，并自动寻找当前参数条件下的较优魔晶石与幸运符使用方案。

所有成本最终统一折算为“灵魂宝石价值”进行计算，以便比较不同材料、不同服务器经济环境下的真实成本。

---

## 2. 一代翅膀规则

一代翅膀模型包括：

- +4追4玛雅武器；
- 祝福宝石；
- 灵魂宝石；
- 玛雅宝石；
- 圣物合成金币费用；
- 低级魔晶石；
- 圣物转化金币费用。

程序会枚举不同低级魔晶石数量下的成功率与期望成本。

---

## 3. 二代翅膀规则

二代圣物材料：

- +9追4一代翅膀/披风 ×1；
- 洛克之羽 ×1；
- 玛雅宝石 ×1；
- 5,000,000 金币。

二代圣物合成成功率默认为 100%。

二代翅膀转化材料：

- 二代翅膀圣物 ×1；
- 中级魔晶石 ×N；
- 幸运符 ×M；
- 10,000,000 金币。

成功率默认为：

基础 53%，每颗中级魔晶石 +5%，每张幸运符 +10%，上限 100%。

---

## 4. 中级魔晶石规则

中级魔晶石可直接输入价值，也可按合成规则计算：

- +9追16卓越品质武器/防具 ×1；
- 50,000 金币；
- 成功率 100%；
- 每次产出 3 颗中级魔晶石。

---

## 5. 生命宝石追加

模型假设：

- 成功则追加等级 +1档；
- 失败则追加归零；
- 追4、追8、追12、追16分别对应连续成功1、2、3、4次。

---

## 6. 免责声明

本工具基于用户输入参数进行计算。实际游戏中的合成成功率、市场价格、宝石价值和金币价值可能随服务器、时间及市场环境发生变化。本工具仅提供理论计算结果与决策参考。
""")
    with guide_tab_en:
        st.markdown("""
# User Guide

This calculator estimates the expected cost of synthesizing Level 1 and Level 2 Wings in MU Online. All values are converted into Soul-equivalent cost.

Level 2 Wing synthesis consists of Level 2 Relic synthesis and Relic-to-Wing conversion. Medium Magic Stone can be entered directly or calculated from +9+16 Excellent equipment, 50,000 Gold, 100% success rate, and 3 stones per synthesis.

All results depend on user-defined exchange ratios, market values and success rates.
""")

# ============================================================
# 11. Author / 作者
# ============================================================

st.markdown("---")
st.markdown("#### Developed by 作者：Razz")
st.markdown("GitHub: https://github.com/razzer1114/MuOnline_item_upgrade_cost_calculator")
st.markdown("💬 如果有问题、意见或建议，请移步贴吧讨论：")
st.markdown("装备强化app贴：https://tieba.baidu.com/p/10677589188")
st.markdown("翅膀合成app贴：https://tieba.baidu.com/p/10761263145")

# ============================================================
# 12. Disclaimer / 免责声明
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
# 13. Visit Counter / 访问统计
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
    unsafe_allow_html=True,
)
