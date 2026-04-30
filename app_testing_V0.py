# app.py
# MU Online Item Upgrade Optimizer with Streamlit

import itertools
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st


# ============================================================
# 1. Core Model
# ============================================================

cost_soul = 1
transient_states = list(range(9))
absorbing_state = 9


def fail_state(i):
    if i == 0:
        return 0
    elif 1 <= i <= 6:
        return i - 1
    elif i in [7, 8]:
        return 0
    else:
        raise ValueError("Invalid state")


def generate_strategies():
    strategies = []
    for choices in itertools.product(["B", "S"], repeat=6):
        strategy = list(choices) + ["S", "S", "S"]
        strategies.append(strategy)
    return strategies


def build_transition_matrix(strategy, p_soul):
    q_soul = 1 - p_soul
    Q = np.zeros((9, 9))

    for i in transient_states:
        action = strategy[i]

        if action == "B":
            next_state = i + 1
            if next_state < absorbing_state:
                Q[i, next_state] = 1.0

        elif action == "S":
            success_state = i + 1
            failure_state = fail_state(i)

            if success_state < absorbing_state:
                Q[i, success_state] += p_soul

            if failure_state < absorbing_state:
                Q[i, failure_state] += q_soul

    return Q


def evaluate_strategy(strategy, p_soul, cost_bless):
    Q = build_transition_matrix(strategy, p_soul)
    N = np.linalg.inv(np.eye(9) - Q)

    bless_cost_vector = np.zeros(9)
    soul_cost_vector = np.zeros(9)
    total_cost_vector = np.zeros(9)

    for i in transient_states:
        if strategy[i] == "B":
            bless_cost_vector[i] = 1
            total_cost_vector[i] = cost_bless
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


def find_optimal_strategy(p_soul, cost_bless):
    results = []

    for strategy in generate_strategies():
        result = evaluate_strategy(strategy, p_soul, cost_bless)
        results.append(result)

    df = pd.DataFrame(results)
    df = df.sort_values(by="expected_total_cost").reset_index(drop=True)
    df.insert(0, "rank", range(1, len(df) + 1))

    return df


def generate_switching_curve(p_soul, cost_min, cost_max, num_points):
    cost_values = np.linspace(cost_min, cost_max, num_points)

    expected_costs = []
    best_strategies = []

    for cost_bless in cost_values:
        result_df = find_optimal_strategy(p_soul, cost_bless)
        best = result_df.iloc[0]

        expected_costs.append(best["expected_total_cost"])
        best_strategies.append(best["strategy"])

    return cost_values, np.array(expected_costs), best_strategies


def find_switching_points(cost_values, expected_costs, best_strategies):
    switch_points = []

    for i in range(1, len(best_strategies)):
        if best_strategies[i] != best_strategies[i - 1]:
            switch_points.append({
                "index": i,
                "cost_bless": cost_values[i],
                "expected_total_cost": expected_costs[i],
                "from_strategy": best_strategies[i - 1],
                "to_strategy": best_strategies[i]
            })

    return pd.DataFrame(switch_points)


# ============================================================
# 2. Plot Functions
# ============================================================

def plot_switching_curve(cost_values, expected_costs, switch_df, p_soul):
    fig, ax = plt.subplots(figsize=(10, 6))

    ax.plot(
        cost_values,
        expected_costs,
        linewidth=2,
        label="Optimal expected cost"
    )

    for _, row in switch_df.iterrows():
        x = row["cost_bless"]
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

    ax.set_xlabel("Relative Bless Cost cost_bless")
    ax.set_ylabel("Minimum Expected Total Cost")
    ax.set_title(f"Strategy Switching Curve, p_soul = {p_soul}")
    ax.grid(True, alpha=0.3)
    ax.legend()

    fig.tight_layout()
    return fig


# ============================================================
# 3. Streamlit App
# ============================================================

st.set_page_config(
    page_title="MU Online Upgrade Optimizer",
    layout="wide"
)

st.title("MU Online Item Upgrade Optimizer")
st.caption("Markov Chain + Bellman-style Strategy Optimization")

st.sidebar.header("Parameter Settings")

item_type = st.sidebar.selectbox(
    "Item Type",
    [
        "Custom",
        "Socket item, p = 0.40",
        "Excellent set, p = 0.50",
        "Normal item, p = 0.60",
        "Lucky socket item, p = 0.65",
        "Lucky excellent set, p = 0.75",
        "Lucky normal item, p = 0.85"
    ]
)

preset_map = {
    "Socket item, p = 0.40": 0.40,
    "Excellent set, p = 0.50": 0.50,
    "Normal item, p = 0.60": 0.60,
    "Lucky socket item, p = 0.65": 0.65,
    "Lucky excellent set, p = 0.75": 0.75,
    "Lucky normal item, p = 0.85": 0.85
}

if item_type == "Custom":
    p_soul = st.sidebar.slider(
        "Soul Success Probability p_soul",
        min_value=0.01,
        max_value=0.99,
        value=0.50,
        step=0.01
    )
else:
    p_soul = preset_map[item_type]
    st.sidebar.info(f"Using preset p_soul = {p_soul}")

cost_bless = st.sidebar.slider(
    "Relative Bless Cost cost_bless",
    min_value=0.50,
    max_value=15.00,
    value=5.29,
    step=0.01
)

st.sidebar.header("Curve Settings")

cost_min = st.sidebar.number_input(
    "Minimum cost_bless",
    min_value=0.1,
    max_value=50.0,
    value=0.5,
    step=0.1
)

cost_max = st.sidebar.number_input(
    "Maximum cost_bless",
    min_value=0.1,
    max_value=50.0,
    value=15.0,
    step=0.1
)

num_points = st.sidebar.slider(
    "Number of curve points",
    min_value=50,
    max_value=1000,
    value=300,
    step=50
)

run_button = st.sidebar.button("Run Optimization")


# ============================================================
# 4. Main Display
# ============================================================

if run_button:

    result_df = find_optimal_strategy(p_soul, cost_bless)
    best = result_df.iloc[0]

    soul_only_result = evaluate_strategy(
        list("SSSSSSSSS"),
        p_soul,
        cost_bless
    )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("p_soul", f"{p_soul:.2f}")
    col2.metric("cost_bless", f"{cost_bless:.4f}")
    col3.metric("Best Strategy", best["strategy"])
    col4.metric("Minimum Cost", f"{best['expected_total_cost']:.4f}")

    st.subheader("Optimal Strategy")

    best_df = pd.DataFrame([{
        "rank": best["rank"],
        "strategy": best["strategy"],
        "expected_bless": best["expected_bless"],
        "expected_soul": best["expected_soul"],
        "expected_total_cost": best["expected_total_cost"],
        "soul_only_expected_total_cost": soul_only_result["expected_total_cost"],
        "cost_reduction_vs_soul_only": (
            soul_only_result["expected_total_cost"] - best["expected_total_cost"]
        )
    }])

    st.dataframe(best_df, use_container_width=True)

    st.subheader("Top 10 Strategies")

    st.dataframe(
        result_df.head(10),
        use_container_width=True
    )

    csv_result = result_df.to_csv(index=False, encoding="utf-8-sig")

    st.download_button(
        label="Download Strategy Results CSV",
        data=csv_result,
        file_name="strategy_results_64.csv",
        mime="text/csv"
    )

    st.subheader("Strategy Switching Curve")

    cost_values, expected_costs, best_strategies = generate_switching_curve(
        p_soul=p_soul,
        cost_min=cost_min,
        cost_max=cost_max,
        num_points=num_points
    )

    switch_df = find_switching_points(
        cost_values,
        expected_costs,
        best_strategies
    )

    fig = plot_switching_curve(
        cost_values,
        expected_costs,
        switch_df,
        p_soul
    )

    st.pyplot(fig)

    curve_df = pd.DataFrame({
        "cost_bless": cost_values,
        "expected_total_cost": expected_costs,
        "best_strategy": best_strategies
    })

    st.download_button(
        label="Download Curve Data CSV",
        data=curve_df.to_csv(index=False, encoding="utf-8-sig"),
        file_name="strategy_switching_curve.csv",
        mime="text/csv"
    )

    st.subheader("Strategy Switching Points")

    if switch_df.empty:
        st.info("No strategy switching point found in the selected range.")
    else:
        st.dataframe(switch_df, use_container_width=True)

        st.download_button(
            label="Download Switching Points CSV",
            data=switch_df.to_csv(index=False, encoding="utf-8-sig"),
            file_name="strategy_switching_points.csv",
            mime="text/csv"
        )

else:
    st.info("Set parameters on the left and click **Run Optimization**.")
