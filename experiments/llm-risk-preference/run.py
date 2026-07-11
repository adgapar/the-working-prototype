#!/usr/bin/env python3
"""Factorial sampler for the LLM risk-preference experiment (poker scenarios).

For each (model, variant, item) cell it draws N samples, gets a structured action
via instructor, normalizes it (committed? how much?), and appends one JSON line per
sample to output/runs.jsonl. Resumable: completed tasks are skipped on restart.

The reasoning arm is native:
  - Anthropic: extended thinking off (temp sweep) vs on (thinking budget, temp=1)
  - OpenAI:    reasoning_effort {none, low, medium, high}
  - Mistral:   no thinking (temp sweep)

Usage:
    uv run python run.py --dry-run
    uv run python run.py --models claude-haiku-4-5 --tiers sanity,core --n 3   # smoke
    uv run python run.py                                                       # full run
    uv run python run.py --models claude-opus-4-8,gpt-5.6-terra --tiers core,diagnostic
"""

from __future__ import annotations

import argparse
import json
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from pricing import cost_of
from providers import call_model
from spots import Item, build_items, normalize_response, render_item, system_for

# ---------------------------------------------------------------------------
# Configuration — edit here, or override on the CLI
# ---------------------------------------------------------------------------

MODELS: list[dict] = [
    {"id": "claude-haiku-4-5", "provider": "anthropic"},
    {"id": "claude-sonnet-5", "provider": "anthropic", "no_temp": True},
    {"id": "claude-opus-4-8", "provider": "anthropic", "no_temp": True},
    {"id": "gpt-5.6-luna", "provider": "openai"},
    {"id": "gpt-5.6-terra", "provider": "openai"},
    {"id": "mistral-small-latest", "provider": "mistral"},
    {"id": "mistral-medium-latest", "provider": "mistral"},
]

TEMPERATURES: list[float] = [0.0, 1.0]
# Risk decisions aren't complex coding — low reasoning is plenty; skip medium/high.
OPENAI_REASONING_EFFORTS: list[str] = ["none", "low"]
ANTHROPIC_THINKING_BUDGET = 1024   # a modest "low" thinking budget

N_DEFAULT = 20
CONCURRENCY_DEFAULT = 6

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
RUNS_PATH = os.path.join(OUTPUT_DIR, "runs.jsonl")

_write_lock = threading.Lock()


# ---------------------------------------------------------------------------
# Cell + task expansion
# ---------------------------------------------------------------------------

def expand_cells(models: list[dict]) -> list[dict]:
    cells: list[dict] = []
    for m in models:
        p = m["provider"]
        if p == "anthropic":
            if m.get("no_temp"):  # sonnet-5 / opus-4-8: temp deprecated, adaptive thinking
                cells.append(_cell(m, {}, "default"))
                cells.append(_cell(m, {"thinking": True, "effort": "low"}, "think-low"))
            else:
                for temp in TEMPERATURES:
                    cells.append(_cell(m, {"temperature": temp}, f"t{temp}"))
                cells.append(_cell(
                    m, {"thinking": True, "budget": ANTHROPIC_THINKING_BUDGET, "temperature": 1.0},
                    f"think{ANTHROPIC_THINKING_BUDGET}"))
        elif p == "openai":
            for effort in OPENAI_REASONING_EFFORTS:
                cells.append(_cell(m, {"reasoning_effort": effort}, f"e-{effort}"))
        elif p == "mistral":
            for temp in TEMPERATURES:
                cells.append(_cell(m, {"temperature": temp}, f"t{temp}"))
        else:
            raise ValueError(f"Unknown provider {p} for model {m['id']}")
    return cells


def _cell(m: dict, variant: dict, label: str) -> dict:
    return {"model": m["id"], "provider": m["provider"], "variant": variant, "variant_label": label}


def task_key(cell: dict, item_id: str, i: int) -> str:
    return f"{cell['model']}|{cell['variant_label']}|{item_id}|{i}"


def load_done_keys() -> set[str]:
    done: set[str] = set()
    if not os.path.exists(RUNS_PATH):
        return done
    with open(RUNS_PATH) as f:
        for line in f:
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if rec.get("error") is None and rec.get("action") is not None:
                done.add(rec["task_key"])
    return done


# ---------------------------------------------------------------------------
# One sample
# ---------------------------------------------------------------------------

def run_task(cell: dict, item: Item, i: int) -> dict:
    prompt, response_model, mapping = render_item(item, i)

    rec = {
        "task_key": task_key(cell, item.item_id, i),
        "model": cell["model"], "provider": cell["provider"],
        "variant_label": cell["variant_label"],
        "item_id": item.item_id, "scenario": item.scenario, "kind": item.kind,
        "tier": item.tier, "equity": item.equity, "street": item.street,
        "n_opponents": item.n_opponents, "pot": item.pot, "to_call": item.to_call,
        "stack": item.stack, "breakeven": item.breakeven, "dominant": item.dominant,
        "sample": i,
    }

    t0 = time.time()
    try:
        resp, usage = call_model(
            cell["provider"], cell["model"], system_for(item), prompt,
            cell["variant"], response_model=response_model,
        )
        norm = normalize_response(item, resp, mapping)
        rec["latency_s"] = round(time.time() - t0, 2)
        rec.update(norm)          # action, committed, committed_frac, amount, illegal
        rec.update(usage)         # input_tokens, output_tokens, reasoning_tokens
        rec["cost_usd"] = cost_of(cell["model"], usage["input_tokens"], usage["output_tokens"])
        rec["error"] = None
    except Exception as e:  # noqa: BLE001
        rec["latency_s"] = round(time.time() - t0, 2)
        rec.update({"action": None, "committed": None, "committed_frac": None,
                    "amount": None, "illegal": None, "input_tokens": None,
                    "output_tokens": None, "reasoning_tokens": None, "cost_usd": None,
                    "error": f"{type(e).__name__}: {e}"[:300]})

    return rec


def append_record(rec: dict) -> None:
    with _write_lock:
        with open(RUNS_PATH, "a") as f:
            f.write(json.dumps(rec) + "\n")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Sample LLM poker risk decisions into runs.jsonl")
    p.add_argument("--models", help="Comma-separated model ids (default: all in MODELS)")
    p.add_argument("--tiers", default="sanity,core,diagnostic",
                   help="Comma-separated item tiers to run (default: all)")
    p.add_argument("--scenarios", default=None,
                   help="Comma-separated scenarios to run step by step, e.g. S1 or S1,S2 "
                        "(default: all). Values: S1 S2 S3 S4 abstract sanity")
    p.add_argument("--n", type=int, default=N_DEFAULT, help=f"Samples per cell (default {N_DEFAULT})")
    p.add_argument("--concurrency", type=int, default=CONCURRENCY_DEFAULT)
    p.add_argument("--dry-run", action="store_true", help="Count tasks and exit; no API calls")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    models = MODELS
    if args.models:
        wanted = {m.strip() for m in args.models.split(",")}
        models = [m for m in MODELS if m["id"] in wanted]
        if not models:
            raise SystemExit(f"No known models match {sorted(wanted)}")

    tiers = {t.strip() for t in args.tiers.split(",")}
    items = build_items(tiers)
    if args.scenarios:
        wanted_scen = {s.strip() for s in args.scenarios.split(",")}
        items = [it for it in items if it.scenario in wanted_scen]
        if not items:
            raise SystemExit(f"No items match scenarios {sorted(wanted_scen)}")
    cells = expand_cells(models)

    all_tasks = [(c, it, i) for c in cells for it in items for i in range(args.n)]
    done = load_done_keys()
    todo = [t for t in all_tasks if task_key(t[0], t[1].item_id, t[2]) not in done]

    print(f"Models: {[m['id'] for m in models]}")
    print(f"Cells: {len(cells)} | Items: {len(items)} (tiers={sorted(tiers)}) | N: {args.n}")
    print(f"Total tasks: {len(all_tasks)} | already done: {len(done)} | to run: {len(todo)}")

    if args.dry_run:
        print("\n[dry-run] No API calls made.")
        return
    if not todo:
        print("Nothing to do — all tasks already completed. Analyze with analyze.py.")
        return

    done_count, errors, cost, in_tok, out_tok, start = 0, 0, 0.0, 0, 0, time.time()
    with ThreadPoolExecutor(max_workers=args.concurrency) as ex:
        futures = [ex.submit(run_task, c, it, i) for (c, it, i) in todo]
        for fut in as_completed(futures):
            rec = fut.result()
            append_record(rec)
            done_count += 1
            errors += 1 if rec["error"] else 0
            cost += rec.get("cost_usd") or 0.0
            in_tok += rec.get("input_tokens") or 0
            out_tok += rec.get("output_tokens") or 0
            if done_count % 25 == 0 or done_count == len(todo):
                rate = done_count / max(time.time() - start, 1e-6)
                print(f"  {done_count}/{len(todo)} done | {errors} err | {rate:.1f}/s | "
                      f"{in_tok/1000:.0f}k in / {out_tok/1000:.0f}k out | ${cost:.2f} so far")

    print(f"\nDone. Wrote {done_count} records ({errors} errors) to {RUNS_PATH}")
    print(f"Tokens: {in_tok/1000:.0f}k in / {out_tok/1000:.0f}k out | est. cost ${cost:.2f} "
          f"(this run; check pricing.py)")
    print("Analyze with:  uv run python analyze.py  |  Cost breakdown:  uv run python costs.py")


if __name__ == "__main__":
    main()
