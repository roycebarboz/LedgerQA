# 02: SECDataClientAdapter + doc_type router

**What to build:** All edgartools calls isolated behind one `SECDataClientAdapter` abstraction, plus a routing layer that reads a Filing's `doc_type` and dispatches to an XBRL-engine path (10-K/10-Q) or a layout-engine path (8-K/Earnings). Extraction logic itself is stubbed — this ticket is purely correct wiring and isolation, so later library swaps or engine implementations touch one place each.

**Blocked by:** None (can start immediately, prefactor)

**Status:** done

- [x] edgartools version pinned in the dependency manifest
- [x] No code outside `SECDataClientAdapter` calls edgartools directly
- [x] Router dispatches purely on `Filing.doc_type` (10K/10Q → XBRL stub, 8K/Earnings → layout stub), never inferred from question content
- [x] `set_identity`-style compliant User-Agent configured globally at adapter init

## Comments

Wired through the spec's single seam: `ledgerqa/pipeline.py` now exposes
`answer_question(question, company, doc_scope, *, client=None, catalog=None)`,
which resolves each doc_name to a `SourceDocument`, asks the SEC client for the
`Filing` behind it, and dispatches on `doc_type`. Both engines
(`ledgerqa/engines/xbrl.py`, `ledgerqa/engines/layout.py`) return an explicit
"insufficient data: … not implemented yet" `AnswerResult`, so the eval harness
runs end-to-end at a 0% pass rate rather than crashing.

Files: `sec_client.py` (the `SECDataClient` port, importable without pulling in
edgartools), `sec_adapter.py` (the only edgartools importer), `router.py`,
`pipeline.py`, `source_documents.py` (financebench doc manifest →
`SourceDocument`, including accession-number extraction from `doc_link`),
`engines/`, plus `DocType`/`Filing`/`SourceDocument` in `types.py`.

Dependency manifest created from scratch (none existed): `pyproject.toml` pins
`edgartools==5.58.0` exactly, with mypy/pytest/ruff as dev extras.

Two things not on the checklist but needed to make the wiring honest:
- Resolution order — an EDGAR-resolved `Filing.doc_type` wins over the
  manifest's label; a `SourceDocument` with no accession_number (orphan
  off-EDGAR press release) routes on its own doc_type and never touches EDGAR.
- `SECDataClientAdapter` refuses to start without a contactable identity
  (`LEDGERQA_SEC_IDENTITY`), rather than silently issuing bannable requests.

Filing resolution itself is deliberately thin: only 40 of financebench's 361
`doc_link`s carry an accession number, so company/period → accession lookup is
left to ticket 03 rather than guessed at here.

Tests: `tests/test_answer_question_routing.py` (seam-level, fake SEC client
only — includes a check that all 150 financebench questions route: 127 XBRL, 23
layout), `tests/test_sec_adapter.py` (identity compliance, form → DocType),
`tests/test_edgartools_isolation.py` (AST lint: no module under `ledgerqa/`
except `sec_adapter.py` imports edgartools).

### Review follow-ups

Applied from `/code-review`:
- Dropped `SECDataClient.get_filings` / the adapter's implementation of it —
  uncalled, untested, and wrong by inspection (`edgar.Company` wants a
  CIK/ticker, financebench gives names like "3M"). Company/period lookup lands
  in ticket 03 with a caller and a test.
- Dropped `Filing.is_superseded` — ticket 09's field, unused here.
- `company` now accepts a list as well as a scalar, per the spec's
  "filter parameters accept a list" decision.
- `NO_CITATION`/`UNKNOWN_PAGE` moved next to `Citation` in `types.py`.
- The insufficient-data answer now names why each doc_name was rejected
  (absent from catalog vs. no engine for its doc_type), instead of blaming
  routing for both.
- `DocType` added to `CONTEXT.md`; ruff now enforces E501/I (this also fixed
  two over-length lines in ticket 01's `eval_runner.py`).

Deferred deliberately:
- The routing tests read the engine from the answer string. That is the only
  externally visible difference between the routes while both engines are
  stubs; tickets 03/05 replace each assertion with gold-answer + citation
  assertions. Called out in the test module's docstring.
- `answer_question` never constructs a live client — a live EDGAR call has to
  sit behind the cache tiers (ticket 11), so the client stays injected. With no
  client, routing uses the catalog's doc_type, which is all an orphan
  SourceDocument ever has.
- Multi-document `doc_scope` answers from the first routable document; chaining
  across several needs the agent loop (ticket 08).
