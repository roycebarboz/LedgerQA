"""XBRL single-Fact extraction, observed through `answer_question`.

Tests assert only on the returned `AnswerResult` and, via the grader, on the
gold financebench record — never on the engine object or the concept it tried
internally. The SEC network boundary is a fake supplying one canned Fact.

Citation here carries `accession_number`/`item_label` rather than a PDF page:
an XBRL Fact has no page of its own, so `citation_matches` (grader.py, which
checks `evidence_page_num`) will not pass yet for these answers. Mapping a
Fact back to a rendered page is the layout engine's concern (ticket 05/07);
this ticket only verifies numeric accuracy via the grader.
"""

from ledgerqa.eval_runner import load_gold_questions
from ledgerqa.grader import grade
from ledgerqa.pipeline import answer_question
from ledgerqa.types import DocType, Fact, Filing, SourceDocument
from tests.test_answer_question_routing import FakeSECDataClient, StubCatalog

THREE_M_2018_10K = SourceDocument(
    doc_name="3M_2018_10K",
    company="3M",
    doc_type=DocType.TEN_K,
    accession_number="0000066740-19-000014",
)
THREE_M_2018_FILING = Filing(
    accession_number="0000066740-19-000014",
    company="3M",
    doc_type=DocType.TEN_K,
)


def test_a_resolved_fact_is_returned_scaled_to_the_questions_stated_unit():
    capex_fact = Fact(
        concept="us-gaap:PaymentsToAcquirePropertyPlantAndEquipment",
        value=1_577_000_000.0,
        label="Purchases of property, plant and equipment (PP&E)",
        accession_number=THREE_M_2018_FILING.accession_number,
        fiscal_year=2018,
    )
    client = FakeSECDataClient(filing=THREE_M_2018_FILING, fact=capex_fact)

    result = answer_question(
        "What is the FY2018 capital expenditure amount (in USD millions) for 3M?",
        "3M",
        ["3M_2018_10K"],
        client=client,
        catalog=StubCatalog(THREE_M_2018_10K),
    )

    assert result.answer == "$1577.00"


def test_the_citation_carries_the_accession_number_and_source_item_label():
    capex_fact = Fact(
        concept="us-gaap:PaymentsToAcquirePropertyPlantAndEquipment",
        value=1_577_000_000.0,
        label="Purchases of property, plant and equipment (PP&E)",
        accession_number=THREE_M_2018_FILING.accession_number,
        fiscal_year=2018,
    )
    client = FakeSECDataClient(filing=THREE_M_2018_FILING, fact=capex_fact)

    result = answer_question(
        "What is the FY2018 capital expenditure amount (in USD millions) for 3M?",
        "3M",
        ["3M_2018_10K"],
        client=client,
        catalog=StubCatalog(THREE_M_2018_10K),
    )

    assert result.citation.accession_number == "0000066740-19-000014"
    assert result.citation.item_label == "Purchases of property, plant and equipment (PP&E)"


def test_the_concept_query_carries_the_fiscal_year_and_accession_number():
    client = FakeSECDataClient(filing=THREE_M_2018_FILING, fact=None)

    answer_question(
        "What is the FY2018 capital expenditure amount (in USD millions) for 3M?",
        "3M",
        ["3M_2018_10K"],
        client=client,
        catalog=StubCatalog(THREE_M_2018_10K),
    )

    accession_number, concept, fiscal_year = client.requested_facts[0]
    assert accession_number == "0000066740-19-000014"
    assert concept == "us-gaap:PaymentsToAcquirePropertyPlantAndEquipment"
    assert fiscal_year == 2018


def test_an_unresolvable_concept_answers_an_explicit_not_found():
    """No candidate concept in ledgerqa.concepts resolves for this Fact, so the
    engine must say so rather than answer with a guessed value."""
    client = FakeSECDataClient(filing=THREE_M_2018_FILING, fact=None)

    result = answer_question(
        "What is the FY2018 capital expenditure amount (in USD millions) for 3M?",
        "3M",
        ["3M_2018_10K"],
        client=client,
        catalog=StubCatalog(THREE_M_2018_10K),
    )

    assert "not found" in result.answer.lower()


def test_a_resolved_fact_matches_the_gold_answer_via_the_grader():
    """The grader's numeric check is the pass/fail signal ticket 03 is built
    against; the citation-page check is out of scope (see module docstring)."""
    gold_question = next(
        q for q in load_gold_questions() if q["financebench_id"] == "financebench_id_03029"
    )
    capex_fact = Fact(
        concept="us-gaap:PaymentsToAcquirePropertyPlantAndEquipment",
        value=1_577_000_000.0,
        label="Purchases of property, plant and equipment (PP&E)",
        accession_number=THREE_M_2018_FILING.accession_number,
        fiscal_year=2018,
    )
    client = FakeSECDataClient(filing=THREE_M_2018_FILING, fact=capex_fact)

    result = answer_question(
        gold_question["question"],
        gold_question["company"],
        [gold_question["doc_name"]],
        client=client,
        catalog=StubCatalog(THREE_M_2018_10K),
    )

    assert grade(result, gold_question).numeric_match is True
