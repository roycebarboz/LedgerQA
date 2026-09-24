"""XBRL extraction engine — the 10-K/10-Q path.

Answers a single standard-tagged US-GAAP concept for one fiscal year, as
resolved by `ledgerqa.concepts` from the question text. A custom/extension
tag or a concept this engine doesn't recognize needs the calculation-linkbase
walk / LLM fallback (ticket 04) — this engine reports "not found" rather than
guessing.
"""

from dataclasses import dataclass

from ledgerqa.concepts import extract_fiscal_year, extract_scale, resolve_concepts
from ledgerqa.engines import insufficient_data
from ledgerqa.sec_client import SECDataClient
from ledgerqa.types import UNKNOWN_PAGE, AnswerResult, Citation, Filing, SourceDocument


@dataclass(frozen=True)
class XBRLExtractionEngine:
    name: str = "XBRL"

    def extract(
        self,
        question: str,
        source_document: SourceDocument,
        filing: Filing | None,
        *,
        client: SECDataClient | None = None,
    ) -> AnswerResult:
        accession_number = (
            filing.accession_number if filing is not None else source_document.accession_number
        )
        if client is None or accession_number is None:
            return insufficient_data(self.name, source_document, "no live SEC client available")

        fiscal_year = extract_fiscal_year(question)
        if fiscal_year is None:
            return insufficient_data(
                self.name, source_document, "no fiscal year found in the question"
            )

        concepts = resolve_concepts(question)
        if concepts is None:
            return insufficient_data(
                self.name, source_document, "question doesn't map to a known standard GAAP concept"
            )

        for concept in concepts:
            fact = client.get_fact(accession_number, concept, fiscal_year)
            if fact is not None:
                scale = extract_scale(question)
                return AnswerResult(
                    answer=f"${fact.value / scale:.2f}",
                    citation=Citation(
                        page_num=UNKNOWN_PAGE,
                        accession_number=fact.accession_number,
                        item_label=fact.label,
                    ),
                )

        return AnswerResult(
            answer=(
                f"not found: no standard-tagged Fact for FY{fiscal_year} "
                f"(doc_name={source_document.doc_name}, tried {', '.join(concepts)})"
            ),
            citation=Citation(page_num=UNKNOWN_PAGE, accession_number=accession_number),
        )
