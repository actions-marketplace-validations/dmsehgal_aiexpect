"""Run a test body several times and pass on a pass-rate, not a single sample.

    @llmexpect.consistent(samples=5, min_pass_rate=0.8)
    def test_refund_policy(bot):
        expect(bot.ask("refund policy?")).to_mean("30-day returns")

Non-deterministic output makes a single run a coin flip. This turns the flake
into a measurement and records it under the Consistency sub-score.
"""
from __future__ import annotations

import functools
import inspect
from typing import Any, Callable, List

from .results import CheckResult, collector


def consistent(samples: int = 5, min_pass_rate: float = 0.8) -> Callable:
    if samples < 1:
        raise ValueError("samples must be >= 1")
    if not 0 <= min_pass_rate <= 1:
        raise ValueError("min_pass_rate must be between 0 and 1")

    def deco(fn: Callable) -> Callable:
        if inspect.iscoroutinefunction(fn):
            raise TypeError("@consistent does not support async tests yet")

        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> None:
            failures: List[str] = []
            for i in range(samples):
                try:
                    fn(*args, **kwargs)
                except AssertionError as e:
                    failures.append(f"run {i + 1}: {str(e).splitlines()[0]}")
            passed_runs = samples - len(failures)
            rate = passed_runs / samples
            ok = rate >= min_pass_rate
            collector.add(
                CheckResult(
                    name="consistent",
                    category="consistency",
                    tier=1,
                    passed=ok,
                    score=rate,
                    reason=f"{passed_runs}/{samples} runs passed ({rate:.0%}), required {min_pass_rate:.0%}",
                    details={"samples": samples, "min_pass_rate": min_pass_rate, "failures": failures},
                )
            )
            if not ok:
                raise AssertionError(
                    f"consistency: only {passed_runs}/{samples} runs passed ({rate:.0%}), "
                    f"required {min_pass_rate:.0%}\n" + "\n".join("  " + f for f in failures)
                )

        wrapper.__llmexpect_consistent__ = {"samples": samples, "min_pass_rate": min_pass_rate}  # type: ignore[attr-defined]
        return wrapper

    return deco
