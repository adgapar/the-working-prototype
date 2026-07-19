# Multi-Turn History Format: does collapsing history into one turn mitigate "lost in conversation"?

An extension of **"LLMs Get Lost in Multi-Turn Conversation"** (Laban et al., 2025 — [arXiv:2505.06120](https://arxiv.org/abs/2505.06120), [code](https://github.com/microsoft/lost_in_conversation)).

## The question

The paper shows that when a fully-specified instruction is *sharded* — broken into pieces revealed one per turn — LLMs degrade sharply versus getting everything up front. The degradation splits into a small **aptitude** loss and a large **reliability** loss (models become unpredictable). Their proposed causes: premature answer attempts, early wrong assumptions, and **self-anchoring on prior outputs** — "when LLMs take a wrong turn, they get lost and don't recover."

The paper varied *how much* history exists (Full / Concat / Sharded) but never varied **how the model receives it**. In every condition the assistant is called with a **native multi-turn message array** — it is *extending its own prior generations*, one step per turn.

This experiment adds one condition that changes only the representation:

> **Embedded** — the exact same sharded conversation, but at each assistant call the entire history is **collapsed into a single user turn** (a narrative transcript the model *reads*), instead of a native multi-turn array it *extends*.

Hypothesis (from `mi/research/future-experiments.md`): reading history as one turn may reduce self-anchoring, because the model is no longer retrieving its own prior message-array outputs — it's reading a transcript of them. If so, Embedded should recover some of the Sharded performance drop and, more importantly, **shrink the reliability gap**.

## Conditions

| Condition | History given to the assistant | Turns |
|---|---|---|
| **Full** | complete instruction, one message | single |
| **Concat** | all shards concatenated into one message | single |
| **Sharded / native** | shards revealed 1/turn, native message array | multi |
| **Sharded / embedded** *(new)* | shards revealed 1/turn, **history collapsed into one user turn** each step | multi |

Full and Concat are the paper's controls. `Sharded` is the paper's multi-turn condition. `Embedded` is ours. The only difference between `Sharded` and `Embedded` is the assistant's *view* of history — user simulator, shard reveal order, answer verification, extraction, and exact-match scoring are byte-for-byte identical.

## The change (the whole contribution)

`simulator_embedded.py` is a copy of upstream `simulator_sharded.py` with exactly one line of behavior changed — the assistant call:

```python
# Sharded (native multi-turn array — model extends its own prior outputs):
generate(extract_conversation(self.trace, to_str=False), ...)

# Embedded (history collapsed into one user turn — model reads a transcript):
embedded_input = build_embedded_input(self.system_message, self.trace)  # -> [system, single user turn]
generate(embedded_input, ...)
```

`build_embedded_input` renders prior turns as `[user] … / [assistant] …` prose inside one user message, wrapped with a short "here is the conversation so far … write your next reply" frame. `run_simulations.py` adds an `embedded` branch and `--N_embedded_runs`.

## Layout

This folder is **self-contained** — the upstream code is vendored (not cloned at runtime). See `NOTICE.md` for attribution and the exact list of what's original vs. upstream. Code runs from the folder root; `results/` holds the run logs and parsed numbers.

## Setup / reproduce

```bash
python3 -m venv .venv && ./.venv/bin/pip install -r requirements.txt
export OPENAI_API_KEY=...   # (or AZURE_OPENAI_API_KEY + AZURE_OPENAI_ENDPOINT)

# reproduce the reported run (103 instances × 10 runs × 4 conditions, ~$7, resumable):
./.venv/bin/python run_simulations.py --dataset_file data/sharded_math.json \
  --tasks math --models gpt-4.1-mini --system_model gpt-4o-mini --user_model gpt-4o-mini \
  --N_full_runs 10 --N_concat_runs 10 --N_sharded_runs 10 --N_embedded_runs 10 \
  --N_workers 16 --log_folder results/logs_gpt41mini

# fair re-grade (removes the extraction artifact — see "Grading" below), plus the raw view:
./.venv/bin/python analyze.py  --log_folder results/logs_gpt41mini --json results/ablation103_raw.json
./.venv/bin/python regrade.py  --log_folder results/logs_gpt41mini --dataset_file data/sharded_math.json \
  --json results/ablation103_regraded.json
```

`run_simulations.py` is resumable — it tops up to `N` runs/instance from whatever is already logged, so an interrupted run just needs the same command again. (The assistant under test is `gpt-4.1-mini`; the user-simulator and answer-extractor are held fixed on `gpt-4o-mini`.)

To reproduce the **ablation** (adds the `embeddedmin` and `embeddeduser` arms; also resumable, and skips arms already present in the folder):

```bash
./.venv/bin/python run_ablation.py --dataset_file data/sharded_math.json \
  --assistant_model gpt-4.1-mini --N_runs 10 --workers 16 --log_folder results/logs_gpt41mini
./.venv/bin/python regrade.py --log_folder results/logs_gpt41mini --dataset_file data/sharded_math.json \
  --json results/ablation103_regraded.json
```

## Design choices

- **Task = sharded GSM8K math.** Answer is a number → **deterministic exact-match scoring**, no LLM judge in the primary scorer, so no judge noise polluting the reliability signal. (One wrinkle surfaced anyway — see *Grading* below.)
- **Assistant under test = `gpt-4.1-mini`; scaffolding fixed on `gpt-4o-mini`.** Only the model being measured changes; the user-simulator and the answer-extractor are held constant so the comparison is clean.
- **103 instances × 10 runs × 4 conditions = 4,120 conversations**, ~$7. Repetitions (10/instance) are what buy the per-instance variance estimate the reliability metric needs.
- **Temperature = 1.0** (upstream default). Reliability only shows up above T=0 — the paper's key finding is that lowering temperature does *not* fix multi-turn unreliability.

## Grading: the extraction artifact (and the fix)

The upstream scorer extracts the answer with a small LLM step that requires the answer to be a substring of the response. The **embedded** condition makes the model answer more conversationally (markdown, `**$1,198**`, trailing "Would you like to…?"), and that extractor fails ~**3× more often on embedded** (9.4%) than on sharded (3.0%) — scoring answers `0` *even when the correct number is stated*. Left uncorrected, this alone manufactures a chunk of embedded's apparent deficit.

`regrade.py` fixes it: for every conversation scored not-correct, an LLM judge (gpt-4.1-mini, T=0) checks whether any answer-attempt turn actually states the gold answer (ignoring formatting / follow-up questions). It **only ever flips wrong→right** and is applied identically to every condition, so it can only *remove* false negatives. On the full run it flipped 274/1034 wrongs (26%); spot-checks confirmed the flips are genuinely correct answers. **All numbers below are post-re-grade.** (Raw, pre-re-grade tables are in `results/ablation103_raw.json` for comparison.)

## Metrics (paper's decomposition)

- **Performance** — mean score over all runs.
- **Aptitude (P90)** — average per-instance 90th-percentile (best-case) score.
- **Unreliability (P90−P10)** — average per-instance gap between best and worst runs. **Lower = more reliable.** This is the headline: the paper's central result is that multi-turn inflates this gap.

Headline comparison: **Embedded − Sharded** on performance and on unreliability.

## Results

`gpt-4.1-mini` (assistant under test; user-sim + extractor fixed on `gpt-4o-mini`), **103** GSM8K instances × 10 runs, T=1.0. Post-re-grade (see *Grading*). Per-instance scores in [`results/ablation103_regraded.json`](results/ablation103_regraded.json).

### Part 1 — the experiment as designed (4 conditions)

| Condition | Performance % | Aptitude (P90) % | Unreliability (P90−P10) % |
|---|---:|---:|---:|
| Full (single-turn baseline) | 96.6 | 99.0 | 5.1 |
| Concat (all shards, one turn) | 95.7 | 99.0 | 6.4 |
| Sharded / native (multi-turn) | 84.1 | 96.3 | 27.3 |
| **Sharded / embedded (collapsed)** | **79.1** | **94.4** | **37.4** |

**Lost-in-conversation reproduces.** Single-turn Full (96.6%) drops to multi-turn Sharded (84.1%, **−12.5 pts**); unreliability jumps 5.1 → 27.3 (**5×**). Concat (95.7%) stays next to Full, so it's the *turn-by-turn sharding*, not rephrasing. Milder than the paper's headline because gpt-4.1-mini is stronger than the mini tier they feature, but the signature (small aptitude loss, large reliability loss) is theirs.

**And the naive "embedded" collapse makes it *worse*, not better:** −5.0 performance and +10.1 unreliability vs native Sharded. Taken alone, that refutes the hypothesis. But *why* it's worse turns out to matter more than *that* it's worse — which is what the ablation is for.

### Part 2 — ablation: what actually caused the backfire

`embedded` bundles two things on top of "collapse to one turn": it includes **the model's own prior turns** in the transcript, and it adds a **"write your next reply" framing**. Two extra arms turn each off independently (same 103 instances):

| Arm | own turns? | framing? | Perf % | Aptitude % | Unreliability % |
|---|:-:|:-:|---:|---:|---:|
| Sharded / native | — | — | 84.1 | 96.3 | 27.3 |
| **Embedded** (transcript + framing) | yes | yes | 79.1 | 94.4 | 37.4 |
| Embedded-min (no framing) | yes | no | 82.6 | 94.5 | 26.9 |
| Embedded-user (no own turns) | no | yes | **88.1** | 99.0 | **24.2** |
| Concat (neither; merged instruction) | no | no | 95.7 | 99.0 | 6.4 |

**The collapse to one turn is not the culprit.** Both arms that collapse history but **drop the model's own prior turns** — Embedded-user and Concat — match or *beat* native multi-turn. Embedded-user is the best multi-turn arm in the whole table: **+4.0 performance and −3.1 unreliability vs native Sharded.**

The backfire decomposes cleanly:
- **Re-feeding the model its own prior turns** costs ≈ **−9 perf / +13 unreliability** (Embedded → Embedded-user).
- **The "write your reply" framing** costs ≈ **−3.5 perf / +10.5 unreliability** (Embedded → Embedded-min), and it's also what produced most of the extraction artifact (chat-mode verbosity).

**Mechanism — the paper's self-anchoring, amplified.** The sharded setup makes the model emit hedging, clarifying "could you tell me…?" turns. Replaying *those* as a transcript under a chat-reply frame **re-anchors** it into that mode — the opposite of the de-anchoring the hypothesis hoped for. Strip the model's own outputs from the collapsed history and the anchor is gone; reliability improves past native multi-turn.

**Bottom line.** The takeaway is not "don't collapse history." It's: *collapse the **user's** information into one turn and it helps (Concat, Embedded-user); dump the **whole transcript including the model's own prior turns** back in under a "reply" frame and it hurts.* How you collapse matters more than whether you collapse — and the failure mode it triggers is exactly the self-anchoring the paper names.

## Limitations

- **One task, one model.** Math is the mildest of the paper's six tasks (single numeric answer, semi-decomposable); code / database / API-calling could behave differently. This is a claim about gpt-4.1-mini on GSM8K, not all models.
- **Not a perfect 2×2.** Three of the four (own-turns × framing) corners are transcript-style arms; the fourth (neither) is Concat, which is a *merged instruction*, not a transcript — so the "neither" corner isn't a like-for-like embedded variant. The three transcript corners are enough to attribute the effect, and Concat corroborates the direction.
- **Re-grade dependency.** Headlines rest on the fair re-grade (the raw scorer under-credits the chatty arms). It only flips wrong→right and was spot-checked, but it's an LLM judge, not an oracle — raw tables are kept for scrutiny.

## Attribution

Built on [microsoft/lost_in_conversation](https://github.com/microsoft/lost_in_conversation) (MIT License, © Microsoft), vendored at a pinned commit. `simulator_embedded.py`, `analyze.py`, `regrade.py`, and `run_ablation.py` are original; `run_simulations.py`, `tasks/tasks.py`, and `model_openai.py` carry small marked patches; everything else is upstream. Full breakdown in `NOTICE.md`.
