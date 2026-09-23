"""XBRL extraction engine — the 10-K/10-Q path. Extraction lands in ticket 03."""

from dataclasses import dataclass

from ledgerqa.engines import insufficient_data
from ledgerqa.types import AnswerResult, Filing, SourceDocument


@dataclass(frozen=True)
class XBRLExtractionEngine:
    name: str = "XBRL"

    def extract(
        self,
        question: str,
        source_document: SourceDocument,
        filing: Filing | None,
    ) -> AnswerResult:
        return insufficient_data(self.name, source_document)
