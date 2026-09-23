"""The single place LedgerQA talks to edgartools.

Everything edgartools-shaped is translated here into LedgerQA's own vocabulary
(`Filing`, `DocType`), so a later swap to another SEC data library touches this
file alone. See `sec_client.SECDataClient` for the interface this implements.
"""

import os

import edgar

from ledgerqa.types import DocType, Filing

IDENTITY_ENV_VAR = "LEDGERQA_SEC_IDENTITY"

_DOC_TYPES_BY_FORM = {
    "10-K": DocType.TEN_K,
    "10-Q": DocType.TEN_Q,
    "8-K": DocType.EIGHT_K,
}


class MissingIdentityError(RuntimeError):
    """No compliant SEC User-Agent is configured.

    SEC EDGAR blocks requests that don't identify a contactable party, so the
    adapter refuses to start rather than get the whole pipeline banned.
    """


def doc_type_from_form(form: str) -> DocType | None:
    """Map an EDGAR form string onto a LedgerQA DocType.

    An amendment (`10-K/A`) keeps its base doc_type — it is extracted the same
    way; supersession is a separate concern (ticket 09).
    """
    return _DOC_TYPES_BY_FORM.get(form.strip().upper().removesuffix("/A"))


def _require_identity(identity: str | None) -> str:
    identity = (identity if identity is not None else os.environ.get(IDENTITY_ENV_VAR, "")).strip()
    if "@" not in identity or "." not in identity.rpartition("@")[2]:
        raise MissingIdentityError(
            f"Set {IDENTITY_ENV_VAR} to a compliant SEC User-Agent "
            f'(e.g. "LedgerQA Research name@example.com"); got {identity!r}'
        )
    return identity


class SECDataClientAdapter:
    """Reads Filings from SEC EDGAR via edgartools."""

    def __init__(self, identity: str | None = None):
        self.identity = _require_identity(identity)
        edgar.set_identity(self.identity)

    def get_filing(self, accession_number: str) -> Filing | None:
        found = edgar.find(accession_number)
        if not isinstance(found, edgar.Filing):
            return None
        return self._to_filing(found)

    @staticmethod
    def _to_filing(filing: "edgar.Filing") -> Filing | None:
        """Translate an edgartools Filing; None for forms LedgerQA doesn't ingest."""
        doc_type = doc_type_from_form(filing.form)
        if doc_type is None:
            return None
        period_of_report = getattr(filing, "period_of_report", None)
        return Filing(
            accession_number=filing.accession_no,
            company=filing.company,
            doc_type=doc_type,
            period_of_report_date=str(period_of_report) if period_of_report else None,
        )
