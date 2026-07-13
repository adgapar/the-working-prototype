# LLM Risk-Appetite — Analysis

Records: 6600 | errors: 0 | cells: 15

## Data health

| cell | records | errors | illegal |
|---|---:|---:|---:|
| claude-haiku-4-5 / t0.0 | 440 | 0 | 0 |
| claude-haiku-4-5 / t1.0 | 440 | 0 | 0 |
| claude-haiku-4-5 / think1024 | 440 | 0 | 0 |
| claude-opus-4-8 / default | 440 | 0 | 0 |
| claude-opus-4-8 / think-low | 440 | 0 | 0 |
| claude-sonnet-5 / default | 440 | 0 | 0 |
| claude-sonnet-5 / think-low | 440 | 0 | 0 |
| gpt-5.6-luna / e-low | 440 | 0 | 0 |
| gpt-5.6-luna / e-none | 440 | 0 | 0 |
| gpt-5.6-terra / e-low | 440 | 0 | 0 |
| gpt-5.6-terra / e-none | 440 | 0 | 0 |
| mistral-medium-latest / t0.0 | 440 | 0 | 0 |
| mistral-medium-latest / t1.0 | 440 | 0 | 0 |
| mistral-small-latest / t0.0 | 440 | 0 | 0 |
| mistral-small-latest / t1.0 | 440 | 0 | 0 |

## Sanity (dominated call/fold)

| cell | pass | n | floor |
|---|---:|---:|:--:|
| claude-haiku-4-5 / t0.0 | 100% | 40 | OK |
| claude-haiku-4-5 / t1.0 | 100% | 40 | OK |
| claude-haiku-4-5 / think1024 | 100% | 40 | OK |
| claude-opus-4-8 / default | 100% | 40 | OK |
| claude-opus-4-8 / think-low | 100% | 40 | OK |
| claude-sonnet-5 / default | 100% | 40 | OK |
| claude-sonnet-5 / think-low | 100% | 40 | OK |
| gpt-5.6-luna / e-low | 100% | 40 | OK |
| gpt-5.6-luna / e-none | 100% | 40 | OK |
| gpt-5.6-terra / e-low | 100% | 40 | OK |
| gpt-5.6-terra / e-none | 100% | 40 | OK |
| mistral-medium-latest / t0.0 | 100% | 40 | OK |
| mistral-medium-latest / t1.0 | 100% | 40 | OK |
| mistral-small-latest / t0.0 | 100% | 40 | OK |
| mistral-small-latest / t1.0 | 100% | 40 | OK |

## allin — call rate vs equity, 2to1 (break-even 33%)

threshold = equity where call rate hits 50%; premium = threshold − break-even (positive ⇒ demands extra edge to stack off ⇒ risk averse).

| cell | 25% | 40% | 55% | threshold | premium |
|---|---:|---:|---:|---:|---:|
| claude-haiku-4-5 / t0.0 | 0% | 0% | 100% | 48% | +14pt |
| claude-haiku-4-5 / t1.0 | 0% | 0% | 100% | 48% | +14pt |
| claude-haiku-4-5 / think1024 | 0% | 95% | 100% | 33% | -0pt |
| claude-opus-4-8 / default | 0% | 100% | 100% | 32% | -1pt |
| claude-opus-4-8 / think-low | 0% | 100% | 100% | 32% | -1pt |
| claude-sonnet-5 / default | 0% | 0% | 100% | 48% | +14pt |
| claude-sonnet-5 / think-low | 0% | 0% | 100% | 48% | +14pt |
| gpt-5.6-luna / e-low | 0% | 100% | 100% | 32% | -1pt |
| gpt-5.6-luna / e-none | 95% | 100% | 100% | 25% | -8pt |
| gpt-5.6-terra / e-low | 20% | 100% | 100% | 31% | -3pt |
| gpt-5.6-terra / e-none | 5% | 95% | 100% | 32% | -1pt |
| mistral-medium-latest / t0.0 | 0% | 100% | 100% | 32% | -1pt |
| mistral-medium-latest / t1.0 | 5% | 90% | 100% | 33% | -0pt |
| mistral-small-latest / t0.0 | 75% | 100% | 100% | 25% | -8pt |
| mistral-small-latest / t1.0 | 65% | 100% | 100% | 25% | -8pt |

## allin — call rate vs equity, 4to1 (break-even 20%)

threshold = equity where call rate hits 50%; premium = threshold − break-even (positive ⇒ demands extra edge to stack off ⇒ risk averse).

| cell | 12% | 25% | 40% | threshold | premium |
|---|---:|---:|---:|---:|---:|
| claude-haiku-4-5 / t0.0 | 0% | 0% | 0% | 40% | +20pt |
| claude-haiku-4-5 / t1.0 | 0% | 0% | 0% | 40% | +20pt |
| claude-haiku-4-5 / think1024 | 0% | 100% | 100% | 18% | -2pt |
| claude-opus-4-8 / default | 0% | 100% | 100% | 18% | -2pt |
| claude-opus-4-8 / think-low | 0% | 100% | 100% | 18% | -2pt |
| claude-sonnet-5 / default | 0% | 100% | 100% | 18% | -2pt |
| claude-sonnet-5 / think-low | 0% | 100% | 100% | 18% | -2pt |
| gpt-5.6-luna / e-low | 0% | 95% | 100% | 19% | -1pt |
| gpt-5.6-luna / e-none | 0% | 100% | 100% | 18% | -2pt |
| gpt-5.6-terra / e-low | 0% | 90% | 100% | 19% | -1pt |
| gpt-5.6-terra / e-none | 0% | 100% | 100% | 18% | -2pt |
| mistral-medium-latest / t0.0 | 0% | 5% | 100% | 32% | +12pt |
| mistral-medium-latest / t1.0 | 0% | 35% | 90% | 29% | +9pt |
| mistral-small-latest / t0.0 | 0% | 60% | 100% | 23% | +3pt |
| mistral-small-latest / t1.0 | 5% | 85% | 100% | 19% | -1pt |

## draw — call rate chasing (cheap=+EV, steep=−EV)

| cell | flop_cheap | flop_fair | flop_steep | turn_cheap | turn_steep |
|---|---:|---:|---:|---:|---:|
| claude-haiku-4-5 / t0.0 | 100% | 100% | 100% | 100% | 100% |
| claude-haiku-4-5 / t1.0 | 100% | 100% | 100% | 100% | 100% |
| claude-haiku-4-5 / think1024 | 100% | 90% | 35% | 100% | 0% |
| claude-opus-4-8 / default | 100% | 100% | 100% | 100% | 0% |
| claude-opus-4-8 / think-low | 100% | 100% | 100% | 100% | 0% |
| claude-sonnet-5 / default | 100% | 100% | 100% | 100% | 0% |
| claude-sonnet-5 / think-low | 100% | 100% | 100% | 100% | 0% |
| gpt-5.6-luna / e-low | 100% | 100% | 100% | 100% | 0% |
| gpt-5.6-luna / e-none | 100% | 100% | 100% | 100% | 0% |
| gpt-5.6-terra / e-low | 100% | 55% | 55% | 100% | 0% |
| gpt-5.6-terra / e-none | 100% | 100% | 0% | 100% | 0% |
| mistral-medium-latest / t0.0 | 100% | 100% | 100% | 100% | 100% |
| mistral-medium-latest / t1.0 | 100% | 100% | 100% | 100% | 95% |
| mistral-small-latest / t0.0 | 100% | 100% | 100% | 100% | 100% |
| mistral-small-latest / t1.0 | 100% | 100% | 100% | 100% | 100% |

## sunk — call rate as buried $ grows (forward decision is −EV throughout)

rising left→right = sunk-cost fallacy / loss aversion; flat-and-low = rational.

| cell | $40 in | $100 in | $160 in |
|---|---:|---:|---:|
| claude-haiku-4-5 / t0.0 | 0% | 0% | 0% |
| claude-haiku-4-5 / t1.0 | 0% | 0% | 0% |
| claude-haiku-4-5 / think1024 | 0% | 0% | 0% |
| claude-opus-4-8 / default | 0% | 0% | 0% |
| claude-opus-4-8 / think-low | 0% | 0% | 0% |
| claude-sonnet-5 / default | 0% | 0% | 0% |
| claude-sonnet-5 / think-low | 0% | 0% | 0% |
| gpt-5.6-luna / e-low | 0% | 0% | 0% |
| gpt-5.6-luna / e-none | 0% | 0% | 0% |
| gpt-5.6-terra / e-low | 0% | 0% | 0% |
| gpt-5.6-terra / e-none | 0% | 0% | 0% |
| mistral-medium-latest / t0.0 | 0% | 0% | 0% |
| mistral-medium-latest / t1.0 | 0% | 0% | 0% |
| mistral-small-latest / t0.0 | 0% | 0% | 0% |
| mistral-small-latest / t1.0 | 0% | 5% | 0% |

## bet — mean committed fraction of stack vs equity (aggression)

| cell | 30% | 50% | 70% | 85% |
|---|---:|---:|---:|---:|
| claude-haiku-4-5 / t0.0 | 0.00 | 0.06 | 0.12 | 0.12 |
| claude-haiku-4-5 / t1.0 | 0.00 | 0.05 | 0.11 | 0.12 |
| claude-haiku-4-5 / think1024 | 0.01 | 0.05 | 0.19 | 0.13 |
| claude-opus-4-8 / default | 0.00 | 0.14 | 0.15 | 0.15 |
| claude-opus-4-8 / think-low | 0.00 | 0.15 | 0.15 | 0.15 |
| claude-sonnet-5 / default | 0.08 | 0.14 | 0.15 | 0.15 |
| claude-sonnet-5 / think-low | 0.10 | 0.14 | 0.15 | 0.15 |
| gpt-5.6-luna / e-low | 0.00 | 0.16 | 0.15 | 0.14 |
| gpt-5.6-luna / e-none | 0.01 | 0.04 | 0.15 | 0.13 |
| gpt-5.6-terra / e-low | 0.05 | 0.19 | 0.15 | 0.21 |
| gpt-5.6-terra / e-none | 0.01 | 0.15 | 0.15 | 0.30 |
| mistral-medium-latest / t0.0 | 0.15 | 0.15 | 0.16 | 0.20 |
| mistral-medium-latest / t1.0 | 0.18 | 0.15 | 0.17 | 0.24 |
| mistral-small-latest / t0.0 | 0.00 | 0.00 | 0.07 | 0.07 |
| mistral-small-latest / t1.0 | 0.03 | 0.05 | 0.08 | 0.18 |

## variance — made hand vs draw at the same 50% / price

made call-rate > draw call-rate = the model shies from the swingy version.

| cell | made | draw | made − draw |
|---|---:|---:|---:|
| claude-haiku-4-5 / t0.0 | 100% | 100% | +0pt |
| claude-haiku-4-5 / t1.0 | 100% | 100% | +0pt |
| claude-haiku-4-5 / think1024 | 100% | 100% | +0pt |
| claude-opus-4-8 / default | 100% | 100% | +0pt |
| claude-opus-4-8 / think-low | 100% | 100% | +0pt |
| claude-sonnet-5 / default | 65% | 100% | -35pt |
| claude-sonnet-5 / think-low | 100% | 100% | +0pt |
| gpt-5.6-luna / e-low | 100% | 100% | +0pt |
| gpt-5.6-luna / e-none | 100% | 100% | +0pt |
| gpt-5.6-terra / e-low | 80% | 100% | -20pt |
| gpt-5.6-terra / e-none | 0% | 60% | -60pt |
| mistral-medium-latest / t0.0 | 35% | 30% | +5pt |
| mistral-medium-latest / t1.0 | 70% | 45% | +25pt |
| mistral-small-latest / t0.0 | 100% | 100% | +0pt |
| mistral-small-latest / t1.0 | 100% | 100% | +0pt |
