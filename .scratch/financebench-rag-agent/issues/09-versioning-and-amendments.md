# 09: Point-in-time Fact versioning + amendment supersession

**What to build:** Facts are versioned by accession_number (`valid_from`/`valid_to`) so a restated figure in a later filing never overwrites the original — both remain queryable. A 10-K/A amendment is ingested as a new Filing; the original Filing's Chunks and Facts are flagged `is_superseded = TRUE` (never deleted). Default queries exclude superseded data; an explicit flag opts back in.

**Blocked by:** 03

**Status:** ready-for-agent

- [ ] Querying a prior-year Fact by default returns the value as originally filed, not a later restatement
- [ ] An explicit "latest/restated" query returns the newer accession_number's value instead
- [ ] Ingesting a 10-K/A flags the original Filing's rows `is_superseded = TRUE` without deleting them
- [ ] Default retrieval filters out superseded rows; an explicit override includes them
