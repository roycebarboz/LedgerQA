"""Extraction engines: one per structural family of Filing.

An engine turns a question plus a resolved SourceDocument/Filing into an
`AnswerResult`. Both engines currently answer "insufficient data" — the
extraction itself lands in tickets 03 (XBRL) and 05 (layout). The router and
the engine interface are what ship now, so those tickets each touch one file.
"""

from typing import Protocol

from ledgerqa.sec_client import SECDataClient
from ledgerqa.types import NO_CITATION, AnswerResult, Filing, SourceDocument


class ExtractionEngine(Protocol):
    """The seam tickets 03 and 05 implement behind."""

    @property
    def name(self) -> str: ...

    def extract(
        self,
        question: str,
        source_document: SourceDocument,
        filing: Filing | None,
        *,
        client: SECDataClient | None = None,
    ) -> AnswerResult: ...


def insufficient_data(
    engine_name: str,
    source_document: SourceDocument,
    reason: str | None = None,
) -> AnswerResult:
    default_reason = f"{engine_name} extraction engine is not implemented yet"
    return AnswerResult(
        answer=(
            f"insufficient data: {reason or default_reason} "
            f"(doc_name={source_document.doc_name}, doc_type={source_document.doc_type})"
        ),
        citation=NO_CITATION,
    )
