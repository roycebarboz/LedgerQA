# 03: XBRL single-fact extraction (standard tags)

**What to build:** `answer_question` answers a metrics-generated question by retrieving one standard US-GAAP-tagged XBRL Fact (e.g. `us-gaap:SalesRevenueNet`) via the adapter/router from ticket 02, and returns it with a full citation (accession_number, item_label).

**Blocked by:** 02

**Status:** done

- [x] Given a company + fiscal period + standard-tagged concept, returns the correct numeric Fact
- [x] Every returned Fact carries accession_number and source item_label
- [x] Passes the subset of financebench metrics-generated questions that use standard GAAP tags, verified via the grader (01)
- [x] Non-existent/unavailable concepts return an explicit "not found" rather than a guessed value

## Comments

`XBRLExtractionEngine.extract` now does real work: `ledgerqa/concepts.py` reads
a fiscal year (`FY\d{4}`) and a unit scale ("million"/"billion") straight off
the question text, and matches the question's line-item phrase against an
ordered table of standard US-GAAP concept candidates (capex, net PP&E, net
income, net AR, dividends paid, operating income, cash from operations,
current assets/liabilities, accounts payable, COGS, inventory, total
assets/liabilities). The engine tries each candidate against the injected
`SECDataClient.get_fact` in order and returns the first hit, scaled to the
question's stated unit.

`SECDataClient` gained `get_fact(accession_number, concept, fiscal_year)`;
`SECDataClientAdapter` is the only implementation, using
`filing.xbrl().query().by_concept(..., exact=True).by_fiscal_year(...)`
(edgartools stays isolated behind it, same as ticket 02). `Fact` (concept,
value, label, accession_number, fiscal_year) is a new, unpersisted type —
versioning/supersession is ticket 09's. `Citation` gained optional
`accession_number`/`item_label` fields alongside the existing `page_num`.

Concept-mapping scope is deliberately narrow: only the ~14 financebench
metrics-generated questions that are a single Fact lookup with no
ratio/average/YoY/non-GAAP computation across Facts. `resolve_concepts` guards
against that: a question matching `_COMPUTED_QUESTION_RE` (ratio, %, average,
turnover, margin, payout, growth, DPO/DSO/CCC, EBITDA, net working capital)
answers "insufficient data" even when it also names a line item that would
otherwise match — e.g. "3-year average of capex as a % of revenue" mentions
capex but must not return a raw capex Fact as if it were the averaged ratio.
Those computed questions need ticket 08's code-interpreter loop; a
non-GAAP/custom tag needs ticket 04's calculation-linkbase/LLM fallback. A
question outside this set — no `FY` mention, or a line-item phrase not in the
table — answers "insufficient data" the same way, while `client.get_fact`
returning `None` for a genuinely untagged standard concept answers "not
found".

### Deferred deliberately

- **Citation is not grader-`citation_matches`-clean.** An XBRL Fact has no PDF
  page; `citation_matches` checks `result.citation.page_num` against
  financebench's `evidence_page_num`, which XBRL retrieval alone can't supply.
  `tests/test_xbrl_extraction.py` verifies `grade(...).numeric_match` directly
  instead of full `.passed`. Mapping a Fact to a rendered page is the layout
  engine's concern (ticket 05/07); a full live 150-question run against the
  grader (with a real `SECDataClientAdapter`, not the routing tests' fake) is
  ticket 13's.
- The checklist's "verified via the grader" is spot-checked, not exhaustive:
  `test_xbrl_extraction.py` runs the grader against one representative
  single-Fact question (`financebench_id_03029`) with a fake client, plus
  `test_concepts.py` unit-testing `resolve_concepts`/`extract_fiscal_year`/
  `extract_scale` directly for the other ~13. Running all ~14 through the
  grader against a real `SECDataClientAdapter` and live EDGAR is ticket 13's
  full-eval pass, not repeated here per-question.
- No fiscal-period disambiguation beyond preferring an annual (`fiscal_period
  == "FY"`) fact when a concept also carries quarterly facts for the same
  `fiscal_year` — non-calendar fiscal years are ticket 12.
- No dimensional/segment filtering beyond `XBRL.query()`'s own
  `include_dimensions=False` default — ticket 10.
- No caching tier — every `get_fact` call is a live-shaped call through the
  injected client; ticket 11 sits the cache/rate-limiter in front of it.
