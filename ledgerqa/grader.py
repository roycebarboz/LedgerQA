"""Pure (system_answer, gold_question) -> pass/fail grader.

No ingestion or extraction dependency: this module only knows about
`AnswerResult` and financebench's gold JSON records.
"""

import re
from dataclasses import dataclass

from ledgerqa.types import AnswerResult

NUMERIC_TOLERANCE = 0.01

_NON_NUMERIC_CHARS_RE = re.compile(r"[^0-9.\-]")


def parse_numeric(value: str) -> float | None:
    """Parse a numeric answer, stripping currency symbols/punctuation.

    Accounting-style negatives written as "(1,577)" are honored.
    Returns None when the value isn't numeric (qualitative answers).
    """
    cleaned = value.strip().replace(",", "")
    is_paren_negative = cleaned.startswith("(") and cleaned.endswith(")")
    cleaned = _NON_NUMERIC_CHARS_RE.sub("", cleaned)
    if cleaned in ("", "-", "."):
        return None
    try:
        number = float(cleaned)
    except ValueError:
        return None
    return -number if is_paren_negative else number


def numeric_match(system_value: str, gold_value: str) -> bool | None:
    """±1% tolerance numeric comparison. None if either side isn't numeric."""
    system_num = parse_numeric(system_value)
    gold_num = parse_numeric(gold_value)
    if system_num is None or gold_num is None:
        return None
    if gold_num == 0:
        return system_num == 0
    return abs(system_num - gold_num) / abs(gold_num) <= NUMERIC_TOLERANCE


def text_match(system_value: str, gold_value: str) -> bool:
    return system_value.strip().lower() == gold_value.strip().lower()


def citation_matches(result: AnswerResult, gold_question: dict) -> bool:
    gold_pages = {
        e["evidence_page_num"]
        for e in gold_question.get("evidence", [])
        if e.get("evidence_page_num") is not None
    }
    if not gold_pages:
        return False
    return result.citation.page_num in gold_pages


@dataclass(frozen=True)
class GradeResult:
    financebench_id: str
    numeric_match: bool | None
    citation_match: bool
    passed: bool


def grade(result: AnswerResult, gold_question: dict) -> GradeResult:
    gold_answer = gold_question["answer"]
    num_match = numeric_match(result.answer, gold_answer)
    answer_ok = num_match if num_match is not None else text_match(result.answer, gold_answer)
    cite_ok = citation_matches(result, gold_question)
    return GradeResult(
        financebench_id=gold_question["financebench_id"],
        numeric_match=num_match,
        citation_match=cite_ok,
        passed=bool(answer_ok) and cite_ok,
    )
