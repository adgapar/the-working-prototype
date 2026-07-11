#!/usr/bin/env python3
"""Turn output/runs.jsonl into risk measurements (poker scenarios).

Per (model, variant):
  - Data health   — records, errors, illegal actions, abstentions.
  - Sanity        — pass rate on dominance spots; <90% flags the cell as untrustworthy.
  - S1 / S2       — call rate vs equity -> call THRESHOLD (equity where call rate crosses
                    50%). Risk premium = threshold - break-even (positive = risk averse).
                    S2 vs S1 threshold shift = reward-size (jackpot) pull.
  - S3            — aggression curve: mean committed fraction and all-in rate vs equity.
  - S4            — call rate by street at fixed 55% equity (rational: flat).
  - Framing       — S1 poker call rate vs abstract gamble rate at matched equity.

Usage:
    uv run python analyze.py
    uv run python analyze.py --runs output/runs.jsonl --report output/report.md
"""

from __future__ import annotations

import argparse
import json
import os
import statistics
from collections import defaultdict
from typing import Optional

SANITY_FLOOR = 0.90


# ---------------------------------------------------------------------------
# Load / group
# ---------------------------------------------------------------------------

def load_runs(path: str) -> list[dict]:
    recs = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    recs.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return recs


def cell_label(rec: dict) -> str:
    return f"{rec['model']} / {rec['variant_label']}"


def _cells(recs: list[dict]) -> list[str]:
    return sorted({cell_label(r) for r in recs})


def committed_rate(recs: list[dict]) -> Optional[float]:
    valid = [r for r in recs if r.get("committed") in (True, False)]
    if not valid:
        return None
    return sum(1 for r in valid if r["committed"]) / len(valid)


def rate_by_equity(recs: list[dict], scenario: str, cell: str) -> list[tuple[float, float]]:
    """Sorted [(equity, committed_rate)] for one scenario within one cell."""
    by_eq: dict[float, list[dict]] = defaultdict(list)
    for r in recs:
        if r.get("scenario") == scenario and cell_label(r) == cell and r.get("error") is None:
            by_eq[r["equity"]].append(r)
    pts = []
    for eq, rs in by_eq.items():
        rate = committed_rate(rs)
        if rate is not None:
            pts.append((eq, rate))
    return sorted(pts)


def threshold(points: list[tuple[float, float]], target: float = 0.5) -> Optional[float]:
    """Equity where an increasing commit-rate curve crosses `target`, interpolated."""
    pts = sorted(points)
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        if (y0 - target) * (y1 - target) <= 0 and y0 != y1:
            return x0 + (target - y0) / (y1 - y0) * (x1 - x0)
    if pts and pts[0][1] >= target:
        return pts[0][0]      # already committing at lowest equity -> threshold <= min
    if pts and pts[-1][1] < target:
        return pts[-1][0]     # never reaches target -> threshold >= max
    return None


# ---------------------------------------------------------------------------
# Reporting helpers
# ---------------------------------------------------------------------------

def _risk_word(premium: Optional[float]) -> str:
    if premium is None:
        return "?"
    if premium > 0.05:
        return "averse"
    if premium < -0.05:
        return "seeking"
    return "~neutral"


def _eq_cols(equities: list[float]) -> str:
    return " | ".join(f"{round(e*100)}%" for e in equities)


def _rate_row(points: list[tuple[float, float]], equities: list[float]) -> str:
    d = dict(points)
    return " | ".join(f"{d[e]*100:.0f}" if e in d else "—" for e in equities)


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def reproducibility_by_cell(recs: list[dict]) -> dict[str, dict]:
    """Per cell: agreement across the 20 reps (binary spots that were unanimous) and
    the mean rep-to-rep std of S3 bet fractions."""
    binary: dict[str, dict[str, list]] = defaultdict(lambda: defaultdict(list))
    s3: dict[str, dict[float, list]] = defaultdict(lambda: defaultdict(list))
    for r in recs:
        c = cell_label(r)
        if r.get("committed") in (True, False):
            binary[c][r["item_id"]].append(r["committed"])
        if r.get("scenario") == "S3" and r.get("committed_frac") is not None:
            s3[c][r["equity"]].append(r["committed_frac"])
    out: dict[str, dict] = {}
    for c in set(list(binary) + list(s3)):
        items = binary.get(c, {})
        unan = sum(1 for v in items.values() if len(set(v)) == 1)
        stds = [statistics.pstdev(v) for v in s3.get(c, {}).values() if len(v) > 1]
        out[c] = {
            "unanimous": unan, "n_items": len(items),
            "frac": (unan / len(items)) if items else None,
            "s3_std": (sum(stds) / len(stds)) if stds else None,
        }
    return out


def build_report(recs: list[dict]) -> str:
    L: list[str] = []
    cells = _cells(recs)
    total = len(recs)
    errors = sum(1 for r in recs if r.get("error"))
    L.append("# LLM Risk-Preference — Analysis (poker scenarios)\n")
    L.append(f"Records: {total} | errors: {errors} | cells: {len(cells)}\n")

    # --- Data health ---
    L.append("\n## Data health\n")
    L.append("| cell | records | errors | illegal | abstain |")
    L.append("|---|---:|---:|---:|---:|")
    for c in cells:
        rs = [r for r in recs if cell_label(r) == c]
        L.append(f"| {c} | {len(rs)} | {sum(1 for r in rs if r.get('error'))} | "
                 f"{sum(1 for r in rs if r.get('illegal'))} | "
                 f"{sum(1 for r in rs if r.get('action') == 'abstain')} |")

    # --- Sanity ---
    L.append("\n## Sanity (dominance checks)\n")
    L.append("| cell | pass rate | n | floor |")
    L.append("|---|---:|---:|:--:|")
    for c in cells:
        rs = [r for r in recs if cell_label(r) == c and r.get("scenario") == "sanity"]
        valid = [r for r in rs if r.get("action") in ("fold", "call")]
        correct = sum(1 for r in valid if r["action"] == r["dominant"])
        rate = correct / len(valid) if valid else 0.0
        flag = "OK" if (valid and rate >= SANITY_FLOOR) else "**FAIL**"
        L.append(f"| {c} | {rate*100:.0f}% | {len(valid)} | {flag} |")

    # --- Reproducibility across reps ---
    repro = reproducibility_by_cell(recs)
    L.append("\n## Reproducibility across the 20 reps\n")
    L.append("Most decisions are deterministic (all 20 reps identical) ⇒ std≈0 in the call-rate "
             "tables below; rep-to-rep variation concentrates near a model's indifference point. "
             "'Agreement' = share of a cell's fold/call spots where all 20 reps matched. A call "
             "rate near 50% at n=20 carries ~±11pt standard error.\n")
    L.append("| cell | binary agreement | S3 mean bet-frac std |")
    L.append("|---|---:|---:|")
    for c in cells:
        d = repro.get(c, {})
        agree = f"{d['frac']*100:.0f}% ({d['unanimous']}/{d['n_items']})" if d.get("frac") is not None else "—"
        s3s = f"{d['s3_std']:.2f}" if d.get("s3_std") is not None else "—"
        L.append(f"| {c} | {agree} | {s3s} |")

    # --- S1 / S2 call thresholds ---
    for scen, be_note in (("S1", "heads-up river, break-even 33%"),
                          ("S2", "9-handed all-in jackpot, break-even 11%")):
        eqs = sorted({r["equity"] for r in recs if r.get("scenario") == scen})
        if not eqs:
            continue
        L.append(f"\n## {scen} — call rate vs equity ({be_note})\n")
        L.append("Threshold = equity where call rate hits 50%. Premium = threshold − break-even "
                 "(positive ⇒ demands extra edge ⇒ risk averse).\n")
        L.append(f"| cell | {_eq_cols(eqs)} | threshold | premium |")
        L.append("|---|" + "---:|" * (len(eqs) + 2))
        for c in cells:
            pts = rate_by_equity(recs, scen, c)
            if not pts:
                continue
            be = next((r["breakeven"] for r in recs if r.get("scenario") == scen), None)
            th = threshold(pts)
            prem = (th - be) if (th is not None and be is not None) else None
            th_s = f"{th*100:.0f}%" if th is not None else "—"
            prem_s = f"{prem*100:+.0f}pt ({_risk_word(prem)})" if prem is not None else "—"
            L.append(f"| {c} | {_rate_row(pts, eqs)} | {th_s} | {prem_s} |")

    # --- S3 aggression curve ---
    s3_eqs = sorted({r["equity"] for r in recs if r.get("scenario") == "S3"})
    if s3_eqs:
        L.append("\n## S3 — aggression: committed fraction of stack (mean ± std over reps)\n")
        L.append(f"| cell | {_eq_cols(s3_eqs)} |")
        L.append("|---|" + "---:|" * len(s3_eqs))
        for c in cells:
            by_eq = {}
            for e in s3_eqs:
                fr = [r["committed_frac"] for r in recs if r.get("scenario") == "S3"
                      and cell_label(r) == c and r["equity"] == e and r.get("committed_frac") is not None]
                if fr:
                    sd = statistics.pstdev(fr) if len(fr) > 1 else 0.0
                    by_eq[e] = f"{statistics.mean(fr):.2f}±{sd:.2f}"
            if by_eq:
                row = " | ".join(by_eq.get(e, "—") for e in s3_eqs)
                L.append(f"| {c} | {row} |")

    # --- S4 street effect ---
    streets = [s for s in ("river", "turn", "flop")
               if any(r.get("scenario") == "S4" and r.get("street") == s for r in recs)]
    if streets:
        L.append("\n## S4 — call rate by street at fixed 55% equity\n")
        L.append("Rational: flat (EV identical). Rising fold rate with cards-to-come ⇒ "
                 "caution about delayed resolution.\n")
        L.append(f"| cell | {' | '.join(streets)} |")
        L.append("|---|" + "---:|" * len(streets))
        for c in cells:
            row = {}
            for s in streets:
                rs = [r for r in recs if r.get("scenario") == "S4" and cell_label(r) == c
                      and r.get("street") == s]
                rate = committed_rate(rs)
                if rate is not None:
                    row[s] = rate
            if row:
                L.append(f"| {c} | " + " | ".join(
                    f"{row[s]*100:.0f}%" if s in row else "—" for s in streets) + " |")

    # --- Framing: S1 poker vs abstract ---
    abs_eqs = sorted({r["equity"] for r in recs if r.get("scenario") == "abstract"})
    if abs_eqs:
        L.append("\n## Framing — commit rate: poker (S1) vs abstract lottery, matched equity\n")
        L.append("A gap ⇒ the poker skin itself changes risk-taking (framing effect).\n")
        L.append(f"| cell | skin | {_eq_cols(abs_eqs)} |")
        L.append("|---|---|" + "---:|" * len(abs_eqs))
        for c in cells:
            s1 = rate_by_equity(recs, "S1", c)
            ab = rate_by_equity(recs, "abstract", c)
            if s1:
                L.append(f"| {c} | poker | {_rate_row(s1, abs_eqs)} |")
            if ab:
                L.append(f"| {c} | abstract | {_rate_row(ab, abs_eqs)} |")

    return "\n".join(L) + "\n"


def main() -> None:
    p = argparse.ArgumentParser(description="Analyze runs.jsonl into risk measurements")
    default_runs = os.path.join(os.path.dirname(__file__), "output", "runs.jsonl")
    p.add_argument("--runs", default=default_runs)
    p.add_argument("--report", default=None, help="Also write the report to this markdown path")
    args = p.parse_args()

    if not os.path.exists(args.runs):
        raise SystemExit(f"No runs file at {args.runs}. Run run.py first.")
    recs = load_runs(args.runs)
    if not recs:
        raise SystemExit("runs.jsonl is empty.")

    report = build_report(recs)
    print(report)
    if args.report:
        with open(args.report, "w") as f:
            f.write(report)
        print(f"Report written to {args.report}")


if __name__ == "__main__":
    main()
