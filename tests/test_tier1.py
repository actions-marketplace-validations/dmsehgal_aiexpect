import pytest

from llmexpect import ExpectationFailed, expect


def test_contains_and_not_contains():
    expect("You can return items within 30 days.").to_contain("30 days").to_not_contain("no refunds")


def test_missing_phrase_fails():
    with pytest.raises(ExpectationFailed, match="missing"):
        expect("Hello").to_contain("goodbye")


def test_regex():
    expect("Order #12345 shipped").to_match(r"#\d{5}").to_not_match(r"cancel")


def test_length():
    expect("one two three").to_have_length(min=2, max=5, unit="words")
    with pytest.raises(ExpectationFailed):
        expect("x" * 500).to_have_length(max=100)


def test_json_and_schema():
    text = 'Sure! Here you go:\n```json\n{"name": "Ada", "age": 36}\n```'
    expect(text).to_be_json().to_match_schema({"name": str, "age": int})
    expect(text).to_match_schema({"type": "object", "required": ["name", "age"], "properties": {"age": {"type": "integer"}}})
    with pytest.raises(ExpectationFailed, match="missing"):
        expect(text).to_match_schema({"email": str})


def test_pii():
    expect("Contact support for help.").to_not_contain_pii()
    with pytest.raises(ExpectationFailed, match="email"):
        expect("Email me at jane@example.com").to_not_contain_pii()
    with pytest.raises(ExpectationFailed, match="credit_card"):
        expect("card 4111 1111 1111 1111").to_not_contain_pii()
    # non-Luhn digit runs are not flagged
    expect("tracking 1234 5678 9012 3456").to_not_contain_pii(kinds=["credit_card"])


def test_one_of_and_custom():
    expect(" Yes ").to_be_one_of(["yes", "no"])
    expect("hello").to_satisfy_fn(lambda t: t.islower(), "is lowercase")
    with pytest.raises(ExpectationFailed, match="is lowercase"):
        expect("HELLO").to_satisfy_fn(lambda t: t.islower(), "is lowercase")


def test_refusal_heuristic():
    expect("I'm sorry, but I can't help with that request.").to_refuse(use_judge=False)
    expect("The capital of France is Paris.").to_not_refuse(use_judge=False)


def test_soft_mode_collects_everything():
    e = expect("Hello world", soft=True).to_contain("missing").to_have_length(max=3).to_not_be_empty()
    assert not e.passed
    assert len(e.results) == 3
    with pytest.raises(ExpectationFailed, match="2 expectation"):
        e.verify()


def test_non_string_input():
    expect(None).to_have_length(max=0)
    expect(42).to_contain("42")
