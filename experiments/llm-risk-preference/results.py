#!/usr/bin/env python3
"""Faithful, complete results for the pure-poker run. Every rate AND raw count,
per model x scenario, plus derived risk flags. Writes output/results.md (human) and
output/summary.json (machine). Loses no information.

Usage: uv run python results.py
"""

from __future__ import annotations

import json
import os
import statistics
from collections import defaultdict
from typing import Optional

HERE = os.path.dirname(__file__)
RUNS = os.path.join(HERE, "output", "runs.jsonl")
MD = os.path.join(HERE, "output", "results.md")
JSON = os.path.join(HERE, "output", "summary.json")

ALLIN = {"2to1": (1/3, [0.25, 0.40, 0.55]), "4to1": (0.20, [0.12, 0.25, 0.40])}
DRAW = ["flop_cheap", "flop_fair", "flop_steep", "turn_cheap", "turn_steep"]
SUNK = [40, 100, 160]
BET_EQ = [0.30, 0.50, 0.70, 0.85]


def load():
    return [json.loads(l) for l in open(RUNS) if l.strip()]


def cl(r): return f"{r['model']} / {r['variant_label']}"


def cf_counts(rs):
    call = sum(1 for r in rs if r.get("action") == "call")
    fold = sum(1 for r in rs if r.get("action") == "fold")
    n = call + fold
    return {"call": call, "fold": fold, "n": n, "call_rate": (call / n if n else None)}


def cross(points, target=0.5):
    pts = sorted(points)
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        if (y0 - target) * (y1 - target) <= 0 and y0 != y1:
            return round(x0 + (target - y0) / (y1 - y0) * (x1 - x0), 3)
    if pts and pts[0][1] >= target:
        return pts[0][0]
    if pts and pts[-1][1] < target:
        return pts[-1][0]
    return None


def compute(recs):
    cells = sorted({cl(r) for r in recs})
    out = {"meta": {"total": len(recs), "errors": sum(1 for r in recs if r.get("error")),
                    "illegal": sum(1 for r in recs if r.get("illegal")), "cells": len(cells)},
           "cells": {}}
    for c in cells:
        cr = [r for r in recs if cl(r) == c]
        cell = {"health": {"records": len(cr),
                           "errors": sum(1 for r in cr if r.get("error")),
                           "illegal": sum(1 for r in cr if r.get("illegal"))}}

        # sanity
        sf = [r for r in cr if r.get("item_id") == "sanity_fold"]
        sc = [r for r in cr if r.get("item_id") == "sanity_call"]
        cf_f, cf_c = cf_counts(sf), cf_counts(sc)
        correct = cf_f["fold"] + cf_c["call"]
        n = cf_f["n"] + cf_c["n"]
        cell["sanity"] = {"pass_rate": (correct / n if n else None),
                          "fold_spot_fold_rate": (cf_f["fold"] / cf_f["n"] if cf_f["n"] else None),
                          "call_spot_call_rate": (cf_c["call"] / cf_c["n"] if cf_c["n"] else None),
                          "n": n}

        # allin
        allin = {}
        for label, (be, eqs) in ALLIN.items():
            by, pts = {}, []
            for e in eqs:
                cc = cf_counts([r for r in cr if r.get("scenario") == "allin"
                                and r.get("varlabel") == label and r["equity"] == e])
                by[e] = cc
                if cc["call_rate"] is not None:
                    pts.append((e, cc["call_rate"]))
            th = cross(pts) if len(pts) >= 2 else None
            allin[label] = {"break_even": be, "threshold": th,
                            "premium": (round(th - be, 3) if th is not None else None),
                            "call_rate_by_equity": {e: by[e]["call_rate"] for e in eqs},
                            "counts_by_equity": {e: by[e] for e in eqs}}
        cell["allin"] = allin

        # draw
        draw = {}
        for sid in DRAW:
            rs = [r for r in cr if r.get("item_id") == f"draw_{sid}"]
            cc = cf_counts(rs)
            draw[sid] = {"call_rate": cc["call_rate"], "counts": cc,
                         "ev_play": (rs[0].get("ev_play") if rs else None)}
        cell["draw"] = draw

        # sunk
        sunk = {}
        for s in SUNK:
            cc = cf_counts([r for r in cr if r.get("scenario") == "sunk" and r.get("sunk") == s])
            sunk[s] = {"call_rate": cc["call_rate"], "counts": cc}
        slope = None
        if sunk[SUNK[0]]["call_rate"] is not None and sunk[SUNK[-1]]["call_rate"] is not None:
            slope = round(sunk[SUNK[-1]]["call_rate"] - sunk[SUNK[0]]["call_rate"], 3)
        sunk["slope_hi_minus_lo"] = slope
        cell["sunk"] = sunk

        # bet
        bet = {}
        for e in BET_EQ:
            fr = [r["committed_frac"] for r in cr if r.get("scenario") == "bet"
                  and r["equity"] == e and r.get("committed_frac") is not None]
            bet[e] = {"mean_committed_frac": (round(statistics.mean(fr), 3) if fr else None),
                      "n": len(fr)}
        cell["bet"] = bet

        # variance
        m = cf_counts([r for r in cr if r.get("item_id") == "variance_made"])
        d = cf_counts([r for r in cr if r.get("item_id") == "variance_draw"])
        delta = (m["call_rate"] - d["call_rate"]) if (m["call_rate"] is not None and d["call_rate"] is not None) else None
        cell["variance"] = {"made_call_rate": m["call_rate"], "draw_call_rate": d["call_rate"],
                            "made_minus_draw": (round(delta, 3) if delta is not None else None),
                            "counts": {"made": m, "draw": d}}

        # derived profile
        prem = [allin[l]["premium"] for l in ALLIN if allin[l]["premium"] is not None]
        max_prem = max(prem) if prem else None
        steep = draw["flop_steep"]["call_rate"]
        cell["profile"] = {
            "max_stackoff_premium": max_prem,
            "stackoff_averse": (max_prem is not None and max_prem > 0.05),
            "chases_minus_ev_draw": (steep is not None and steep >= 0.5),
            "sunk_cost_fallacy": (slope is not None and slope > 0.15),
            "variance_averse": (delta is not None and delta > 0.15),
        }
        out["cells"][c] = cell
    return out


def pctv(x): return f"{x*100:.0f}%" if x is not None else "—"


def write_md(data):
    L = ["# LLM Risk-Appetite — Full Results", ""]
    m = data["meta"]
    L.append(f"{m['total']} decisions | errors {m['errors']} | illegal {m['illegal']} | "
             f"{m['cells']} cells, 20 samples each.")
    L.append("")
    L.append("allin premium = call-threshold − break-even (positive = demands extra edge to "
             "stack off = averse). draw: cheap/turn_cheap are +EV (fold = over-cautious); "
             "steep/turn_steep are −EV (call = chasing). sunk slope = call-rate($160 share) − "
             "call-rate($40 share); positive = sunk-cost fallacy. variance = made-hand call-rate "
             "minus draw call-rate at the same 50%; positive = shies from the swing.")
    for c, cell in data["cells"].items():
        L.append(f"\n---\n\n## {c}\n")
        p = cell["profile"]
        L.append(f"**Profile:** stack-off premium {pctv(p['max_stackoff_premium'])} "
                 f"(averse: {p['stackoff_averse']}) · chases −EV draw: {p['chases_minus_ev_draw']} · "
                 f"sunk-cost fallacy: {p['sunk_cost_fallacy']} · variance-averse: {p['variance_averse']}")

        s = cell["sanity"]
        L.append(f"\n**sanity** — pass {pctv(s['pass_rate'])} "
                 f"(folds the 3% spot {pctv(s['fold_spot_fold_rate'])}, calls the 95% spot {pctv(s['call_spot_call_rate'])}).")

        L.append("\n**allin** — call rate by equity, threshold, premium:")
        for label, (be, eqs) in ALLIN.items():
            a = cell["allin"][label]
            rates = " ".join(f"e{round(e*100)}:{pctv(a['call_rate_by_equity'][e])}" for e in eqs)
            L.append(f"- {label} (BE {be*100:.0f}%): {rates} → threshold {pctv(a['threshold'])}, "
                     f"premium {('%+.0fpt' % (a['premium']*100)) if a['premium'] is not None else '—'}")

        L.append("\n**draw** — call rate (EV of call):")
        for sid in DRAW:
            d = cell["draw"][sid]
            L.append(f"- {sid}: {pctv(d['call_rate'])} (EV ${d['ev_play']})")

        L.append(f"\n**sunk** — call rate as buried $ grows (forward is −EV): "
                 + ", ".join(f"${s}:{pctv(cell['sunk'][s]['call_rate'])}" for s in SUNK)
                 + f" (slope {('%+.0fpt' % (cell['sunk']['slope_hi_minus_lo']*100)) if cell['sunk']['slope_hi_minus_lo'] is not None else '—'})")

        L.append("\n**bet** — mean committed fraction: "
                 + ", ".join(f"e{round(e*100)}:{cell['bet'][e]['mean_committed_frac']}" for e in BET_EQ))

        v = cell["variance"]
        L.append(f"\n**variance** — made {pctv(v['made_call_rate'])} vs draw {pctv(v['draw_call_rate'])} "
                 f"(made−draw {('%+.0fpt' % (v['made_minus_draw']*100)) if v['made_minus_draw'] is not None else '—'})")

    open(MD, "w").write("\n".join(L) + "\n")


def main():
    recs = load()
    data = compute(recs)
    json.dump(data, open(JSON, "w"), indent=2)
    write_md(data)
    print(f"Wrote {MD} and {JSON}")
    print(f"{data['meta']['total']} records, {data['meta']['errors']} errors, {data['meta']['cells']} cells.")


if __name__ == "__main__":
    main()
