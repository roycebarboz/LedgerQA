"""doc_type -> extraction engine.

Dispatch is on Filing/SourceDocument metadata alone. Question content never
reaches this module: a numeric question about an earnings release must still
route to the layout engine, not to a dead XBRL lookup.
"""

from ledgerqa.engines import ExtractionEngine
from ledgerqa.engines.layout import LayoutExtractionEngine
from ledgerqa.engines.xbrl import XBRLExtractionEngine
from ledgerqa.types import DocType

_ENGINES_BY_DOC_TYPE: dict[DocType, ExtractionEngine] = {
    DocType.TEN_K: XBRLExtractionEngine(),
    DocType.TEN_Q: XBRLExtractionEngine(),
    DocType.EIGHT_K: LayoutExtractionEngine(),
    DocType.EARNINGS: LayoutExtractionEngine(),
}


class UnroutableDocTypeError(ValueError):
    """No extraction engine is registered for this doc_type."""


def route(doc_type: DocType) -> ExtractionEngine:
    try:
        return _ENGINES_BY_DOC_TYPE[doc_type]
    except KeyError as exc:
        raise UnroutableDocTypeError(doc_type) from exc
