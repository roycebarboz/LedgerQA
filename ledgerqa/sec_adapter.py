"""The single place LedgerQA talks to edgartools.

Everything edgartools-shaped is translated here into LedgerQA's own vocabulary
(`Filing`, `DocType`), so a later swap to another SEC data library touches this
file alone. See `sec_client.SECDataClient` for the interface this implements.
"""

import os

import edgar

from ledgerqa.types import DocType, Fact, Filing

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
        found = self._find_filing(accession_number)
        if found is None:
            return None
        return self._to_filing(found)

    def get_fact(
        self,
        accession_number: str,
        concept: str,
        fiscal_year: int | None = None,
    ) -> Fact | None:
        found = self._find_filing(accession_number)
        if found is None:
            return None
        xbrl = found.xbrl()
        if xbrl is None:
            return None

        query = xbrl.query().by_concept(concept, exact=True)
        if fiscal_year is not None:
            query = query.by_fiscal_year(fiscal_year)
        facts = query.execute()
        if not facts:
            return None

        # An annual ("FY") fact is preferred when the concept also has
        # quarterly facts tagged for the same fiscal_year.
        annual_facts = [f for f in facts if f.get("fiscal_period") == "FY"]
        fact = (annual_facts or facts)[0]
        value = fact.get("numeric_value")
        if value is None:
            return None

        raw_fiscal_year = fact.get("fiscal_year")
        return Fact(
            concept=concept,
            value=float(value),
            label=str(fact.get("label") or concept),
            accession_number=found.accession_no,
            fiscal_year=int(raw_fiscal_year) if raw_fiscal_year is not None else None,
        )

    @staticmethod
    def _find_filing(accession_number: str) -> "edgar.Filing | None":
        found = edgar.find(accession_number)
        return found if isinstance(found, edgar.Filing) else None

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
