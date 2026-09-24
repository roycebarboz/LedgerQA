"""The port every SEC data source plugs into.

Declared apart from `sec_adapter` so callers can depend on the interface
without importing edgartools. `SECDataClientAdapter` is the only implementation
today; swapping to sec-api or Calcbench means writing a second one.

Lookup by company/period, rather than by accession number, lands with the
extraction path that needs it (ticket 03).
"""

from typing import Protocol

from ledgerqa.types import Fact, Filing


class SECDataClient(Protocol):
    def get_filing(self, accession_number: str) -> Filing | None:
        """The Filing for an accession number, or None if EDGAR has no such submission."""
        ...

    def get_fact(
        self,
        accession_number: str,
        concept: str,
        fiscal_year: int | None = None,
    ) -> Fact | None:
        """A single standard-tagged XBRL Fact, or None if `concept` isn't tagged in this Filing.

        `concept` is a standard US-GAAP QName (e.g.
        "us-gaap:PaymentsToAcquirePropertyPlantAndEquipment"). A custom/extension
        tag resolving to the same line item is ticket 04's concern.
        """
        ...
