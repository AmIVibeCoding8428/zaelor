"""Monte Carlo Simulation engine.

Deterministic *process*, stochastic *inputs*: given an asset allocation and a
monthly SIP amount, simulates NUM_SIMULATIONS random portfolio paths over the
retirement horizon and reports the probability of reaching the target corpus,
plus median/best/worst-case trajectories for charting. No AI involved.

All return/volatility/inflation assumptions are named constants below —
these are the numbers that must be surfaced in the frontend's
"Assumptions & Limitations" section, so keep them here and don't inline
any of them elsewhere.
"""

import numpy as np

NUM_SIMULATIONS = 10_000

# Fixed so identical inputs always produce identical output (deterministic *process*,
# not deterministic in the sense of no randomness — the random draws themselves are
# reproducible run to run).
DEFAULT_SEED = 42

# Percentile bands used for the best/worst-case chart lines.
BEST_CASE_PERCENTILE = 90
WORST_CASE_PERCENTILE = 10

# Long-term nominal INR assumptions per asset class. These are illustrative,
# real-world-informed estimates (not live market data) used purely to drive
# the simulation — they must be disclosed to the user as assumptions.
#   Indian Equity        — Nifty 50 long-run nominal CAGR ~12%, high volatility
#   International ETFs   — US/global equity index, INR terms (incl. avg INR depreciation ~9%, vol 15%
#   Indian Debt           — high-quality bonds/FDs/debt mutual funds ~7%, low volatility
#   Gold (ETF/MF)          — long-run nominal INR gold returns ~8%, moderate volatility
#   REITs/Real Estate      — Indian REITs + real estate proxies ~9%, moderate volatility
#   Cash                   — savings/liquid funds ~4%, minimal volatility
ASSET_CLASS_ASSUMPTIONS = {
    "Indian Equity": {"expected_return": 0.12, "volatility": 0.18},
    "International ETFs": {"expected_return": 0.09, "volatility": 0.15},
    "Indian Debt": {"expected_return": 0.07, "volatility": 0.05},
    "Gold": {"expected_return": 0.08, "volatility": 0.15},
    "REITs/Real Estate": {"expected_return": 0.09, "volatility": 0.12},
    "Cash": {"expected_return": 0.04, "volatility": 0.01},
}

ASSET_CLASSES = tuple(ASSET_CLASS_ASSUMPTIONS.keys())

# Long-term India CPI inflation assumption. Not applied to the simulation
# math (the target corpus is treated as a fixed nominal INR figure supplied
# by the user) — kept here purely for frontend disclosure.
ANNUAL_INFLATION_RATE = 0.06

# Floors a single asset's simulated annual return so a bad draw can't imply
# losing more than 95% of that asset's value in one year.
MIN_ANNUAL_ASSET_RETURN = -0.95

CONTRIBUTION_TIMING_NOTE = (
    "Contributions use a mid-year convention: each year's SIP contributions are "
    "assumed invested evenly through the year, so they earn roughly half that "
    "year's simulated return."
)


def _allocation_weights(allocations: dict) -> np.ndarray:
    return np.array([allocations.get(asset_class, 0) / 100 for asset_class in ASSET_CLASSES])


def _simulate_portfolio_values(weights, years, num_simulations, existing_corpus, annual_contribution, seed):
    rng = np.random.default_rng(seed)

    means = np.array([ASSET_CLASS_ASSUMPTIONS[c]["expected_return"] for c in ASSET_CLASSES])
    stds = np.array([ASSET_CLASS_ASSUMPTIONS[c]["volatility"] for c in ASSET_CLASSES])

    asset_returns = rng.normal(loc=means, scale=stds, size=(num_simulations, years, len(ASSET_CLASSES)))
    asset_returns = np.clip(asset_returns, MIN_ANNUAL_ASSET_RETURN, None)

    portfolio_returns = asset_returns @ weights  # shape: (num_simulations, years)

    values = np.zeros((num_simulations, years + 1))
    values[:, 0] = existing_corpus
    for year in range(1, years + 1):
        year_return = portfolio_returns[:, year - 1]
        values[:, year] = (
            values[:, year - 1] * (1 + year_return)
            + annual_contribution * (1 + year_return) ** 0.5
        )

    return values[:, 1:]  # drop year 0 (starting point), keep one column per simulated year


def run_monte_carlo_simulation(
    allocations: dict,
    monthly_sip_amount: float,
    years_to_retirement: int,
    target_corpus: float,
    existing_corpus: float = 0.0,
    num_simulations: int = NUM_SIMULATIONS,
    seed: int = DEFAULT_SEED,
) -> dict:
    """Run the Monte Carlo retirement corpus simulation.

    allocations: dict of asset class -> percentage (as returned by
        allocation_engine.generate_asset_allocation()["allocations"]).
    monthly_sip_amount: monthly contribution amount, in the same currency as
        target_corpus (INR).
    years_to_retirement: simulation horizon in years.
    target_corpus: the INR corpus the user wants to hit by retirement.
    existing_corpus: starting portfolio value, if any.
    """
    years = max(int(years_to_retirement), 0)

    if years == 0:
        success = existing_corpus >= target_corpus
        return {
            "probability_of_success": 100.0 if success else 0.0,
            "median_case": [],
            "best_case": [],
            "worst_case": [],
            "final_median_corpus": existing_corpus,
            "num_simulations": num_simulations,
            "years_to_retirement": 0,
            "assumptions": _assumptions_block(num_simulations),
        }

    weights = _allocation_weights(allocations)
    annual_contribution = monthly_sip_amount * 12

    values = _simulate_portfolio_values(
        weights, years, num_simulations, existing_corpus, annual_contribution, seed
    )

    final_values = values[:, -1]
    probability_of_success = float((final_values >= target_corpus).mean() * 100)

    median_case = np.median(values, axis=0)
    best_case = np.percentile(values, BEST_CASE_PERCENTILE, axis=0)
    worst_case = np.percentile(values, WORST_CASE_PERCENTILE, axis=0)

    return {
        "probability_of_success": round(probability_of_success, 1),
        "median_case": median_case.tolist(),
        "best_case": best_case.tolist(),
        "worst_case": worst_case.tolist(),
        "final_median_corpus": float(median_case[-1]),
        "num_simulations": num_simulations,
        "years_to_retirement": years,
        "assumptions": _assumptions_block(num_simulations),
    }


def _assumptions_block(num_simulations):
    return {
        "asset_class_assumptions": ASSET_CLASS_ASSUMPTIONS,
        "annual_inflation_rate": ANNUAL_INFLATION_RATE,
        "num_simulations": num_simulations,
        "contribution_timing": CONTRIBUTION_TIMING_NOTE,
    }
