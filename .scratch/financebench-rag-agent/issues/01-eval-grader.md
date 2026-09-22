# 01: Eval grader (standalone)

**What to build:** A runnable scorer that takes an `AnswerResult` (answer + citation) and financebench's gold `answer`/`evidence_page_num` fields and reports pass/fail, with zero dependency on any ingestion or extraction code — it must run today against a hand-written stub `answer_question` that returns hardcoded values.

**Blocked by:** None (can start immediately)

**Status:** done

- [x] Numeric answers compared with ±1% tolerance after stripping currency symbols/punctuation
- [x] Citation accuracy checked: returned citation's page/section metadata matches `evidence_page_num`
- [x] Runs against all 150 financebench open-source questions and reports per-question pass/fail plus an aggregate pass rate
- [x] Runs successfully against a stub `answer_question` (no real pipeline required) to prove it has no ingestion dependency

## Comments

Implemented in `ledgerqa/grader.py` (pure `grade(result, gold_question)`) and `ledgerqa/eval_runner.py` (`run_eval`, `load_gold_questions`, `format_report`). Tests in `tests/test_grader.py` and `tests/test_eval_runner.py`; the latter runs the full 150-question dataset against both a failing stub and a gold-echoing stub with zero ingestion imports. Non-numeric gold answers fall back to normalized string equality (not specified in the checklist but needed since ~1/3 of financebench answers are qualitative).
