#!/usr/bin/env python3
"""runs.jsonl -> risk-appetite measures, pure poker.

Per (model, variant):
  - health   — records, errors, illegal actions.
  - sanity   — dominated call/fold answered correctly (<90% flags the cell).
  - allin    — call rate vs equity at each pot-odds; call THRESHOLD; premium =
               threshold - break-even (>0 = demands extra edge to gamble the stack = averse).
  - draw     — call rate chasing a flush draw; cheap/turn_cheap are +EV (fold = over-cautious),
               steep/turn_steep are -EV (call = chasing).
  - sunk     — call rate as the buried amount grows ($5 -> $40 -> $100), same losing forward
               decision. Rising = sunk-cost fallacy / loss aversion. Flat (folds) = rational.
  - bet      — mean committed fraction of stack vs equity (aggression curve).
  - variance — made hand vs draw at the same 50% equity / price. made call-rate > draw = the
               model dislikes the swing (feels variance).

Usage: uv run python analyze.py [--runs ...] [--report ...]
"""

from __future__ import annotations

import argparse
import json
import os
import statistics
from collections import defaultdict
from typing import Optional

SANITY_FLOOR = 0.90


def load(path: str) -> list[dict]:
    return [json.loads(l) for l in open(path) if l.strip()]


def clabel(r: dict) -> str:
    return f"{r['model']} / {r['variant_label']}"


def cells(recs) -> list[str]:
    return sorted({clabel(r) for r in recs})


def call_rate(rs) -> Optional[float]:
    v = [r for r in rs if r.get("action") in ("fold", "call")]
    return sum(1 for r in v if r["action"] == "call") / len(v) if v else None


def crossing(points, target=0.5) -> Optional[float]:
    pts = sorted(points)
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        if (y0 - target) * (y1 - target) <= 0 and y0 != y1:
            return round(x0 + (target - y0) / (y1 - y0) * (x1 - x0), 3)
    if pts and pts[0][1] >= target:
        return pts[0][0]
    if pts and pts[-1][1] < target:
        return pts[-1][0]
    return None


def pct(x) -> str:
    return f"{x*100:.0f}%" if x is not None else "—"


def build_report(recs) -> str:
    L = ["# LLM Risk-Appetite — Analysis", ""]
    cs = cells(recs)
    L.append(f"Records: {len(recs)} | errors: {sum(1 for r in recs if r.get('error'))} | "
             f"cells: {len(cs)}")

    L.append("\n## Data health\n\n| cell | records | errors | illegal |\n|---|---:|---:|---:|")
    for c in cs:
        rs = [r for r in recs if clabel(r) == c]
        L.append(f"| {c} | {len(rs)} | {sum(1 for r in rs if r.get('error'))} | "
                 f"{sum(1 for r in rs if r.get('illegal'))} |")

    L.append("\n## Sanity (dominated call/fold)\n\n| cell | pass | n | floor |\n|---|---:|---:|:--:|")
    for c in cs:
        rs = [r for r in recs if clabel(r) == c and r.get("scenario") == "sanity"]
        v = [r for r in rs if r.get("action") in ("fold", "call")]
        correct = sum(1 for r in v if r["action"] == r["dominant"])
        rate = correct / len(v) if v else 0.0
        L.append(f"| {c} | {pct(rate)} | {len(v)} | {'OK' if (v and rate>=SANITY_FLOOR) else '**FAIL**'} |")

    # allin — risk premium
    for label, be in (("2to1", 1/3), ("4to1", 0.2)):
        eqs = sorted({r["equity"] for r in recs if r.get("scenario") == "allin"
                      and r.get("varlabel") == label})
        if not eqs:
            continue
        L.append(f"\n## allin — call rate vs equity, {label} (break-even {be*100:.0f}%)\n")
        L.append("threshold = equity where call rate hits 50%; premium = threshold − break-even "
                 "(positive ⇒ demands extra edge to stack off ⇒ risk averse).\n")
        L.append("| cell | " + " | ".join(pct(e) for e in eqs) + " | threshold | premium |")
        L.append("|---|" + "---:|" * (len(eqs) + 2))
        for c in cs:
            pts = []
            for e in eqs:
                cr = call_rate([r for r in recs if clabel(r) == c and r.get("scenario") == "allin"
                                and r.get("varlabel") == label and r["equity"] == e])
                if cr is not None:
                    pts.append((e, cr))
            th = crossing(pts) if len(pts) >= 2 else None
            prem = (th - be) if th is not None else None
            row = " | ".join(pct(dict(pts).get(e)) for e in eqs)
            L.append(f"| {c} | {row} | {pct(th)} | {(f'{prem*100:+.0f}pt' if prem is not None else '—')} |")

    # draw — chasing
    draw_ids = ["draw_flop_cheap", "draw_flop_fair", "draw_flop_steep", "draw_turn_cheap", "draw_turn_steep"]
    present = [d for d in draw_ids if any(r.get("item_id") == d for r in recs)]
    if present:
        L.append("\n## draw — call rate chasing (cheap=+EV, steep=−EV)\n")
        L.append("| cell | " + " | ".join(d.replace("draw_", "") for d in present) + " |")
        L.append("|---|" + "---:|" * len(present))
        for c in cs:
            row = " | ".join(pct(call_rate([r for r in recs if clabel(r) == c and r.get("item_id") == d]))
                             for d in present)
            L.append(f"| {c} | {row} |")

    # sunk — loss aversion
    sunk_lvls = sorted({r["sunk"] for r in recs if r.get("scenario") == "sunk" and r.get("sunk") is not None})
    if sunk_lvls:
        L.append("\n## sunk — call rate as buried $ grows (forward decision is −EV throughout)\n")
        L.append("rising left→right = sunk-cost fallacy / loss aversion; flat-and-low = rational.\n")
        L.append("| cell | " + " | ".join(f"${int(s)} in" for s in sunk_lvls) + " |")
        L.append("|---|" + "---:|" * len(sunk_lvls))
        for c in cs:
            row = " | ".join(pct(call_rate([r for r in recs if clabel(r) == c
                             and r.get("scenario") == "sunk" and r.get("sunk") == s])) for s in sunk_lvls)
            L.append(f"| {c} | {row} |")

    # bet — aggression
    beq = sorted({r["equity"] for r in recs if r.get("scenario") == "bet"})
    if beq:
        L.append("\n## bet — mean committed fraction of stack vs equity (aggression)\n")
        L.append("| cell | " + " | ".join(pct(e) for e in beq) + " |")
        L.append("|---|" + "---:|" * len(beq))
        for c in cs:
            row = []
            for e in beq:
                fr = [r["committed_frac"] for r in recs if clabel(r) == c and r.get("scenario") == "bet"
                      and r["equity"] == e and r.get("committed_frac") is not None]
                row.append(f"{statistics.mean(fr):.2f}" if fr else "—")
            L.append(f"| {c} | " + " | ".join(row) + " |")

    # variance — made vs draw
    if any(r.get("scenario") == "variance" for r in recs):
        L.append("\n## variance — made hand vs draw at the same 50% / price\n")
        L.append("made call-rate > draw call-rate = the model shies from the swingy version.\n")
        L.append("| cell | made | draw | made − draw |")
        L.append("|---|---:|---:|---:|")
        for c in cs:
            m = call_rate([r for r in recs if clabel(r) == c and r.get("item_id") == "variance_made"])
            d = call_rate([r for r in recs if clabel(r) == c and r.get("item_id") == "variance_draw"])
            delta = (m - d) if (m is not None and d is not None) else None
            L.append(f"| {c} | {pct(m)} | {pct(d)} | {(f'{delta*100:+.0f}pt' if delta is not None else '—')} |")

    return "\n".join(L) + "\n"


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--runs", default=os.path.join(os.path.dirname(__file__), "output", "runs.jsonl"))
    p.add_argument("--report", default=None)
    a = p.parse_args()
    if not os.path.exists(a.runs):
        raise SystemExit(f"No runs file at {a.runs}.")
    recs = load(a.runs)
    if not recs:
        raise SystemExit("empty.")
    rep = build_report(recs)
    print(rep)
    if a.report:
        open(a.report, "w").write(rep)
        print(f"Report written to {a.report}")


if __name__ == "__main__":
    main()
