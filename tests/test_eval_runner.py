from ledgerqa.eval_runner import EvalReport, load_gold_questions, run_eval
from ledgerqa.types import AnswerResult, Citation


def test_load_gold_questions_returns_all_150_financebench_questions():
    questions = load_gold_questions()
    assert len(questions) == 150
    assert {"financebench_id", "question", "answer", "evidence"} <= questions[0].keys()


def _always_wrong_stub(question: str, company: str, doc_scope: list[str]) -> AnswerResult:
    return AnswerResult(answer="not a real answer", citation=Citation(page_num=-1))


def _echo_gold_stub_factory(gold_by_question: dict):
    def _stub(question: str, company: str, doc_scope: list[str]) -> AnswerResult:
        gold = gold_by_question[question]
        page_num = gold["evidence"][0]["evidence_page_num"]
        return AnswerResult(answer=gold["answer"], citation=Citation(page_num=page_num))

    return _stub


def test_run_eval_has_no_ingestion_dependency_and_covers_all_150_questions():
    """Proves the grader runs standalone: a hand-written stub answer_question,
    no ingestion/extraction pipeline, still produces a full report."""
    report = run_eval(_always_wrong_stub)
    assert isinstance(report, EvalReport)
    assert len(report.results) == 150
    assert report.pass_rate == 0.0


def test_run_eval_reports_perfect_pass_rate_for_a_stub_that_echoes_gold():
    gold_questions = load_gold_questions()
    gold_by_question = {q["question"]: q for q in gold_questions}
    stub = _echo_gold_stub_factory(gold_by_question)

    report = run_eval(stub, gold_questions=gold_questions)

    assert len(report.results) == 150
    assert report.pass_rate == 1.0


def test_eval_report_exposes_per_question_pass_fail():
    report = run_eval(_always_wrong_stub, gold_questions=load_gold_questions()[:3])
    assert [r.passed for r in report.results] == [False, False, False]
