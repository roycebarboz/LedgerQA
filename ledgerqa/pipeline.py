"""`answer_question` — the single entry point the whole system is exercised through.

The pipeline resolves each doc_name in scope to a SourceDocument, asks the SEC
client for the Filing behind it, and hands the pair to whichever extraction
engine the router picks for that doc_type. The question text is passed to the
engine but never consulted for routing.

The SEC client is injected rather than constructed here: a live EDGAR call must
sit behind the cache tiers (ticket 11), so `answer_question` has no way to
reach the network on its own. With no client, routing falls back to the
catalog's own doc_type, which is all an orphan SourceDocument ever has.

Answering from more than one document in scope needs the multi-tool agent loop
(ticket 08); today the first routable document answers.
"""

from ledgerqa.router import UnroutableDocTypeError, route
from ledgerqa.sec_client import SECDataClient
from ledgerqa.source_documents import SourceDocumentCatalog
from ledgerqa.types import NO_CITATION, AnswerResult, Filing, SourceDocument


def answer_question(
    question: str,
    company: str | list[str],
    doc_scope: list[str],
    *,
    client: SECDataClient | None = None,
    catalog: SourceDocumentCatalog | None = None,
) -> AnswerResult:
    """Answer `question` about `company`, restricted to the SourceDocuments in `doc_scope`.

    `company` and `doc_scope` both take a list, so cross-filing questions don't
    need a signature change later; a single company may be passed bare.
    """
    catalog = catalog if catalog is not None else SourceDocumentCatalog.from_manifest()
    companies = [company] if isinstance(company, str) else list(company)

    rejections: list[str] = []
    for doc_name in doc_scope:
        source_document = catalog.get(doc_name)
        if source_document is None:
            rejections.append(f"{doc_name}: not in the SourceDocument catalog")
            continue
        filing = _resolve_filing(source_document, client)
        doc_type = filing.doc_type if filing is not None else source_document.doc_type
        try:
            engine = route(doc_type)
        except UnroutableDocTypeError:
            rejections.append(f"{doc_name}: no extraction engine for doc_type {doc_type}")
            continue
        return engine.extract(question, source_document, filing, client=client)

    return AnswerResult(
        answer=(
            f"insufficient data: no document in scope is answerable for {', '.join(companies)} "
            f"({'; '.join(rejections) or 'doc_scope was empty'})"
        ),
        citation=NO_CITATION,
    )


def _resolve_filing(
    source_document: SourceDocument,
    client: SECDataClient | None,
) -> Filing | None:
    """The Filing behind a SourceDocument, or None when it is an orphan."""
    accession_number = source_document.accession_number
    if client is None or accession_number is None:
        return None
    return client.get_filing(accession_number)
