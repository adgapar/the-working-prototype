#!/usr/bin/env python3
"""
Analyze a Full / Concat / Sharded / Embedded sweep.

Reports the paper's own three-way decomposition per condition:
  - Performance : mean score over ALL runs (aptitude + reliability combined)
  - Aptitude    : average per-instance P90 (best-case) score
  - Unreliability: average per-instance (P90 - P10) gap  [lower = more reliable]

The headline question: does the EMBEDDED format (sharded turns collapsed into a
single narrative user turn) recover the Sharded performance drop and/or shrink
the Sharded unreliability, relative to native multi-turn Sharded?

Usage:
    python analyze.py --log_folder logs_main [--json results/results.json]
"""
import json, glob, argparse, statistics as st
from collections import defaultdict

COND_ORDER = ["full", "concat", "sharded", "embedded"]
COND_LABEL = {
    "full": "Full (single-turn baseline)",
    "concat": "Concat (all shards, one turn)",
    "sharded": "Sharded / native (multi-turn)",
    "embedded": "Sharded / embedded (collapsed)",
}


def percentile(xs, p):
    """Linear-interpolation percentile on a sorted copy of xs (p in 0..100)."""
    if not xs:
        return float("nan")
    ys = sorted(xs)
    if len(ys) == 1:
        return ys[0]
    k = (len(ys) - 1) * (p / 100.0)
    lo = int(k)
    hi = min(lo + 1, len(ys) - 1)
    return ys[lo] + (ys[hi] - ys[lo]) * (k - lo)


def load(log_folder):
    # scores[cond][task_id] = [score per run]
    scores = defaultdict(lambda: defaultdict(list))
    for f in glob.glob(f"{log_folder}/math/*/*.jsonl"):
        with open(f) as fh:
            lines = fh.readlines()
        for line in lines:
            if not line.strip():
                continue
            d = json.loads(line)
            ct = d["conv_type"].split("-")[0]  # strip temperature suffix
            s = d.get("score")
            if s is None:
                s = 1.0 if d.get("is_correct") else 0.0
            scores[ct][d["task_id"]].append(float(s))
    return scores


def summarize(scores):
    rows = {}
    for ct, per_inst in scores.items():
        all_runs = [s for runs in per_inst.values() for s in runs]
        apt = [percentile(runs, 90) for runs in per_inst.values()]
        unrel = [percentile(runs, 90) - percentile(runs, 10) for runs in per_inst.values()]
        inst_means = [sum(runs) / len(runs) for runs in per_inst.values()]
        rows[ct] = {
            "n_instances": len(per_inst),
            "n_runs_total": len(all_runs),
            "runs_per_instance": round(len(all_runs) / max(1, len(per_inst)), 1),
            "performance": round(100 * sum(all_runs) / len(all_runs), 1),
            "aptitude_p90": round(100 * sum(apt) / len(apt), 1),
            "unreliability_p90_p10": round(100 * sum(unrel) / len(unrel), 1),
            "avg_instance_std": round(100 * (sum(st.pstdev(r) for r in per_inst.values()) / len(per_inst)), 1),
        }
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--log_folder", default="logs_main")
    ap.add_argument("--json", default=None)
    args = ap.parse_args()

    scores = load(args.log_folder)
    rows = summarize(scores)

    hdr = f'{"condition":<34}{"inst":>5}{"runs":>6}{"perf%":>7}{"apt(P90)%":>11}{"unreliab%":>11}{"avgStd%":>9}'
    print(hdr)
    print("-" * len(hdr))
    for ct in COND_ORDER:
        if ct not in rows:
            continue
        r = rows[ct]
        print(f'{COND_LABEL[ct]:<34}{r["n_instances"]:>5}{r["n_runs_total"]:>6}'
              f'{r["performance"]:>7}{r["aptitude_p90"]:>11}{r["unreliability_p90_p10"]:>11}{r["avg_instance_std"]:>9}')

    # Key deltas
    if "sharded" in rows and "embedded" in rows:
        sh, em = rows["sharded"], rows["embedded"]
        print("\nKey deltas (Embedded - Sharded):")
        print(f'  performance:   {em["performance"]-sh["performance"]:+.1f} pts  (recovering the multi-turn drop?)')
        print(f'  aptitude:      {em["aptitude_p90"]-sh["aptitude_p90"]:+.1f} pts')
        print(f'  unreliability: {em["unreliability_p90_p10"]-sh["unreliability_p90_p10"]:+.1f} pts  (negative = MORE reliable)')
    if "full" in rows and "sharded" in rows:
        print(f'\nReplication check (Full - Sharded performance): '
              f'{rows["full"]["performance"]-rows["sharded"]["performance"]:+.1f} pts '
              f'(paper reports a large drop here)')

    if args.json:
        import os
        os.makedirs(os.path.dirname(args.json) or ".", exist_ok=True)
        with open(args.json, "w") as f:
            json.dump({"conditions": rows,
                       "per_instance_scores": {ct: dict(v) for ct, v in scores.items()}}, f, indent=2)
        print(f"\nSaved {args.json}")


if __name__ == "__main__":
    main()
