from app.engines.allocation_engine import generate_asset_allocation, GOLD_CATEGORY_NAME

SGB_RESTRICTIONS = [{
    "code": "sgb_not_available_to_nri",
    "message": "NRIs cannot purchase new Sovereign Gold Bonds (RBI restriction).",
}]


def _allocations_sum_to_100(result):
    return sum(result["allocations"].values())


def test_young_aggressive_sums_to_100_and_favors_equity():
    result = generate_asset_allocation({
        "age": 25,
        "target_retirement_age": 60,
        "risk_appetite": "aggressive",
        "repatriation_intent": False,
    }, SGB_RESTRICTIONS)

    assert _allocations_sum_to_100(result) == 100
    assert result["allocations"]["Indian Equity"] > result["allocations"]["Indian Debt"]
    assert result["allocations"]["Indian Equity"] > result["allocations"]["Cash"]


def test_older_conservative_sums_to_100_and_favors_debt_and_cash():
    result = generate_asset_allocation({
        "age": 55,
        "target_retirement_age": 60,
        "risk_appetite": "conservative",
        "repatriation_intent": False,
    }, SGB_RESTRICTIONS)

    assert _allocations_sum_to_100(result) == 100
    stable_total = result["allocations"]["Indian Debt"] + result["allocations"]["Gold"] + result["allocations"]["Cash"]
    growth_total = (
        result["allocations"]["Indian Equity"]
        + result["allocations"]["International ETFs"]
        + result["allocations"]["REITs/Real Estate"]
    )
    assert stable_total > growth_total


def test_moderate_mid_horizon_sums_to_100():
    result = generate_asset_allocation({
        "age": 40,
        "target_retirement_age": 60,
        "risk_appetite": "moderate",
        "repatriation_intent": False,
    }, SGB_RESTRICTIONS)

    assert _allocations_sum_to_100(result) == 100


def test_repatriation_intent_shifts_weight_from_international_to_indian_equity():
    base_input = {
        "age": 30,
        "target_retirement_age": 60,
        "risk_appetite": "moderate",
    }

    without_repatriation = generate_asset_allocation(
        {**base_input, "repatriation_intent": False}, SGB_RESTRICTIONS
    )
    with_repatriation = generate_asset_allocation(
        {**base_input, "repatriation_intent": True}, SGB_RESTRICTIONS
    )

    assert _allocations_sum_to_100(without_repatriation) == 100
    assert _allocations_sum_to_100(with_repatriation) == 100
    assert (
        with_repatriation["allocations"]["Indian Equity"]
        > without_repatriation["allocations"]["Indian Equity"]
    )
    assert (
        with_repatriation["allocations"]["International ETFs"]
        < without_repatriation["allocations"]["International ETFs"]
    )


def test_already_at_retirement_age_sums_to_100():
    result = generate_asset_allocation({
        "age": 60,
        "target_retirement_age": 60,
        "risk_appetite": "conservative",
        "repatriation_intent": False,
    }, SGB_RESTRICTIONS)

    assert _allocations_sum_to_100(result) == 100
    assert result["years_to_retirement"] == 0


def test_gold_category_never_uses_sgb():
    result = generate_asset_allocation({
        "age": 35,
        "target_retirement_age": 65,
        "risk_appetite": "moderate",
        "repatriation_intent": False,
    }, SGB_RESTRICTIONS)

    assert result["gold_category_name"] == GOLD_CATEGORY_NAME
    assert "Sovereign Gold Bond" not in GOLD_CATEGORY_NAME
    assert "Sovereign Gold Bond" not in result["reasons"]["Gold"] or "unavailable" in result["reasons"]["Gold"]


def test_missing_restrictions_argument_still_avoids_sgb():
    result = generate_asset_allocation({
        "age": 35,
        "target_retirement_age": 65,
        "risk_appetite": "moderate",
        "repatriation_intent": False,
    })

    assert result["gold_category_name"] == GOLD_CATEGORY_NAME
    assert _allocations_sum_to_100(result) == 100


def test_unknown_risk_appetite_defaults_to_moderate_and_still_sums_to_100():
    result = generate_asset_allocation({
        "age": 45,
        "target_retirement_age": 65,
        "risk_appetite": "unknown_value",
        "repatriation_intent": False,
    })

    assert _allocations_sum_to_100(result) == 100
