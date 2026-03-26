"""Decision engine for Carnival casino offer expected value."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Literal, Optional

GameplayType = Literal["slots", "tables"]


@dataclass(frozen=True)
class RewardBundle:
    freeplay: float = 0.0
    obc: float = 0.0
    beverage_benefit: str = "none"


@dataclass(frozen=True)
class EVConfig:
    """Configurable business assumptions for the EV model."""

    elite_tipping_point: int = 8200
    echo_cap_point: int = 40000
    premier_tipping_point: int = 3000
    # Slots reach elite about 85% faster than tables in the project findings.
    gameplay_multiplier: Dict[str, float] = None  # type: ignore[assignment]
    # Median-like reward bundles anchored to the observed project data.
    tier_reward_bundles: Dict[str, RewardBundle] = None  # type: ignore[assignment]
    # Practical cash-equivalent rates for each perk.
    freeplay_redemption_rate: float = 0.95
    obc_redemption_rate: float = 0.85
    beverage_value_map: Dict[str, float] = None  # type: ignore[assignment]
    beverage_usage_rate: float = 0.35
    # Cost model: expected gambling loss needed to earn one point.
    cost_per_point: Dict[str, float] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.gameplay_multiplier is None:
            object.__setattr__(
                self,
                "gameplay_multiplier",
                {
                    "slots": 1.00,
                    "tables": 1.00 / 1.85,
                },
            )
        if self.tier_reward_bundles is None:
            object.__setattr__(
                self,
                "tier_reward_bundles",
                {
                    "basic": RewardBundle(
                        freeplay=0.0,
                        obc=200.0,
                        beverage_benefit="casino_only",
                    ),
                    "premier": RewardBundle(
                        freeplay=50.0,
                        obc=200.0,
                        beverage_benefit="everywhere_member_companion",
                    ),
                    "elite": RewardBundle(
                        freeplay=300.0,
                        obc=200.0,
                        beverage_benefit="everywhere_member_companion",
                    ),
                    "echo": RewardBundle(
                        freeplay=2500.0,
                        obc=500.0,
                        beverage_benefit="everywhere_member_companion",
                    ),
                },
            )
        if self.beverage_value_map is None:
            object.__setattr__(
                self,
                "beverage_value_map",
                {
                    "none": 0.0,
                    "casino_only": 180.0,
                    "everywhere_member_only": 420.0,
                    "everywhere_member_companion": 840.0,
                },
            )
        if self.cost_per_point is None:
            object.__setattr__(
                self,
                "cost_per_point",
                {
                    "slots": 0.10,
                    "tables": 0.08,
                },
            )


DEFAULT_CONFIG = EVConfig()


def _normalize_gameplay(gameplay_type: str) -> str:
    normalized = gameplay_type.strip().lower()
    if normalized not in {"slots", "tables"}:
        raise ValueError("gameplay_type must be 'slots' or 'tables'")
    return normalized


def _normalize_beverage_benefit(beverage_benefit: Optional[str]) -> str:
    if not beverage_benefit:
        return "none"

    normalized = beverage_benefit.strip().lower()
    aliases = {
        "none": "none",
        "casino_only": "casino_only",
        "drinks on us! (casino only)": "casino_only",
        "everywhere_member_only": "everywhere_member_only",
        "drinks on us! everywhere (member only)": "everywhere_member_only",
        "everywhere_member_companion": "everywhere_member_companion",
        "drinks on us! everywhere (member + companion)": "everywhere_member_companion",
    }
    if normalized in aliases:
        return aliases[normalized]

    raise ValueError("Unsupported beverage_benefit value")


def effective_points(
    casino_points: float,
    gameplay_type: GameplayType,
    config: EVConfig = DEFAULT_CONFIG,
) -> float:
    gameplay = _normalize_gameplay(gameplay_type)
    return casino_points * config.gameplay_multiplier[gameplay]


def infer_offer_tier(
    casino_points: float,
    gameplay_type: GameplayType,
    config: EVConfig = DEFAULT_CONFIG,
) -> str:
    progress_points = effective_points(casino_points, gameplay_type, config)

    if progress_points >= config.echo_cap_point:
        return "echo"
    if progress_points >= config.elite_tipping_point:
        return "elite"
    if progress_points >= config.premier_tipping_point:
        return "premier"
    return "basic"


def infer_reward_bundle(
    casino_points: float,
    gameplay_type: GameplayType,
    freeplay_rewards: Optional[float] = None,
    obc_rewards: Optional[float] = None,
    beverage_benefit: Optional[str] = None,
    config: EVConfig = DEFAULT_CONFIG,
) -> RewardBundle:
    tier = infer_offer_tier(casino_points, gameplay_type, config)
    baseline = config.tier_reward_bundles[tier]

    return RewardBundle(
        freeplay=baseline.freeplay if freeplay_rewards is None else freeplay_rewards,
        obc=baseline.obc if obc_rewards is None else obc_rewards,
        beverage_benefit=(
            baseline.beverage_benefit
            if beverage_benefit is None
            else _normalize_beverage_benefit(beverage_benefit)
        ),
    )


def calculate_reward_value(
    bundle: RewardBundle,
    config: EVConfig = DEFAULT_CONFIG,
) -> dict:
    beverage_key = _normalize_beverage_benefit(bundle.beverage_benefit)
    freeplay_value = bundle.freeplay * config.freeplay_redemption_rate
    obc_value = bundle.obc * config.obc_redemption_rate
    beverage_face_value = config.beverage_value_map[beverage_key]
    beverage_value = beverage_face_value * config.beverage_usage_rate
    total_reward_value = freeplay_value + obc_value + beverage_value

    return {
        "freeplay_value": freeplay_value,
        "obc_value": obc_value,
        "beverage_value": beverage_value,
        "total_reward_value": total_reward_value,
    }


def calculate_expected_value_breakdown(
    casino_points: float,
    gameplay_type: GameplayType,
    freeplay_rewards: float,
    obc_rewards: Optional[float] = None,
    beverage_benefit: Optional[str] = None,
    config: EVConfig = DEFAULT_CONFIG,
) -> dict:
    gameplay = _normalize_gameplay(gameplay_type)
    tier = infer_offer_tier(casino_points, gameplay, config)
    bundle = infer_reward_bundle(
        casino_points=casino_points,
        gameplay_type=gameplay,
        freeplay_rewards=freeplay_rewards,
        obc_rewards=obc_rewards,
        beverage_benefit=beverage_benefit,
        config=config,
    )
    reward_breakdown = calculate_reward_value(bundle, config)
    gaming_cost = casino_points * config.cost_per_point[gameplay]
    expected_value = reward_breakdown["total_reward_value"] - gaming_cost

    return {
        "tier": tier,
        "effective_points": effective_points(casino_points, gameplay, config),
        "bundle": bundle,
        "reward_breakdown": reward_breakdown,
        "gaming_cost": gaming_cost,
        "expected_value": expected_value,
    }


def calculate_expected_value(
    casino_points: float,
    gameplay_type: GameplayType,
    freeplay_rewards: float,
    obc_rewards: Optional[float] = None,
    beverage_benefit: Optional[str] = None,
    config: EVConfig = DEFAULT_CONFIG,
) -> float:
    """Return EV for the current offer bundle minus estimated gambling cost."""

    breakdown = calculate_expected_value_breakdown(
        casino_points=casino_points,
        gameplay_type=gameplay_type,
        freeplay_rewards=freeplay_rewards,
        obc_rewards=obc_rewards,
        beverage_benefit=beverage_benefit,
        config=config,
    )
    return breakdown["expected_value"]


def _marginal_ev_to_target(
    casino_points: float,
    gameplay_type: GameplayType,
    current_bundle: RewardBundle,
    target_tier: str,
    target_effective_points: int,
    config: EVConfig = DEFAULT_CONFIG,
) -> Optional[dict]:
    gameplay = _normalize_gameplay(gameplay_type)
    current_effective_points = effective_points(casino_points, gameplay, config)

    if current_effective_points >= target_effective_points:
        return None

    multiplier = config.gameplay_multiplier[gameplay]
    raw_points_needed = (target_effective_points - current_effective_points) / multiplier
    target_bundle = config.tier_reward_bundles[target_tier]

    current_reward_value = calculate_reward_value(current_bundle, config)["total_reward_value"]
    target_reward_value = calculate_reward_value(target_bundle, config)["total_reward_value"]
    incremental_reward_value = max(target_reward_value - current_reward_value, 0.0)
    marginal_cost = raw_points_needed * config.cost_per_point[gameplay]
    marginal_ev = incremental_reward_value - marginal_cost

    return {
        "target_tier": target_tier,
        "target_effective_points": target_effective_points,
        "raw_points_needed": raw_points_needed,
        "incremental_reward_value": incremental_reward_value,
        "marginal_cost": marginal_cost,
        "marginal_ev": marginal_ev,
    }


def recommend_strategy(
    casino_points: float,
    gameplay_type: GameplayType,
    freeplay_rewards: float,
    obc_rewards: Optional[float] = None,
    beverage_benefit: Optional[str] = None,
    config: EVConfig = DEFAULT_CONFIG,
) -> dict:
    """Recommend continue/stop based on whether marginal EV is positive."""

    gameplay = _normalize_gameplay(gameplay_type)
    current_effective_points = effective_points(casino_points, gameplay, config)
    current_bundle = infer_reward_bundle(
        casino_points=casino_points,
        gameplay_type=gameplay,
        freeplay_rewards=freeplay_rewards,
        obc_rewards=obc_rewards,
        beverage_benefit=beverage_benefit,
        config=config,
    )
    current_breakdown = calculate_expected_value_breakdown(
        casino_points=casino_points,
        gameplay_type=gameplay,
        freeplay_rewards=current_bundle.freeplay,
        obc_rewards=current_bundle.obc,
        beverage_benefit=current_bundle.beverage_benefit,
        config=config,
    )

    candidate_paths = [
        _marginal_ev_to_target(
            casino_points=casino_points,
            gameplay_type=gameplay,
            current_bundle=current_bundle,
            target_tier="elite",
            target_effective_points=config.elite_tipping_point,
            config=config,
        ),
        _marginal_ev_to_target(
            casino_points=casino_points,
            gameplay_type=gameplay,
            current_bundle=current_bundle,
            target_tier="echo",
            target_effective_points=config.echo_cap_point,
            config=config,
        ),
    ]
    candidate_paths = [path for path in candidate_paths if path is not None]
    best_path = max(candidate_paths, key=lambda path: path["marginal_ev"], default=None)

    current_ev = current_breakdown["expected_value"]
    marginal_ev = best_path["marginal_ev"] if best_path else 0.0

    if marginal_ev > 0:
        return {
            "recommendation": "Continue Playing",
            "reason": (
                "You are currently at a loss, but reaching the next tier adds "
                f"+${marginal_ev:.2f} in expected value."
            ),
            "current_tier": current_breakdown["tier"],
            "current_effective_points": current_effective_points,
            "current_ev": current_ev,
            "current_breakdown": current_breakdown,
            "best_path": best_path,
        }

    return {
        "recommendation": "Stop Playing",
        "reason": "Further play is unlikely to recover losses or improve rewards.",
        "current_tier": current_breakdown["tier"],
        "current_effective_points": current_effective_points,
        "current_ev": current_ev,
        "current_breakdown": current_breakdown,
        "best_path": best_path,
    }
