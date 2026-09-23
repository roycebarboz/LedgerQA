"""The SEC boundary: the one module allowed to touch edgartools.

These tests exercise the adapter's own public surface (identity compliance and
the edgartools form -> DocType mapping) — the one place where edgartools's
vocabulary is translated into LedgerQA's. No test here makes a live request.
"""

import edgar
import pytest

from ledgerqa.sec_adapter import MissingIdentityError, SECDataClientAdapter, doc_type_from_form
from ledgerqa.sec_client import SECDataClient
from ledgerqa.types import DocType

IDENTITY = "LedgerQA Tests tests@example.com"


@pytest.fixture
def recorded_identities(monkeypatch) -> list[str]:
    identities: list[str] = []
    monkeypatch.setattr(edgar, "set_identity", identities.append)
    return identities


def test_adapter_init_sets_a_compliant_user_agent_globally(recorded_identities):
    SECDataClientAdapter(identity=IDENTITY)

    assert recorded_identities == [IDENTITY]


def test_adapter_reads_the_identity_from_the_environment(monkeypatch, recorded_identities):
    monkeypatch.setenv("LEDGERQA_SEC_IDENTITY", IDENTITY)

    SECDataClientAdapter()

    assert recorded_identities == [IDENTITY]


def test_adapter_refuses_to_start_without_an_identity(monkeypatch, recorded_identities):
    """SEC requires a contactable User-Agent; starting without one would get
    the ingestion pipeline blocked."""
    monkeypatch.delenv("LEDGERQA_SEC_IDENTITY", raising=False)

    with pytest.raises(MissingIdentityError):
        SECDataClientAdapter()

    assert recorded_identities == []


def test_adapter_rejects_an_identity_without_a_contact_address(recorded_identities):
    with pytest.raises(MissingIdentityError):
        SECDataClientAdapter(identity="LedgerQA")

    assert recorded_identities == []


@pytest.mark.parametrize(
    ("form", "expected"),
    [
        ("10-K", DocType.TEN_K),
        ("10-K/A", DocType.TEN_K),
        ("10-Q", DocType.TEN_Q),
        ("10-Q/A", DocType.TEN_Q),
        ("8-K", DocType.EIGHT_K),
        ("8-K/A", DocType.EIGHT_K),
    ],
)
def test_edgartools_forms_map_onto_ledgerqa_doc_types(form, expected):
    assert doc_type_from_form(form) is expected


def test_an_out_of_scope_form_has_no_doc_type():
    assert doc_type_from_form("DEF 14A") is None


def test_the_adapter_satisfies_the_sec_client_port(recorded_identities):
    """`answer_question` accepts any SECDataClient; the real adapter must be one."""
    client: SECDataClient = SECDataClientAdapter(identity=IDENTITY)

    assert callable(client.get_filing)
