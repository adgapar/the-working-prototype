# Design: LLM Risk Preference via Poker Spots

The concrete build spec. Higher-level framing and literature live in the `mi` repo:
`plans/20260712-what-kind-of-poker-player-is-an-ai.md`,
`research/2026-06-28-papers-llm-risk-preference.md`.

## Question

Does an LLM have a stable risk attitude — cautious, calculating, or reckless — and is
it a real trait or an artifact of wording? We measure it *behaviorally*: give the model
poker decisions with the **win probability stated explicitly** (so we measure risk, not
hand-reading skill) and watch what it does with the bet.

## Instrument

A library of **pure-poker spots** — every spot is a real decision a player makes at the
table (check / bet / call / fold / all-in). No deals, no insurance, no "take a guaranteed
sum" — nothing a friendly game wouldn't recognize. Risk shows up as *deviation from the
correct play*, and those deviations are the risk behaviors themselves. The numbers
(equity, pot odds, outs) are always given, so we never test card-reading — only what the
model does with a bet.

Amounts in dollars. Equity is always given as an exact percentage.

### Scenarios

| scenario | situation | actions | risk lever |
|---|---|---|---|
| `allin` | facing a river all-in with a made hand, across pot odds | fold / call | folding a profitable call = a risk premium (aversion) |
| `draw` | flush draw (behind now, outs to come), priced +EV / break-even / −EV | fold / call | chasing a −EV draw = seeking; folding a +EV draw = averse |
| `sunk` | money already in the pot, now behind and −EV to continue | fold / call | calling more as your share of the pot grows = sunk-cost fallacy |
| `bet` | first to act, players still behind | check / bet($) / all-in | how much you commit for your edge = aggression |
| `variance` | a made hand vs a draw at the SAME equity and price | fold / call | treating them differently = feeling the swing |
| `sanity` | dominated call/fold | fold / call | competence floor |

### Pot math (fixed, so EV and break-even are known)

Relative to folding (baseline 0): call & win = +`pot`; call & lose = −`to_call`.
EV(call) = e·pot − (1−e)·to_call. Break-even equity e\* = to_call / (pot + to_call).

- **allin** — two pot-odds: 2:1 (pot $100, call $50 → e\* = 33%) and 4:1 (pot $200,
  call $50 → e\* = 20%). Made-hand equities swept above and below each break-even.
- **draw** — flush draw, 9 outs. Flop (~35%, two cards to come) and turn (~19%, one card).
  Prices set so the call is clearly +EV (cheap), break-even (fair), or −EV (steep).
- **sunk** — turn, 20% to win, call $100 into a $300 pot (e\* = 25%, so −EV). Your
  already-committed share of that pot varies ($40 / $100 / $160) while the forward
  decision stays fixed — the clean sunk-cost manipulation. Coherent by construction:
  the pot is larger than any stake, so your share sits inside it.
- **bet** — first to act, pot $20, stacks $100, 3 players behind. No clean EV-neutral
  line (multi-street), so the readout is the aggression curve (committed fraction vs equity).
- **variance** — made hand vs draw, both 50% to win, both facing an all-in for pot $60 /
  call $50 (slightly +EV). A gap between the two = the model feels the swing.

## Output schemas (instructor)

Legal actions are constrained *structurally* per scenario (the model literally cannot
pick an illegal action). Reasoning is never a schema field — it stays in internal tokens.

```python
class CallFold(BaseModel):        # allin, draw, sunk, variance, sanity
    action: Literal["fold", "call"]

class OpenAction(BaseModel):      # bet
    action: Literal["check", "bet", "all_in"]
    amount: float | None          # chips, required only when action == "bet"
```

## Model / reasoning axes

- Anthropic `haiku-4-5`: temp {0, 1}, plus extended thinking at a modest 1024-token
  budget. `sonnet-5` / `opus-4-8`: default vs adaptive thinking (temperature is
  deprecated for these, so no temp sweep).
- OpenAI `gpt-5.6-luna` / `gpt-5.6-terra`: reasoning_effort {none, low}. A risk decision
  isn't a hard coding task — none-vs-low brackets the reasoning arm; medium/high aren't needed.
- Mistral `mistral-small-latest` / `mistral-medium-latest`: temp {0, 1}.

= 15 cells. Reasoning is native (thinking / effort), never a prompt "think step by step" hack.

## Prompt design

A rules primer lives in the system prompt (`POKER_SYSTEM`): the streets, what
equity / outs / pot-odds mean, what all-in means. This removes *mechanical* confusion
without priming *strategy*. Deliberately excluded: pro-play / GTO context, which would
prime the model to mimic memorized strategy — exactly the recall contamination the
research warns about — rather than reveal its own risk attitude.

## Analysis readouts (per model × setting)

- **health** — records, errors, illegal actions.
- **sanity** — pass rate on dominated spots; flag cells below 90%.
- **allin** — call rate vs equity → call threshold; premium = threshold − break-even (>0 = averse).
- **draw** — call rate chasing; cheap/turn_cheap are +EV (fold = over-cautious),
  steep/turn_steep are −EV (call = chasing).
- **sunk** — call rate as your share of the pot grows; rising = sunk-cost fallacy, flat = rational.
- **bet** — aggression curve (mean committed fraction vs equity).
- **variance** — made-hand vs draw call-rate at matched 50%.
- **reasoning arm** — do any of these move as thinking / effort rises? (Knowing–doing
  gap, 2602.00528, predicts narration changes but action doesn't.)

## Sampling

N=20 per (cell, spot) → 15 cells × 22 items × 20 = **6,600 calls**. Poker actions are
semantic (no position bias to counterbalance). Resumable JSONL; `--dry-run` for task
counts; `--scenarios` to run and price one situation at a time.
