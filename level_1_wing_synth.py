# ============================================================
# MU Online Wing Synthesis Expected Cost Calculator
# 奇迹MU 一代翅膀合成期望成本计算器
# ============================================================

import pandas as pd


# ============================================================
# 1. 参数设置 / Parameters
# ============================================================

# ---------- 基础价值换算 / Basic value conversion ----------
gold_per_soul = 10_000_000        # 1000万金币 = 1 灵魂
life_value = 1.0                  # 1生命 = 1灵魂
soul_value = 1.0                  # 灵魂作为基准单位
bless_value = 3.0                 # 1祝福 = ? 灵魂，可修改

chaos_gold = 500_000              # 玛雅宝石价值：50万金币
maya_weapon_plus4_no_option_gold = 5_000_000  # +4不追加玛雅武器：500万金币

# ---------- 圣物合成金币消耗 / Relic synthesis gold cost ----------
relic_synthesis_gold = 10_000     # 合成一代翅膀圣物消耗金币

# ---------- 圣物转化金币消耗 / Relic-to-wing conversion gold cost ----------
wing_conversion_gold = 1_000_000  # 圣物转化为翅膀消耗金币

# ---------- 生命宝石追加规则 / Life jewel option rule ----------
life_success_rate = 0.50          # 生命宝石成功率
target_option_level = 1           # 追4 = 1；追8 = 2；追12 = 3；追16 = 4

# ---------- 一代翅膀转化规则 / 1st wing conversion rule ----------
base_success_rate = 0.20          # 一代翅膀基础成功率 20%
max_success_rate = 1.00           # 一代翅膀成功率上限 100%
magic_stone_bonus = 0.05          # 每颗低级魔晶石提升 5%
magic_stone_value = bless_value   # 低级魔晶石价值，暂按 1祝福

max_magic_stone_count = 16        # 一代从20%到100%最多需要16颗


# ============================================================
# 2. 工具函数 / Helper functions
# ============================================================

def gold_to_soul(gold: float) -> float:
    """
    将金币价值换算为灵魂价值
    Convert gold value into Soul-equivalent value.
    """
    return gold / gold_per_soul


def expected_life_jewels_to_target(target_level: int, p: float = 0.5) -> float:
    """
    计算从无追加到目标追加等级的期望生命宝石消耗。
    规则：成功 +1，失败归零。

    target_level:
        1 = 追4
        2 = 追8
        3 = 追12
        4 = 追16

    Expected trials for k consecutive successes:
        E = (1 - p^k) / ((1 - p) * p^k)
    """
    if target_level <= 0:
        return 0.0

    if not 0 < p < 1:
        raise ValueError("生命宝石成功率必须在 0 和 1 之间")

    return (1 - p ** target_level) / ((1 - p) * (p ** target_level))


def option_name(level: int) -> str:
    """
    追加等级名称
    """
    mapping = {
        0: "无追加",
        1: "追4",
        2: "追8",
        3: "追12",
        4: "追16",
    }
    return mapping.get(level, f"追{level * 4}")


def wing_success_rate(stone_count: int) -> float:
    """
    根据魔晶石数量计算一代翅膀转化成功率
    """
    return min(
        base_success_rate + stone_count * magic_stone_bonus,
        max_success_rate
    )


# ============================================================
# 3. 成本计算 / Cost calculation
# ============================================================

# 金币类成本换算
chaos_value = gold_to_soul(chaos_gold)
maya_weapon_plus4_no_option_value = gold_to_soul(maya_weapon_plus4_no_option_gold)
relic_synthesis_gold_value = gold_to_soul(relic_synthesis_gold)
wing_conversion_gold_value = gold_to_soul(wing_conversion_gold)

# 追加属性成本
expected_life_count = expected_life_jewels_to_target(
    target_option_level,
    life_success_rate
)

expected_option_cost = expected_life_count * life_value

# +4追4玛雅武器成本
maya_weapon_plus4_with_option_cost = (
    maya_weapon_plus4_no_option_value
    + expected_option_cost
)

# 一代翅膀圣物成本
relic_cost = (
    maya_weapon_plus4_with_option_cost
    + bless_value
    + soul_value
    + chaos_value
    + relic_synthesis_gold_value
)


# ============================================================
# 4. 枚举不同魔晶石数量 / Enumerate strategies
# ============================================================

records = []

for n in range(max_magic_stone_count + 1):
    p = wing_success_rate(n)

    single_attempt_cost = (
        relic_cost
        + wing_conversion_gold_value
        + n * magic_stone_value
    )

    expected_total_cost = single_attempt_cost / p

    records.append({
        "低级魔晶石数量": n,
        "转化成功率": p,
        "单次尝试成本_灵魂": single_attempt_cost,
        "期望总成本_灵魂": expected_total_cost,
    })

df = pd.DataFrame(records)

best_row = df.loc[df["期望总成本_灵魂"].idxmin()]


# ============================================================
# 5. 输出结果 / Output results
# ============================================================

print("=" * 70)
print("奇迹MU 一代翅膀合成期望成本计算")
print("=" * 70)

print("\n【基础参数】")
print(f"金币换算：{gold_per_soul:,.0f} 金币 = 1 灵魂")
print(f"祝福价值：{bless_value:.4f} 灵魂")
print(f"生命价值：{life_value:.4f} 灵魂")
print(f"玛雅价值：{chaos_value:.4f} 灵魂")
print(f"+4不追加玛雅武器价值：{maya_weapon_plus4_no_option_value:.4f} 灵魂")
print(f"低级魔晶石价值：{magic_stone_value:.4f} 灵魂")

print("\n【追加属性成本】")
print(f"目标追加：{option_name(target_option_level)}")
print(f"生命宝石成功率：{life_success_rate:.2%}")
print(f"期望生命宝石消耗：{expected_life_count:.4f} 颗")
print(f"期望追加成本：{expected_option_cost:.4f} 灵魂")

print("\n【一代翅膀圣物成本】")
print(f"+4{option_name(target_option_level)}玛雅武器成本：{maya_weapon_plus4_with_option_cost:.4f} 灵魂")
print(f"祝福宝石：{bless_value:.4f} 灵魂")
print(f"灵魂宝石：{soul_value:.4f} 灵魂")
print(f"玛雅宝石：{chaos_value:.4f} 灵魂")
print(f"圣物合成金币：{relic_synthesis_gold_value:.6f} 灵魂")
print(f"一代翅膀圣物总成本：{relic_cost:.4f} 灵魂")

print("\n【不同魔晶石数量下的期望成本】")
print(df.to_string(index=False, formatters={
    "转化成功率": lambda x: f"{x:.2%}",
    "单次尝试成本_灵魂": lambda x: f"{x:.4f}",
    "期望总成本_灵魂": lambda x: f"{x:.4f}",
}))

print("\n【最优方案】")
print(f"建议使用低级魔晶石数量：{int(best_row['低级魔晶石数量'])} 颗")
print(f"对应转化成功率：{best_row['转化成功率']:.2%}")
print(f"单次尝试成本：{best_row['单次尝试成本_灵魂']:.4f} 灵魂")
print(f"合成一代翅膀期望总成本：{best_row['期望总成本_灵魂']:.4f} 灵魂")

print("=" * 70)
