from dataclasses import dataclass


@dataclass(frozen=True)
class Citation:
    page_num: int


@dataclass(frozen=True)
class AnswerResult:
    answer: str
    citation: Citation
