"""Runs the grader against financebench's 150 open-source questions.

Depends only on `ledgerqa.grader` and an `answer_question`-shaped callable —
no ingestion or extraction pipeline is required to exercise this module.
"""

import json
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from ledgerqa.grader import GradeResult, grade
from ledgerqa.types import AnswerResult

DEFAULT_DATASET_PATH = (
    Path(__file__).resolve().parent.parent / "financebench" / "data" / "financebench_open_source.jsonl"
)

AnswerQuestionFn = Callable[[str, str, list[str]], AnswerResult]


def load_gold_questions(path: Path = DEFAULT_DATASET_PATH) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


@dataclass(frozen=True)
class EvalReport:
    results: list[GradeResult]

    @property
    def pass_rate(self) -> float:
        if not self.results:
            return 0.0
        return sum(1 for r in self.results if r.passed) / len(self.results)


def run_eval(
    answer_question: AnswerQuestionFn,
    gold_questions: list[dict] | None = None,
) -> EvalReport:
    questions = gold_questions if gold_questions is not None else load_gold_questions()
    results = [
        grade(answer_question(q["question"], q["company"], [q["doc_name"]]), q) for q in questions
    ]
    return EvalReport(results=results)


def format_report(report: EvalReport) -> str:
    lines = [f"{r.financebench_id}: {'PASS' if r.passed else 'FAIL'}" for r in report.results]
    lines.append(f"Pass rate: {report.pass_rate:.1%} ({sum(r.passed for r in report.results)}/{len(report.results)})")
    return "\n".join(lines)


if __name__ == "__main__":

    def stub_answer_question(question: str, company: str, doc_scope: list[str]) -> AnswerResult:
        from ledgerqa.types import Citation

        return AnswerResult(answer="stub: no pipeline wired up yet", citation=Citation(page_num=-1))

    print(format_report(run_eval(stub_answer_question)))
