#!/usr/bin/env python3
"""
Ablation: decompose WHY the collapsed-to-one-turn (embedded) arm behaves as it does.

Runs six conditions on the SAME instances so they're directly comparable:
  full          - single-turn baseline
  concat        - all shards, one clean merged instruction (no transcript, no framing)
  sharded       - native multi-turn message array
  embedded      - full transcript collapsed to one user turn, WITH "write your reply" framing
  embeddedmin   - same collapse, NO framing instruction        (isolates framing)
  embeddeduser  - only USER turns collapsed, WITH framing       (isolates including own prior turns)

Resumable: skips (task_id, conv_type) pairs already present in the log folder.

Usage:
  python run_ablation.py --dataset_file data/sharded_math_subset20.json \
    --assistant_model gpt-4.1-mini --N_runs 10 --workers 16 --log_folder results/logs_ablation20
"""
import argparse, json, glob, random
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import tqdm

from simulator_full import ConversationSimulatorFull
from simulator_sharded import ConversationSimulatorSharded
from simulator_embedded import ConversationSimulatorEmbedded

CONDITIONS = ["full", "concat", "sharded", "embedded", "embeddedmin", "embeddeduser"]


def existing_counts(log_folder, dataset_fn):
    """(conv_type, task_id) -> count already logged."""
    ds = dataset_fn.split("/")[-1]
    c = Counter()
    for f in glob.glob(f"{log_folder}/math/*/*.jsonl"):
        for line in open(f):
            if not line.strip():
                continue
            d = json.loads(line)
            if d["dataset_fn"] == ds:
                c[(d["conv_type"].split("-")[0], d["task_id"])] += 1
    return c


def make_sim(cond, sample, a_model, s_model, u_model, dataset_fn, log_folder):
    if cond == "full":
        return ConversationSimulatorFull(sample, a_model, s_model, dataset_fn=dataset_fn, log_folder=log_folder)
    if cond == "concat":
        return ConversationSimulatorFull(sample, a_model, s_model, run_concat=True, dataset_fn=dataset_fn, log_folder=log_folder)
    if cond == "sharded":
        return ConversationSimulatorSharded(sample, a_model, s_model, u_model, dataset_fn=dataset_fn, log_folder=log_folder)
    variant = {"embedded": "embedded", "embeddedmin": "minimal", "embeddeduser": "useronly"}[cond]
    return ConversationSimulatorEmbedded(sample, a_model, s_model, u_model, dataset_fn=dataset_fn, log_folder=log_folder, variant=variant)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset_file", default="data/sharded_math_subset20.json")
    ap.add_argument("--assistant_model", default="gpt-4.1-mini")
    ap.add_argument("--system_model", default="gpt-4o-mini")
    ap.add_argument("--user_model", default="gpt-4o-mini")
    ap.add_argument("--N_runs", type=int, default=10)
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--log_folder", default="results/logs_ablation20")
    args = ap.parse_args()

    samples = [d for d in json.load(open(args.dataset_file)) if d["task"] == "math"]
    have = existing_counts(args.log_folder, args.dataset_file)

    todos = []
    for cond in CONDITIONS:
        for s in samples:
            need = args.N_runs - have[(cond, s["task_id"])]
            todos += [(cond, s)] * max(0, need)
    random.shuffle(todos)
    print(f"{len(samples)} instances x {len(CONDITIONS)} conditions x {args.N_runs} runs; {len(todos)} to run")
    print(Counter(c for c, _ in todos))

    def work(todo):
        cond, s = todo
        try:
            make_sim(cond, s, args.assistant_model, args.system_model, args.user_model,
                     args.dataset_file, args.log_folder).run(verbose=False)
        except Exception as e:
            import traceback
            tqdm.tqdm.write(f"\033[91m[err {cond} {s['task_id']}] {e}\033[0m")

    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        list(tqdm.tqdm(ex.map(work, todos), total=len(todos)))


if __name__ == "__main__":
    main()
