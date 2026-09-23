# 08: Multi-tool agent loop + code-interpreter math

**What to build:** The full `answer_question` entry point — one unified agent loop with atomic tools (`get_sections_list`, `retrieve_chunks_from_section`, `get_financial_statement_dataframe`, a code-interpreter tool) that the model chains autonomously. All arithmetic (ratios, percentage changes, multi-period comparisons) executes in the code-interpreter sandbox, never as LLM token-level output. A hard cap of 6 tool-calls and 30s per call is enforced.

**Blocked by:** 03, 06

**Status:** ready-for-agent

- [ ] Domain-relevant computed questions (e.g. "Is 3M capital-intensive?") answered correctly by chaining retrieval + XBRL facts + code-interpreter math
- [ ] No arithmetic appears as raw LLM-generated text output; all computed values trace back to a code-interpreter execution
- [ ] Exceeding 6 tool-calls or a 30s per-call timeout returns an explicit "insufficient data" answer rather than continuing or erroring unhandled
- [ ] Answers still carry full citation back to the Facts/Chunks used
- [ ] Verified against the financebench domain-relevant and novel-generated question slices, via the grader (01)
