Status: ready-for-agent

# Financebench RAG Agent

## Problem Statement

A financial analyst wants precise, cited answers to questions about a company's SEC filings — exact numbers from financial statements, qualitative context from MD&A/Risk Factors, and reasoning that blends both — without manually digging through 10-Ks, 10-Qs, 8-Ks, and earnings releases. Existing approaches that reconstruct tables from HTML/PDF layout are unreliable; the analyst needs answers grounded in the filer's own tagged data wherever it exists, with a verifiable citation back to the exact filing and page.

## Solution

Build a single-entry-point RAG agent — `answer_question(question, company, doc_scope) → AnswerResult` — that routes each Filing to the right extraction engine (XBRL for 10-K/10-Q, layout-aware parsing for 8-K/Earnings), stores every extracted Fact versioned and cited to its exact accession_number, and answers questions by chaining retrieval and a code-interpreter tool so no arithmetic happens inside the LLM's own token stream. The system is validated against financebench's 150 open-source questions with a grader that checks both numeric accuracy and citation accuracy, built before any ingestion code exists.

## User Stories

1. As an analyst, I want to ask "What was the FY2018 CapEx for 3M?" and get the exact figure sourced from the cash flow statement, so that I don't have to open the PDF myself.
2. As an analyst, I want the answer to cite the accession_number and item_label it came from, so that I can verify it against the original filing.
3. As an analyst, I want custom/non-GAAP XBRL tags (e.g. `tsla_AutomotiveSalesRevenue`) correctly mapped to standard concepts via the calculation linkbase, so that ticker-specific tagging quirks don't produce wrong answers.
4. As an analyst, I want a fallback to HTML-table extraction + LLM verification when XBRL tag mapping fails outright, so that a missing standard tag doesn't just produce "no data."
5. As an analyst, I want to ask a computed question ("Is 3M capital-intensive?") and get a correct ratio (CapEx/Revenue, Fixed Assets/Total Assets, ROA) computed from raw Facts, so that I get analyst-grade reasoning, not just raw numbers.
6. As an analyst, I want all arithmetic performed by a code-interpreter sandbox, not generated as LLM token output, so that ratio/percentage answers are never subject to LLM arithmetic error.
7. As an analyst, I want to ask about a prior year's figures and get the value as originally filed, not silently overwritten by a later restatement, so that historical analysis isn't corrupted by hindsight data.
8. As an analyst, I want to be able to explicitly request the restated (later-filed) value when I want it, so that both point-in-time and current views are available.
9. As an analyst, I want amended filings (10-K/A) to supersede the original in default search results, so that I see the corrected filing by default.
10. As an analyst, I want the ability to explicitly view pre-amendment (superseded) data when I ask for it, so that historical audit trails aren't destroyed.
11. As an analyst, I want questions answered from Risk Factors (Item 1A), MD&A (Item 7), and Business Description sections with clean section boundaries, so that answers aren't polluted by adjacent unrelated sections.
12. As an analyst, I want narrative-text answers (e.g. "why did wireless revenue increase?") to cite the specific paragraph/section they were drawn from, so that I can trace the claim back to source text.
13. As an analyst, I want questions requiring multi-step reasoning (checking a footnote, then cross-verifying against the balance sheet) to be answered by one agent that can chain multiple tool calls, so that I don't need to know in advance whether my question is "simple" or "complex."
14. As an analyst, I want questions about 8-K/Earnings-release documents (which lack XBRL tagging) to still be answered accurately, using layout-aware parsing instead of XBRL, so that non-10-K/10-Q filings aren't a blind spot.
15. As an analyst, I want non-GAAP metrics defined only in earnings releases (Adjusted EBITDA, FX-adjusted sales growth) answered correctly even though they have no XBRL tag, so that management's own reported figures are available to query.
16. As an analyst, I want segment-level breakdowns (e.g. product line, division) available as distinct queryable data, not collapsed into consolidated totals, so that segment-specific questions ("which segment dragged down growth?") are answerable.
17. As an analyst, I want a query never to silently mix a segment-dimensioned Fact with a consolidated one, so that segment math isn't accidentally wrong.
18. As an analyst, I want the system to work for the ~32 companies and 84 filings actually referenced by the financebench evaluation set during development, not the full SEC universe, so that dev-cycle cost and latency stay small.
19. As a developer, I want a `SECDataClientAdapter` abstraction wrapping all edgartools calls, so that a future library swap (e.g. to sec-api or Calcbench) touches one file, not the whole codebase.
20. As a developer, I want the edgartools dependency version-pinned, so that upstream breaking changes don't silently break ingestion.
21. As a developer, I want a routing layer that decides XBRL-engine vs layout-engine purely from a Filing's `doc_type`, never inferred from whether the question "looks numeric," so that non-GAAP numeric questions on 8-Ks don't get misrouted into a dead XBRL lookup.
22. As a developer, I want an automatic "messy layout" fallback trigger (oversized chunk with no discovered sub-elements) instead of a manually maintained override list, so that new messy filings don't require manual intervention to handle.
23. As a developer, I want every live SEC EDGAR request to carry a compliant `User-Agent` (via `set_identity`) and be throttled below the 10 req/sec ban threshold, so that the ingestion pipeline never gets rate-limited or blocked.
24. As a developer, I want a tiered lookup order — cache, then batch-populated local store, then live EDGAR call as last resort — so that repeated or agent-triggered lookups don't hit SEC EDGAR directly mid-conversation.
25. As a developer, I want every Chunk and Fact tagged with `accession_number` (and Chunks additionally with `item_label`, `exhibit_number`, `chunk_index`), so that text and tabular data join by exact filing rather than by loose ticker/year matching.
26. As a developer, I want text chunked at structural boundaries (sub-section/paragraph, not fixed character counts), 800–1000 tokens with 150–200 token overlap, with the section heading prepended as chunk metadata, so that retrieval doesn't return context-free fragments.
27. As a developer, I want an eval grader — numeric tolerance match against financebench's gold `answer` field, plus a citation check against `evidence_page_num` — built and runnable before any ingestion code exists, so that every later pipeline change has an immediate regression signal.
28. As a developer, I want a hard cap on tool-calls (6) and per-call timeout (30s) per question in the agent loop, so that a broken multi-step chain fails fast as "insufficient data" instead of looping indefinitely or blowing the budget.
29. As a developer, I want the retrieval/database filter parameters to accept a list of companies/filings (even though only single-company questions exist today), so that extending to cross-filing comparison later doesn't require a schema rewrite.
30. As a developer, I want fiscal periods normalized (`fiscal_year`, `fiscal_quarter`) alongside the raw `period_of_report_date`, so that non-calendar-fiscal-year companies (e.g. Microsoft's June year-end) don't silently break cross-company or cross-period comparisons.
31. As a developer, I want the domain vocabulary (Filing, SourceDocument, Fact, Metric, Chunk, Segment) used consistently across code, schema, and documentation, so that "fact" doesn't ambiguously mean both a stored value and a computed ratio.

## Implementation Decisions

- **Single seam**: all functionality is exercised through one entry point, `answer_question(question, company, doc_scope) → AnswerResult`. Internal modules (router, extraction engines, cache tiers, agent loop, code-interpreter tool) are not independently exposed as test seams.
- **doc_type router**: a routing layer inspects `Filing.doc_type` before any extraction begins. `10K`/`10Q` → XBRL extraction engine (edgartools). `8K`/`Earnings` → layout-aware extraction engine (sec-parser). Routing is by `doc_type` metadata only, never inferred from question content.
- **XBRL extraction path**: map to standard US-GAAP anchor tags first (e.g. `us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax`). If a custom/extension tag is present, resolve it via the XBRL calculation linkbase (which child elements roll up into Gross Profit/Net Income) rather than manual string-matching dictionaries. If programmatic mapping fails entirely, fall back to raw HTML income-statement table extraction, passed to a cheap LLM to identify the matching GAAP line item string.
- **Layout extraction path**: sec-parser drives 8-K/Earnings-release extraction, using layout signals (boldness, spacing, geometry) rather than text pattern matching. Same engine also serves as fallback for 10-K/10-Q sections that come back as an unparsed monolithic blob (common in pre-2020 filings).
- **Messy-layout fallback trigger**: automatic — if a parsed section produces a single chunk over ~15,000 characters with no discovered sub-elements, flag it and re-route through the layout engine. This threshold ships as an initial estimate and is tuned from eval-harness failures rather than a separate calibration pass.
- **Segment data access**: segment-dimensioned statements are retrieved via `xbrl.get_statement("SegmentDisclosure").to_dataframe()`; an `is_dimensioned` boolean column distinguishes segment rows from consolidated rows. No flattening of hierarchical/dimensional data into a single flat fact table.
- **Fact vs Metric split**: a Fact is stored and versioned (tied to one accession_number, with `valid_from`/`valid_to` for restatements). A Metric is computed at query time from one or more Facts and is never persisted — always recomputed to avoid staleness.
- **Restatement handling**: a restated figure in a later filing never overwrites the original Fact row. A new Fact row is inserted, keyed to the new accession_number, with its own `valid_from`. Both are queryable; default queries return the value valid as of the filing being asked about unless the caller explicitly asks for the latest/restated view.
- **Amendment handling (10-K/A)**: an amendment is ingested as a new Filing/accession_number. The original Filing's Chunks and Facts are flagged `is_superseded = TRUE`, never deleted. Default retrieval filters `WHERE is_superseded = FALSE`; a caller can explicitly opt into superseded data.
- **Chunk schema**: `accession_number`, `item_label`, `exhibit_number` (nullable), `chunk_index`, plus a `contains_table: boolean` flag — table-derived chunks are the same entity type as narrative chunks, not a separate type.
- **Fiscal normalization**: every Filing stores the raw `period_of_report_date` plus a normalized `fiscal_year`/`fiscal_quarter` pair, so non-calendar fiscal years don't break period comparisons.
- **Caching/lookup order**: Redis cache → pgvector/batch-populated local store → live SEC EDGAR call, strictly in that order. Live calls are never triggered directly by mid-conversation agent tool-calls without first checking the cache.
- **Rate limiting**: live EDGAR calls throttled to a safe ceiling (e.g. 8 req/sec) below SEC's 10 req/sec threshold via a token-bucket/semaphore limiter; `set_identity` sets a compliant `User-Agent` globally at startup.
- **edgartools isolation**: all edgartools calls go through a `SECDataClientAdapter` abstraction class; no direct edgartools calls elsewhere in the codebase. edgartools version is pinned in the dependency manifest.
- **Agent loop architecture**: one unified multi-tool agent loop (no rigid question-type routing branches). Tools are atomic and descriptive (e.g. `get_sections_list`, `retrieve_chunks_from_section`, `get_financial_statement_dataframe`, a code-interpreter tool). The model chains calls autonomously based on the question.
- **Math execution**: all arithmetic (ratios, percentage changes, multi-period comparisons) executes in a local code-interpreter/function-tool sandbox operating on retrieved DataFrames — never as LLM-generated token-level arithmetic.
- **Agent loop budget**: hard cap of 6 tool-calls per question, 30-second timeout per call; exceeding the cap returns an explicit "insufficient data" answer rather than continuing indefinitely.
- **Query scope flexibility**: filter parameters (company, doc_scope) accept a list rather than a single scalar, even though every known question is single-company-anchored, to avoid a schema rewrite if cross-filing comparison questions are added later.
- **Ingestion scope**: limited to the 84 filings / 32 companies actually referenced by financebench's 150 open-source questions (not the full 361-filing document-information list), for development and evaluation.
- **Domain vocabulary**: code, schema, and documentation use the terms defined in `CONTEXT.md` (Filing, SourceDocument, Fact, Metric, Chunk, Segment) consistently; no synonym drift.

## Testing Decisions

- **What makes a good test here**: tests exercise `answer_question` end-to-end — a question in, an `AnswerResult` (answer + citation) out — and assert against financebench's gold `answer` and `evidence_page_num` fields. Tests do not assert on internal representations (e.g. which extraction engine ran, intermediate DataFrame shape, chunk boundaries) — only on the externally observable answer and citation.
- **Grader (the eval harness)**: a standalone component with no ingestion dependency — it is a pure function of `(system_answer, gold_answer, gold_evidence) → pass/fail`. Numeric answers pass on a ±1% tolerance after stripping currency/punctuation. Citation accuracy checks whether the returned citation's page/section metadata matches `evidence_page_num`. This is built and runnable first, before any ingestion or extraction code, so every subsequent pipeline change has an immediate regression signal.
- **Structural extraction QA**: a small fixed set of 5 filings spanning known structural variance (a cleanly structured large-cap 10-K, a custom-XBRL-heavy filer, a small-cap filing with messy older tables, a pre-2020 legacy-HTML 10-K, and an amended 10-K/A) is used for binary pass/fail eyeball checks on section-boundary extraction quality — independent of the financebench numeric grader, since it tests extraction cleanliness rather than final-answer correctness.
- **Prior art**: none — this is a greenfield codebase with no existing test suite to follow conventions from. The seam and grader design set the precedent for everything built after.
- **Cost/latency guardrails as test conditions**: the agent-loop tool-call cap (6) and timeout (30s) are treated as enforced behavior, not just a performance tuning knob — a test should confirm a pathological/looping question is stopped and answered "insufficient data" rather than running unbounded.

## Out of Scope

- Full SEC-universe ingestion (all 361 filings in financebench's document-information list, or beyond it to the full ~7,000+ public equity universe). Ingestion is scoped to the 84 filings / 32 companies the evaluation set actually touches.
- Cross-company/cross-filing synthesis questions (e.g. "compare Apple's and Microsoft's CapEx"). The schema and filter parameters are built to not preclude this later, but no such question exists in financebench today and none is being built now.
- Production deployment, horizontal scaling, multi-tenant access control, or a user-facing UI. This spec covers the answering pipeline and its evaluation only.
- sec-parser threshold calibration as a standalone exercise — the 15,000-character messy-layout trigger ships as an initial estimate and is tuned reactively from eval-harness failures, not validated in a dedicated calibration pass.
- Non-10-K/10-Q/8-K/Earnings document types (e.g. proxy statements, S-1s) — out of scope unless/until financebench's question set requires them.
- Formal multi-context domain-doc structure (`CONTEXT-MAP.md`) — this repo is single-context; no signal exists that this project will become a monorepo.

## Further Notes

- Estimated build-phase cost (gpt-4o-mini for the agent loop, text-embedding-3-small for the vector store): ~$65–155 total across the dev cycle (embedding the corpus is near-negligible, ~$0.11 per full ingestion pass; the agent-loop eval runs dominate at ~$1–3 per full 150-question pass, times 30–50 dev-cycle iterations).
- Build order: eval grader (standalone) → doc_type router + `SECDataClientAdapter` → XBRL/layout extraction → agent loop wiring. Each stage is validated against the grader before the next stage begins.
- A prior spike (`chunking stratergy/scripts/check_docling_chunks.py`) used Docling's `HybridChunker` for PDF-based chunking experiments. This is confirmed leftover from an earlier design direction and is not part of this spec's implementation path (sec-parser is the production text-extraction engine); the script can be left in place as dead code or removed.
- financebench's 150 open-source questions split evenly across three `question_type` values (50 metrics-generated, 50 domain-relevant, 50 novel-generated) — all three are answerable through the same single agent-loop architecture; none requires a structurally distinct code path, though `novel-generated` questions frequently require the same code-interpreter math path as `domain-relevant` ones despite initially looking text-only.
