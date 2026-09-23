"""The SourceDocument catalog: financebench `doc_name` -> SourceDocument.

financebench ships a document-information manifest whose `doc_type` field is
the authoritative label for documents that never reach EDGAR (off-EDGAR
earnings press releases). Where a manifest `doc_link` carries an accession
number, it is recorded so the SEC adapter can resolve the real Filing; where it
does not, the SourceDocument stays an orphan rather than getting a fake one.
"""

import json
import re
from pathlib import Path

from ledgerqa.types import DocType, SourceDocument

DEFAULT_MANIFEST_PATH = (
    Path(__file__).resolve().parent.parent
    / "financebench"
    / "data"
    / "financebench_document_information.jsonl"
)

_MANIFEST_DOC_TYPES = {
    "10k": DocType.TEN_K,
    "10k_annualreport": DocType.TEN_K,
    "10q": DocType.TEN_Q,
    "8k": DocType.EIGHT_K,
    "earnings": DocType.EARNINGS,
}

_ACCESSION_RE = re.compile(r"(\d{10})-?(\d{2})-?(\d{6})")


class UnknownDocTypeError(ValueError):
    """The manifest labelled a document with a doc_type LedgerQA doesn't ingest."""


def parse_doc_type(manifest_doc_type: str) -> DocType:
    try:
        return _MANIFEST_DOC_TYPES[manifest_doc_type.strip().lower()]
    except KeyError as exc:
        raise UnknownDocTypeError(manifest_doc_type) from exc


def parse_accession_number(doc_link: str) -> str | None:
    """Pull an accession number out of a document URL, normalized to dashes."""
    match = _ACCESSION_RE.search(doc_link or "")
    return "-".join(match.groups()) if match else None


class SourceDocumentCatalog:
    """Read-only lookup of the SourceDocuments the evaluation set references."""

    def __init__(self, source_documents: list[SourceDocument]):
        self._by_doc_name = {doc.doc_name: doc for doc in source_documents}

    @classmethod
    def from_manifest(cls, path: Path = DEFAULT_MANIFEST_PATH) -> "SourceDocumentCatalog":
        with path.open(encoding="utf-8") as f:
            records = [json.loads(line) for line in f if line.strip()]
        return cls(
            [
                SourceDocument(
                    doc_name=record["doc_name"],
                    company=record["company"],
                    doc_type=parse_doc_type(record["doc_type"]),
                    accession_number=parse_accession_number(record.get("doc_link", "")),
                )
                for record in records
            ]
        )

    def get(self, doc_name: str) -> SourceDocument | None:
        return self._by_doc_name.get(doc_name)
