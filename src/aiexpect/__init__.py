"""aiexpect - assertions for non-deterministic AI text.

    from aiexpect import expect
    expect(reply).to_mean("you can return within 30 days").to_not_contain_pii()
"""
from . import history, probes, snapshots
from .config import configure, settings
from .consistency import consistent
from .expectation import Expectation, ExpectationFailed, expect, expect_ai
from .results import CheckResult, collector, summarize

__version__ = "0.2.2"
__all__ = [
    "CheckResult",
    "Expectation",
    "ExpectationFailed",
    "__version__",
    "collector",
    "configure",
    "consistent",
    "expect",
    "expect_ai",
    "history",
    "probes",
    "snapshots",
    "settings",
    "summarize",
]
