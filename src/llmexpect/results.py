"""Result objects and the global collector every assertion reports into.

Every assertion produces one :class:`CheckResult`. The :class:`Collector` keeps
them for the duration of a test session so the pytest plugin can turn them into
a report. Categories map each check onto one of the six Trust Score sub-scores.
"""
from __future__ import annotations

import threading
import time
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

# The six sub-scores of the Trust Score. Every check belongs to exactly one.
CATEGORIES = ("accuracy", "groundedness", "relevance", "safety", "consistency", "format")

CATEGORY_LABELS = {
    "accuracy": "Accuracy",
    "groundedness": "Groundedness",
    "relevance": "Relevance",
    "safety": "Safety",
    "consistency": "Consistency",
    "format": "Format",
}

CATEGORY_HELP = {
    "accuracy": "Does the answer say what it should say?",
    "groundedness": "Is every claim supported by the source material (no hallucination)?",
    "relevance": "Does the answer address the question that was asked?",
    "safety": "Free of PII, banned content, and unsafe compliance?",
    "consistency": "Does the model give a passing answer reliably across repeated runs?",
    "format": "Length, schema, JSON, regex and other structural constraints.",
}


@dataclass
class CheckResult:
    """One assertion outcome."""

    name: str                 # e.g. "to_mean"
    category: str             # one of CATEGORIES
    tier: int                 # 1 = rules, 2 = embeddings, 3 = LLM judge
    passed: bool
    score: float              # 0..1, how well the text satisfied the check
    reason: str = ""          # human explanation, shown in the report
    text: str = ""            # the AI text under test (truncated in reports)
    expected: str = ""        # what we compared against, if any
    details: Dict[str, Any] = field(default_factory=dict)
    test_id: str = ""         # pytest node id, when available
    duration_ms: float = 0.0
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class Collector:
    """Thread-safe store for all CheckResults in a session."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._results: List[CheckResult] = []
        self.current_test_id: str = ""

    def add(self, result: CheckResult) -> None:
        with self._lock:
            if not result.test_id:
                result.test_id = self.current_test_id
            self._results.append(result)

    def results(self) -> List[CheckResult]:
        with self._lock:
            return list(self._results)

    def clear(self) -> None:
        with self._lock:
            self._results.clear()

    def __len__(self) -> int:
        return len(self._results)


# One collector per process. The pytest plugin reads from it at session end.
collector = Collector()


def summarize(results: List[CheckResult]) -> Dict[str, Any]:
    """Compute the Trust Score and sub-scores from a list of results.

    Trust Score is the plain mean of the available category scores, scaled
    to 0-100. A category with no checks is reported as ``None`` and ignored,
    so a suite that never tests safety is not penalised for it, but the
    report says so.
    """
    by_cat: Dict[str, List[CheckResult]] = {c: [] for c in CATEGORIES}
    for r in results:
        by_cat.setdefault(r.category, []).append(r)

    subscores: Dict[str, Optional[float]] = {}
    for cat in CATEGORIES:
        rs = by_cat.get(cat, [])
        subscores[cat] = round(100 * sum(r.score for r in rs) / len(rs), 1) if rs else None

    present = [v for v in subscores.values() if v is not None]
    trust = round(sum(present) / len(present), 1) if present else None

    by_check: Dict[str, Dict[str, Any]] = {}
    for r in results:
        b = by_check.setdefault(r.name, {"total": 0, "passed": 0, "tier": r.tier, "category": r.category})
        b["total"] += 1
        b["passed"] += int(r.passed)
    for b in by_check.values():
        b["pass_rate"] = round(100 * b["passed"] / b["total"], 1) if b["total"] else 0.0

    by_test: Dict[str, Dict[str, Any]] = {}
    for r in results:
        t = by_test.setdefault(r.test_id or "(no test)", {"total": 0, "passed": 0})
        t["total"] += 1
        t["passed"] += int(r.passed)

    total = len(results)
    passed = sum(1 for r in results if r.passed)
    return {
        "trust_score": trust,
        "subscores": subscores,
        "total_checks": total,
        "passed_checks": passed,
        "failed_checks": total - passed,
        "pass_rate": round(100 * passed / total, 1) if total else 0.0,
        "by_check": by_check,
        "by_test": by_test,
        "tiers": {
            "1": sum(1 for r in results if r.tier == 1),
            "2": sum(1 for r in results if r.tier == 2),
            "3": sum(1 for r in results if r.tier == 3),
        },
    }
