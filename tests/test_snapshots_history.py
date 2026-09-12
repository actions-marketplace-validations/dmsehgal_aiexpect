import json

import pytest

import aiexpect
from aiexpect import ExpectationFailed, collector, expect, history, snapshots
from aiexpect.report import build_payload, render_html


@pytest.fixture(autouse=True)
def _snapshot_dir(tmp_path):
    aiexpect.settings.snapshot_dir = str(tmp_path / "snaps")
    aiexpect.settings.snapshot_mode = "auto"
    snapshots.reset_counters()
    collector.current_test_id = "tests/test_x.py::test_demo"
    yield
    collector.current_test_id = ""


def test_snapshot_created_then_matched():
    e = expect("You can return items within 30 days.").to_match_snapshot()
    assert e.results[-1].details["created"] is True
    snapshots.reset_counters()
    expect("Items can be returned within 30 days.").to_match_snapshot()  # reworded, same meaning


def test_snapshot_drift_fails():
    expect("Returns accepted within 30 days.").to_match_snapshot()
    snapshots.reset_counters()
    with pytest.raises(ExpectationFailed, match="update-snapshots"):
        expect("The weather in Paris is lovely in spring.").to_match_snapshot()


def test_snapshot_strict_mode_fails_on_missing():
    aiexpect.settings.snapshot_mode = "strict"
    with pytest.raises(ExpectationFailed, match="strict"):
        expect("anything").to_match_snapshot()


def test_snapshot_update_mode_overwrites():
    expect("first").to_match_snapshot(name="n")
    aiexpect.settings.snapshot_mode = "update"
    e = expect("second").to_match_snapshot(name="n")
    assert "updated" in e.results[-1].reason
    assert snapshots.load(snapshots.snapshot_key(collector.current_test_id, "n"))["text"] == "second"


def test_multiple_unnamed_snapshots_get_distinct_keys():
    k1 = snapshots.snapshot_key("t::a", None)
    k2 = snapshots.snapshot_key("t::a", None)
    assert k1 != k2 and "/" not in k1 and ":" not in k1


def test_history_append_load_and_trend(tmp_path):
    p = tmp_path / "h.jsonl"
    for v in (60, 72.5, 81):
        history.append({"trust_score": v, "subscores": {}, "total_checks": 3, "passed_checks": 2}, str(p))
    rows = history.load(str(p))
    assert [r["trust_score"] for r in rows] == [60, 72.5, 81]
    assert len(history.load(str(p), limit=2)) == 2
    payload = build_payload(collector.results(), history=rows)
    html = render_html(payload)
    assert "Trust Score trend" in html and json.dumps(payload)


def test_trend_needs_two_runs():
    html = render_html(build_payload([], history=[{"ts": "x", "trust_score": 50}]))
    assert "two or more runs" in html
