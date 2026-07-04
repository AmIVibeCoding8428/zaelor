from app.engines.tax_engine import generate_tax_account_layer


def _account(result, account_type):
    return next(a for a in result["recommended_accounts"] if a["account_type"] == account_type)


def test_no_trc_uses_standard_tds_rates():
    result = generate_tax_account_layer({
        "has_trc_form10f": False,
        "repatriation_intent": True,
        "existing_indian_assets": 5_000_000,
        "existing_foreign_assets": 0,
    })

    tax = result["tax_treatment"]
    assert tax["dividends"]["applicable_tds_rate"] == 0.20
    assert tax["nro_interest"]["applicable_tds_rate"] == 0.30
    assert tax["dividends"]["dtaa_applied"] is False

    flag_codes = [f["code"] for f in result["risk_flags"]]
    assert "missing_dtaa_documentation" in flag_codes
    assert "nro_repatriation_cap" in flag_codes


def test_trc_form10f_unlocks_dtaa_rates():
    result = generate_tax_account_layer({
        "has_trc_form10f": True,
        "repatriation_intent": True,
        "existing_indian_assets": 5_000_000,
        "existing_foreign_assets": 0,
    })

    tax = result["tax_treatment"]
    assert tax["dividends"]["applicable_tds_rate"] == 0.10
    assert tax["nro_interest"]["applicable_tds_rate"] == 0.125
    assert tax["dividends"]["dtaa_applied"] is True

    flag_codes = [f["code"] for f in result["risk_flags"]]
    assert "missing_dtaa_documentation" not in flag_codes


def test_nre_and_fcnr_are_always_tax_exempt():
    result = generate_tax_account_layer({"has_trc_form10f": False})

    tax = result["tax_treatment"]
    assert tax["nre_interest"]["tax"] == "exempt"
    assert tax["nre_interest"]["tds_rate"] == 0.0
    assert tax["fcnr_interest"]["tax"] == "exempt"
    assert tax["fcnr_interest"]["tds_rate"] == 0.0


def test_capital_gains_rates_are_fixed_regardless_of_dtaa():
    no_trc = generate_tax_account_layer({"has_trc_form10f": False})
    with_trc = generate_tax_account_layer({"has_trc_form10f": True})

    for result in (no_trc, with_trc):
        tax = result["tax_treatment"]
        assert tax["equity_stcg"]["rate"] == 0.20
        assert tax["equity_ltcg"]["rate"] == 0.125
        assert tax["equity_ltcg"]["exemption_threshold_inr"] == 125_000
        assert tax["debt_ltcg"]["rate"] == 0.125
        assert tax["debt_ltcg"]["indexation"] is False


def test_mutual_fund_dtaa_treatment_is_flagged_as_assumption():
    result = generate_tax_account_layer({"has_trc_form10f": True})

    mf_treatment = result["tax_treatment"]["mutual_fund_bond_capital_gains_dtaa"]
    assert mf_treatment["is_assumption"] is True

    flag_codes = [f["code"] for f in result["risk_flags"]]
    assert "mutual_fund_capital_gains_dtaa_assumption" in flag_codes


def test_no_existing_indian_assets_does_not_recommend_nro():
    result = generate_tax_account_layer({
        "has_trc_form10f": False,
        "repatriation_intent": False,
        "existing_indian_assets": 0,
        "existing_foreign_assets": 0,
    })

    nre = _account(result, "NRE")
    nro = _account(result, "NRO")
    assert nre["recommended"] is True
    assert nro["recommended"] is False

    flag_codes = [f["code"] for f in result["risk_flags"]]
    assert "nro_repatriation_cap" not in flag_codes


def test_sgb_restriction_is_flagged():
    result = generate_tax_account_layer({"has_trc_form10f": True})

    restriction_codes = [r["code"] for r in result["investment_restrictions"]]
    assert "sgb_not_available_to_nri" in restriction_codes
