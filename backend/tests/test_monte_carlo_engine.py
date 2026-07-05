from app.engines.monte_carlo_engine import run_monte_carlo_simulation

MODERATE_ALLOCATION = {
    "Indian Equity": 45,
    "International ETFs": 19,
    "Indian Debt": 14,
    "Gold": 6,
    "REITs/Real Estate": 11,
    "Cash": 5,
}

CONSERVATIVE_ALLOCATION = {
    "Indian Equity": 7,
    "International ETFs": 3,
    "Indian Debt": 44,
    "Gold": 22,
    "REITs/Real Estate": 2,
    "Cash": 22,
}


def _assert_case_ordering(result):
    for best, median, worst in zip(result["best_case"], result["median_case"], result["worst_case"]):
        assert best >= median >= worst


def test_probability_of_success_is_within_0_to_100_and_arrays_match_horizon():
    years = 25
    result = run_monte_carlo_simulation(
        allocations=MODERATE_ALLOCATION,
        monthly_sip_amount=50_000,
        years_to_retirement=years,
        target_corpus=50_000_000,
        num_simulations=2_000,
        seed=42,
    )

    assert 0 <= result["probability_of_success"] <= 100
    assert len(result["median_case"]) == years
    assert len(result["best_case"]) == years
    assert len(result["worst_case"]) == years
    _assert_case_ordering(result)


def test_case_ordering_holds_for_conservative_allocation():
    years = 10
    result = run_monte_carlo_simulation(
        allocations=CONSERVATIVE_ALLOCATION,
        monthly_sip_amount=30_000,
        years_to_retirement=years,
        target_corpus=10_000_000,
        num_simulations=2_000,
        seed=7,
    )

    assert len(result["median_case"]) == years
    _assert_case_ordering(result)


def test_higher_sip_increases_probability_of_success():
    common_kwargs = dict(
        allocations=MODERATE_ALLOCATION,
        years_to_retirement=20,
        target_corpus=30_000_000,
        num_simulations=3_000,
        seed=1,
    )

    low_sip = run_monte_carlo_simulation(monthly_sip_amount=10_000, **common_kwargs)
    high_sip = run_monte_carlo_simulation(monthly_sip_amount=80_000, **common_kwargs)

    assert high_sip["probability_of_success"] >= low_sip["probability_of_success"]


def test_final_median_corpus_matches_last_median_case_value():
    result = run_monte_carlo_simulation(
        allocations=MODERATE_ALLOCATION,
        monthly_sip_amount=40_000,
        years_to_retirement=15,
        target_corpus=20_000_000,
        num_simulations=2_000,
        seed=3,
    )

    assert result["final_median_corpus"] == result["median_case"][-1]


def test_existing_corpus_already_meets_target_at_zero_years():
    result = run_monte_carlo_simulation(
        allocations=MODERATE_ALLOCATION,
        monthly_sip_amount=50_000,
        years_to_retirement=0,
        target_corpus=1_000_000,
        existing_corpus=2_000_000,
    )

    assert result["probability_of_success"] == 100.0
    assert result["median_case"] == []
    assert result["best_case"] == []
    assert result["worst_case"] == []


def test_existing_corpus_below_target_at_zero_years_fails():
    result = run_monte_carlo_simulation(
        allocations=MODERATE_ALLOCATION,
        monthly_sip_amount=50_000,
        years_to_retirement=0,
        target_corpus=5_000_000,
        existing_corpus=1_000_000,
    )

    assert result["probability_of_success"] == 0.0


def test_stepup_contribution_produces_higher_final_corpus_than_flat():
    common_kwargs = dict(
        allocations=MODERATE_ALLOCATION,
        monthly_sip_amount=40_000,
        years_to_retirement=25,
        target_corpus=50_000_000,
        num_simulations=3_000,
        seed=11,
    )

    flat = run_monte_carlo_simulation(annual_step_up_pct=0.0, **common_kwargs)
    stepped_up = run_monte_carlo_simulation(annual_step_up_pct=0.05, **common_kwargs)

    assert stepped_up["final_median_corpus"] > flat["final_median_corpus"]
    assert stepped_up["annual_step_up_pct"] == 0.05
    assert flat["annual_step_up_pct"] == 0.0


def test_assumptions_block_exposes_named_constants():
    result = run_monte_carlo_simulation(
        allocations=MODERATE_ALLOCATION,
        monthly_sip_amount=50_000,
        years_to_retirement=5,
        target_corpus=10_000_000,
        num_simulations=500,
        seed=9,
    )

    assumptions = result["assumptions"]
    assert "Indian Equity" in assumptions["asset_class_assumptions"]
    assert assumptions["asset_class_assumptions"]["Indian Equity"]["expected_return"] == 0.12
    assert assumptions["annual_inflation_rate"] == 0.06
    assert assumptions["num_simulations"] == 500
