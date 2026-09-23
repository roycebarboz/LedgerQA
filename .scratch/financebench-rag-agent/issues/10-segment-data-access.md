# 10: Segment-dimensioned data access

**What to build:** Segment-level breakdowns (e.g. product line, division) retrieved via `xbrl.get_statement("SegmentDisclosure").to_dataframe()`, distinguished from consolidated totals by an `is_dimensioned` flag, queryable as distinct data rather than collapsed into consolidated figures.

**Blocked by:** 03

**Status:** ready-for-agent

- [ ] Segment-specific questions (e.g. "which segment dragged down growth?") answerable using dimensioned rows
- [ ] A query never silently mixes a segment-dimensioned Fact with a consolidated one in the same computation
- [ ] `is_dimensioned` flag correctly distinguishes segment rows from consolidated rows for a multi-segment filer
