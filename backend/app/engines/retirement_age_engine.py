"""Recommended Retirement Age engine.

Deterministic search over candidate retirement ages: re-runs the Monte Carlo
simulation once per candidate age (age+1 through max_age), holding every
other input constant (risk appetite, repatriation intent, target corpus,
existing corpus, and — critically — the user's own stated monthly feasible
investment, not the back-solved "required" SIP). Returns the earliest age at
which probability of success crosses the acceptable threshold. No AI
involved.
"""

from app.engines import allocation_engine, monte_carlo_engine

DEFAULT_THRESHOLD_PCT = 80.0
DEFAULT_MAX_AGE = 70

# Fewer paths than the headline simulation (10,000) since this runs once per
# candidate age (~dozens of runs) — precise enough to compare ages, fast
# enough to stay inside a single request.
SEARCH_NUM_SIMULATIONS = 2_000
SEARCH_SEED = 42


def _probability_at_age(user_input, investment_restrictions, existing_corpus, candidate_age, annual_step_up_pct):
    allocation = allocation_engine.generate_asset_allocation(
        {**user_input, "target_retirement_age": candidate_age},
        investment_restrictions=investment_restrictions,
    )
    years = allocation["years_to_retirement"]
    if years <= 0:
        return None

    result = monte_carlo_engine.run_monte_carlo_simulation(
        allocations=allocation["allocations"],
        monthly_sip_amount=user_input["monthly_feasible_investment_amount"],
        years_to_retirement=years,
        target_corpus=user_input["target_retirement_corpus"],
        existing_corpus=existing_corpus,
        num_simulations=SEARCH_NUM_SIMULATIONS,
        seed=SEARCH_SEED,
        annual_step_up_pct=annual_step_up_pct,
    )
    return years, result["probability_of_success"]


def _explain(stated_age, candidate_age, baseline_probability, probability, target_corpus, meets_threshold):
    corpus_cr = target_corpus / 1e7

    if not meets_threshold:
        return (
            f"Even working until {candidate_age}, your probability of reaching ₹{corpus_cr:.2f} Cr tops out "
            f"around {probability:.1f}% at your current monthly investment — raising your SIP or your "
            f"feasible investment amount will move this further than working longer will."
        )
    if candidate_age == stated_age:
        return (
            f"Your stated retirement age of {stated_age} already clears an {probability:.1f}% probability of "
            f"reaching ₹{corpus_cr:.2f} Cr — no change needed."
        )
    if candidate_age < stated_age:
        return (
            f"Your current savings pace already supports retiring {stated_age - candidate_age} year(s) earlier, "
            f"at {candidate_age}, with a {probability:.1f}% probability of reaching ₹{corpus_cr:.2f} Cr."
        )
    baseline_text = f"{baseline_probability:.1f}%" if baseline_probability is not None else "a lower probability"
    return (
        f"Retiring at {candidate_age} instead of {stated_age} lifts your probability of reaching "
        f"₹{corpus_cr:.2f} Cr from {baseline_text} to {probability:.1f}%, by giving your portfolio "
        f"{candidate_age - stated_age} more year(s) to compound."
    )


def find_recommended_retirement_age(
    user_input: dict,
    investment_restrictions: list,
    existing_corpus: float,
    threshold: float = DEFAULT_THRESHOLD_PCT,
    max_age: int = DEFAULT_MAX_AGE,
    annual_step_up_pct: float = 0.0,
) -> dict:
    """Find the earliest retirement age at which probability of success
    crosses `threshold`, scanning age+1 through max_age.
    """
    age = user_input["age"]
    stated_age = user_input["target_retirement_age"]
    target_corpus = user_input["target_retirement_corpus"]

    probabilities_by_age = {}
    for candidate_age in range(age + 1, max_age + 1):
        outcome = _probability_at_age(user_input, investment_restrictions, existing_corpus, candidate_age, annual_step_up_pct)
        if outcome is None:
            continue
        _, probability = outcome
        probabilities_by_age[candidate_age] = probability

    baseline_probability = probabilities_by_age.get(stated_age)

    recommended_age = None
    for candidate_age in sorted(probabilities_by_age):
        if probabilities_by_age[candidate_age] >= threshold:
            recommended_age = candidate_age
            break

    meets_threshold = recommended_age is not None
    if not meets_threshold and probabilities_by_age:
        recommended_age = max(probabilities_by_age, key=probabilities_by_age.get)

    if recommended_age is None:
        # No feasible candidate ages at all (e.g. age already >= max_age).
        return {
            "recommended_retirement_age": stated_age,
            "stated_retirement_age": stated_age,
            "probability_of_success": baseline_probability,
            "probability_at_stated_age": baseline_probability,
            "threshold_used": threshold,
            "meets_threshold": False,
            "explanation": "Not enough runway before the maximum modeled age to recommend a different retirement age.",
        }

    probability = probabilities_by_age[recommended_age]

    return {
        "recommended_retirement_age": recommended_age,
        "stated_retirement_age": stated_age,
        "probability_of_success": probability,
        "probability_at_stated_age": baseline_probability,
        "threshold_used": threshold,
        "meets_threshold": meets_threshold,
        "explanation": _explain(
            stated_age, recommended_age, baseline_probability, probability, target_corpus, meets_threshold
        ),
    }
