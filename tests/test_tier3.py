import pytest

from aiexpect import ExpectationFailed, expect
from aiexpect.backends import judges

POLICY = "Returns accepted within 30 days. Refunds take 5 business days."


def test_grounded():
    e = expect("You can return within 30 days; refunds take about 5 business days.").to_be_grounded_in(POLICY)
    assert e.results[-1].tier == 3
    assert e.results[-1].details["judge"] == "fake:keyword"


def test_hallucination_caught():
    with pytest.raises(ExpectationFailed, match="unicorn"):
        expect("Returns within 30 days, and every order ships with a free unicorn.").to_be_grounded_in(POLICY)


def test_answer_and_tone():
    expect("Refunds take 5 business days.").to_answer("How long do refunds take?").to_have_tone("polite and concise")
    with pytest.raises(ExpectationFailed, match="rude"):
        expect("Ugh, read the FAQ. grumpy.").to_have_tone("polite")


def test_rubric_and_consistent_with():
    expect("Step 1: unplug. Step 2: wait 10s. Step 3: plug in.").to_satisfy("Gives numbered steps", category="format")
    expect("Refunds take 5 days.").to_be_consistent_with("Refund processing time is five days.")


def test_judge_cache_hits(tmp_path):
    import aiexpect

    aiexpect.settings.cache = True
    j = judges._judge
    v1 = j.judge("TASK: anything")
    v2 = j.judge("TASK: anything")
    assert not v1.cached and v2.cached


def test_judge_json_parsing():
    assert judges._parse_verdict('prefix {"score": 2, "reason": "x"} suffix')["score"] == 1.0
    with pytest.raises(judges.JudgeError):
        judges._parse_verdict("no json here")


def test_no_judge_configured_message(monkeypatch):
    monkeypatch.setattr(judges, "_judge", None)
    monkeypatch.setattr(judges, "_resolved", False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr(judges, "_ollama_reachable", lambda: False)
    with pytest.raises(judges.JudgeError, match="ollama"):
        expect("x").to_be_grounded_in("y")


def test_from_spec():
    assert isinstance(judges.from_spec("ollama:llama3.1"), judges.OllamaJudge)
    j = judges.from_spec("openai-compatible:qwen@http://localhost:8000/v1")
    assert j.model == "qwen" and j.base_url == "http://localhost:8000/v1"
    with pytest.raises(judges.JudgeError):
        judges.from_spec("nope")
