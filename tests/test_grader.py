from ledgerqa.grader import citation_matches, grade, numeric_match, parse_numeric
from ledgerqa.types import AnswerResult, Citation

GOLD_QUESTION = {
    "financebench_id": "financebench_id_03029",
    "answer": "$1577.00",
    "evidence": [{"evidence_page_num": 59}],
}


def test_parse_numeric_strips_currency_and_commas():
    assert parse_numeric("$1,577.00") == 1577.0


def test_parse_numeric_handles_parenthesized_negatives():
    assert parse_numeric("(1,577)") == -1577.0


def test_parse_numeric_returns_none_for_non_numeric_text():
    assert parse_numeric("Yes, 3M is capital-intensive") is None


def test_numeric_match_within_one_percent_tolerance_passes():
    assert numeric_match("$1580.00", "$1577.00") is True


def test_numeric_match_beyond_one_percent_tolerance_fails():
    assert numeric_match("$1700.00", "$1577.00") is False


def test_numeric_match_is_none_when_either_side_is_non_numeric():
    assert numeric_match("no data", "$1577.00") is None


def test_citation_matches_when_page_num_in_gold_evidence():
    result = AnswerResult(answer="$1577.00", citation=Citation(page_num=59))
    assert citation_matches(result, GOLD_QUESTION) is True


def test_citation_matches_false_when_page_num_differs():
    result = AnswerResult(answer="$1577.00", citation=Citation(page_num=12))
    assert citation_matches(result, GOLD_QUESTION) is False


def test_grade_passes_on_correct_numeric_answer_and_citation():
    result = AnswerResult(answer="$1577.00", citation=Citation(page_num=59))
    outcome = grade(result, GOLD_QUESTION)
    assert outcome.numeric_match is True
    assert outcome.citation_match is True
    assert outcome.passed is True


def test_grade_fails_when_citation_wrong_even_if_answer_correct():
    result = AnswerResult(answer="$1577.00", citation=Citation(page_num=1))
    outcome = grade(result, GOLD_QUESTION)
    assert outcome.numeric_match is True
    assert outcome.citation_match is False
    assert outcome.passed is False


def test_grade_falls_back_to_text_match_for_non_numeric_gold_answer():
    gold = {
        "financebench_id": "financebench_id_qual",
        "answer": "Yes, 3M is capital-intensive.",
        "evidence": [{"evidence_page_num": 4}],
    }
    result = AnswerResult(answer="Yes, 3M is capital-intensive.", citation=Citation(page_num=4))
    outcome = grade(result, gold)
    assert outcome.numeric_match is None
    assert outcome.passed is True
