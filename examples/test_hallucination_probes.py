"""Run the built-in hallucination probe pack against your bot.

Tier 1 (keyword answer key) works offline. With a judge configured
(AIEXPECT_JUDGE=ollama:llama3.2) paraphrased corrections are recognised too.
Swap `honest_bot` for your real assistant."""
import pytest

from aiexpect import probes


def honest_bot(question: str) -> str:
    # A bot that happens to know the answer key. Yours will be more interesting.
    for p in probes.all():
        if p.question == question:
            return p.reference
    return "I'm not sure."


@pytest.mark.parametrize("probe", probes.all(), ids=lambda p: p.id)
def test_hallucination_probe(probe):
    probes.check(honest_bot(probe.question), probe)
