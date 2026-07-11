#!/usr/bin/env python3
"""Cost & token breakdown from output/runs.jsonl.

Aggregates logged token usage per model (and per cell) and applies pricing.py to
estimate dollars. Token counts are real (from the API); dollars are only as good as
the prices in pricing.py.

Usage:
    uv run python costs.py
    uv run python costs.py --runs output/runs.jsonl --by-cell
"""

from __future__ import annotations

import argparse
import json
import os
from collections import defaultdict

from pricing import PRICING, cost_of


def load(path: str) -> list[dict]:
    out = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return out


def summarize(recs: list[dict], key) -> dict:
    agg: dict = defaultdict(lambda: {"calls": 0, "in": 0, "out": 0, "reason": 0,
                                     "cost": 0.0, "priced": 0, "no_usage": 0})
    for r in recs:
        k = key(r)
        a = agg[k]
        a["calls"] += 1
        it, ot = r.get("input_tokens"), r.get("output_tokens")
        if it is None or ot is None:
            a["no_usage"] += 1
            continue
        a["in"] += it
        a["out"] += ot
        a["reason"] += r.get("reasoning_tokens") or 0
        # Always recompute from tokens × current pricing (the logged cost_usd is a
        # run-time snapshot and goes stale if prices are edited; tokens don't).
        c = cost_of(r["model"], it, ot)
        if c is not None:
            a["cost"] += c
            a["priced"] += 1
    return agg


def print_table(title: str, agg: dict) -> None:
    print(f"\n## {title}\n")
    print(f"{'key':<34} {'calls':>6} {'in(k)':>7} {'out(k)':>7} {'reason(k)':>9} {'cost($)':>9}")
    print("-" * 76)
    tot = {"calls": 0, "in": 0, "out": 0, "reason": 0, "cost": 0.0}
    for k in sorted(agg):
        a = agg[k]
        flag = "  (no price)" if a["cost"] == 0 and a["calls"] else ""
        print(f"{k:<34} {a['calls']:>6} {a['in']/1000:>7.0f} {a['out']/1000:>7.0f} "
              f"{a['reason']/1000:>9.1f} {a['cost']:>9.2f}{flag}")
        for m in ("calls", "in", "out", "reason", "cost"):
            tot[m] += a[m]
    print("-" * 76)
    print(f"{'TOTAL':<34} {tot['calls']:>6} {tot['in']/1000:>7.0f} {tot['out']/1000:>7.0f} "
          f"{tot['reason']/1000:>9.1f} {tot['cost']:>9.2f}")


def main() -> None:
    p = argparse.ArgumentParser(description="Token & cost breakdown from runs.jsonl")
    default_runs = os.path.join(os.path.dirname(__file__), "output", "runs.jsonl")
    p.add_argument("--runs", default=default_runs)
    p.add_argument("--by-cell", action="store_true", help="Break down by model+variant, not just model")
    args = p.parse_args()

    if not os.path.exists(args.runs):
        raise SystemExit(f"No runs file at {args.runs}. Run run.py first.")
    recs = load(args.runs)
    if not recs:
        raise SystemExit("runs.jsonl is empty.")

    missing_price = sorted({r["model"] for r in recs if r["model"] not in PRICING})
    if missing_price:
        print(f"WARNING: no pricing.py entry for {missing_price} — cost shown as 0 for those.")

    print_table("By model", summarize(recs, lambda r: r["model"]))
    if args.by_cell:
        print_table("By cell (model / variant)",
                    summarize(recs, lambda r: f"{r['model']} / {r['variant_label']}"))
    print("\n(Token counts are real; dollars depend on pricing.py.)")


if __name__ == "__main__":
    main()
