# 03: XBRL single-fact extraction (standard tags)

**What to build:** `answer_question` answers a metrics-generated question by retrieving one standard US-GAAP-tagged XBRL Fact (e.g. `us-gaap:SalesRevenueNet`) via the adapter/router from ticket 02, and returns it with a full citation (accession_number, item_label).

**Blocked by:** 02

**Status:** ready-for-agent

- [ ] Given a company + fiscal period + standard-tagged concept, returns the correct numeric Fact
- [ ] Every returned Fact carries accession_number and source item_label
- [ ] Passes the subset of financebench metrics-generated questions that use standard GAAP tags, verified via the grader (01)
- [ ] Non-existent/unavailable concepts return an explicit "not found" rather than a guessed value
