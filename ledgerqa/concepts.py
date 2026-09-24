"""Question text -> (fiscal_year, unit scale, standard US-GAAP concept candidates).

Covers only financebench's single-Fact metrics-generated questions: one line
item, one fiscal year, no ratio/average/YoY computation across multiple Facts.
Those computed questions need the code-interpreter agent loop (ticket 08);
a non-GAAP/custom-tagged metric (e.g. "adjusted EBITDA") isn't in this table at
all and resolves to no concept, same as an unrecognized one — both need ticket
04's calculation-linkbase/LLM fallback, not a guess here.
"""

import re
from dataclasses import dataclass

_FISCAL_YEAR_RE = re.compile(r"\bFY\s*(\d{4})\b", re.IGNORECASE)
_SCALE_BY_WORD = {"million": 1_000_000, "billion": 1_000_000_000}
_SCALE_RE = re.compile(r"\b(million|billion)s?\b", re.IGNORECASE)

# A question asking for a ratio/average/change/non-GAAP roll-up across more
# than one Fact — that needs the code-interpreter agent loop (ticket 08) or a
# non-GAAP tag fallback (ticket 04), never a single raw Fact answered as if it
# were the whole answer.
_COMPUTED_QUESTION_RE = re.compile(
    r"ratio|%|percent|average|turnover|margin|payout|growth|cagr|yoy|year-over-year|"
    r"\bdpo\b|\bdso\b|\bccc\b|ebitda|net working capital",
    re.IGNORECASE,
)


def extract_fiscal_year(question: str) -> int | None:
    match = _FISCAL_YEAR_RE.search(question)
    return int(match.group(1)) if match else None


def extract_scale(question: str) -> int:
    """Divide a raw XBRL dollar value by this to match the question's stated unit."""
    match = _SCALE_RE.search(question)
    return _SCALE_BY_WORD[match.group(1).lower()] if match else 1


@dataclass(frozen=True)
class ConceptRule:
    trigger: re.Pattern[str]
    concepts: tuple[str, ...]


# Ordered most-specific first: a rule higher in this list wins when a question
# text could match more than one (e.g. "total current assets" before "total assets").
_RULES: tuple[ConceptRule, ...] = (
    ConceptRule(
        re.compile(r"capital expenditure|capex", re.IGNORECASE),
        (
            "us-gaap:PaymentsToAcquirePropertyPlantAndEquipment",
            "us-gaap:PaymentsForCapitalImprovements",
        ),
    ),
    ConceptRule(
        re.compile(r"net (?:property,? plant,? and equipment|ppn?e)", re.IGNORECASE),
        ("us-gaap:PropertyPlantAndEquipmentNet",),
    ),
    ConceptRule(
        re.compile(r"net (?:accounts receivable|ar)\b", re.IGNORECASE),
        ("us-gaap:AccountsReceivableNetCurrent", "us-gaap:ReceivablesNetCurrent"),
    ),
    ConceptRule(
        re.compile(r"cash dividends|dividends paid", re.IGNORECASE),
        ("us-gaap:PaymentsOfDividendsCommonStock", "us-gaap:PaymentsOfDividends"),
    ),
    ConceptRule(
        re.compile(r"net income", re.IGNORECASE),
        (
            "us-gaap:NetIncomeLossAttributableToParent",
            "us-gaap:ProfitLoss",
            "us-gaap:NetIncomeLoss",
        ),
    ),
    ConceptRule(
        re.compile(r"operating income", re.IGNORECASE),
        ("us-gaap:OperatingIncomeLoss",),
    ),
    ConceptRule(
        re.compile(r"cash flow from operating activities|cash from operations", re.IGNORECASE),
        ("us-gaap:NetCashProvidedByUsedInOperatingActivities",),
    ),
    ConceptRule(
        re.compile(r"total current assets", re.IGNORECASE),
        ("us-gaap:AssetsCurrent",),
    ),
    ConceptRule(
        re.compile(r"total current liabilities", re.IGNORECASE),
        ("us-gaap:LiabilitiesCurrent",),
    ),
    ConceptRule(
        re.compile(r"accounts payable", re.IGNORECASE),
        ("us-gaap:AccountsPayableCurrent", "us-gaap:AccountsPayableTradeCurrent"),
    ),
    ConceptRule(
        re.compile(r"\bcogs\b|cost of goods sold", re.IGNORECASE),
        ("us-gaap:CostOfGoodsAndServicesSold", "us-gaap:CostOfRevenue", "us-gaap:CostOfGoodsSold"),
    ),
    ConceptRule(
        re.compile(r"inventor(?:y|ies)", re.IGNORECASE),
        ("us-gaap:InventoryNet",),
    ),
    ConceptRule(
        re.compile(r"total assets", re.IGNORECASE),
        ("us-gaap:Assets",),
    ),
    ConceptRule(
        re.compile(r"total liabilities", re.IGNORECASE),
        ("us-gaap:Liabilities",),
    ),
)


def resolve_concepts(question: str) -> tuple[str, ...] | None:
    """Standard US-GAAP concept candidates for `question`'s line item, tried in order.

    None both when no rule's line-item phrase matches and when the question
    asks for a ratio/average/non-GAAP roll-up a single Fact can't answer.
    """
    if _COMPUTED_QUESTION_RE.search(question):
        return None
    for rule in _RULES:
        if rule.trigger.search(question):
            return rule.concepts
    return None
