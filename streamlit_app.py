"""Streamlit app for Carnival casino EV decisions."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from carnival_ev_strategy import (
    DEFAULT_CONFIG,
    calculate_expected_value_breakdown,
    infer_reward_bundle,
    recommend_strategy,
)


def _format_currency(value: float) -> str:
    return f"${value:,.2f}"


def _next_threshold(current_tier: str) -> tuple[str, int]:
    if current_tier == "basic":
        return ("premier", DEFAULT_CONFIG.premier_tipping_point)
    if current_tier == "premier":
        return ("elite", DEFAULT_CONFIG.elite_tipping_point)
    if current_tier == "elite":
        return ("echo", DEFAULT_CONFIG.echo_cap_point)
    return ("echo", DEFAULT_CONFIG.echo_cap_point)


st.set_page_config(
    page_title="Player EV Decision Engine",
    page_icon="🎰",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .stApp {
        background:
            radial-gradient(circle at top left, rgba(15, 76, 129, 0.10), transparent 28%),
            linear-gradient(180deg, #f6f8fb 0%, #eef3f8 100%);
    }
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1400px;
    }
    h1, h2, h3 {
        letter-spacing: -0.02em;
    }
    .dashboard-hero {
        background: linear-gradient(135deg, #0f172a 0%, #123a63 100%);
        color: white;
        border-radius: 20px;
        padding: 1.4rem 1.6rem;
        margin-bottom: 1.25rem;
        box-shadow: 0 18px 40px rgba(15, 23, 42, 0.18);
    }
    .hero-kicker {
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        opacity: 0.72;
        margin-bottom: 0.45rem;
    }
    .hero-title {
        font-size: 2rem;
        font-weight: 700;
        margin-bottom: 0.35rem;
    }
    .hero-subtitle {
        font-size: 1rem;
        opacity: 0.84;
        max-width: 820px;
    }
    .section-label {
        font-size: 0.82rem;
        text-transform: uppercase;
        letter-spacing: 0.10em;
        color: #46607a;
        margin-top: 0.35rem;
        margin-bottom: 0.25rem;
        font-weight: 700;
    }
    .section-title {
        font-size: 1.3rem;
        font-weight: 700;
        color: #11263c;
        margin-bottom: 0.9rem;
    }
    .panel-card {
        background: rgba(255, 255, 255, 0.88);
        border: 1px solid rgba(17, 38, 60, 0.08);
        border-radius: 18px;
        padding: 1rem 1.1rem;
        box-shadow: 0 10px 24px rgba(15, 23, 42, 0.06);
        margin-bottom: 1rem;
    }
    .subtle-copy {
        color: #587089;
        font-size: 0.96rem;
        margin-bottom: 0.2rem;
    }
    div[data-testid="metric-container"] {
        background: rgba(255, 255, 255, 0.88);
        border: 1px solid rgba(17, 38, 60, 0.08);
        padding: 1rem 1rem 0.9rem 1rem;
        border-radius: 18px;
        box-shadow: 0 10px 24px rgba(15, 23, 42, 0.06);
    }
    div[data-testid="metric-container"] label {
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #ffffff 0%, #f4f7fb 100%);
        border-right: 1px solid rgba(17, 38, 60, 0.06);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="dashboard-hero">
        <div class="hero-kicker">Casino Analytics</div>
        <div class="hero-title">Player EV Decision Engine</div>
        <div class="hero-subtitle">
            A decision-support tool for evaluating expected value, tier progression, and reward
            optimization.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("## About This Project")

st.info(
    """
    This app was built as a data-driven decision support tool using publicly shared player
    experiences and reward data.

    The goal is to help users better understand expected value (EV), tier progression, and
    trade-offs when engaging with casino reward systems.

    It is not affiliated with any casino and does not access or reverse-engineer proprietary
    systems.
    """
)

st.markdown("## Community Contribution")

st.success(
    """
    This model is inspired by aggregated, anonymized data points shared by the player
    community.

    If you have additional data points or experiences, future versions of this tool could
    incorporate them to improve accuracy and transparency.
    """
)

with st.sidebar:
    st.header("Player Inputs")
    casino_points = st.number_input(
        "Casino points",
        min_value=0,
        value=7600,
        step=100,
        help="Approximate casino points earned on the sailing.",
    )
    gameplay_type = st.selectbox(
        "Gameplay type",
        options=["slots", "tables"],
        index=0,
        help="Slots get faster effective tier progress than tables.",
    )
    st.divider()
    st.subheader("Optional Overrides")
    use_manual_rewards = st.toggle(
        "Override inferred rewards",
        value=False,
        help="Use this if you want to plug in a known offer instead of the inferred tier bundle.",
    )

baseline_bundle = infer_reward_bundle(
    casino_points=casino_points,
    gameplay_type=gameplay_type,
    config=DEFAULT_CONFIG,
)

if use_manual_rewards:
    with st.sidebar:
        freeplay_rewards = st.number_input(
            "Freeplay reward",
            min_value=0.0,
            value=float(baseline_bundle.freeplay),
            step=25.0,
        )
        obc_rewards = st.number_input(
            "OBC reward",
            min_value=0.0,
            value=float(baseline_bundle.obc),
            step=25.0,
        )
        beverage_benefit = st.selectbox(
            "Beverage benefit",
            options=[
                "casino_only",
                "everywhere_member_only",
                "everywhere_member_companion",
                "none",
            ],
            index=[
                "casino_only",
                "everywhere_member_only",
                "everywhere_member_companion",
                "none",
            ].index(baseline_bundle.beverage_benefit),
        )
    bundle = infer_reward_bundle(
        casino_points=casino_points,
        gameplay_type=gameplay_type,
        freeplay_rewards=freeplay_rewards,
        obc_rewards=obc_rewards,
        beverage_benefit=beverage_benefit,
        config=DEFAULT_CONFIG,
    )
else:
    bundle = baseline_bundle

breakdown = calculate_expected_value_breakdown(
    casino_points=casino_points,
    gameplay_type=gameplay_type,
    freeplay_rewards=bundle.freeplay,
    obc_rewards=bundle.obc,
    beverage_benefit=bundle.beverage_benefit,
    config=DEFAULT_CONFIG,
)

decision = recommend_strategy(
    casino_points=casino_points,
    gameplay_type=gameplay_type,
    freeplay_rewards=bundle.freeplay,
    obc_rewards=bundle.obc,
    beverage_benefit=bundle.beverage_benefit,
    config=DEFAULT_CONFIG,
)

expected_value = breakdown["expected_value"]
best_path = decision["best_path"]
marginal_ev = best_path["marginal_ev"] if best_path else 0.0
continue_to_next_tier_ev = expected_value + marginal_ev
reward_breakdown = breakdown["reward_breakdown"]

if marginal_ev > 0 and best_path:
    recommendation = (
        f"Push to {best_path['target_tier'].title()} "
        f"— +${marginal_ev:,.2f} Expected Gain Remaining"
    )
    explanation = (
        "You are currently at a loss, but reaching the next tier adds "
        f"+${marginal_ev:,.2f} in expected value."
    )
    zone_message = ("success", "Positive progression zone")
else:
    recommendation = "Stop Playing — Negative Return Zone"
    explanation = "Further play is unlikely to recover losses or improve rewards."
    zone_message = ("error", "Negative return zone")

st.markdown('<div class="section-label">Overview</div>', unsafe_allow_html=True)
st.markdown('<div class="section-title">Decision Snapshot</div>', unsafe_allow_html=True)

top_metrics = st.columns(4)
top_metrics[0].metric("Inferred Tier", breakdown["tier"].title())
top_metrics[1].metric("Effective Points", f"{breakdown['effective_points']:,.0f}")
top_metrics[2].metric("Reward Value", _format_currency(reward_breakdown["total_reward_value"]))
top_metrics[3].metric("Expected Value", _format_currency(expected_value))

main_col, side_col = st.columns([1.65, 1], gap="large")

with main_col:
    st.markdown('<div class="section-label">Decision</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Recommendation Engine</div>', unsafe_allow_html=True)

    zone_fn = st.success if zone_message[0] == "success" else st.error
    zone_fn(zone_message[1])
    st.info(recommendation)
    st.markdown(f'<div class="subtle-copy">{explanation}</div>', unsafe_allow_html=True)

    decision_metrics = st.columns(2)
    decision_metrics[0].metric("Total EV", _format_currency(expected_value))
    decision_metrics[1].metric("Marginal EV to Next Tier", _format_currency(marginal_ev))

    st.markdown('<div class="section-label">Simulation</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Decision Simulator</div>', unsafe_allow_html=True)
    st.caption(
        "Compare the expected value of stopping now versus continuing to the next tier milestone."
    )

    simulator_col1, simulator_col2 = st.columns(2, gap="large")
    with simulator_col1:
        st.markdown('<div class="panel-card">', unsafe_allow_html=True)
        st.markdown("### Stop Now")
        st.metric("Current Total EV", _format_currency(expected_value))
        st.markdown("</div>", unsafe_allow_html=True)

    with simulator_col2:
        st.markdown('<div class="panel-card">', unsafe_allow_html=True)
        st.markdown("### Continue Playing")
        st.metric("EV at Next Tier", _format_currency(continue_to_next_tier_ev))
        st.metric("Marginal EV Gain", _format_currency(marginal_ev))
        st.markdown("</div>", unsafe_allow_html=True)

    simulator_metrics = st.columns(3)
    simulator_metrics[0].metric("Stop Now EV", _format_currency(expected_value))
    simulator_metrics[1].metric("Continue EV", _format_currency(continue_to_next_tier_ev))
    simulator_metrics[2].metric("Delta", _format_currency(marginal_ev))

    st.markdown('<div class="section-label">Comparison</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Decision Comparison</div>', unsafe_allow_html=True)
    comparison_metrics = st.columns(2)
    comparison_metrics[0].metric("Stop Now EV", _format_currency(expected_value))
    comparison_metrics[1].metric(
        "Continue to Next Tier EV",
        _format_currency(continue_to_next_tier_ev),
    )

    st.markdown('<div class="section-label">Progress</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Tier Progress</div>', unsafe_allow_html=True)
    next_tier, next_threshold = _next_threshold(breakdown["tier"])
    if breakdown["tier"] == "echo":
        st.progress(100, text="At or beyond the Echo cap.")
    else:
        current_threshold = 0
        if breakdown["tier"] == "premier":
            current_threshold = DEFAULT_CONFIG.premier_tipping_point
        elif breakdown["tier"] == "elite":
            current_threshold = DEFAULT_CONFIG.elite_tipping_point

        progress_span = max(next_threshold - current_threshold, 1)
        progress_value = int(
            max(
                0.0,
                min(
                    1.0,
                    (breakdown["effective_points"] - current_threshold) / progress_span,
                ),
            )
            * 100
        )
        st.progress(
            progress_value,
            text=(
                f"{breakdown['effective_points']:,.0f} effective points. "
                f"Next milestone: {next_tier.title()} at {next_threshold:,}."
            ),
        )

    if best_path:
        next_path_metrics = st.columns(3)
        next_path_metrics[0].metric("Target Tier", best_path["target_tier"].title())
        next_path_metrics[1].metric("Points Needed", f"{best_path['raw_points_needed']:,.0f}")
        next_path_metrics[2].metric("Marginal EV", _format_currency(best_path["marginal_ev"]))

    st.markdown('<div class="section-label">Visuals</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Analytics View</div>', unsafe_allow_html=True)
    chart_col1, chart_col2 = st.columns(2, gap="large")

    with chart_col1:
        st.markdown('<div class="panel-card">', unsafe_allow_html=True)
        st.caption("Value vs Cost")
        ev_chart = pd.DataFrame(
            {
                "Amount": [
                    reward_breakdown["freeplay_value"],
                    reward_breakdown["obc_value"],
                    reward_breakdown["beverage_value"],
                    breakdown["gaming_cost"],
                ]
            },
            index=["Freeplay Value", "OBC Value", "Beverage Value", "Gaming Cost"],
        )
        st.bar_chart(ev_chart, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with chart_col2:
        st.markdown('<div class="panel-card">', unsafe_allow_html=True)
        st.caption("Tier Milestones")
        milestone_chart = pd.DataFrame(
            {
                "Threshold": [
                    DEFAULT_CONFIG.premier_tipping_point,
                    DEFAULT_CONFIG.elite_tipping_point,
                    DEFAULT_CONFIG.echo_cap_point,
                    breakdown["effective_points"],
                ]
            },
            index=["Premier", "Elite", "Echo Cap", "Current"],
        )
        st.bar_chart(milestone_chart, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

with side_col:
    st.markdown('<div class="section-label">Inputs</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Offer Profile</div>', unsafe_allow_html=True)
    st.markdown('<div class="panel-card">', unsafe_allow_html=True)
    st.caption("Inferred Offer Bundle")
    st.write(
        {
            "freeplay": _format_currency(bundle.freeplay),
            "obc": _format_currency(bundle.obc),
            "beverage_benefit": bundle.beverage_benefit,
        }
    )
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="section-label">Economics</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">EV Breakdown</div>', unsafe_allow_html=True)
    st.markdown('<div class="panel-card">', unsafe_allow_html=True)
    st.caption("Current Offer Value")
    st.write(
        {
            "freeplay_value": _format_currency(reward_breakdown["freeplay_value"]),
            "obc_value": _format_currency(reward_breakdown["obc_value"]),
            "beverage_value": _format_currency(reward_breakdown["beverage_value"]),
            "gaming_cost": _format_currency(breakdown["gaming_cost"]),
        }
    )
    st.markdown("</div>", unsafe_allow_html=True)

    with st.expander("Model Assumptions"):
        st.write(
            {
                "premier_tipping_point": DEFAULT_CONFIG.premier_tipping_point,
                "elite_tipping_point": DEFAULT_CONFIG.elite_tipping_point,
                "echo_cap_point": DEFAULT_CONFIG.echo_cap_point,
                "gameplay_multiplier": DEFAULT_CONFIG.gameplay_multiplier,
                "cost_per_point": DEFAULT_CONFIG.cost_per_point,
                "freeplay_redemption_rate": DEFAULT_CONFIG.freeplay_redemption_rate,
                "obc_redemption_rate": DEFAULT_CONFIG.obc_redemption_rate,
                "beverage_usage_rate": DEFAULT_CONFIG.beverage_usage_rate,
            }
        )

st.markdown(
    """
    <div class="section-label">Run Locally</div>
    """,
    unsafe_allow_html=True,
)
st.code(
    "streamlit run /Users/jessicadudzinski/Documents/Portfolio\\ Projects/streamlit_app.py",
    language="bash",
)

st.markdown(
    """
    <div class="section-label">Disclaimer</div>
    <div class="section-title">Disclaimer</div>
    """,
    unsafe_allow_html=True,
)
st.caption(
    "This tool is a simulated decision-support model built for educational and analytical "
    "purposes only. It does not represent or reverse-engineer any actual casino systems, "
    "algorithms, or proprietary reward structures. All values, thresholds, and outcomes are "
    "hypothetical and intended to demonstrate decision-making using expected value modeling."
)
