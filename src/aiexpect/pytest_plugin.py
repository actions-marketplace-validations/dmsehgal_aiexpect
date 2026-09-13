"""pytest integration. Auto-loaded via the ``pytest11`` entry point.

    pytest --aiexpect-report=report.html --aiexpect-json=report.json

Both default to ``aiexpect-report.html`` / ``.json`` in the current directory;
``--aiexpect-no-report`` disables them. A one-line Trust Score summary is
printed at the end of every run that used aiexpect.
"""
from __future__ import annotations

import os
from typing import Any

import pytest

from . import history as history_mod
from . import snapshots
from .config import settings
from .report import build_payload, render_html, write_json
from .results import CATEGORY_LABELS, collector


def pytest_addoption(parser: Any) -> None:
    group = parser.getgroup("aiexpect", "aiexpect: assertions for AI text")
    group.addoption("--aiexpect-report", default="aiexpect-report.html", metavar="PATH", help="HTML report path")
    group.addoption("--aiexpect-json", default="aiexpect-report.json", metavar="PATH", help="JSON report path")
    group.addoption("--aiexpect-no-report", action="store_true", help="Do not write aiexpect reports")
    group.addoption("--aiexpect-judge", default=None, metavar="SPEC", help="LLM judge, e.g. ollama:llama3.2 or anthropic:claude-opus-5")
    group.addoption("--aiexpect-min-trust", type=float, default=None, metavar="N",
                    help="Fail the session if the Trust Score is below N (0-100)")
    group.addoption("--aiexpect-update-snapshots", action="store_true", help="Overwrite semantic snapshots")
    group.addoption("--aiexpect-snapshot-mode", default=None, choices=["auto", "strict", "update"],
                    help="auto: create missing snapshots, strict: fail on missing (CI), update: overwrite")
    group.addoption("--aiexpect-history", default=None, metavar="PATH",
                    help="Run history file for the trend chart (default .aiexpect_history.jsonl; 'none' disables)")


def pytest_configure(config: Any) -> None:
    spec = config.getoption("--aiexpect-judge")
    if spec:
        from .config import configure

        configure(judge=spec)
    if config.getoption("--aiexpect-update-snapshots"):
        settings.snapshot_mode = "update"
    elif config.getoption("--aiexpect-snapshot-mode"):
        settings.snapshot_mode = config.getoption("--aiexpect-snapshot-mode")
    hist = config.getoption("--aiexpect-history")
    if hist is not None:
        settings.history_path = "" if hist.lower() == "none" else hist
    snapshots.reset_counters()
    config.addinivalue_line("markers", "aiexpect: test uses aiexpect assertions")


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_call(item: Any):
    collector.current_test_id = item.nodeid
    yield
    collector.current_test_id = ""


@pytest.fixture
def aiexpect_results():
    """Results recorded so far in this session (list of CheckResult)."""
    return collector.results()


def pytest_sessionfinish(session: Any, exitstatus: int) -> None:
    results = collector.results()
    if not results:
        return
    config = session.config
    payload = build_payload(results, meta={"rootdir": str(config.rootdir)})
    config._aiexpect_summary = payload["summary"]  # for terminal summary
    if config.getoption("--aiexpect-no-report"):
        return
    history_mod.append(payload["summary"])
    payload["history"] = history_mod.load()
    html_path = config.getoption("--aiexpect-report")
    json_path = config.getoption("--aiexpect-json")
    if json_path:
        write_json(json_path, results, payload["meta"], payload["history"])
    if html_path:
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(render_html(payload))
    config._aiexpect_paths = (html_path, json_path)
    min_trust = config.getoption("--aiexpect-min-trust")
    if min_trust is not None and payload["summary"]["trust_score"] is not None:
        if payload["summary"]["trust_score"] < min_trust:
            session.exitstatus = 1


def pytest_terminal_summary(terminalreporter: Any, exitstatus: int, config: Any) -> None:
    s = getattr(config, "_aiexpect_summary", None)
    if not s:
        return
    tr = terminalreporter
    tr.write_sep("=", "aiexpect")
    trust = s["trust_score"]
    tr.write_line(f"Trust Score: {trust:.0f}/100" if trust is not None else "Trust Score: n/a")
    parts = []
    for cat, v in s["subscores"].items():
        parts.append(f"{CATEGORY_LABELS[cat]} {v:.0f}" if v is not None else f"{CATEGORY_LABELS[cat]} –")
    tr.write_line("  " + " · ".join(parts))
    tr.write_line(f"  {s['passed_checks']}/{s['total_checks']} checks passed ({s['pass_rate']:.0f}%)")
    min_trust = config.getoption("--aiexpect-min-trust")
    if min_trust is not None and trust is not None and trust < min_trust:
        tr.write_line(f"  FAILED: Trust Score {trust:.0f} is below --aiexpect-min-trust={min_trust:g}", red=True)
    paths = getattr(config, "_aiexpect_paths", None)
    if paths and paths[0]:
        full = os.path.abspath(paths[0])
        try:
            shown = os.path.relpath(full)
        except ValueError:  # different drive on Windows
            shown = full
        tr.write_line(f"  report: {shown if not shown.startswith('..') else full}")
