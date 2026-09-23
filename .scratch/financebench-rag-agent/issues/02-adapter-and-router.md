# 02: SECDataClientAdapter + doc_type router

**What to build:** All edgartools calls isolated behind one `SECDataClientAdapter` abstraction, plus a routing layer that reads a Filing's `doc_type` and dispatches to an XBRL-engine path (10-K/10-Q) or a layout-engine path (8-K/Earnings). Extraction logic itself is stubbed — this ticket is purely correct wiring and isolation, so later library swaps or engine implementations touch one place each.

**Blocked by:** None (can start immediately, prefactor)

**Status:** ready-for-agent

- [ ] edgartools version pinned in the dependency manifest
- [ ] No code outside `SECDataClientAdapter` calls edgartools directly
- [ ] Router dispatches purely on `Filing.doc_type` (10K/10Q → XBRL stub, 8K/Earnings → layout stub), never inferred from question content
- [ ] `set_identity`-style compliant User-Agent configured globally at adapter init
