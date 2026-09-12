import json
import random

import pytest

from aiexpect import collector, consistent, expect, summarize
from aiexpect.report import build_payload, render_html


def test_consistent_passes_on_rate():
    calls = {"n": 0}

    @consistent(samples=5, min_pass_rate=0.6)
    def body():
        calls["n"] += 1
        expect("ok" if calls["n"] != 2 else "bad").to_contain("ok")

    body()
    assert calls["n"] == 5
    last = collector.results()[-1]
    assert last.name == "consistent" and last.score == 0.8


def test_consistent_fails_below_rate():
    @consistent(samples=4, min_pass_rate=1.0)
    def body():
        expect(random.choice(["a", "b"])).to_contain("zzz")

    with pytest.raises(AssertionError, match="0/4 runs"):
        body()


def test_consistent_keeps_signature_for_fixtures():
    import inspect

    @consistent(samples=2)
    def body(tmp_path, monkeypatch):
        pass

    assert list(inspect.signature(body).parameters) == ["tmp_path", "monkeypatch"]


def test_summary_and_html_render(tmp_path):
    collector.clear()
    expect("hello 30 days").to_contain("30 days").to_not_contain_pii()
    expect("no json here", soft=True).to_be_json()
    results = collector.results()
    s = summarize(results)
    assert s["total_checks"] == 3 and s["failed_checks"] == 1
    assert s["subscores"]["accuracy"] == 100.0
    assert s["subscores"]["format"] == 0.0
    assert s["subscores"]["groundedness"] is None
    assert s["trust_score"] == round((100 + 100 + 0) / 3, 1)

    payload = build_payload(results, meta={"suite": "unit"})
    html = render_html(payload)
    assert "Trust Score" in html and "to_be_json" in html and "<svg" in html
    p = tmp_path / "r.html"
    p.write_text(html)
    json.dumps(payload)  # must be serialisable
