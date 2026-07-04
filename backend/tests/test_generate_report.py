from app import create_app
from app.plan_service import build_plan

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


def _sample_plan():
    return {
        **build_plan(SAMPLE_INPUT),
        "memo": "A professional wealth advisory summary for this client.",
    }


def test_generate_report_returns_valid_pdf():
    response = _client().post(
        "/generate-report",
        json={"user_input": SAMPLE_INPUT, "plan": _sample_plan()},
    )

    assert response.status_code == 200
    assert response.content_type == "application/pdf"
    assert "attachment" in response.headers["Content-Disposition"]
    assert len(response.data) > 0
    assert response.data.startswith(b"%PDF")


def test_generate_report_missing_plan_returns_400():
    response = _client().post("/generate-report", json={"user_input": SAMPLE_INPUT})

    assert response.status_code == 400
    assert "error" in response.get_json()


def test_generate_report_incomplete_plan_returns_400():
    incomplete_plan = {"tax_and_accounts": {}, "asset_allocation": {}}

    response = _client().post(
        "/generate-report",
        json={"user_input": SAMPLE_INPUT, "plan": incomplete_plan},
    )

    assert response.status_code == 400
    assert "error" in response.get_json()
