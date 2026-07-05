"""Orchestrates the 4 deterministic engines into a single structured wealth plan."""

from app.engines import allocation_engine, monte_carlo_engine, retirement_age_engine, sip_engine, tax_engine

REQUIRED_FIELDS = [
    "age",
    "target_retirement_age",
    "country_of_residence",
    "monthly_income",
    "monthly_expenses",
    "monthly_feasible_investment_amount",
    "existing_indian_assets",
    "existing_foreign_assets",
    "risk_appetite",
    "target_retirement_corpus",
    "repatriation_intent",
    "has_trc_form10f",
]


class InvalidPlanInput(ValueError):
    """Raised when the questionnaire payload is missing required fields."""


def validate_input(user_input: dict) -> None:
    missing = [field for field in REQUIRED_FIELDS if field not in user_input]
    if missing:
        raise InvalidPlanInput(f"Missing required fields: {', '.join(missing)}")


def build_plan(user_input: dict) -> dict:
    """Run all 4 engines in order and combine their outputs into one structured plan."""
    validate_input(user_input)

    tax_and_accounts = tax_engine.generate_tax_account_layer(user_input)

    asset_allocation = allocation_engine.generate_asset_allocation(
        user_input, investment_restrictions=tax_and_accounts["investment_restrictions"]
    )

    existing_corpus = (
        (user_input.get("existing_indian_assets") or 0)
        + (user_input.get("existing_foreign_assets") or 0)
    )
    years_to_retirement = asset_allocation["years_to_retirement"]

    sip_plan = sip_engine.calculate_sip_plan({
        "target_corpus": user_input["target_retirement_corpus"],
        "years_to_retirement": years_to_retirement,
        "allocations": asset_allocation["allocations"],
        "monthly_income": user_input.get("monthly_income"),
        "monthly_expenses": user_input.get("monthly_expenses"),
        "monthly_feasible_investment_amount": user_input["monthly_feasible_investment_amount"],
        "existing_corpus": existing_corpus,
    })

    monte_carlo = monte_carlo_engine.run_monte_carlo_simulation(
        allocations=asset_allocation["allocations"],
        monthly_sip_amount=sip_plan["monthly_sip_required"]["total"],
        years_to_retirement=years_to_retirement,
        target_corpus=user_input["target_retirement_corpus"],
        existing_corpus=existing_corpus,
    )

    # SIP step-up benefit: same starting SIP, with vs. without the annual
    # step-up, so the client can see what stepping up actually buys them.
    step_up_pct = sip_plan["sip_step_up"]["annual_step_up_pct"] / 100
    monte_carlo_with_stepup = monte_carlo_engine.run_monte_carlo_simulation(
        allocations=asset_allocation["allocations"],
        monthly_sip_amount=sip_plan["sip_step_up"]["starting_monthly_sip"],
        years_to_retirement=years_to_retirement,
        target_corpus=user_input["target_retirement_corpus"],
        existing_corpus=existing_corpus,
        annual_step_up_pct=step_up_pct,
    )
    monte_carlo_without_stepup = monte_carlo_engine.run_monte_carlo_simulation(
        allocations=asset_allocation["allocations"],
        monthly_sip_amount=sip_plan["sip_step_up"]["starting_monthly_sip"],
        years_to_retirement=years_to_retirement,
        target_corpus=user_input["target_retirement_corpus"],
        existing_corpus=existing_corpus,
        annual_step_up_pct=0.0,
    )
    sip_plan["sip_step_up"]["probability_of_success_with_stepup"] = monte_carlo_with_stepup["probability_of_success"]
    sip_plan["sip_step_up"]["probability_of_success_without_stepup"] = monte_carlo_without_stepup["probability_of_success"]
    sip_plan["sip_step_up"]["projected_benefit"] = round(
        monte_carlo_with_stepup["probability_of_success"] - monte_carlo_without_stepup["probability_of_success"], 1
    )

    recommended_retirement_age = retirement_age_engine.find_recommended_retirement_age(
        user_input,
        investment_restrictions=tax_and_accounts["investment_restrictions"],
        existing_corpus=existing_corpus,
    )

    return {
        "currency": "INR",
        "tax_and_accounts": tax_and_accounts,
        "asset_allocation": asset_allocation,
        "monte_carlo": monte_carlo,
        "sip_plan": sip_plan,
        "recommended_retirement_age": recommended_retirement_age,
    }
