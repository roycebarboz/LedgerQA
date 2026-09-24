"""Question text -> (fiscal_year, scale, concept candidates), in isolation from the engine."""

from ledgerqa.concepts import extract_fiscal_year, extract_scale, resolve_concepts


def test_extracts_the_fiscal_year_from_an_fy_mention():
    assert extract_fiscal_year("What is the FY2018 capital expenditure for 3M?") == 2018


def test_no_fiscal_year_mention_returns_none():
    assert extract_fiscal_year("Why did 3M describe its business as capital intensive?") is None


def test_extracts_a_million_scale():
    assert extract_scale("What is total assets (in USD millions)?") == 1_000_000


def test_extracts_a_billion_scale():
    assert extract_scale("Answer in USD billions.") == 1_000_000_000


def test_defaults_to_no_scaling_when_no_unit_is_named():
    assert extract_scale("What is the FY2018 capital expenditure for 3M?") == 1


def test_resolves_capital_expenditure_to_its_standard_concept():
    concepts = resolve_concepts("What is the FY2018 capital expenditure amount for 3M?")
    assert concepts is not None
    assert "us-gaap:PaymentsToAcquirePropertyPlantAndEquipment" in concepts


def test_prefers_current_assets_over_the_generic_total_assets_rule():
    concepts = resolve_concepts("What is total current assets for Nike?")
    assert concepts == ("us-gaap:AssetsCurrent",)


def test_an_unrecognized_metric_resolves_to_no_concept():
    """A non-GAAP metric like 'adjusted EBITDA' has no standard tag to try;
    ticket 04's fallback path handles it, not a guess here."""
    assert resolve_concepts("What was AMCOR's FY2023 adjusted EBITDA?") is None


def test_a_ratio_question_does_not_resolve_even_though_it_names_a_line_item():
    """'3 year average of capex as a % of revenue' mentions capex, but the
    question needs multiple Facts averaged and divided — a single raw capex
    Fact would silently answer the wrong thing. That's ticket 08's agent
    loop, not this engine."""
    assert resolve_concepts("What is the 3 year average of capex as a % of revenue?") is None


def test_a_dpo_question_does_not_resolve_despite_mentioning_accounts_payable():
    question = (
        "What is the FY2017 days payable outstanding (DPO)? DPO is defined as: "
        "365 * average accounts payable / COGS."
    )
    assert resolve_concepts(question) is None


def test_an_ebitda_less_capex_question_does_not_resolve_despite_mentioning_capex():
    question = "What is the FY2022 unadjusted EBITDA less capex for PepsiCo?"
    assert resolve_concepts(question) is None
