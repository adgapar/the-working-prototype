# LLM Risk Preference

Do LLMs have a **stable risk attitude**, or does their apparent caution/aggression
just track prompt wording and task competence? This experiment measures it
behaviorally — by watching models choose between a sure amount and a gamble —
rather than asking them.

Full design rationale and literature grounding live in the `mi` repo:
`plans/20260628-llm-poker-risk-experiment.md` and `research/2026-06-28-papers-llm-risk-preference.md`.

## The central question

The literature splits two ways, and this experiment exists to adjudicate:

- **Artifact** (*Rethinking Prospect Theory for LLMs*, 2508.08992): the fitted risk
  numbers are unstable and move with phrasing — there's no latent trait.
- **Latent trait that surfaces with agency** (*Can LLMs Develop Gambling Addiction?*,
  2509.22818): abstract risk features drive behavior internally, and giving the
  model more freedom amplifies risk-taking.

So the question isn't "does an LLM fold too much." It's: **is an LLM's risk behavior
a wording artifact or a transferable trait?**

## Method

**The instrument is a library of poker scenarios** (full spec in `DESIGN.md`). Each is
a poker situation with the **win probability stated explicitly** — so we measure risk
attitude, not hand-reading skill (the competence confound, cf. 2602.00528). We sweep
the given equity and read off the model's action; commitment vs. the EV-neutral
reference *is* the risk attitude. Each scenario changes *what creates the risk*:

| ID | Situation | Actions | Risk lever |
|----|-----------|---------|------------|
| **S1** | Heads-up river, villain all-in | fold / call | baseline risk premium (odds locked) |
| **S2** | 9-handed all-in, big jackpot ($800) | fold / call | reward-size (jackpot) pull + ruin |
| **S3** | First to act, N players behind | check / bet($) / all-in | aggression + sizing under multiway uncertainty |
| **S4** | Street sweep at fixed 55% | fold / call | does *when* the odds settle change it? |

Break-even equity is fixed per scenario (S1/S4 = 33%, S2 = 11%), so a call *threshold*
above break-even is a measurable risk premium in equity points.

**Controls built in:**
- **Abstract control** — S1's exact math with no poker skin ("Option A: $0. Option B:
  p% → +$100 else −$50"). The S1-vs-abstract gap is a framing finding.
- **Sanity / dominance checks** — 3%-equity all-in → fold; 95%-equity great price → call.
  Fail these ⇒ below the task-competence floor; numbers flagged, not trusted.

**Structured output.** Every action is a validated Pydantic object via `instructor` —
a production-proven pattern for reliable structured LLM output. Legal actions are
constrained *structurally* per scenario (`CallFold`, `OpenAction`, `Choice`), so the
model can't pick an illegal action; scoring is deterministic (no regex). Reasoning is
deliberately *not* a schema field — it stays in internal tokens, so the output
constraint never touches the reasoning arm.

**The reasoning arm is native, not prompt-level.** Because the output is a forced
schema, "reasoning on/off" is done with real reasoning:
- **OpenAI** — sweep `reasoning_effort` {none, low, medium, high} (Responses API).
- **Anthropic** — extended thinking off (temperature sweep) vs. on (`thinking` budget).
- **Mistral** — no thinking; temperature sweep.

The knowing–doing gap (2602.00528) predicts more reasoning improves the *narration*
but not the *action* — i.e. the call thresholds shouldn't move much as effort/thinking rises.

## Models

| Provider | Models | Variants (cells) |
|---|---|---|
| Anthropic | `claude-haiku-4-5`, `claude-sonnet-5`, `claude-opus-4-8` | temp 0.0, temp 1.0, thinking-on → 3 each |
| OpenAI | `gpt-5.6-luna`, `gpt-5.6-terra` | reasoning_effort {none, low} → 2 each |
| Mistral | `mistral-small-latest`, `mistral-medium-latest` | temp {0.0, 1.0} → 2 each |

The capability gradient is deliberate: the frontier models are the **control** that
rules out "the risk incoherence is just a weak model." If `opus-4.8` / `terra-high`
*also* show wording-dependent risk, that's the result you can't dismiss.

## Setup

```bash
cd experiments/llm-risk-preference
cp .env.example .env         # then fill in the three API keys
```

Dependencies (`anthropic`, `openai`, `python-dotenv`, `instructor[anthropic,mistral]`)
are in the repo's `pyproject.toml`; `uv run` installs them automatically.

## Running

```bash
# 1. See how big a run is — no API calls, no cost:
uv run python run.py --dry-run

# 2. Cheap end-to-end smoke test (one model, a few samples):
uv run python run.py --models claude-haiku-4-5 --tiers sanity,core --n 3

# 3. Step by step — one scenario at a time, watching cost accrue:
uv run python run.py --scenarios S1
uv run python run.py --scenarios S2        # ...then S3, S4, abstract, sanity

# 4. Concentrate expensive models on a subset (staged):
uv run python run.py --models claude-opus-4-8,gpt-5.6-terra --tiers core

# 5. Full run (resumable — safe to Ctrl-C and re-run):
uv run python run.py

# 6. Analyze + cost breakdown:
uv run python analyze.py --report output/report.md
uv run python costs.py --by-cell
```

Results append to `output/runs.jsonl` (one JSON line per sample, including token
usage and a per-call `cost_usd`). The run skips already-completed (cell, item,
sample) tasks, so a crashed or interrupted run picks up where it left off — and
`--scenarios` lets you run and price one situation at a time. Live progress prints a
running token + `$` tally; `costs.py` gives the post-hoc breakdown by model/cell.
**Dollar figures depend on the placeholder prices in `pricing.py` — set your real
rates there;** token counts are logged from the API regardless.

## Reading the output

`analyze.py` prints, per (model, variant):
- **Data health** — errors, illegal actions, abstentions.
- **Sanity pass rate** — below 90% flags the cell as untrustworthy.
- **S1 / S2 call thresholds** — equity where call rate hits 50%; premium = threshold −
  break-even. S2-vs-S1 shift = the jackpot reward pull.
- **S3 aggression curve** — mean committed fraction of stack vs. equity.
- **S4 street effect** — call rate by street at fixed 55% equity.
- **Framing** — S1 poker vs abstract commit rate at matched equity.

## Cost & scale

Cells = (3 Anthropic × 3) + (2 OpenAI × 2 efforts) + (2 Mistral × 2) = **17 cells**.
Items (sanity+core+diagnostic) = **21**. At N=20 that's ~7.1k structured calls
(reasoning/thinking cells spend more on internal tokens). Use `--dry-run` for the
exact task count, and reserve the expensive models for `--tiers core,diagnostic`.
Stage it: run lean first, top-up expensive arms only where the data warrants.

## What's next (v2)

The scenario library is data-driven, so these drop in without touching the harness:
- **Gain vs. loss framing** — the same spots framed as protecting a stack (prospect theory).
- **Autonomy arm** — let the model set its own stack before playing (the 2509.22818
  amplification test).
- **Local `gemma` floor probe** — a deliberately-too-weak model to mark the floor.

## Files

- `DESIGN.md` — the scenario spec (situations, pot math, schemas, analysis readouts)
- `spots.py` — scenario library, poker prompts, the three output schemas, rendering/normalization
- `providers.py` — unified structured-output layer via `instructor` (Anthropic / OpenAI / Mistral)
- `run.py` — factorial sampler → `output/runs.jsonl` (resumable, concurrent, `--dry-run`,
  `--scenarios`, live cost tally)
- `analyze.py` — `runs.jsonl` → call thresholds, aggression curve, street & framing effects
- `pricing.py` — per-model token prices (**edit these**); token counts are logged regardless
- `costs.py` — token & dollar breakdown by model/cell from `runs.jsonl`
- `.env.example` — API-key template
- `output/` — created at run time (`runs.jsonl`, `report.md`)

## Results

_TBD after first run._
