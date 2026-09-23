# 04: XBRL custom-tag fallback (calc linkbase → LLM table fallback)

**What to build:** When a company uses a custom/extension XBRL tag instead of a standard one (e.g. `tsla_AutomotiveSalesRevenue`), resolve it by walking the XBRL calculation linkbase to find what it rolls up into. If that fails, fall back to extracting the raw HTML income-statement table and asking a cheap LLM to identify the matching GAAP line item string.

**Blocked by:** 03

**Status:** ready-for-agent

- [ ] Custom tags resolved via calculation linkbase before any LLM fallback is attempted
- [ ] LLM table-extraction fallback only triggers when linkbase resolution fails outright
- [ ] Raises pass rate on the financebench metrics-generated questions that use non-standard tags, verified via the grader (01)
- [ ] Fallback path's answer still carries a full citation (accession_number, item_label)
