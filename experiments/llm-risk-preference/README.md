# LLM Risk Preference

Do LLMs have a **stable risk attitude**, or does their apparent caution/aggression
just track prompt wording and task competence? This experiment measures it
behaviorally, from pure poker decisions, rather than asking the model.

Higher-level framing and literature grounding live in the `mi` repo:
`plans/20260712-what-kind-of-poker-player-is-an-ai.md` and
`research/2026-06-28-papers-llm-risk-preference.md`.

## The question

The literature splits two ways:

- **Artifact** (*Rethinking Prospect Theory for LLMs*, 2508.08992): the fitted risk
  numbers are unstable and move with phrasing — there's no latent trait.
- **Latent trait that surfaces with agency** (*Can LLMs Develop Gambling Addiction?*,
  2509.22818): abstract risk features drive behavior internally, and more freedom
  amplifies risk-taking.

So the question isn't "does an LLM fold too much." It's whether an LLM's risk behavior
is a wording artifact or a transferable trait.

## Method

The instrument is a library of **pure-poker spots** (full spec in `DESIGN.md`). Every
spot states the model's **win probability explicitly**, so we measure risk attitude,
not hand-reading skill (the competence confound, cf. 2602.00528). Only real table
actions are offered — check / bet / call / fold / all-in — no deals, no insurance,
nothing a friendly game wouldn't recognize. Risk shows up as **deviation from the
EV-correct play**, and those deviations are the risk behaviors:

| scenario | situation | actions | what it measures |
|---|---|---|---|
| `allin` | facing a river all-in with a made hand, across pot odds (2:1, 4:1) | fold / call | risk premium — folding a +EV call = aversion |
| `draw` | chasing a flush draw, priced +EV / break-even / −EV, flop and turn | fold / call | chasing — calling a −EV draw = seeking |
| `sunk` | −EV to continue; your share of the pot varies | fold / call | sunk-cost / loss aversion |
| `bet` | first to act | check / bet($) / all-in | aggression (committed fraction vs equity) |
| `variance` | made hand vs draw at the same 50% and price | fold / call | feeling the swing |
| `sanity` | dominated call/fold | fold / call | competence floor |

Break-even equity is fixed per spot, so a call *threshold* above break-even is a
measurable risk premium in equity points.

**Structured output.** Every action is a validated Pydantic object via `instructor`.
Legal actions are constrained *structurally* per scenario (`CallFold`, `OpenAction`),
so the model can't return an illegal action and scoring is deterministic. Reasoning is
never a schema field — it stays in internal tokens, so the output constraint never
touches the reasoning arm.

**The reasoning arm is native, not prompt-level:**
- **Anthropic** — extended thinking off (temperature sweep) vs on (thinking budget / adaptive effort).
- **OpenAI** — `reasoning_effort` {none, low} (Responses API).
- **Mistral** — no thinking; temperature sweep.

## Models

| Provider | Models | Settings (cells) |
|---|---|---|
| Anthropic | `claude-haiku-4-5` | temp 0, temp 1, thinking-on → 3 |
| Anthropic | `claude-sonnet-5`, `claude-opus-4-8` | default, thinking-low → 2 each |
| OpenAI | `gpt-5.6-luna`, `gpt-5.6-terra` | reasoning_effort {none, low} → 2 each |
| Mistral | `mistral-small-latest`, `mistral-medium-latest` | temp {0, 1} → 2 each |

**15 cells.** The capability gradient is deliberate: the frontier models are the
control that rules out "the risk behavior is just a weak model."

## Setup

```bash
cd experiments/llm-risk-preference
cp .env.example .env         # then fill in the three API keys
```

Dependencies are in the repo's `pyproject.toml`; `uv run` installs them automatically.

## Running

```bash
# See how big a run is — no API calls:
uv run python run.py --dry-run

# Cheap smoke test (one model, a few samples):
uv run python run.py --models claude-haiku-4-5 --tiers sanity,core --n 3

# One scenario at a time (allin, draw, sunk, bet, variance, sanity):
uv run python run.py --scenarios sunk

# Full run (resumable — safe to Ctrl-C and re-run):
uv run python run.py

# Analyze, faithful results, cost breakdown:
uv run python analyze.py --report output/report.md
uv run python results.py
uv run python costs.py
```

Results append to `output/runs.jsonl` (one JSON line per sample, with token usage and
a per-call `cost_usd`). The run skips already-completed (cell, item, sample) tasks, so
an interrupted run resumes, and `--scenarios` runs/prices one situation at a time.
**Dollar figures depend on the prices in `pricing.py`** — token counts are logged from
the API regardless.

## Reading the output

- `analyze.py` → `output/report.md` — per (model, setting) tables: data health, sanity,
  allin thresholds/premiums, draw chasing, sunk-cost slope, bet aggression, variance.
- `results.py` → `output/results.md` + `output/summary.json` — the faithful,
  lossless view: every rate and raw count per cell, plus derived risk flags.
- `costs.py` — token & dollar breakdown by model.

## Scale

15 cells × 22 items × N=20 = **6,600 structured calls**. Use `--dry-run` for the
exact task count, and reserve the expensive models for `--tiers core` via `--models`.

## Deferred

Gain/loss framing (the same spots as protecting a stack), an autonomy arm (let the
model size its own bet — the 2509.22818 amplification test), and a local weak-model
floor probe. The scenario library is data-driven, so these drop in without touching
the harness.

## Files

- `DESIGN.md` — the spot spec (situations, pot math, schemas, analysis readouts)
- `spots.py` — scenario library, poker prompts, output schemas, rendering/normalization
- `providers.py` — unified structured-output layer via `instructor` (Anthropic / OpenAI / Mistral)
- `run.py` — factorial sampler → `output/runs.jsonl` (resumable, concurrent, `--dry-run`, `--scenarios`, live cost tally)
- `analyze.py` — `runs.jsonl` → per-dimension tables (`output/report.md`)
- `results.py` — `runs.jsonl` → faithful lossless results (`output/results.md`, `output/summary.json`)
- `pricing.py` — per-model token prices; token counts are logged regardless
- `costs.py` — token & dollar breakdown from `runs.jsonl`
- `.env.example` — API-key template
