"""SIP Calculator engine.

Deterministic, closed-form annuity math. Back-calculates the monthly SIP
required to reach the target corpus using the allocation-weighted expected
return, splits it per asset class, and checks it against what the user says
they can actually invest. Return assumptions are imported from
monte_carlo_engine so the two engines can never drift apart. No AI involved.
"""

from app.engines.monte_carlo_engine import ASSET_CLASS_ASSUMPTIONS

# When the required SIP exceeds what the user can invest, we first try
# extending the horizon one year at a time, up to this cap; beyond it we
# fall back to suggesting a lower, achievable corpus at the original horizon.
MAX_EXTRA_YEARS = 20

# Default annual SIP step-up — the client is expected to raise their monthly
# contribution by this fraction every year (e.g. with each pay raise) rather
# than investing a flat amount for the whole horizon.
DEFAULT_ANNUAL_STEP_UP_PCT = 0.05


def _weighted_annual_return(allocations: dict) -> float:
    return sum(
        (allocations.get(asset_class, 0) / 100) * assumptions["expected_return"]
        for asset_class, assumptions in ASSET_CLASS_ASSUMPTIONS.items()
    )


def _monthly_rate(annual_rate: float) -> float:
    return (1 + annual_rate) ** (1 / 12) - 1


def _future_value_factor(monthly_rate: float, months: int) -> float:
    """Future value of 1/month invested for `months` months (ordinary annuity)."""
    if monthly_rate == 0:
        return float(months)
    return ((1 + monthly_rate) ** months - 1) / monthly_rate


def _required_monthly_sip(target_corpus, existing_corpus, annual_return, years):
    months = years * 12
    monthly_rate = _monthly_rate(annual_return)
    corpus_from_existing = existing_corpus * (1 + annual_return) ** years
    remaining_target = target_corpus - corpus_from_existing
    if remaining_target <= 0:
        return 0.0
    return remaining_target / _future_value_factor(monthly_rate, months)


def _achievable_corpus(monthly_sip, existing_corpus, annual_return, years):
    months = years * 12
    monthly_rate = _monthly_rate(annual_return)
    return (
        existing_corpus * (1 + annual_return) ** years
        + monthly_sip * _future_value_factor(monthly_rate, months)
    )


def _stepup_future_value_factor(monthly_rate, annual_return, years, step_up_pct):
    """Future value, per unit of year-1 monthly SIP, of `years` years of monthly
    contributions that grow by `step_up_pct` at the start of each year.

    Each year's 12 monthly contributions are first grown to a year-end value
    via the ordinary monthly annuity factor, then that year-end lump sum is
    compounded at the annual rate for the remaining years. Because
    (1 + monthly_rate)**12 == (1 + annual_return) by construction, this is
    exactly equivalent to (not an approximation of) continuous monthly
    compounding — setting step_up_pct=0 reproduces `_future_value_factor`
    applied to the full monthly horizon.
    """
    if years <= 0:
        return 0.0
    factor_12 = _future_value_factor(monthly_rate, 12)
    return sum(
        (1 + step_up_pct) ** year_index * (1 + annual_return) ** (years - 1 - year_index)
        for year_index in range(years)
    ) * factor_12


def _required_monthly_sip_with_stepup(target_corpus, existing_corpus, annual_return, years, step_up_pct):
    monthly_rate = _monthly_rate(annual_return)
    corpus_from_existing = existing_corpus * (1 + annual_return) ** years
    remaining_target = target_corpus - corpus_from_existing
    if remaining_target <= 0:
        return 0.0
    factor = _stepup_future_value_factor(monthly_rate, annual_return, years, step_up_pct)
    if factor <= 0:
        return 0.0
    return remaining_target / factor


def _achievable_corpus_with_stepup(monthly_sip_year1, existing_corpus, annual_return, years, step_up_pct):
    monthly_rate = _monthly_rate(annual_return)
    factor = _stepup_future_value_factor(monthly_rate, annual_return, years, step_up_pct)
    return existing_corpus * (1 + annual_return) ** years + monthly_sip_year1 * factor


def _split_sip_by_allocation(total_sip: float, allocations: dict) -> dict:
    breakdown = {
        asset_class: round(total_sip * pct / 100, 2)
        for asset_class, pct in allocations.items()
        if pct > 0
    }
    # Absorb rounding drift into the largest line so the breakdown sums exactly.
    if breakdown:
        drift = round(total_sip - sum(breakdown.values()), 2)
        if drift:
            largest = max(breakdown, key=breakdown.get)
            breakdown[largest] = round(breakdown[largest] + drift, 2)
    return breakdown


def _find_feasible_extension(target_corpus, existing_corpus, annual_return, years, feasible_sip):
    """Smallest number of extra years that brings the required SIP within budget."""
    for extra_years in range(1, MAX_EXTRA_YEARS + 1):
        required = _required_monthly_sip(
            target_corpus, existing_corpus, annual_return, years + extra_years
        )
        if required <= feasible_sip:
            return extra_years, required
    return None, None


def calculate_sip_plan(user_input: dict, annual_step_up_pct: float = DEFAULT_ANNUAL_STEP_UP_PCT) -> dict:
    """Calculate the required monthly SIP and check it against the user's budget.

    Expected keys in user_input:
        target_corpus (float): INR corpus goal at retirement.
        years_to_retirement (int)
        allocations (dict): asset class -> percentage, from allocation_engine.
        monthly_income (float)
        monthly_expenses (float)
        monthly_feasible_investment_amount (float): user's self-declared budget.
        existing_corpus (float, optional): current investable assets.

    annual_step_up_pct: fraction (e.g. 0.05 for 5%) by which the client is
        recommended to raise their SIP every year. `monthly_sip_required`
        stays the flat-SIP figure (unchanged behavior); the step-up
        alternative is surfaced separately under `sip_step_up`, since a
        growing SIP reaches the same target from a lower starting amount.
    """
    target_corpus = user_input["target_corpus"]
    years = int(user_input["years_to_retirement"])
    allocations = user_input["allocations"]
    monthly_income = user_input.get("monthly_income", 0) or 0
    monthly_expenses = user_input.get("monthly_expenses", 0) or 0
    feasible_sip = user_input["monthly_feasible_investment_amount"]
    existing_corpus = user_input.get("existing_corpus", 0) or 0

    annual_return = _weighted_annual_return(allocations)

    required_sip = _required_monthly_sip(target_corpus, existing_corpus, annual_return, years)
    required_sip = round(required_sip, 2)

    stepup_starting_sip = round(
        _required_monthly_sip_with_stepup(target_corpus, existing_corpus, annual_return, years, annual_step_up_pct),
        2,
    )

    result = {
        "monthly_sip_required": {
            "total": required_sip,
            "by_asset_class": _split_sip_by_allocation(required_sip, allocations),
        },
        "sip_step_up": {
            "annual_step_up_pct": round(annual_step_up_pct * 100, 2),
            "starting_monthly_sip": stepup_starting_sip,
            "by_asset_class": _split_sip_by_allocation(stepup_starting_sip, allocations),
            "flat_monthly_sip_required": required_sip,
        },
        "weighted_expected_annual_return": round(annual_return, 4),
        "monthly_surplus": round(monthly_income - monthly_expenses, 2),
        "monthly_feasible_investment_amount": feasible_sip,
        "feasibility_status": "on_track",
        "alternative_suggestion": None,
    }

    if required_sip <= feasible_sip:
        return result

    result["feasibility_status"] = "not_feasible"

    extra_years, extended_sip = _find_feasible_extension(
        target_corpus, existing_corpus, annual_return, years, feasible_sip
    )
    if extra_years is not None:
        result["alternative_suggestion"] = {
            "type": "extend_timeline",
            "adjusted_years": years + extra_years,
            "extra_years": extra_years,
            "monthly_sip_required": round(extended_sip, 2),
            "target_corpus": target_corpus,
        }
    else:
        achievable = _achievable_corpus(feasible_sip, existing_corpus, annual_return, years)
        result["alternative_suggestion"] = {
            "type": "reduce_corpus",
            "adjusted_corpus": round(achievable, 2),
            "monthly_sip_required": feasible_sip,
            "years_to_retirement": years,
        }

    return result
