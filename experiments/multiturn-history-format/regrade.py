#!/usr/bin/env python3
"""
Fair re-grade to remove the answer-EXTRACTION artifact.

Problem: the built-in scorer uses an extractive LLM step that fails ~3x more
often on the embedded condition (verbose/markdown answers with trailing
questions), scoring answers 0 even when the correct number is stated. That
biases the sharded-vs-embedded comparison.

Fix: for every conversation currently scored NOT-correct, ask a judge whether
ANY of its answer-attempt turns actually states the gold answer (formatting /
commas / $ / follow-up questions ignored). If yes, flip to correct. This only
ever flips wrong->right, so it can only *remove* false negatives, and it is
applied identically to all four conditions.

Outputs the corrected Performance / Aptitude / Unreliability table.

Usage:
    python regrade.py --log_folder results/logs_gpt41mini --json results/results_gpt41mini_regraded.json
"""
import json, glob, argparse, re
from concurrent.futures import ThreadPoolExecutor
from model_openai import generate
from analyze import percentile, summarize, COND_ORDER, COND_LABEL

JUDGE_MODEL = "gpt-4.1-mini"

JUDGE_PROMPT = """A student is solving a math word problem. The correct final answer is: {gold}

Here is one of the student's messages:
---
{response}
---

Ignoring formatting (commas, $, bold, LaTeX) and any follow-up questions the student adds, does this message state {gold} as its answer to the problem? Reply with exactly one word: YES or NO."""


def gold_map(dataset_fn):
    return {d["task_id"]: d["answer"].split("####")[1].strip() for d in json.load(open(dataset_fn))}


def answer_attempt_texts(trace):
    """Return the assistant messages that the harness classified as answer attempts.
    The system-verification log follows each assistant turn."""
    texts, pending = [], None
    for msg in trace:
        if msg["role"] == "assistant":
            pending = msg["content"]
        elif msg["role"] == "log" and msg.get("content", {}).get("type") == "system-verification":
            if pending is not None and msg["content"].get("response", {}).get("response_type") == "answer_attempt":
                texts.append(pending)
            pending = None
    # fallback: if nothing was classified as an attempt, use the last assistant msg
    if not texts:
        assts = [m["content"] for m in trace if m["role"] == "assistant"]
        if assts:
            texts.append(assts[-1])
    return texts


def judge_states_answer(gold, response):
    out = generate([{"role": "user", "content": JUDGE_PROMPT.format(gold=gold, response=response)}],
                   model=JUDGE_MODEL, temperature=0.0, max_tokens=3)
    return out.strip().upper().startswith("YES")


def regrade_conv(d, gold):
    """Return corrected 0/1 for one conversation."""
    if d.get("is_correct"):
        return 1.0
    g = gold[d["task_id"]]
    # cheap pre-filter: only bother the judge if the gold digits appear at all
    candidates = [t for t in answer_attempt_texts(d["trace"]) if g in re.sub(r"[,\$]", "", t)]
    for t in candidates:
        if judge_states_answer(g, t):
            return 1.0
    return 0.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--log_folder", required=True)
    ap.add_argument("--dataset_file", default="data/sharded_math.json")
    ap.add_argument("--json", default=None)
    ap.add_argument("--workers", type=int, default=16)
    args = ap.parse_args()

    gold = gold_map(args.dataset_file)

    # load all conversations
    convs = []
    for f in glob.glob(f"{args.log_folder}/math/*/*.jsonl"):
        for line in open(f):
            if line.strip():
                convs.append(json.loads(line))

    n_wrong = sum(1 for d in convs if not d.get("is_correct"))
    print(f"{len(convs)} conversations; re-grading {n_wrong} currently-wrong with {JUDGE_MODEL} judge...")

    def work(d):
        return (d["conv_type"].split("-")[0], d["task_id"], regrade_conv(d, gold),
                bool(d.get("is_correct")))

    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        results = list(ex.map(work, convs))

    scores = {}
    flips = 0
    for ct, tid, corrected, was_correct in results:
        scores.setdefault(ct, {}).setdefault(tid, []).append(corrected)
        if corrected == 1.0 and not was_correct:
            flips += 1
    print(f"Judge flipped {flips} conversations wrong->right ({100*flips/max(1,n_wrong):.0f}% of wrongs)\n")

    rows = summarize(scores)
    hdr = f'{"condition":<34}{"inst":>5}{"runs":>6}{"perf%":>7}{"apt(P90)%":>11}{"unreliab%":>11}{"avgStd%":>9}'
    print(hdr); print("-" * len(hdr))
    for ct in COND_ORDER:
        if ct in rows:
            r = rows[ct]
            print(f'{COND_LABEL[ct]:<34}{r["n_instances"]:>5}{r["n_runs_total"]:>6}'
                  f'{r["performance"]:>7}{r["aptitude_p90"]:>11}{r["unreliability_p90_p10"]:>11}{r["avg_instance_std"]:>9}')
    if "sharded" in rows and "embedded" in rows:
        sh, em = rows["sharded"], rows["embedded"]
        print("\nKey deltas (Embedded - Sharded), AFTER fair re-grade:")
        print(f'  performance:   {em["performance"]-sh["performance"]:+.1f} pts')
        print(f'  aptitude:      {em["aptitude_p90"]-sh["aptitude_p90"]:+.1f} pts')
        print(f'  unreliability: {em["unreliability_p90_p10"]-sh["unreliability_p90_p10"]:+.1f} pts  (negative = MORE reliable)')

    if args.json:
        import os
        os.makedirs(os.path.dirname(args.json) or ".", exist_ok=True)
        json.dump({"conditions": rows, "regrade_flips": flips,
                   "per_instance_scores": scores}, open(args.json, "w"), indent=2)
        print(f"\nSaved {args.json}")


if __name__ == "__main__":
    main()
