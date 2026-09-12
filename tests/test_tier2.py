import pytest

from aiexpect import ExpectationFailed, expect


def test_mean_lexical_backend():
    reply = "Customers may return any item within 30 days for a full refund."
    e = expect(reply).to_mean("you can return items within 30 days and get refunded")
    assert e.results[-1].details["backend"] == "lexical"
    assert e.results[-1].score > 0.45


def test_mean_fails_on_unrelated():
    with pytest.raises(ExpectationFailed, match="similarity"):
        expect("The weather is sunny today.").to_mean("our refund policy lasts 30 days")


def test_not_mean():
    expect("The weather is sunny today.").to_not_mean("our refund policy lasts 30 days")


def test_relevant_to():
    expect("Refunds are processed in 5 business days after we receive the item.").to_be_relevant_to(
        "how long does a refund take?"
    )


def test_custom_threshold():
    expect("cats").to_mean("dogs", threshold=0.0)
