"""Self-contained HTML report: one file, no CDN, works offline, light + dark.

Charts are inline SVG built here in Python so the report has zero runtime
dependencies. Colours follow a colour-blind-validated palette: a single blue
for magnitude, and reserved status colours (always paired with a label) for
pass/fail.
"""
from __future__ import annotations

import html
import json
from typing import Any, Dict, List

from ..results import CATEGORIES, CATEGORY_HELP, CATEGORY_LABELS

_CSS = """
:root{color-scheme:light;--bg:#f9f9f7;--surface:#fcfcfb;--ink:#0b0b0b;--ink2:#52514e;--muted:#898781;
--grid:#e1e0d9;--axis:#c3c2b7;--border:rgba(11,11,11,.10);--blue:#2a78d6;--blue-soft:#9ec5f4;
--good:#0ca30c;--good-ink:#006300;--critical:#d03b3b;--warning:#fab219;--serious:#ec835a;--good-bg:rgba(12,163,12,.10);--bad-bg:rgba(208,59,59,.10)}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){color-scheme:dark;--bg:#0d0d0d;--surface:#1a1a19;--ink:#fff;--ink2:#c3c2b7;
--muted:#898781;--grid:#2c2c2a;--axis:#383835;--border:rgba(255,255,255,.10);--blue:#3987e5;--blue-soft:#1c5cab;--good-ink:#0ca30c}}
:root[data-theme=dark]{color-scheme:dark;--bg:#0d0d0d;--surface:#1a1a19;--ink:#fff;--ink2:#c3c2b7;--muted:#898781;--grid:#2c2c2a;--axis:#383835;--border:rgba(255,255,255,.10);--blue:#3987e5;--blue-soft:#1c5cab;--good-ink:#0ca30c}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif}
.wrap{max-width:1180px;margin:0 auto;padding:28px 20px 60px}
h1{font-size:22px;margin:0 0 4px}h2{font-size:15px;margin:28px 0 10px;color:var(--ink2);text-transform:uppercase;letter-spacing:.04em}
.sub{color:var(--muted);margin:0 0 20px}
.hero{display:grid;grid-template-columns:260px 1fr;gap:16px;align-items:stretch}
@media(max-width:760px){.hero{grid-template-columns:1fr}}
.card{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:16px}
.trust{display:flex;flex-direction:column;justify-content:center;align-items:center;text-align:center}
.trust .n{font-size:64px;font-weight:700;line-height:1}.trust .l{color:var(--ink2);margin-top:6px}.trust .h{color:var(--muted);font-size:12px;margin-top:10px}
.tiles{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}@media(max-width:560px){.tiles{grid-template-columns:repeat(2,1fr)}}
.tile{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:12px 14px}
.tile .v{font-size:26px;font-weight:600}.tile .k{color:var(--ink2);font-weight:500}.tile .d{color:var(--muted);font-size:12px;margin-top:2px}
.tile .na{color:var(--muted);font-size:18px}
.bar{height:6px;background:var(--grid);border-radius:3px;margin-top:8px;overflow:hidden}.bar i{display:block;height:100%;background:var(--blue);border-radius:3px}
.row{display:grid;grid-template-columns:1fr 1fr;gap:16px}@media(max-width:760px){.row{grid-template-columns:1fr}}
.kpis{display:flex;gap:20px;flex-wrap:wrap;color:var(--ink2)}.kpis b{color:var(--ink);font-size:18px;margin-right:4px}
svg text{fill:var(--ink2);font-size:12px}svg .muted{fill:var(--muted)}svg .grid{stroke:var(--grid)}svg .axis{stroke:var(--axis)}
svg .mark{fill:var(--blue)}svg .mark:hover{opacity:.85}svg .val{fill:var(--ink);font-size:11px}
table{width:100%;border-collapse:collapse;font-size:13px}th{text-align:left;color:var(--muted);font-weight:500;padding:8px 10px;border-bottom:1px solid var(--grid)}
td{padding:8px 10px;border-bottom:1px solid var(--grid);vertical-align:top}tr:last-child td{border-bottom:0}
.num{font-variant-numeric:tabular-nums;text-align:right}
.pill{display:inline-flex;align-items:center;gap:5px;padding:2px 9px;border-radius:999px;font-size:12px;font-weight:600}
.pass{background:var(--good-bg);color:var(--good-ink)}.fail{background:var(--bad-bg);color:var(--critical)}
.tier{color:var(--muted);font-size:11px;border:1px solid var(--border);border-radius:4px;padding:0 5px;margin-left:6px}
.mono{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:12px;color:var(--ink2);white-space:pre-wrap;word-break:break-word}
details{border-bottom:1px solid var(--grid);padding:8px 0}details:last-child{border-bottom:0}
summary{cursor:pointer;display:grid;grid-template-columns:90px 1fr 70px 60px;gap:10px;align-items:center;list-style:none}
summary::-webkit-details-marker{display:none}
summary .name{font-weight:600}summary .test{color:var(--muted);font-size:12px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.dl{display:grid;grid-template-columns:110px 1fr;gap:6px 12px;margin:10px 0 4px}.dl dt{color:var(--muted)}.dl dd{margin:0}
.filters{display:flex;gap:8px;margin:0 0 12px;flex-wrap:wrap}.filters button{background:var(--surface);color:var(--ink2);border:1px solid var(--border);border-radius:999px;padding:4px 12px;cursor:pointer;font:inherit;font-size:12px}
.filters button.on{background:var(--blue);color:#fff;border-color:var(--blue)}
.empty{color:var(--muted);padding:30px;text-align:center}
.foot{color:var(--muted);font-size:12px;margin-top:40px}
"""


def _e(s: Any) -> str:
    return html.escape(str(s), quote=True)


def _score_color(v: float) -> str:
    return "var(--good-ink)" if v >= 80 else ("var(--critical)" if v < 50 else "var(--ink)")


def _bar_chart(items: List[Dict[str, Any]], width: int = 560) -> str:
    """Horizontal bars: pass-rate per assertion type. Single series, direct-labelled."""
    if not items:
        return '<div class="empty">No checks recorded</div>'
    row_h, top, left, right = 26, 8, 150, 60
    h = top + row_h * len(items) + 24
    plot_w = width - left - right
    out = [f'<svg viewBox="0 0 {width} {h}" width="100%" role="img" aria-label="Pass rate by assertion">']
    for gx in (0, 25, 50, 75, 100):
        x = left + plot_w * gx / 100
        out.append(f'<line class="grid" x1="{x:.1f}" y1="{top}" x2="{x:.1f}" y2="{h - 22}" stroke-width="1"/>')
        out.append(f'<text class="muted" x="{x:.1f}" y="{h - 6}" text-anchor="middle">{gx}%</text>')
    for i, it in enumerate(items):
        y = top + i * row_h
        w = plot_w * it["pass_rate"] / 100
        out.append(f'<text x="{left - 8}" y="{y + 17}" text-anchor="end">{_e(it["name"])}</text>')
        out.append(
            f'<rect class="mark" x="{left}" y="{y + 5}" width="{max(w, 2):.1f}" height="16" rx="4">'
            f'<title>{_e(it["name"])}: {it["passed"]}/{it["total"]} passed ({it["pass_rate"]}%)</title></rect>'
        )
        out.append(f'<text class="val" x="{left + w + 6:.1f}" y="{y + 17}">{it["pass_rate"]:.0f}% ({it["passed"]}/{it["total"]})</text>')
    out.append(f'<line class="axis" x1="{left}" y1="{top}" x2="{left}" y2="{h - 22}" stroke-width="1"/>')
    out.append("</svg>")
    return "".join(out)


def _histogram(scores: List[float], width: int = 560) -> str:
    """Score distribution in 10 bins. Single hue; count labels on non-empty bins."""
    if not scores:
        return '<div class="empty">No scores recorded</div>'
    bins = [0] * 10
    for s in scores:
        bins[min(9, int(s * 10))] += 1
    top, left, bottom, right = 12, 36, 28, 10
    h = 200
    plot_w, plot_h = width - left - right, h - top - bottom
    mx = max(bins) or 1
    bw = plot_w / 10
    out = [f'<svg viewBox="0 0 {width} {h}" width="100%" role="img" aria-label="Score distribution">']
    for g in range(5):
        y = top + plot_h - plot_h * g / 4
        out.append(f'<line class="grid" x1="{left}" y1="{y:.1f}" x2="{width - right}" y2="{y:.1f}" stroke-width="1"/>')
        out.append(f'<text class="muted" x="{left - 6}" y="{y + 4:.1f}" text-anchor="end">{round(mx * g / 4)}</text>')
    for i, c in enumerate(bins):
        x = left + i * bw
        bh = plot_h * c / mx
        y = top + plot_h - bh
        out.append(
            f'<rect class="mark" x="{x + 2:.1f}" y="{y:.1f}" width="{bw - 4:.1f}" height="{bh:.1f}" rx="4">'
            f'<title>{i / 10:.1f}–{(i + 1) / 10:.1f}: {c} checks</title></rect>'
        )
        if c:
            out.append(f'<text class="val" x="{x + bw / 2:.1f}" y="{y - 4:.1f}" text-anchor="middle">{c}</text>')
        out.append(f'<text class="muted" x="{x + bw / 2:.1f}" y="{h - 8}" text-anchor="middle">{i / 10:.1f}</text>')
    out.append(f'<line class="axis" x1="{left}" y1="{top + plot_h}" x2="{width - right}" y2="{top + plot_h}" stroke-width="1"/>')
    out.append("</svg>")
    return "".join(out)


def render_html(payload: Dict[str, Any]) -> str:
    s = payload["summary"]
    checks = payload["checks"]
    trust = s["trust_score"]
    trust_txt = f"{trust:.0f}" if trust is not None else "–"
    trust_col = _score_color(trust) if trust is not None else "var(--muted)"

    tiles = []
    for cat in CATEGORIES:
        v = s["subscores"].get(cat)
        n = sum(1 for c in checks if c["category"] == cat)
        if v is None:
            tiles.append(f'<div class="tile"><div class="k">{CATEGORY_LABELS[cat]}</div><div class="na">not tested</div><div class="d">{_e(CATEGORY_HELP[cat])}</div></div>')
        else:
            tiles.append(
                f'<div class="tile"><div class="k">{CATEGORY_LABELS[cat]}</div><div class="v" style="color:{_score_color(v)}">{v:.0f}</div>'
                f'<div class="d">{n} check{"s" if n != 1 else ""} · {_e(CATEGORY_HELP[cat])}</div><div class="bar"><i style="width:{v}%"></i></div></div>'
            )

    by_check = sorted(
        ({"name": k, **v} for k, v in s["by_check"].items()), key=lambda x: (x["pass_rate"], -x["total"])
    )
    by_test = sorted(s["by_test"].items(), key=lambda kv: (kv[1]["passed"] == kv[1]["total"], kv[0]))
    PASS_PILL = '<span class="pill pass">✓ pass</span>'
    FAIL_PILL = '<span class="pill fail">✗ fail</span>'
    test_rows = "".join(
        f'<tr><td class="mono">{_e(t)}</td><td class="num">{v["passed"]}/{v["total"]}</td>'
        f'<td>{PASS_PILL if v["passed"] == v["total"] else FAIL_PILL}</td></tr>'
        for t, v in by_test
    ) or '<tr><td colspan="3" class="empty">No tests recorded</td></tr>'

    details = []
    for c in checks:
        pill = PASS_PILL if c["passed"] else FAIL_PILL
        extra = {k: v for k, v in c["details"].items() if k not in ("label",)}
        dl = [
            ("Reason", c["reason"]),
            ("Text", c["text"]),
        ]
        if c["expected"]:
            dl.append(("Expected", c["expected"]))
        if c.get("duration_ms"):
            dl.append(("Duration", f'{c["duration_ms"]} ms'))
        if extra:
            dl.append(("Details", json.dumps(extra, indent=1, ensure_ascii=False)[:1500]))
        dl_html = "".join(f'<dt>{_e(k)}</dt><dd class="mono">{_e(v)}</dd>' for k, v in dl)
        label = f' · {_e(c["details"]["label"])}' if c["details"].get("label") else ""
        details.append(
            f'<details data-status="{"pass" if c["passed"] else "fail"}" data-tier="{c["tier"]}">'
            f'<summary>{pill}<span><span class="name">{_e(c["name"])}</span><span class="tier">tier {c["tier"]}</span>{label}'
            f'<div class="test">{_e(c["test_id"] or "")}</div></span>'
            f'<span class="num">{c["score"]:.2f}</span><span class="muted">{_e(CATEGORY_LABELS.get(c["category"], c["category"]))}</span></summary>'
            f'<dl class="dl">{dl_html}</dl></details>'
        )
    details_html = "".join(details) or '<div class="empty">No checks recorded. Call expect(...) in a test and re-run.</div>'

    meta = payload.get("meta", {})
    meta_line = " · ".join(f"{_e(k)}: {_e(v)}" for k, v in meta.items())
    tiers = s["tiers"]

    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>aiexpect report</title><style>{_CSS}</style></head><body><div class="wrap">
<h1>aiexpect report</h1><p class="sub">{_e(payload["generated_at"])} · aiexpect {_e(payload["version"])} · Python {_e(payload["python"])}{(" · " + meta_line) if meta_line else ""}</p>
<div class="hero">
  <div class="card trust"><div class="n" style="color:{trust_col}">{trust_txt}</div><div class="l">Trust Score / 100</div>
  <div class="h">Mean of the sub-scores that were tested. 80+ is healthy, under 50 needs attention.</div></div>
  <div class="tiles">{"".join(tiles)}</div>
</div>
<h2>At a glance</h2>
<div class="card kpis"><span><b>{s["total_checks"]}</b>checks</span><span><b>{s["passed_checks"]}</b>passed</span><span><b>{s["failed_checks"]}</b>failed</span>
<span><b>{s["pass_rate"]:.0f}%</b>pass rate</span><span><b>{len(s["by_test"])}</b>tests</span>
<span title="Tier 1 = rules, Tier 2 = embeddings, Tier 3 = LLM judge"><b>{tiers["1"]}/{tiers["2"]}/{tiers["3"]}</b>checks by tier 1/2/3</span></div>
<div class="row">
  <div><h2>Pass rate by assertion</h2><div class="card">{_bar_chart(by_check)}</div></div>
  <div><h2>Score distribution</h2><div class="card">{_histogram([c["score"] for c in checks])}</div></div>
</div>
<h2>Tests</h2><div class="card" style="padding:0 6px"><table><thead><tr><th>Test</th><th class="num">Checks passed</th><th>Status</th></tr></thead><tbody>{test_rows}</tbody></table></div>
<h2>Every check</h2>
<div class="filters"><button class="on" data-f="all">All</button><button data-f="fail">Failed only</button><button data-f="pass">Passed only</button><button data-f="t3">LLM-judged</button></div>
<div class="card" style="padding:4px 16px">{details_html}</div>
<p class="foot">Generated by <a href="https://github.com/dmsehgal/aiexpect">aiexpect</a>. Tier 1 = deterministic rules, Tier 2 = local embeddings, Tier 3 = LLM judge (your own model and key).</p>
</div>
<script>
document.querySelectorAll('.filters button').forEach(b=>b.addEventListener('click',()=>{{
  document.querySelectorAll('.filters button').forEach(x=>x.classList.remove('on'));b.classList.add('on');
  const f=b.dataset.f;document.querySelectorAll('details[data-status]').forEach(d=>{{
    d.hidden = f==='all'?false : f==='t3' ? d.dataset.tier!=='3' : d.dataset.status!==f;}});
}}));
</script></body></html>"""
