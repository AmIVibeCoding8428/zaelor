"""Asset Allocation Engine.

Deterministic, rule-based. Given age, retirement horizon, risk appetite,
and repatriation intent, recommends a percentage split across asset
categories. No AI involved — Claude only turns this structured output
into prose downstream.
"""

GOLD_CATEGORY_NAME = "Gold ETF/Mutual Fund"

RISK_ADJUSTMENTS = {
    "conservative": -15,
    "moderate": 0,
    "aggressive": 15,
}

# Share of the "growth" bucket (Indian Equity + International ETFs + REITs)
GROWTH_SHARES = {
    False: {"Indian Equity": 0.60, "International ETFs": 0.25, "REITs/Real Estate": 0.15},
    True: {"Indian Equity": 0.68, "International ETFs": 0.17, "REITs/Real Estate": 0.15},
}

# Share of the "stable" bucket (Indian Debt + Gold + Cash), by risk appetite
STABLE_SHARES = {
    "conservative": {"Indian Debt": 0.50, "Gold": 0.25, "Cash": 0.25},
    "moderate": {"Indian Debt": 0.55, "Gold": 0.25, "Cash": 0.20},
    "aggressive": {"Indian Debt": 0.60, "Gold": 0.25, "Cash": 0.15},
}


def _years_to_retirement(age, target_retirement_age):
    return max(target_retirement_age - age, 0)


def _growth_allocation_pct(years_to_retirement, risk_appetite):
    base = 15 + years_to_retirement * 2.4
    base = min(max(base, 15), 80)
    adjustment = RISK_ADJUSTMENTS.get(risk_appetite, 0)
    return min(max(base + adjustment, 10), 90)


def _round_and_fix_to_100(raw_allocations):
    rounded = {category: round(value) for category, value in raw_allocations.items()}
    diff = 100 - sum(rounded.values())
    if diff != 0:
        largest_category = max(rounded, key=rounded.get)
        rounded[largest_category] += diff
    return rounded


def _build_reasons(allocations, years_to_retirement, risk_appetite, repatriation_intent):
    horizon_phrase = f"{years_to_retirement}+ years to retirement" if years_to_retirement >= 20 \
        else f"{years_to_retirement} years to retirement"
    risk_label = {
        "conservative": "a conservative risk appetite",
        "moderate": "a moderate risk appetite",
        "aggressive": "an aggressive risk appetite",
    }.get(risk_appetite, "a moderate risk appetite")

    return {
        "Indian Equity": (
            f"{allocations['Indian Equity']}% Indian Equity — {horizon_phrase} combined with "
            f"{risk_label} shapes this equity allocation."
        ),
        "International ETFs": (
            f"{allocations['International ETFs']}% International ETFs — adds geographic diversification"
            + (
                ", kept modest since repatriation intent favors building an India-based corpus."
                if repatriation_intent
                else "."
            )
        ),
        "Indian Debt": (
            f"{allocations['Indian Debt']}% Indian Debt — anchors the portfolio with stable, "
            "lower-volatility returns."
        ),
        "Gold": (
            f"{allocations['Gold']}% {GOLD_CATEGORY_NAME} — inflation hedge and diversification "
            "(new Sovereign Gold Bonds are unavailable to NRIs)."
        ),
        "REITs/Real Estate": (
            f"{allocations['REITs/Real Estate']}% REITs/Real Estate — adds real-asset exposure and "
            "income without the liquidity constraints of direct property ownership."
        ),
        "Cash": (
            f"{allocations['Cash']}% Cash — maintains liquidity for near-term needs and market flexibility."
        ),
    }


def generate_asset_allocation(user_input: dict, investment_restrictions: list = None) -> dict:
    """Generate a recommended asset allocation for an NRI user.

    Expected keys in user_input:
        age (int)
        target_retirement_age (int)
        risk_appetite (str): "conservative" | "moderate" | "aggressive"
        repatriation_intent (bool)

    investment_restrictions: optional list of restriction dicts as returned by
        tax_engine.generate_tax_account_layer()["investment_restrictions"].
        The gold category always uses Gold ETF/Mutual Fund — new Sovereign Gold
        Bonds are never offered as an investment option to NRIs, regardless of
        whether this list is supplied.
    """
    age = user_input["age"]
    target_retirement_age = user_input["target_retirement_age"]
    risk_appetite = user_input.get("risk_appetite", "moderate")
    if risk_appetite not in RISK_ADJUSTMENTS:
        risk_appetite = "moderate"
    repatriation_intent = bool(user_input.get("repatriation_intent", False))

    years_to_retirement = _years_to_retirement(age, target_retirement_age)
    growth_pct = _growth_allocation_pct(years_to_retirement, risk_appetite)
    stable_pct = 100 - growth_pct

    growth_shares = GROWTH_SHARES[repatriation_intent]
    stable_shares = STABLE_SHARES[risk_appetite]

    raw_allocations = {
        "Indian Equity": growth_pct * growth_shares["Indian Equity"],
        "International ETFs": growth_pct * growth_shares["International ETFs"],
        "REITs/Real Estate": growth_pct * growth_shares["REITs/Real Estate"],
        "Indian Debt": stable_pct * stable_shares["Indian Debt"],
        "Gold": stable_pct * stable_shares["Gold"],
        "Cash": stable_pct * stable_shares["Cash"],
    }

    allocations = _round_and_fix_to_100(raw_allocations)
    reasons = _build_reasons(allocations, years_to_retirement, risk_appetite, repatriation_intent)

    return {
        "allocations": allocations,
        "reasons": reasons,
        "gold_category_name": GOLD_CATEGORY_NAME,
        "years_to_retirement": years_to_retirement,
    }
