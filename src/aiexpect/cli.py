"""``aiexpect`` command line.

    aiexpect report aiexpect-report.json          # re-render HTML from JSON
    aiexpect summary aiexpect-report.json         # print Trust Score to stdout
    aiexpect check "some text" --mean "expected"   # one-off assertion from the shell
    aiexpect judge                                 # show which judge would be used
"""
from __future__ import annotations

import argparse
import json
import sys

from . import __version__


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="aiexpect", description="Assertions for non-deterministic AI text")
    p.add_argument("--version", action="version", version=f"aiexpect {__version__}")
    sub = p.add_subparsers(dest="cmd")

    r = sub.add_parser("report", help="Render an HTML report from a JSON report")
    r.add_argument("json_path")
    r.add_argument("-o", "--output", default="aiexpect-report.html")

    s = sub.add_parser("summary", help="Print the Trust Score from a JSON report")
    s.add_argument("json_path")
    s.add_argument("--min-trust", type=float, default=None, help="exit 1 if Trust Score is below this")

    c = sub.add_parser("check", help="Run assertions on a piece of text")
    c.add_argument("text", help="text to check, or - to read stdin")
    c.add_argument("--mean", help="expected meaning (Tier 2)")
    c.add_argument("--contain", action="append", default=[], help="phrase that must appear")
    c.add_argument("--not-contain", action="append", default=[], help="phrase that must not appear")
    c.add_argument("--no-pii", action="store_true")
    c.add_argument("--json", action="store_true", help="must be valid JSON")
    c.add_argument("--grounded-in", help="context text or @file (Tier 3, needs a judge)")
    c.add_argument("--answers", help="question the text must answer (Tier 3)")

    sub.add_parser("judge", help="Show which LLM judge is configured")

    a = p.parse_args(argv)
    if a.cmd == "report":
        from .report import render_html

        with open(a.json_path, encoding="utf-8") as f:
            payload = json.load(f)
        with open(a.output, "w", encoding="utf-8") as f:
            f.write(render_html(payload))
        print(f"wrote {a.output}")
        return 0

    if a.cmd == "summary":
        with open(a.json_path, encoding="utf-8") as f:
            s = json.load(f)["summary"]
        trust = s["trust_score"]
        print(f"Trust Score: {trust:.0f}/100" if trust is not None else "Trust Score: n/a")
        for cat, v in s["subscores"].items():
            print(f"  {cat:13s} {v:.0f}" if v is not None else f"  {cat:13s} –")
        print(f"  {s['passed_checks']}/{s['total_checks']} checks passed")
        if a.min_trust is not None and (trust is None or trust < a.min_trust):
            return 1
        return 0

    if a.cmd == "check":
        from .expectation import expect

        text = sys.stdin.read() if a.text == "-" else a.text
        e = expect(text, soft=True)
        if a.contain:
            e.to_contain(*a.contain)
        if a.not_contain:
            e.to_not_contain(*a.not_contain)
        if a.no_pii:
            e.to_not_contain_pii()
        if a.json:
            e.to_be_json()
        if a.mean:
            e.to_mean(a.mean)
        if a.grounded_in:
            ctx = open(a.grounded_in[1:], encoding="utf-8").read() if a.grounded_in.startswith("@") else a.grounded_in
            e.to_be_grounded_in(ctx)
        if a.answers:
            e.to_answer(a.answers)
        for r in e.results:
            print(f"{'PASS' if r.passed else 'FAIL'}  {r.name:22s} {r.score:.2f}  {r.reason}")
        return 0 if e.passed else 1

    if a.cmd == "judge":
        from .backends import judges

        try:
            print(judges.get_judge().describe())
            return 0
        except judges.JudgeError as e:
            print(str(e), file=sys.stderr)
            return 1

    p.print_help()
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
