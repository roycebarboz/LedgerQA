# 06: Structural text chunking + citation metadata

**What to build:** Chunk 10-K/10-Q narrative sections (Item 1A Risk Factors, Item 7 MD&A, Business Description) at structural boundaries — not fixed character counts — target 800-1000 tokens with 150-200 token overlap, section heading prepended as metadata. Embed and make retrievable. `answer_question` can answer a single-shot text-lookup question end-to-end using one retrieval call (no agent loop yet).

**Blocked by:** 02

**Status:** ready-for-agent

- [ ] Chunks respect section/paragraph boundaries; no chunk splits mid-sentence at a fixed character cutoff
- [ ] Every Chunk carries accession_number, item_label, exhibit_number (nullable), chunk_index
- [ ] A table-derived chunk uses the same Chunk type with `contains_table: true`, not a separate type
- [ ] A single-fact text-lookup question (e.g. a specific Risk Factor detail) answered end-to-end via one retrieval call, verified via the grader (01)
