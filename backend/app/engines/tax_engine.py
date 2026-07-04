"""Tax & Account Layer engine.

Deterministic, rule-based. Given a user's DTAA documentation status and
repatriation intent, recommends which NRI account types to hold and
returns the applicable TDS/tax rate for each income type. No AI involved —
Claude only turns this structured output into prose downstream.
"""

DTAA_DOC_REQUIREMENT = "Tax Residency Certificate (TRC) + Form 10F"

ACCOUNTS = {
    "NRE": {
        "full_name": "Non-Resident External Account",
        "interest_tax": "exempt",
        "tds_on_interest": 0.0,
        "repatriation": "fully repatriable, no cap",
        "used_for": "Remitting foreign (UAE) income to India and parking it tax-free",
    },
    "NRO": {
        "full_name": "Non-Resident Ordinary Account",
        "interest_tax": "taxable",
        "repatriation": (
            "capped at USD 1,000,000/year for balances and asset-sale proceeds; "
            "current income such as rent/interest has no cap"
        ),
        "used_for": "Holding India-sourced income: rent, dividends, interest, capital gains proceeds",
    },
    "FCNR": {
        "full_name": "Foreign Currency Non-Resident Account",
        "interest_tax": "exempt",
        "tds_on_interest": 0.0,
        "repatriation": "fully repatriable, no cap",
        "used_for": "Holding foreign-currency term deposits without INR conversion/exchange-rate risk",
    },
}

EQUITY_LTCG_EXEMPTION_INR = 125_000


def _recommend_accounts(repatriation_intent, existing_indian_assets, existing_foreign_assets):
    accounts = []

    accounts.append({
        "account_type": "NRE",
        **ACCOUNTS["NRE"],
        "recommended": True,
        "reason": "Primary channel for moving UAE income into India tax-free; recommended for every NRI.",
    })

    nro_recommended = existing_indian_assets > 0
    accounts.append({
        "account_type": "NRO",
        **ACCOUNTS["NRO"],
        "recommended": nro_recommended,
        "reason": (
            "Required to hold existing India-sourced income/assets."
            if nro_recommended
            else "Not currently needed — open if/when India-sourced income (rent, dividends, etc.) arises."
        ),
    })

    fcnr_recommended = existing_foreign_assets > 0 or repatriation_intent
    accounts.append({
        "account_type": "FCNR",
        **ACCOUNTS["FCNR"],
        "recommended": fcnr_recommended,
        "reason": (
            "Useful for parking foreign-currency savings without INR conversion risk, "
            "especially given stated repatriation intent."
            if fcnr_recommended
            else "Optional — only needed if holding foreign-currency deposits."
        ),
    })

    return accounts


def _build_tax_treatment(has_trc_form10f):
    dividend_tds = 0.10 if has_trc_form10f else 0.20
    nro_interest_tds = 0.125 if has_trc_form10f else 0.30

    return {
        "nre_interest": {
            "tax": "exempt",
            "tds_rate": 0.0,
            "dtaa_applicable": False,
        },
        "fcnr_interest": {
            "tax": "exempt",
            "tds_rate": 0.0,
            "dtaa_applicable": False,
        },
        "nro_interest": {
            "tax": "taxable",
            "standard_tds_rate": 0.30,
            "applicable_tds_rate": nro_interest_tds,
            "dtaa_applied": has_trc_form10f,
            "dtaa_requirement": DTAA_DOC_REQUIREMENT,
        },
        "dividends": {
            "tax": "taxable",
            "standard_tds_rate": 0.20,
            "applicable_tds_rate": dividend_tds,
            "dtaa_applied": has_trc_form10f,
            "dtaa_requirement": DTAA_DOC_REQUIREMENT,
        },
        "equity_stcg": {
            "tax": "taxable",
            "rate": 0.20,
            "dtaa_applicable": False,
        },
        "equity_ltcg": {
            "tax": "taxable",
            "rate": 0.125,
            "exemption_threshold_inr": EQUITY_LTCG_EXEMPTION_INR,
            "dtaa_applicable": False,
        },
        "debt_stcg": {
            "tax": "taxable",
            "rate": "slab rate, up to 0.30",
            "dtaa_applicable": False,
        },
        "debt_ltcg": {
            "tax": "taxable",
            "rate": 0.125,
            "indexation": False,
            "dtaa_applicable": False,
        },
        "mutual_fund_bond_capital_gains_dtaa": {
            "tax": "potentially exempt",
            "basis": "DTAA Article 13 (India-UAE)",
            "dtaa_requirement": DTAA_DOC_REQUIREMENT,
            "is_assumption": True,
            "assumption_note": (
                "This is a real but case-law-based interpretation, not a blanket rule under the India-UAE DTAA. "
                "Treat as an assumption, not guaranteed tax treatment, and confirm with a tax advisor."
            ),
        },
    }


def _build_risk_flags(has_trc_form10f, repatriation_intent, existing_indian_assets):
    flags = []

    if not has_trc_form10f:
        flags.append({
            "code": "missing_dtaa_documentation",
            "message": (
                f"No {DTAA_DOC_REQUIREMENT} on file — dividends and NRO interest are being taxed at the "
                "standard (higher) TDS rate instead of the DTAA-reduced rate."
            ),
        })

    if repatriation_intent and existing_indian_assets > 0:
        flags.append({
            "code": "nro_repatriation_cap",
            "message": (
                "NRO balance/asset-sale repatriation is capped at USD 1,000,000/year. "
                "Plan large repatriations in advance if existing Indian assets are being liquidated."
            ),
        })

    flags.append({
        "code": "mutual_fund_capital_gains_dtaa_assumption",
        "message": (
            "Potential full exemption on mutual fund/bond capital gains under DTAA Article 13 is a "
            "case-law-based assumption, not guaranteed. Do not treat as certain."
        ),
    })

    return flags


def generate_tax_account_layer(user_input: dict) -> dict:
    """Generate account and tax/TDS guidance for an NRI user.

    Expected keys in user_input:
        has_trc_form10f (bool): whether the user holds a Tax Residency
            Certificate + Form 10F, unlocking DTAA-reduced TDS rates.
        repatriation_intent (bool): whether the user intends to repatriate
            funds from India to the UAE.
        existing_indian_assets (float): value of existing India-based assets.
        existing_foreign_assets (float): value of existing foreign (UAE/other) assets.
    """
    has_trc_form10f = bool(user_input.get("has_trc_form10f", False))
    repatriation_intent = bool(user_input.get("repatriation_intent", False))
    existing_indian_assets = user_input.get("existing_indian_assets", 0) or 0
    existing_foreign_assets = user_input.get("existing_foreign_assets", 0) or 0

    return {
        "recommended_accounts": _recommend_accounts(
            repatriation_intent, existing_indian_assets, existing_foreign_assets
        ),
        "tax_treatment": _build_tax_treatment(has_trc_form10f),
        "investment_restrictions": [
            {
                "code": "sgb_not_available_to_nri",
                "message": (
                    "NRIs cannot purchase new Sovereign Gold Bonds (RBI restriction). "
                    "Use Gold ETF/Gold Mutual Fund as the gold allocation category instead."
                ),
            }
        ],
        "risk_flags": _build_risk_flags(has_trc_form10f, repatriation_intent, existing_indian_assets),
    }
