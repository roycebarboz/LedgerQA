# 13: Full 150-question eval run + threshold tuning

**What to build:** Run the complete pipeline against all 150 financebench open-source questions through the grader (01), producing an aggregate and per-question-type pass-rate report. Use the real failures to tune the messy-layout threshold from ticket 07 (initially an unvalidated 15,000-character guess) instead of a separate calibration pass.

**Blocked by:** 04, 07, 08, 09, 10, 11, 12

**Status:** ready-for-agent

- [ ] Full 150-question run completes and produces a pass-rate report broken down by question_type (metrics-generated/domain-relevant/novel-generated)
- [ ] Messy-layout threshold (07) adjusted based on observed false-positive/false-negative fallback triggers from real failures
- [ ] Failure cases are categorized (wrong routing, extraction miss, math error, citation mismatch) to guide any follow-up tickets
