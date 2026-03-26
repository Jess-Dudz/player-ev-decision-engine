from carnival_ev_strategy import (
    calculate_expected_value,
    calculate_expected_value_breakdown,
    recommend_strategy,
)


player_points = 7600
gameplay_type = "slots"
current_freeplay = 200
current_obc = 200
beverage_benefit = "Drinks On Us! Everywhere (Member + Companion)"

ev = calculate_expected_value(
    casino_points=player_points,
    gameplay_type=gameplay_type,
    freeplay_rewards=current_freeplay,
    obc_rewards=current_obc,
    beverage_benefit=beverage_benefit,
)

breakdown = calculate_expected_value_breakdown(
    casino_points=player_points,
    gameplay_type=gameplay_type,
    freeplay_rewards=current_freeplay,
    obc_rewards=current_obc,
    beverage_benefit=beverage_benefit,
)

decision = recommend_strategy(
    casino_points=player_points,
    gameplay_type=gameplay_type,
    freeplay_rewards=current_freeplay,
    obc_rewards=current_obc,
    beverage_benefit=beverage_benefit,
)

print(f"Current EV: ${ev:,.2f}")
print(breakdown)
print(decision)
