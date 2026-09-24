from dataclasses import dataclass
from enum import StrEnum


@dataclass(frozen=True)
class Citation:
    page_num: int
    accession_number: str | None = None
    item_label: str | None = None


UNKNOWN_PAGE = -1
"""Citation page for an answer with no verifiable source page.

An XBRL-sourced Fact has no PDF page to cite; it carries `accession_number`/
`item_label` instead, with `page_num` left at UNKNOWN_PAGE until the layout
engine (ticket 05/07) can map a Fact back to a rendered page.
"""


@dataclass(frozen=True)
class AnswerResult:
    answer: str
    citation: Citation


NO_CITATION = Citation(page_num=UNKNOWN_PAGE)


class DocType(StrEnum):
    """The filing forms LedgerQA ingests. Drives extraction-engine routing."""

    TEN_K = "10-K"
    TEN_Q = "10-Q"
    EIGHT_K = "8-K"
    EARNINGS = "Earnings"


@dataclass(frozen=True)
class Filing:
    """An SEC-accepted submission, identified by its accession_number."""

    accession_number: str
    company: str
    doc_type: DocType
    period_of_report_date: str | None = None


@dataclass(frozen=True)
class SourceDocument:
    """The unit financebench's `doc_name` refers to (e.g. `AMCOR_2023Q4_EARNINGS`).

    `accession_number` is None for an orphan — a document with no EDGAR
    submission behind it (e.g. an off-EDGAR press release). An orphan is never
    assigned a fake accession_number.
    """

    doc_name: str
    company: str
    doc_type: DocType
    accession_number: str | None = None

    @property
    def is_orphan(self) -> bool:
        return self.accession_number is None


@dataclass(frozen=True)
class Fact:
    """A single XBRL-tagged value read from one Filing's accession_number.

    Point-in-time only for now: `valid_from`/`valid_to` versioning and
    amendment supersession (see CONTEXT.md's Fact entry) land with ticket 09,
    which extends this dataclass rather than introducing a new one. `label`
    is the filer's own presentation label for the concept (e.g. "Purchases of
    property, plant and equipment (PP&E)"), used as the citation's item_label.
    """

    concept: str
    value: float
    label: str
    accession_number: str
    fiscal_year: int | None = None
