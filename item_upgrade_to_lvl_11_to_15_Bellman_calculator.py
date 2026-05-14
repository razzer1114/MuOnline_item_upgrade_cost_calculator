"""
============================================================
MU Online Item Upgrade Cost Calculator
MU Online 装备强化策略优化计算器（+0 → +15）
============================================================

Author:
Razz

License:
MIT License

Project Description:
本脚本用于计算 MU Online 装备从 +0 强化至 +15 的最优期望成本策略。

本模型基于吸收型马尔可夫链，将装备强化等级视为状态，将强化成功、失败、
回退、归零、装备消失等规则统一写入状态转移矩阵，并通过基本矩阵：

    N = (I - Q)^(-1)

计算从 +0 出发最终达到 +15 所需的期望资源消耗。

------------------------------------------------------------
功能说明
------------------------------------------------------------

1. +0 → +6：
   每一级可选择：
   - B：Bless，祝福宝石，100%成功；
   - S：Soul，灵魂宝石，概率成功。

2. +6 → +9：
   固定使用 Soul，不再枚举 Bless/Soul 策略，但仍然计算成本。

3. +9 → +15：
   固定进入合成强化阶段，每一级可选择：
   - 是否使用装备保护符；
   - 是否使用幸运符。

4. 输出文件：
   - all_strategy_expected_costs.csv
     导出所有枚举策略的期望消耗与总成本排序；

   - best_strategy_transition_matrix.csv
     导出最优策略对应的状态转移矩阵；

   - best_strategy_cost_vectors.csv
     导出最优策略对应的各状态成本向量。

------------------------------------------------------------
参数设置指引
------------------------------------------------------------

p_soul:
    灵魂宝石在 +0 → +9 阶段的强化成功率。

cost_soul:
    灵魂宝石成本，通常设为 1，作为统一计价单位。

cost_bless:
    祝福宝石成本，表示 1 颗祝福等价多少颗灵魂。

item_0_cost:
    +0 装备价值，表示装备消失后重新购买一件 +0 装备所需成本，
    单位同样为“灵魂宝石等价数量”。

talisman_protect_cost:
    装备保护符成本，单位为灵魂宝石等价数量。

talisman_luck_cost:
    幸运符成本，单位为灵魂宝石等价数量。

chaos_cost:
    玛雅之石成本，单位为灵魂宝石等价数量。

luck_success_bonus:
    幸运符增加的成功率。

level_upgrade_info:
    +9 → +15 阶段每一级强化所需资源与基础成功率。
    当前代码默认读取普通装备成功率，即每一行中的第 4 个数值。
"""

import itertools  # 用于枚举 Bless/Soul 策略、保护符策略和幸运符策略的所有组合
import numpy as np  # 用于矩阵、向量和线性代数计算
import pandas as pd  # 用于整理结果表格并导出 CSV 文件


# ============================================================
# 1. 参数设置
# ============================================================

p_soul = 0.4  # 灵魂宝石成功率，例如 0.4 表示 40%
q_soul = 1 - p_soul  # 灵魂宝石失败率，目前仅保留用于说明，后续计算直接使用 1 - p_soul

cost_soul = 1  # 灵魂宝石成本，作为统一成本单位
cost_bless = 7.14 / 1.35  # 祝福宝石成本，表示 1 颗祝福等价多少颗灵魂

item_0_cost = 10  # +0 装备价值，装备消失后重新购买装备的成本
talisman_protect_cost = 3  # 装备保护符成本，折算为灵魂宝石数量
talisman_luck_cost = 2  # 幸运符成本，折算为灵魂宝石数量
chaos_cost = 5  # 玛雅之石成本，折算为灵魂宝石数量

luck_success_bonus = 0.25  # 幸运符成功率加成，这里表示增加 25%

absorbing_state = 15  # 吸收态，表示装备达到 +15 后强化过程结束
transient_states = list(range(15))  # 暂态状态，表示 +0 到 +14，共 15 个状态

# +9 → +15 阶段每一级强化的资源需求和基础成功率
# 字典键 9 表示 +9 → +10，键 10 表示 +10 → +11，以此类推
# 每个列表含义为：
# [祝福数量, 灵魂数量, 玛雅数量, 普通装备成功率, 卓越/套装成功率, 镶宝装备成功率]
level_upgrade_info = {
    9:  [1, 1, 1, 0.60, 0.50, 0.40],  # +9 → +10
    10: [2, 2, 1, 0.60, 0.50, 0.40],  # +10 → +11
    11: [3, 3, 1, 0.55, 0.45, 0.35],  # +11 → +12
    12: [4, 4, 1, 0.55, 0.45, 0.35],  # +12 → +13
    13: [5, 5, 1, 0.50, 0.40, 0.30],  # +13 → +14
    14: [6, 6, 1, 0.50, 0.40, 0.30],  # +14 → +15
}


# ============================================================
# 2. 失败状态函数
# ============================================================

def fail_state(i, use_protect=False):
    """返回当前等级 i 强化失败后的等级。"""

    if i == 0:  # 如果当前是 +0
        return 0  # +0 强化失败后仍然停留在 +0

    elif 1 <= i <= 6:  # 如果当前是 +1 到 +6
        return i - 1  # 失败后退一级

    elif 7 <= i <= 8:  # 如果当前是 +7 或 +8
        return 0  # 失败后回到 +0

    elif 9 <= i <= 14:  # 如果当前是 +9 到 +14
        return 0  # 失败后等级回到 +0；是否损失装备在成本向量中处理

    else:  # 如果输入等级不在合法范围
        raise ValueError("无效状态")  # 抛出错误，提醒调用者检查输入


# ============================================================
# 3. +9以上成功率函数
# ============================================================

def get_high_level_success_rate(i, use_luck=False):
    """返回 +9 → +14 阶段某一级强化的成功率。"""

    base_success = level_upgrade_info[i][3]  # 读取普通装备基础成功率

    if use_luck:  # 如果当前等级使用幸运符
        return min(base_success + luck_success_bonus, 1.0)  # 成功率增加，但不超过 100%

    return base_success  # 如果不使用幸运符，直接返回基础成功率


# ============================================================
# 4. 构建转移矩阵
# ============================================================

def build_transition_matrix(strategy, protect_flags=None, luck_flags=None):
    """构建 16×16 转移矩阵。"""

    Q = np.zeros((absorbing_state + 1, absorbing_state + 1))  # 初始化 16×16 全零矩阵

    if protect_flags is None:  # 如果没有传入保护符使用方案
        protect_flags = [False] * 6  # 默认 +9 → +14 六个阶段都不使用保护符

    if luck_flags is None:  # 如果没有传入幸运符使用方案
        luck_flags = [False] * 6  # 默认 +9 → +14 六个阶段都不使用幸运符

    for i in transient_states:  # 遍历 +0 到 +14 所有暂态状态
        action = strategy[i]  # 读取当前等级使用 Bless 还是 Soul

        if action == "B":  # 如果当前等级使用祝福宝石
            next_state = i + 1  # 祝福宝石 100% 成功，进入下一级
            Q[i, next_state] = 1.0  # 将从 i 到 i+1 的转移概率设为 1

        elif action == "S":  # 如果当前等级使用灵魂宝石或合成强化
            if i <= 8:  # +0 → +9 阶段使用灵魂宝石概率规则
                success_state = i + 1  # 成功后进入下一级
                failure_state = fail_state(i)  # 失败后根据规则回退或归零

                Q[i, success_state] += p_soul  # 写入成功转移概率
                Q[i, failure_state] += 1 - p_soul  # 写入失败转移概率

            else:  # +9 → +15 阶段使用合成强化规则
                use_protect = protect_flags[i - 9]  # 读取当前等级是否使用保护符
                use_luck = luck_flags[i - 9]  # 读取当前等级是否使用幸运符

                success_rate = get_high_level_success_rate(i, use_luck)  # 计算当前等级成功率

                success_state = i + 1  # 成功后进入下一级
                failure_state = fail_state(i, use_protect)  # 失败后回到 +0

                Q[i, success_state] += success_rate  # 写入成功转移概率
                Q[i, failure_state] += 1 - success_rate  # 写入失败转移概率

        else:  # 如果 action 不是 B 或 S
            raise ValueError("未知动作")  # 抛出错误，防止策略字符串异常

    return Q  # 返回完整状态转移矩阵


# ============================================================
# 5. 构建成本向量
# ============================================================

def build_cost_vectors(strategy, protect_flags=None, luck_flags=None):
    """构建各类资源消耗向量。"""

    bless_vec = np.zeros(absorbing_state + 1)  # 每个状态对应的祝福消耗向量
    soul_vec = np.zeros(absorbing_state + 1)  # 每个状态对应的灵魂消耗向量
    chaos_vec = np.zeros(absorbing_state + 1)  # 每个状态对应的玛雅消耗向量
    luck_vec = np.zeros(absorbing_state + 1)  # 每个状态对应的幸运符消耗向量
    protect_vec = np.zeros(absorbing_state + 1)  # 每个状态对应的保护符消耗向量

    item_0_loss_count_vec = np.zeros(absorbing_state + 1)  # 每个状态对应的装备损失数量期望向量
    item_0_loss_cost_vec = np.zeros(absorbing_state + 1)  # 每个状态对应的装备损失价值期望向量

    total_vec = np.zeros(absorbing_state + 1)  # 每个状态对应的总成本向量

    if protect_flags is None:  # 如果没有传入保护符方案
        protect_flags = [False] * 6  # 默认所有 +9 以上阶段都不使用保护符

    if luck_flags is None:  # 如果没有传入幸运符方案
        luck_flags = [False] * 6  # 默认所有 +9 以上阶段都不使用幸运符

    for i in transient_states:  # 遍历 +0 到 +14
        action = strategy[i]  # 读取当前状态使用的强化动作

        if i <= 8:  # +0 → +9 阶段
            if action == "B":  # 如果使用祝福
                bless_vec[i] = 1  # 当前状态消耗 1 颗祝福
                total_vec[i] = cost_bless  # 当前状态总成本为祝福成本

            elif action == "S":  # 如果使用灵魂
                soul_vec[i] = 1  # 当前状态消耗 1 颗灵魂
                total_vec[i] = cost_soul  # 当前状态总成本为灵魂成本

        else:  # +9 → +15 阶段
            B, S, chaos = level_upgrade_info[i][:3]  # 读取当前等级需要的祝福、灵魂、玛雅数量

            use_protect = protect_flags[i - 9]  # 当前等级是否使用保护符
            use_luck = luck_flags[i - 9]  # 当前等级是否使用幸运符

            success_rate = get_high_level_success_rate(i, use_luck)  # 当前等级成功率
            failure_rate = 1 - success_rate  # 当前等级失败率

            bless_vec[i] = B  # 写入祝福消耗数量
            soul_vec[i] = S  # 写入灵魂消耗数量
            chaos_vec[i] = chaos  # 写入玛雅消耗数量

            if use_luck:  # 如果使用幸运符
                luck_vec[i] = 1  # 当前状态消耗 1 个幸运符

            if use_protect:  # 如果使用保护符
                protect_vec[i] = 1  # 当前状态消耗 1 个保护符

            if not use_protect:  # 如果没有使用保护符
                item_0_loss_count_vec[i] = failure_rate  # 当前状态失败导致装备消失的期望数量
                item_0_loss_cost_vec[i] = failure_rate * item_0_cost  # 当前状态失败导致装备损失的期望价值

            total_vec[i] = (  # 当前状态一次强化尝试的期望总成本
                B * cost_bless  # 祝福成本
                + S * cost_soul  # 灵魂成本
                + chaos * chaos_cost  # 玛雅成本
                + luck_vec[i] * talisman_luck_cost  # 幸运符成本
                + protect_vec[i] * talisman_protect_cost  # 保护符成本
                + item_0_loss_cost_vec[i]  # 装备损失期望成本
            )

    return (  # 返回所有成本向量
        bless_vec,
        soul_vec,
        chaos_vec,
        luck_vec,
        protect_vec,
        item_0_loss_count_vec,
        item_0_loss_cost_vec,
        total_vec,
    )


# ============================================================
# 6. 评估单个策略
# ============================================================

def evaluate_strategy(strategy_info):
    """计算单个策略的各类期望消耗。"""

    strategy = strategy_info["strategy"]  # 读取完整强化策略
    protect_flags = strategy_info.get("protect_flags", [False] * 6)  # 读取保护符方案
    luck_flags = strategy_info.get("luck_flags", [False] * 6)  # 读取幸运符方案

    Q = build_transition_matrix(strategy, protect_flags, luck_flags)  # 构建转移矩阵

    I = np.eye(absorbing_state + 1)  # 构建 16×16 单位矩阵

    N = np.linalg.inv(I - Q)  # 计算吸收型马尔可夫链基本矩阵

    (
        bless_vec,
        soul_vec,
        chaos_vec,
        luck_vec,
        protect_vec,
        item_0_loss_count_vec,
        item_0_loss_cost_vec,
        total_vec,
    ) = build_cost_vectors(strategy, protect_flags, luck_flags)  # 构建各类成本向量

    expected_bless = (N @ bless_vec)[0]  # 从 +0 出发的期望祝福消耗
    expected_soul = (N @ soul_vec)[0]  # 从 +0 出发的期望灵魂消耗
    expected_chaos = (N @ chaos_vec)[0]  # 从 +0 出发的期望玛雅消耗
    expected_luck = (N @ luck_vec)[0]  # 从 +0 出发的期望幸运符消耗
    expected_protect = (N @ protect_vec)[0]  # 从 +0 出发的期望保护符消耗
    expected_item_0_loss_count = (N @ item_0_loss_count_vec)[0]  # 从 +0 出发的期望装备损失数量
    expected_item_0_loss_cost = (N @ item_0_loss_cost_vec)[0]  # 从 +0 出发的期望装备损失价值
    expected_total = (N @ total_vec)[0]  # 从 +0 出发的期望总成本

    protect_str = "".join(["1" if x else "0" for x in protect_flags])  # 将保护符方案转为字符串
    luck_str = "".join(["1" if x else "0" for x in luck_flags])  # 将幸运符方案转为字符串

    return {  # 返回当前策略的计算结果
        "strategy": "".join(strategy[:9]),  # 输出 +0 → +9 的 B/S 策略
        "protect_flags": protect_str,  # 输出 +9 → +15 的保护符使用方案
        "luck_flags": luck_str,  # 输出 +9 → +15 的幸运符使用方案
        "expected_bless": expected_bless,  # 期望祝福消耗
        "expected_soul": expected_soul,  # 期望灵魂消耗
        "expected_chaos": expected_chaos,  # 期望玛雅消耗
        "expected_luck": expected_luck,  # 期望幸运符消耗
        "expected_protect": expected_protect,  # 期望保护符消耗
        "expected_item_0_loss_count": expected_item_0_loss_count,  # 期望损失装备数量
        "expected_item_0_loss_cost": expected_item_0_loss_cost,  # 期望损失装备价值
        "expected_total_cost": expected_total,  # 期望总成本
    }


# ============================================================
# 7. 枚举必要组合策略
# ============================================================

def compute_optimal():
    """枚举必要策略组合并排序。"""

    results = []  # 用于存储所有策略的计算结果

    for b_s in itertools.product(["B", "S"], repeat=6):  # 枚举 +0 → +6 的 64 种 B/S 策略
        strategy = list(b_s) + ["S"] * 9  # 拼接完整策略，+6 → +15 默认使用 S

        for protect_flags in itertools.product([False, True], repeat=6):  # 枚举 6 个阶段是否使用保护符
            for luck_flags in itertools.product([False, True], repeat=6):  # 枚举 6 个阶段是否使用幸运符

                strategy_info = {  # 组装当前完整策略信息
                    "strategy": strategy,  # 当前 B/S 强化策略
                    "protect_flags": list(protect_flags),  # 当前保护符方案
                    "luck_flags": list(luck_flags),  # 当前幸运符方案
                }

                res = evaluate_strategy(strategy_info)  # 计算当前策略的期望消耗

                results.append(res)  # 将结果加入列表

    df = pd.DataFrame(results)  # 将所有策略结果转换为表格

    df = df.sort_values("expected_total_cost").reset_index(drop=True)  # 按总期望成本升序排序

    df.insert(0, "rank", range(1, len(df) + 1))  # 增加排名列

    return df  # 返回排序后的结果表


# ============================================================
# 8. 导出最优策略转移矩阵和成本向量
# ============================================================

def export_best_strategy_matrix_and_vectors(df):
    """导出最优策略的转移矩阵和成本向量。"""

    best = df.iloc[0]  # 取排名第 1 的最优策略

    best_strategy = list(best["strategy"]) + ["S"] * 6  # 还原最优策略的完整 15 位 B/S 动作

    best_protect_flags = [x == "1" for x in best["protect_flags"]]  # 将保护符字符串还原为布尔列表

    best_luck_flags = [x == "1" for x in best["luck_flags"]]  # 将幸运符字符串还原为布尔列表

    Q = build_transition_matrix(  # 构建最优策略的转移矩阵
        best_strategy,
        best_protect_flags,
        best_luck_flags,
    )

    (
        bless_vec,
        soul_vec,
        chaos_vec,
        luck_vec,
        protect_vec,
        item_0_loss_count_vec,
        item_0_loss_cost_vec,
        total_vec,
    ) = build_cost_vectors(  # 构建最优策略的成本向量
        best_strategy,
        best_protect_flags,
        best_luck_flags,
    )

    state_labels = [f"+{i}" for i in range(absorbing_state + 1)]  # 生成状态标签 +0 到 +15

    df_Q = pd.DataFrame(Q, index=state_labels, columns=state_labels)  # 将矩阵转成 DataFrame

    df_Q.to_csv(  # 导出最优策略转移矩阵
        "best_strategy_transition_matrix.csv",
        encoding="utf-8-sig",
    )

    df_vectors = pd.DataFrame({  # 整理最优策略的各类成本向量
        "state": state_labels,  # 状态标签
        "bless_vec": bless_vec,  # 祝福消耗向量
        "soul_vec": soul_vec,  # 灵魂消耗向量
        "chaos_vec": chaos_vec,  # 玛雅消耗向量
        "luck_vec": luck_vec,  # 幸运符消耗向量
        "protect_vec": protect_vec,  # 保护符消耗向量
        "item_0_loss_count_vec": item_0_loss_count_vec,  # 装备损失数量向量
        "item_0_loss_cost_vec": item_0_loss_cost_vec,  # 装备损失价值向量
        "total_cost_vec": total_vec,  # 总成本向量
    })

    df_vectors.to_csv(  # 导出最优策略成本向量
        "best_strategy_cost_vectors.csv",
        index=False,
        encoding="utf-8-sig",
    )


# ============================================================
# 9. 主程序
# ============================================================

if __name__ == "__main__":  # 只有直接运行本文件时才执行以下代码

    df_all = compute_optimal()  # 计算所有必要策略组合

    df_all.to_csv(  # 导出所有策略的期望成本结果
        "all_strategy_expected_costs.csv",
        index=False,
        encoding="utf-8-sig",
    )

    export_best_strategy_matrix_and_vectors(df_all)  # 导出最优策略矩阵和成本向量

    print("前5条最优策略：")  # 打印提示信息
    print(df_all.head())  # 打印前 5 条最优策略

    print("\n已导出：")  # 打印导出提示
    print("1. all_strategy_expected_costs.csv")  # 所有策略结果文件
    print("2. best_strategy_transition_matrix.csv")  # 最优策略转移矩阵文件
    print("3. best_strategy_cost_vectors.csv")  # 最优策略成本向量文件