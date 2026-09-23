# 07: Messy-layout auto-fallback

**What to build:** Automatic detection of a messy/unparsed section — a single chunk over ~15,000 characters with no discovered sub-elements — that re-routes that section through the layout engine (05) instead of the standard structural chunker (06). No manually maintained override list.

**Blocked by:** 05, 06

**Status:** ready-for-agent

- [ ] Oversized, sub-element-free chunks trigger the fallback automatically, no manual flagging required
- [ ] Fallback re-extraction produces cleanly bounded chunks (verified against the 5-filing structural QA set: clean/custom-XBRL-heavy/small-cap/pre-2020/amended)
- [ ] The 15,000-character threshold is recorded as a tunable constant, not hardcoded inline in multiple places
