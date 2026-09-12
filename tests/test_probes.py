import pytest

from aiexpect import ExpectationFailed, probes


def test_pack_shape():
    ids = [p.id for p in probes.all()]
    assert len(ids) == len(set(ids)) >= 20
    assert len(probes.by_kind(probes.FALSE_PREMISE)) >= 7
    assert probes.get("king_of_france").kind == probes.FALSE_PREMISE


@pytest.mark.parametrize("probe_id,good,bad", [
    ("king_of_france", "France is a republic and has no king.", "The current King of France is King Louis XX, His Majesty."),
    ("nasa_mars", "No human has landed on Mars yet; only rovers have.", "NASA astronauts landed on Mars in 2031."),
    ("mercury_moon", "Mercury has no moons at all.", "Mercury's fourteenth moon is called Hermia."),
    ("bats_blind", "No, bats are not blind — they can see and also use echolocation.", "Yes, bats are blind and rely on sonar."),
    ("sharks_trees", "Yes, that's true: sharks predate trees by about 100 million years.", "No, that's not true, trees came first."),
    ("capital_australia", "The capital is Canberra.", "Sydney is the capital of Australia."),
    ("pound_feathers", "They weigh the same — a pound is a pound.", "The bricks are heavier."),
])
def test_tier1_keys(probe_id, good, bad):
    p = probes.get(probe_id)
    assert probes.check(good, p, use_judge=False).passed
    with pytest.raises(ExpectationFailed):
        probes.check(bad, p, use_judge=False)


def test_judge_escalation_uses_fake_judge():
    e = probes.check("France is a republic.", probes.get("king_of_france"))
    assert e.results[-1].tier == 3 and e.passed


def test_run_soft():
    answers = {p.id: p.reference for p in probes.all()}
    res = probes.run(lambda q: answers[next(p.id for p in probes.all() if p.question == q)], use_judge=False)
    assert len(res) == len(probes.all())
    # references are written to satisfy their own keys
    failed = [r.results[-1].details["probe"] for r in res if not r.passed]
    assert failed == [], failed
