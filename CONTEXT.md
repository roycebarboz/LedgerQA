# LedgerQA

A RAG system answering financial questions over SEC filings, sourcing tabular data from filer-tagged XBRL and narrative text from filing layout, joined by exact filing identity.

## Language

**Filing**:
An SEC-accepted submission with an accession_number — the official, tracked unit. Versioned: amendments (10-K/A) create a new Filing, the original is flagged `is_superseded`, never deleted.
_Avoid_: Document, submission

**SourceDocument**:
The unit financebench's `doc_name` refers to (e.g. `AMCOR_2023Q4_EARNINGS`). May wrap a Filing 1:1, wrap part of one (e.g. an 8-K's Exhibit 99.1), or stand alone with no accession_number (off-EDGAR press release) — that case is flagged as an orphan, never assigned a fake accession_number.
_Avoid_: Doc, filing (when no accession_number exists)

**Fact**:
A stored, versioned value sourced from a Filing — either an XBRL-tagged number or a layout-extracted one (8-K/Earnings path). Tied to one accession_number; a restatement in a later Filing adds a new Fact row (`valid_from`/`valid_to`), never overwrites the old one.
_Avoid_: Value, metric (see Metric), data point

**Metric**:
A number computed on demand from one or more Facts (e.g. CAPEX ÷ Revenue), produced by the code-interpreter tool at query time. Never persisted, never versioned — always recomputed so it can't go stale.
_Avoid_: Fact, ratio, derived value

**Chunk**:
A structurally-bounded piece of a Filing's narrative text (or table), carrying citation metadata (`accession_number`, `item_label`, `exhibit_number`, `chunk_index`). A table-derived Chunk is the same entity with `contains_table: true`, not a separate type.
_Avoid_: Passage, segment (see Segment — different concept), fragment

**Segment**:
A dimensional breakdown within a Filing's XBRL data (e.g. product line, business division) rather than the consolidated company-wide figure. Identified by the `is_dimensioned` flag on a statement DataFrame; a Fact can be consolidated or Segment-dimensioned, never both.
_Avoid_: Division, breakdown
