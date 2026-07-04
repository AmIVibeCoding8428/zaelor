from unittest.mock import patch

from app import create_app

SAMPLE_INPUT = {
    "age": 35,
    "target_retirement_age": 60,
    "country_of_residence": "UAE",
    "monthly_income": 300_000,
    "monthly_expenses": 150_000,
    "monthly_feasible_investment_amount": 100_000,
    "existing_indian_assets": 2_000_000,
    "existing_foreign_assets": 500_000,
    "risk_appetite": "moderate",
    "target_retirement_corpus": 50_000_000,
    "repatriation_intent": True,
    "has_trc_form10f": True,
}


def _client():
    return create_app().test_client()


@patch("app.routes.generate_wealth_memo")
def test_generate_plan_returns_structured_data_and_memo(mock_generate_wealth_memo):
    mock_generate_wealth_memo.return_value = "A professional wealth advisory summary."

    response = _client().post("/generate-plan", json=SAMPLE_INPUT)

    assert response.status_code == 200
    body = response.get_json()

    assert body["memo"] == "A professional wealth advisory summary."
    assert "tax_and_accounts" in body
    assert "asset_allocation" in body
    assert "monte_carlo" in body
    assert "sip_plan" in body
    mock_generate_wealth_memo.assert_called_once()


def test_generate_plan_missing_fields_returns_400():
    incomplete_input = {"age": 35}

    response = _client().post("/generate-plan", json=incomplete_input)

    assert response.status_code == 400
    assert "error" in response.get_json()


@patch("app.routes.generate_wealth_memo")
def test_generate_plan_claude_failure_returns_502(mock_generate_wealth_memo):
    mock_generate_wealth_memo.side_effect = RuntimeError("ANTHROPIC_API_KEY environment variable is not set.")

    response = _client().post("/generate-plan", json=SAMPLE_INPUT)

    assert response.status_code == 502
    assert "error" in response.get_json()
