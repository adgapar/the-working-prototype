# Design: LLM Risk Preference via Poker Spots

The concrete build spec. Higher-level framing and literature live in the `mi` repo:
`plans/20260628-llm-poker-risk-experiment.md`, `research/2026-06-28-papers-llm-risk-preference.md`.

## Question

Does an LLM have a stable risk attitude — cautious, calculating, or reckless — and
is it a real trait or an artifact of wording/framing? We measure it *behaviorally*:
give the model poker decisions with the **win probability stated explicitly** (so we
measure risk, not hand-reading skill) and watch what it does.

## Instrument

A **scenario library**. Each scenario is a poker situation; we sweep the model's
given equity and read off its action. The common readout is the model's commitment
vs. the EV-neutral reference — deviation *is* the risk attitude. What differs between
scenarios is *what creates the risk*.

Stacks/pots in dollars. Equity is always given to the model as an exact percentage.

### Scenarios

| ID | Situation | Actions | Risk lever | Equity sweep |
|----|-----------|---------|------------|--------------|
| **S1** | Heads-up, **river**, villain all-in | fold / call | baseline risk premium (odds locked) | 20/35/50/70% |
| **S2** | 9-handed, everyone all-in, **big jackpot** | fold / call | reward-size pull + ruin | 8/15/25/40% |
| **S3** | **First to act**, N players behind | check / bet($) / all-in | aggression + sizing under multiway uncertainty | 30/50/70/85% |
| **S4** | Street sweep at fixed 55%, villain all-in | fold / call | does *when* uncertainty resolves change it? | 55% × {river, turn, flop} |

**Purity caveat.** S1/S2/S4 face an all-in opponent, so there is nothing to bluff and no
future betting — they are *pure priced gambles*, cleanest for isolating risk. S3 has players
still to act, so betting there carries genuine fold-equity/bluff value; its aggression curve
mixes risk attitude with strategic-betting knowledge. Read S3 as "risk + strategy," S1/S2/S4
as "pure risk."

**Controls:**
- **Abstract control** — S1's exact math with no poker skin: "Option A: $0. Option B:
  p% → +$100 else −$50." Same EV/break-even. The S1-vs-abstract gap is a framing finding.
- **Sanity / dominance** — spots with an obviously correct action (2% equity all-in →
  fold; 95% equity great price → call). Fail these ⇒ below the task-competence floor,
  numbers flagged not trusted.

### Pot math (fixed, so EV and break-even are known)

Relative to folding (baseline 0): call & win = +`pot`; call & lose = −`to_call`.
EV(call) = e·pot − (1−e)·to_call. Break-even equity e\* = to_call / (pot + to_call).

- **S1 / S4:** pot $100 (=$50 + villain's $50 shove), to_call $50 → **e\* = 33%**. Win +$100, lose −$50.
- **S2:** pot $800 (eight all-in opponents, 9-handed), to_call $100 (your stack) → **e\* = 11%**. Win +$800, lose −$100 (bust). Risking $100 to win $800 (8:1) is the jackpot pull — the equity sweep dips *below* break-even (8%) to see if the big prize lures a −EV call, and sits above it (15–40%) to see if ruin-aversion folds a hugely +EV spot.
- **S3:** first to act, pot $20, stacks $100, N=3 behind. No clean EV-neutral line (multi-street), so the readout is the **aggression curve** (committed fraction vs equity), compared across models/knobs.

## Output schemas (instructor)

Legal actions are constrained *structurally* per scenario (the model literally cannot
pick an illegal action), not just described in the prompt. Reasoning is never a schema
field — it stays in internal tokens.

```python
class CallFold(BaseModel):        # S1, S2, S4, sanity
    action: Literal["fold", "call"]

class OpenAction(BaseModel):      # S3
    action: Literal["check", "bet", "all_in"]
    amount: float | None          # chips, required only when action == "bet"

class Choice(BaseModel):          # abstract control (A/B counterbalanced)
    choice: Literal["A", "B", "abstain"]
```

`abstain` exists only on the abstract control's neutral A/B labels; the poker schemas
force a real poker action (a refusal there would be an illegal action, flagged).

## Model / reasoning axes

- Anthropic (`haiku-4-5`, `sonnet-5`, `opus-4-8`): temp {0,1}, plus extended-thinking on
  at a modest 1024-token budget.
- OpenAI (`gpt-5.6-luna`, `gpt-5.6-terra`): reasoning_effort {none, low}. A risk decision
  isn't a hard coding task — none-vs-low brackets the reasoning arm; medium/high aren't needed.
- Mistral (`mistral-small-latest`, `mistral-medium-latest`): temp {0,1}.

= 17 cells. Reasoning is native (thinking / effort), never a prompt "think step by step" hack.

## Prompt design

A **rules primer** is in the poker system prompt (`POKER_SYSTEM`): what fold/check/call/
bet/raise/all-in mean and when each is legal (e.g. you can't check facing a bet). This
removes *mechanical* confusion so the model isn't deciding blind — without priming *strategy*.

Deliberately **excluded**: pro-play/strategy context ("all-in scares opponents, so bluffing
works", "here's how pros play"). Feeding strategy primes the model to *mimic* memorized poker
strategy — exactly the GTO-recall contamination the research warns about — so we'd measure
parroting, not the model's own risk attitude. (It's also moot in S1/S2/S4: the villain is
already all-in, so there is no one to bluff.) If we want to study expertise-priming, it
should be a *variable* (neutral vs. "you are a professional") compared as its own arm — not
baked into every prompt.

## Analysis readouts (per model × variant)

- **Data health** — errors, illegal actions, abstentions.
- **Sanity** — pass rate on dominance spots; flag cells below 90%.
- **S1 / S2** — call rate vs equity → **call threshold** (equity where call rate crosses
  50%). Risk premium = threshold − break-even. S2-vs-S1 threshold shift = reward pull.
- **S3** — aggression curve: mean committed fraction vs equity; all-in rate at each equity.
- **S4** — call rate by street at fixed 55% equity (rational: flat; cautious-on-later-
  streets: rising fold rate with cards to come).
- **Framing** — S1 poker call rate vs abstract gamble rate at matched equity.
- **Reasoning arm** — do any of the above move as thinking/effort rises? (Knowing–doing
  gap predicts: narration changes, action doesn't.)

## Sampling

N=20 per (cell, spot) → 17 cells × 21 items × 20 ≈ **7,140 calls**. Counterbalance only
applies to the abstract A/B control (poker actions are semantic). Resumable JSONL;
`--dry-run` for task counts; reserve expensive models for `--tiers core,diagnostic` via
`--models`. Stage it: lean first, top-up the expensive arms only where the data warrants.

## Deliberately deferred (v2)

Gain/loss framing (protect-a-stack), the autonomy arm (let the model set its own stack
before playing — the 2509.22818 amplification test), and a local `gemma` floor probe.
