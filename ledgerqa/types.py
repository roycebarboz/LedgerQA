from dataclasses import dataclass
from enum import StrEnum


@dataclass(frozen=True)
class Citation:
    page_num: int


UNKNOWN_PAGE = -1
"""Citation page for an answer with no verifiable source page."""


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
