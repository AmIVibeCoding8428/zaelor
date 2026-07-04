import math

from app.engines.sip_engine import (
    calculate_sip_plan,
    _achievable_corpus,
    _required_monthly_sip,
    _weighted_annual_return,
)

MODERATE_ALLOCATION = {
    "Indian Equity": 45,
    "International ETFs": 19,
    "Indian Debt": 14,
    "Gold": 6,
    "REITs/Real Estate": 11,
    "Cash": 5,
}


def _base_input(**overrides):
    base = {
        "target_corpus": 50_000_000,
        "years_to_retirement": 25,
        "allocations": MODERATE_ALLOCATION,
        "monthly_income": 300_000,
        "monthly_expenses": 150_000,
        "monthly_feasible_investment_amount": 100_000,
        "existing_corpus": 0,
    }
    base.update(overrides)
    return base


def test_breakdown_sums_to_total():
    result = calculate_sip_plan(_base_input())

    breakdown = result["monthly_sip_required"]["by_asset_class"]
    total = result["monthly_sip_required"]["total"]
    assert math.isclose(sum(breakdown.values()), total, abs_tol=0.01)
    # Only asset classes with a non-zero allocation appear.
    assert set(breakdown) <= set(MODERATE_ALLOCATION)


def test_required_sip_actually_reaches_target():
    result = calculate_sip_plan(_base_input())
    annual_return = _weighted_annual_return(MODERATE_ALLOCATION)

    achieved = _achievable_corpus(
        result["monthly_sip_required"]["total"], 0, annual_return, 25
    )
    assert math.isclose(achieved, 50_000_000, rel_tol=1e-4)


def test_feasible_case_is_on_track():
    result = calculate_sip_plan(_base_input(monthly_feasible_investment_amount=200_000))

    assert result["feasibility_status"] == "on_track"
    assert result["alternative_suggestion"] is None


def test_infeasible_case_triggers_and_suggests_timeline_extension():
    # Tight budget but a big-enough horizon extension can still work.
    result = calculate_sip_plan(_base_input(
        target_corpus=100_000_000,
        years_to_retirement=15,
        monthly_feasible_investment_amount=100_000,
    ))

    assert result["feasibility_status"] == "not_feasible"
    assert result["monthly_sip_required"]["total"] > 100_000

    suggestion = result["alternative_suggestion"]
    assert suggestion["type"] == "extend_timeline"
    assert suggestion["adjusted_years"] > 15

    # Sanity check: the suggested SIP at the extended horizon fits the budget
    # and actually reaches the original target.
    annual_return = _weighted_annual_return(MODERATE_ALLOCATION)
    assert suggestion["monthly_sip_required"] <= 100_000
    achieved = _achievable_corpus(
        suggestion["monthly_sip_required"], 0, annual_return, suggestion["adjusted_years"]
    )
    assert achieved >= 100_000_000 * 0.999


def test_extension_is_minimal():
    result = calculate_sip_plan(_base_input(
        target_corpus=100_000_000,
        years_to_retirement=15,
        monthly_feasible_investment_amount=100_000,
    ))

    suggestion = result["alternative_suggestion"]
    annual_return = _weighted_annual_return(MODERATE_ALLOCATION)
    one_year_less = suggestion["adjusted_years"] - 1
    assert _required_monthly_sip(100_000_000, 0, annual_return, one_year_less) > 100_000


def test_hopeless_target_falls_back_to_reduced_corpus():
    # A target so large that even +20 years cannot make it feasible.
    result = calculate_sip_plan(_base_input(
        target_corpus=10_000_000_000,
        years_to_retirement=10,
        monthly_feasible_investment_amount=50_000,
    ))

    assert result["feasibility_status"] == "not_feasible"
    suggestion = result["alternative_suggestion"]
    assert suggestion["type"] == "reduce_corpus"
    assert suggestion["adjusted_corpus"] < 10_000_000_000

    # Sanity check: the feasible SIP really does produce the adjusted corpus.
    annual_return = _weighted_annual_return(MODERATE_ALLOCATION)
    achieved = _achievable_corpus(50_000, 0, annual_return, 10)
    assert math.isclose(achieved, suggestion["adjusted_corpus"], rel_tol=1e-6)


def test_existing_corpus_reduces_required_sip():
    without_corpus = calculate_sip_plan(_base_input())
    with_corpus = calculate_sip_plan(_base_input(existing_corpus=5_000_000))

    assert (
        with_corpus["monthly_sip_required"]["total"]
        < without_corpus["monthly_sip_required"]["total"]
    )


def test_existing_corpus_alone_sufficient_means_zero_sip():
    result = calculate_sip_plan(_base_input(
        target_corpus=10_000_000,
        existing_corpus=10_000_000,
    ))

    assert result["monthly_sip_required"]["total"] == 0.0
    assert result["feasibility_status"] == "on_track"
