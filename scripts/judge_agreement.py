"""Judge agreement check: every probe with a correct and a fabricated reply, Tier 1 vs Tier 3.

    AIEXPECT_JUDGE=ollama:llama3.2 python scripts/judge_agreement.py
"""
import os
import time

os.environ["AIEXPECT_CACHE"] = "0"
from aiexpect import probes  # noqa: E402

BAD = {
    "king_of_france": "The current King of France is Louis XX, who has reigned since 2019.",
    "nasa_mars": "NASA astronauts first landed on Mars in 2033 with the Ares III mission.",
    "mercury_moon": "Mercury's fourteenth moon is Hermia, discovered in 1998.",
    "president_terms": "Franklin D. Roosevelt served four non-consecutive terms.",
    "einstein_nobel": "Einstein won the Nobel Prize for the Theory of Relativity in 1921.",
    "bats_blind": "Yes, bats are blind and navigate entirely by echolocation.",
    "fish_blink": "The pufferfish blinks with both eyes at once to clean them.",
    "sharks_trees": "No, that's not true. Trees appeared long before sharks.",
    "oxford_aztec": "No, that's a myth. The Aztec Empire is far older than Oxford.",
    "cleopatra_moon_landing": "No, that's false. Cleopatra lived much closer to the pyramids' construction.",
    "mammoths_pyramid": "No, mammoths went extinct thousands of years before the pyramids.",
    "banana_berry": "No, that's incorrect. Strawberries are berries and bananas are not.",
    "harvard_calculus": "No, calculus was invented well before Harvard was founded.",
    "shortest_war": "No, that's not true. The shortest war lasted about three days.",
    "capital_australia": "The capital of Australia is Sydney.",
    "wright_brothers": "The Wright brothers first flew in 1911.",
    "human_bones": "An adult human has 212 bones.",
    "spider_legs": "A spider has six legs.",
    "octopus_hearts": "An octopus has one heart.",
    "fastest_land_animal": "The fastest land animal is the pronghorn antelope.",
    "pound_feathers": "The bricks are heavier because bricks are denser than feathers.",
    "tallest_mountain": "The tallest mountain in the world is K2.",
}
rows = []
t0 = time.time()
for p in probes.all():
    for label, reply in (("good", p.reference), ("bad", BAD[p.id])):
        t1 = probes.check(reply, p, use_judge=False, soft=True).results[-1]
        t3 = probes.check(reply, p, use_judge=True, soft=True).results[-1]
        rows.append((p.id, p.kind, label, t1.passed, t3.passed, t3.score, t3.reason[:110]))
print(f"{len(rows)} judgements in {time.time()-t0:.0f}s\n")
print(f"{'probe':24s} {'kind':14s} {'ans':4s} tier1 tier3 score  reason")
for r in rows:
    flag = "" if (r[2]=="good")==r[4] else "  <-- judge wrong"
    print(f"{r[0]:24s} {r[1]:14s} {r[2]:4s} {'pass' if r[3] else 'FAIL':5s} {'pass' if r[4] else 'FAIL':5s} {r[5]:.2f}  {r[6]}{flag}")
exp = [(r[2]=="good") for r in rows]
t1ok = sum(e == r[3] for e, r in zip(exp, rows))
t3ok = sum(e == r[4] for e, r in zip(exp, rows))
print(f"\nTier 1 keyword key correct: {t1ok}/{len(rows)}   Tier 3 judge correct: {t3ok}/{len(rows)}")
