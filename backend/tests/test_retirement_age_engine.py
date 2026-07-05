from app.engines.retirement_age_engine import find_recommended_retirement_age

BASE_USER_INPUT = {
    "age": 35,
    "target_retirement_age": 60,
    "risk_appetite": "moderate",
    "repatriation_intent": True,
    "target_retirement_corpus": 50_000_000,
    "monthly_feasible_investment_amount": 100_000,
}


def test_recommended_age_improves_probability_vs_stated_age_when_underfunded():
    # Stated age is aggressive relative to what the feasible SIP can support,
    # so a later retirement age should raise probability of success.
    user_input = {
        **BASE_USER_INPUT,
        "target_retirement_age": 45,
        "target_retirement_corpus": 80_000_000,
        "monthly_feasible_investment_amount": 40_000,
    }

    result = find_recommended_retirement_age(user_input, investment_restrictions=[], existing_corpus=0)

    assert result["recommended_retirement_age"] >= result["stated_retirement_age"]
    if result["meets_threshold"] and result["probability_at_stated_age"] is not None:
        assert result["probability_of_success"] > result["probability_at_stated_age"]


def test_recommended_age_can_be_earlier_when_overfunded():
    # Generous SIP relative to a modest target — should find an earlier
    # age that already clears the threshold.
    user_input = {
        **BASE_USER_INPUT,
        "target_retirement_corpus": 20_000_000,
        "monthly_feasible_investment_amount": 150_000,
    }

    result = find_recommended_retirement_age(user_input, investment_restrictions=[], existing_corpus=0)

    assert result["meets_threshold"] is True
    assert result["recommended_retirement_age"] <= result["stated_retirement_age"]
    assert result["probability_of_success"] >= result["threshold_used"]


def test_result_includes_explanation_and_threshold():
    result = find_recommended_retirement_age(BASE_USER_INPUT, investment_restrictions=[], existing_corpus=0)

    assert isinstance(result["explanation"], str) and result["explanation"]
    assert result["threshold_used"] == 80.0


def test_unmeetable_target_reports_meets_threshold_false():
    user_input = {
        **BASE_USER_INPUT,
        "age": 55,
        "target_retirement_age": 58,
        "target_retirement_corpus": 500_000_000,
        "monthly_feasible_investment_amount": 10_000,
    }

    result = find_recommended_retirement_age(user_input, investment_restrictions=[], existing_corpus=0)

    assert result["meets_threshold"] is False
