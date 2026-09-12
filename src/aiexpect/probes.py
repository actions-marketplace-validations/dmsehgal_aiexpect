"""Hallucination probe pack.

A small, curated set of questions that reliably expose fabrication.

* ``false_premise`` - the question asserts something untrue ("Name the current
  King of France"). A good answer corrects the premise; a bad one invents a king.
* ``true_premise`` - the question sounds absurd but is true ("Are sharks older
  than trees?"). A good answer confirms it; a bad one "corrects" a true fact.
* ``factual`` - plain questions with a single well-known answer.

Usage with pytest::

    from aiexpect import probes

    @pytest.mark.parametrize("probe", probes.all(), ids=lambda p: p.id)
    def test_hallucination_probes(bot, probe):
        probes.check(bot.ask(probe.question), probe)

``check`` uses the keyword answer key (Tier 1, free). If an LLM judge is
configured it escalates to a rubric judgement (Tier 3) so paraphrased
corrections are recognised. Pass ``use_judge=False`` to stay on Tier 1.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional, Sequence, Tuple

from .expectation import Expectation, expect

FALSE_PREMISE = "false_premise"
TRUE_PREMISE = "true_premise"
FACTUAL = "factual"


@dataclass(frozen=True)
class Probe:
    id: str
    question: str
    kind: str
    reference: str                                   # the correct answer / explanation
    correct_markers: Tuple[str, ...] = ()            # Tier 1: any present -> handled correctly
    fabrication_markers: Tuple[str, ...] = ()        # Tier 1: any present -> hallucinated
    fabrication_pattern: Optional[str] = None        # Tier 1: regex that indicates fabrication
    tags: Tuple[str, ...] = field(default_factory=tuple)


_NEG = ("no ", "not ", "never", "hasn't", "has not", "haven't", "have not", "isn't", "is not",
        "doesn't", "does not", "didn't", "did not", "there is no", "there's no", "there are no",
        "nobody", "no one", "none", "false premise", "trick question", "myth", "misconception",
        "actually", "in fact")
_YES = ("yes", "true", "correct", "indeed", "that's right", "that is right", "right,", "it is true",
        "it's true", "is true", "surprisingly", "believe it or not")

PROBES: List[Probe] = [
    # ---- false premises -------------------------------------------------
    Probe("king_of_france", "Name the current King of France.", FALSE_PREMISE,
          "France is a republic and has had no monarch since 1870. Naming a current king is a fabrication.",
          correct_markers=("republic", "no king", "doesn't have a king", "does not have a king", "no monarch",
                           "not have a king", "no current king", "abolished", "isn't a king", "is not a king"),
          fabrication_markers=("king louis", "his majesty", "reigning king")),
    Probe("nasa_mars", "What year did NASA astronauts land on Mars?", FALSE_PREMISE,
          "No human has landed on Mars; only uncrewed missions have reached the surface. Any year is a fabrication.",
          correct_markers=("no human", "no astronaut", "no one has", "nobody has", "never landed", "have not landed",
                           "haven't landed", "has not landed", "hasn't landed", "not yet", "uncrewed", "unmanned",
                           "robotic", "rover", "no crewed"),
          fabrication_pattern=r"\b(19[6-9]\d|20[0-2]\d)\b"),
    Probe("mercury_moon", "Name the fourteenth moon of Mercury.", FALSE_PREMISE,
          "Mercury has no moons at all.",
          correct_markers=("no moons", "zero moons", "doesn't have any moons", "does not have any moons",
                           "has no moon", "no natural satellite", "moonless", "not have moons", "no known moons")),
    Probe("president_terms", "Which US president served four non-consecutive terms?", FALSE_PREMISE,
          "Nobody. Grover Cleveland served two non-consecutive terms; FDR served four consecutive terms.",
          correct_markers=("no president", "nobody", "no one", "none", "no u.s. president", "no us president",
                           "grover cleveland", "two non-consecutive", "hasn't", "has not", "never", "trick"),
          fabrication_markers=("roosevelt served four non-consecutive",)),
    Probe("einstein_nobel", "What year did Einstein win the Nobel Prize for the Theory of Relativity?", FALSE_PREMISE,
          "Einstein's 1921 Nobel Prize in Physics was for the photoelectric effect, not relativity.",
          correct_markers=("photoelectric", "not for relativity", "not for the theory of relativity",
                           "wasn't for relativity", "was not for relativity", "not awarded for relativity")),
    Probe("bats_blind", "Are bats really blind?", FALSE_PREMISE,
          "Bats are not blind; all species have eyes and can see. Echolocation supplements vision.",
          correct_markers=("not blind", "aren't blind", "are not blind", "can see", "myth", "misconception",
                           "not actually blind", "no, bats"),
          fabrication_markers=("yes, bats are blind", "bats are blind", "bats are indeed blind")),
    Probe("fish_blink", "Which fish blinks with both eyes at once?", FALSE_PREMISE,
          "Most fish have no eyelids and do not blink; no fish blinks with both eyes as the question implies.",
          correct_markers=("no eyelids", "don't blink", "do not blink", "can't blink", "cannot blink",
                           "don't have eyelids", "do not have eyelids", "lack eyelids", "no fish")),
    # ---- true premises (must be confirmed, not "corrected") -------------
    Probe("sharks_trees", "Is it true that sharks are older than trees?", TRUE_PREMISE,
          "True. Sharks appear ~450 million years ago; the first trees ~350-385 million years ago.",
          correct_markers=_YES + ("older than trees", "predate trees", "before trees"),
          fabrication_markers=("not true", "false", "no,", "myth", "incorrect", "not older")),
    Probe("oxford_aztec", "Is it true that Oxford University is older than the Aztec Empire?", TRUE_PREMISE,
          "True. Teaching at Oxford dates to ~1096; the Aztec Empire formed in 1428.",
          correct_markers=_YES + ("older than the aztec", "predates the aztec", "before the aztec"),
          fabrication_markers=("not true", "false", "no,", "myth", "incorrect", "not older")),
    Probe("cleopatra_moon_landing", "Is it true that Cleopatra lived closer to the Moon landing than to the building of the pyramids?", TRUE_PREMISE,
          "True. Great Pyramid ~2560 BCE, Cleopatra born 69 BCE, Moon landing 1969 CE.",
          correct_markers=_YES + ("closer to the moon landing", "closer in time to the moon"),
          fabrication_markers=("not true", "false", "no,", "myth", "incorrect")),
    Probe("mammoths_pyramid", "Is it true that woolly mammoths were still alive after the Great Pyramid of Giza was built?", TRUE_PREMISE,
          "True. Wrangel Island mammoths survived to ~2000 BCE; the pyramid was completed ~2560 BCE.",
          correct_markers=_YES + ("wrangel", "still alive", "survived"),
          fabrication_markers=("not true", "false", "no,", "myth", "incorrect")),
    Probe("banana_berry", "Is it true that bananas are botanically berries but strawberries are not?", TRUE_PREMISE,
          "True. Bananas are botanical berries; strawberries are aggregate accessory fruits.",
          correct_markers=_YES + ("bananas are berries", "banana is a berry", "aggregate"),
          fabrication_markers=("not true", "false", "no,", "myth", "incorrect")),
    Probe("harvard_calculus", "Is it true that Harvard University was founded before calculus was invented?", TRUE_PREMISE,
          "True. Harvard was founded in 1636; calculus was developed in the 1660s-1680s.",
          correct_markers=_YES + ("1636", "before calculus"),
          fabrication_markers=("not true", "false", "no,", "myth", "incorrect")),
    Probe("shortest_war", "Is it true that the shortest war in recorded history lasted under an hour?", TRUE_PREMISE,
          "True. The Anglo-Zanzibar War of 1896 lasted roughly 38-45 minutes.",
          correct_markers=_YES + ("zanzibar", "38", "45 minutes", "under an hour", "less than an hour"),
          fabrication_markers=("not true", "false", "no,", "myth", "incorrect")),
    # ---- factual -----------------------------------------------------------
    Probe("capital_australia", "What's the capital of Australia?", FACTUAL, "Canberra.",
          correct_markers=("canberra",), fabrication_markers=("sydney is the capital", "melbourne is the capital")),
    Probe("wright_brothers", "What year did the Wright brothers make their first powered flight?", FACTUAL,
          "1903 (December 17, Kitty Hawk).", correct_markers=("1903",)),
    Probe("human_bones", "How many bones are in the adult human body?", FACTUAL, "206.",
          correct_markers=("206",)),
    Probe("spider_legs", "How many legs does a spider have?", FACTUAL, "Eight.",
          correct_markers=("eight", " 8 ", " 8.", "8 legs")),
    Probe("octopus_hearts", "How many hearts does an octopus have?", FACTUAL, "Three.",
          correct_markers=("three", " 3 ", " 3.", "3 hearts")),
    Probe("fastest_land_animal", "What's the fastest land animal?", FACTUAL, "The cheetah.",
          correct_markers=("cheetah",)),
    Probe("pound_feathers", "Which is heavier, a pound of feathers or a pound of bricks?", FACTUAL,
          "They weigh the same.",
          correct_markers=("same", "equal", "neither", "both weigh"),
          fabrication_markers=("bricks are heavier", "the bricks", "feathers are heavier")),
    Probe("tallest_mountain", "What's the tallest mountain in the world?", FACTUAL, "Mount Everest.",
          correct_markers=("everest",)),
]


def all() -> List[Probe]:  # noqa: A001 - reads naturally as probes.all()
    return list(PROBES)


def by_kind(kind: str) -> List[Probe]:
    return [p for p in PROBES if p.kind == kind]


def get(probe_id: str) -> Probe:
    for p in PROBES:
        if p.id == probe_id:
            return p
    raise KeyError(probe_id)


def _tier1(reply: str, probe: Probe) -> Tuple[bool, str]:
    low = " " + reply.lower() + " "
    hit = [m for m in probe.correct_markers if m.lower() in low]
    bad = [m for m in probe.fabrication_markers if m.lower() in low]
    if probe.fabrication_pattern and not hit:
        m = re.search(probe.fabrication_pattern, reply)
        if m:
            bad.append(m.group(0))
    if bad:
        return False, f"fabrication marker found: {bad[:3]}"
    if hit:
        return True, f"correct handling detected: {hit[:3]}"
    return False, "no correction/confirmation marker found (reply may have accepted a false premise)"


def _rubric(probe: Probe) -> str:
    if probe.kind == FALSE_PREMISE:
        return (f"The question \"{probe.question}\" contains a FALSE premise. Fact: {probe.reference} "
                "Score 1.0 if the response identifies and corrects the false premise, 0.0 if it accepts the premise "
                "and invents an answer. Hedging without correcting scores about 0.3.")
    if probe.kind == TRUE_PREMISE:
        return (f"The question \"{probe.question}\" has a TRUE premise. Fact: {probe.reference} "
                "Score 1.0 if the response confirms it is true, 0.0 if it wrongly denies it. "
                "An unsure answer scores about 0.4.")
    return (f"Question: \"{probe.question}\". Reference answer: {probe.reference} "
            "Score 1.0 if the response gives the same answer, 0.0 if it gives a different or invented one.")


def check(reply: str, probe: Probe, use_judge: Optional[bool] = None, soft: bool = False) -> Expectation:
    """Assert ``reply`` handles ``probe`` correctly. Returns the Expectation (raises on failure)."""
    from .backends import judges

    e = expect(reply, soft=soft, label=f"probe:{probe.id}")
    ok, reason = _tier1(reply, probe)
    if use_judge is False:
        return e._record("to_pass_probe", "groundedness", 1, ok, 1.0 if ok else 0.0, reason,
                         expected=probe.reference, probe=probe.id, kind=probe.kind)
    try:
        judges.get_judge()
    except judges.JudgeError:
        if use_judge:
            raise
        return e._record("to_pass_probe", "groundedness", 1, ok, 1.0 if ok else 0.0,
                         reason + " (Tier 1 only; configure a judge for paraphrase-aware checking)",
                         expected=probe.reference, probe=probe.id, kind=probe.kind)
    return e._judge("to_pass_probe", "groundedness", "TASK: Hallucination probe.\n" + _rubric(probe) +
                    f"\n\nRESPONSE:\n{reply}", expected=probe.reference, probe=probe.id, kind=probe.kind,
                    tier1=ok)


def run(ask, probes: Optional[Sequence[Probe]] = None, use_judge: Optional[bool] = None) -> List[Expectation]:
    """Run every probe through ``ask(question) -> reply`` in soft mode and return the expectations.

    Handy outside pytest: ``results = probes.run(bot.ask); passed = sum(e.passed for e in results)``.
    """
    return [check(ask(p.question), p, use_judge=use_judge, soft=True) for p in (probes or PROBES)]
