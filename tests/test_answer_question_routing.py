"""Routing behavior observed through the single seam, `answer_question`.

Tests assert only on the returned `AnswerResult` — never on which engine object
was selected, how the catalog resolved a doc_name, or any other internal.
The SEC network boundary (`SECDataClientAdapter`) is substituted by a fake;
nothing else is faked.

While both engines are stubs, the engine that ran is the only externally
visible difference between the two routes, so these tests read it out of the
answer string. Tickets 03 and 05 replace each assertion with a gold-answer and
citation assertion as the engine behind it starts answering for real.
"""

from ledgerqa.eval_runner import load_gold_questions
from ledgerqa.pipeline import answer_question
from ledgerqa.types import DocType, Filing, SourceDocument


class FakeSECDataClient:
    """Stands in for live EDGAR: hands back whatever Filing the test wants."""

    def __init__(self, filing: Filing | None = None):
        self._filing = filing
        self.requested_accession_numbers: list[str] = []

    def get_filing(self, accession_number: str) -> Filing | None:
        self.requested_accession_numbers.append(accession_number)
        return self._filing


class StubCatalog:
    def __init__(self, source_document: SourceDocument):
        self._source_document = source_document

    def get(self, doc_name: str) -> SourceDocument | None:
        return self._source_document if doc_name == self._source_document.doc_name else None


def test_ten_k_source_document_is_answered_by_the_xbrl_engine():
    result = answer_question(
        "What is the FY2018 capital expenditure amount (in USD millions) for 3M?",
        "3M",
        ["3M_2018_10K"],
        client=FakeSECDataClient(),
    )

    assert "xbrl" in result.answer.lower()


def test_earnings_source_document_is_answered_by_the_layout_engine():
    result = answer_question(
        "What was AMCOR's FY2023 adjusted EBITDA?",
        "AMCOR",
        ["AMCOR_2023Q4_EARNINGS"],
        client=FakeSECDataClient(),
    )

    assert "layout" in result.answer.lower()


def test_a_numeric_question_on_an_earnings_document_still_routes_to_layout():
    """Routing is doc_type-driven: a question that "looks numeric" must not
    drag a non-XBRL document into the XBRL path."""
    result = answer_question(
        "What is the exact FY2023 net sales figure in USD millions?",
        "AMCOR",
        ["AMCOR_2023Q4_EARNINGS"],
        client=FakeSECDataClient(),
    )

    assert "layout" in result.answer.lower()
    assert "xbrl" not in result.answer.lower()


def test_a_qualitative_question_on_a_ten_k_still_routes_to_xbrl():
    result = answer_question(
        "Why did 3M describe its business as capital intensive?",
        "3M",
        ["3M_2018_10K"],
        client=FakeSECDataClient(),
    )

    assert "xbrl" in result.answer.lower()


def test_routing_follows_the_resolved_filings_doc_type_not_the_catalog_label():
    """When EDGAR resolves a real Filing, its doc_type is what dispatches."""
    eight_k = Filing(
        accession_number="0001558370-19-000470",
        company="3M",
        doc_type=DocType.EIGHT_K,
    )
    catalog_says_ten_k = SourceDocument(
        doc_name="3M_2018_10K",
        company="3M",
        doc_type=DocType.TEN_K,
        accession_number="0001558370-19-000470",
    )
    client = FakeSECDataClient(filing=eight_k)

    result = answer_question(
        "What is the FY2018 capital expenditure amount for 3M?",
        "3M",
        ["3M_2018_10K"],
        client=client,
        catalog=StubCatalog(catalog_says_ten_k),
    )

    assert client.requested_accession_numbers == ["0001558370-19-000470"]
    assert "layout" in result.answer.lower()


def test_an_orphan_document_is_routed_without_consulting_edgar():
    """An off-EDGAR press release has no accession_number, so there is no
    Filing to fetch — it still routes by its own doc_type."""
    client = FakeSECDataClient()

    result = answer_question(
        "What was the adjusted EBITDA?",
        "AMCOR",
        ["AMCOR_2023Q4_EARNINGS"],
        client=client,
        catalog=StubCatalog(
            SourceDocument(
                doc_name="AMCOR_2023Q4_EARNINGS",
                company="AMCOR",
                doc_type=DocType.EARNINGS,
                accession_number=None,
            )
        ),
    )

    assert client.requested_accession_numbers == []
    assert "layout" in result.answer.lower()


def test_an_unknown_doc_name_answers_insufficient_data_rather_than_raising():
    result = answer_question(
        "What is the FY2018 capital expenditure amount for 3M?",
        "3M",
        ["3M_1066_PAPYRUS"],
        client=FakeSECDataClient(),
    )

    assert "insufficient data" in result.answer.lower()


def test_doc_scope_falls_through_to_the_first_resolvable_document():
    result = answer_question(
        "What is the FY2018 capital expenditure amount for 3M?",
        "3M",
        ["3M_1066_PAPYRUS", "3M_2018_10K"],
        client=FakeSECDataClient(),
    )

    assert "xbrl" in result.answer.lower()


def test_every_financebench_question_routes_to_an_extraction_engine():
    """The whole evaluation set is routable today, so ticket 03/05 failures
    will be extraction failures, not wiring gaps."""
    gold_questions = load_gold_questions()

    unrouted = [
        q["financebench_id"]
        for q in gold_questions
        if "insufficient data: no document in scope"
        in answer_question(q["question"], q["company"], [q["doc_name"]]).answer
    ]

    assert unrouted == []


def test_routing_follows_the_filing_when_the_catalog_understates_the_doc_type():
    """The mirror of the case above: a catalog-labelled earnings document whose
    Filing turns out to be a 10-K routes to XBRL, not layout."""
    catalog_says_earnings = SourceDocument(
        doc_name="AMCOR_2023Q4_EARNINGS",
        company="AMCOR",
        doc_type=DocType.EARNINGS,
        accession_number="0001748790-23-000141",
    )
    client = FakeSECDataClient(
        filing=Filing(
            accession_number="0001748790-23-000141",
            company="AMCOR",
            doc_type=DocType.TEN_K,
        )
    )

    result = answer_question(
        "What was AMCOR's FY2023 adjusted EBITDA?",
        "AMCOR",
        ["AMCOR_2023Q4_EARNINGS"],
        client=client,
        catalog=StubCatalog(catalog_says_earnings),
    )

    assert "xbrl" in result.answer.lower()


def test_company_may_be_passed_as_a_list():
    """Filter parameters take lists so cross-filing questions need no rewrite."""
    result = answer_question(
        "What is the FY2018 capital expenditure amount for 3M?",
        ["3M"],
        ["3M_2018_10K"],
        client=FakeSECDataClient(),
    )

    assert "xbrl" in result.answer.lower()
