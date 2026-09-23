# 05: Layout extraction engine (8-K/Earnings)

**What to build:** A sec-parser-driven extraction path for SourceDocuments whose Filing has no XBRL backend (`doc_type` 8-K/Earnings), using layout signals (boldness, spacing, geometry) rather than text pattern matching, so simple metric/text questions sourced from these documents are answerable.

**Blocked by:** 02

**Status:** ready-for-agent

- [ ] Routed to automatically for `doc_type` 8-K/Earnings via the router from ticket 02, never for 10-K/10-Q
- [ ] Extracts identifiable line items/values from non-XBRL HTML tables (e.g. earnings-release figures)
- [ ] Answers carry a citation (accession_number, item_label where applicable)
- [ ] Verified against the financebench questions anchored to 8-K/Earnings SourceDocuments, via the grader (01)
