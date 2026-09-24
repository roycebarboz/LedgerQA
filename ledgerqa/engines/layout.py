"""Layout extraction engine — the 8-K/Earnings path. Extraction lands in ticket 05."""

from dataclasses import dataclass

from ledgerqa.engines import insufficient_data
from ledgerqa.sec_client import SECDataClient
from ledgerqa.types import AnswerResult, Filing, SourceDocument


@dataclass(frozen=True)
class LayoutExtractionEngine:
    name: str = "layout"

    def extract(
        self,
        question: str,
        source_document: SourceDocument,
        filing: Filing | None,
        *,
        client: SECDataClient | None = None,
    ) -> AnswerResult:
        return insufficient_data(self.name, source_document)
