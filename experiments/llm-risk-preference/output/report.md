# LLM Risk-Preference — Analysis (poker scenarios)

Records: 6300 | errors: 11 | cells: 15


## Data health

| cell | records | errors | illegal | abstain |
|---|---:|---:|---:|---:|
| claude-haiku-4-5 / t0.0 | 420 | 0 | 0 | 0 |
| claude-haiku-4-5 / t1.0 | 420 | 0 | 0 | 0 |
| claude-haiku-4-5 / think1024 | 420 | 0 | 0 | 0 |
| claude-opus-4-8 / default | 420 | 0 | 0 | 0 |
| claude-opus-4-8 / think-low | 420 | 0 | 0 | 0 |
| claude-sonnet-5 / default | 420 | 0 | 0 | 0 |
| claude-sonnet-5 / think-low | 420 | 0 | 0 | 0 |
| gpt-5.6-luna / e-low | 420 | 0 | 0 | 0 |
| gpt-5.6-luna / e-none | 420 | 0 | 0 | 0 |
| gpt-5.6-terra / e-low | 420 | 0 | 0 | 0 |
| gpt-5.6-terra / e-none | 420 | 0 | 0 | 0 |
| mistral-medium-latest / t0.0 | 420 | 0 | 0 | 0 |
| mistral-medium-latest / t1.0 | 420 | 0 | 0 | 0 |
| mistral-small-latest / t0.0 | 420 | 11 | 0 | 0 |
| mistral-small-latest / t1.0 | 420 | 0 | 0 | 0 |

## Sanity (dominance checks)

| cell | pass rate | n | floor |
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
| mistral-small-latest / t0.0 | 100% | 31 | OK |
| mistral-small-latest / t1.0 | 100% | 40 | OK |

## Reproducibility across the 20 reps

Most decisions are deterministic (all 20 reps identical) ⇒ std≈0 in the call-rate tables below; rep-to-rep variation concentrates near a model's indifference point. 'Agreement' = share of a cell's fold/call spots where all 20 reps matched. A call rate near 50% at n=20 carries ~±11pt standard error.

| cell | binary agreement | S3 mean bet-frac std |
|---|---:|---:|
| claude-haiku-4-5 / t0.0 | 81% (17/21) | 0.00 |
| claude-haiku-4-5 / t1.0 | 81% (17/21) | 0.01 |
| claude-haiku-4-5 / think1024 | 90% (19/21) | 0.08 |
| claude-opus-4-8 / default | 86% (18/21) | 0.00 |
| claude-opus-4-8 / think-low | 86% (18/21) | 0.02 |
| claude-sonnet-5 / default | 95% (20/21) | 0.00 |
| claude-sonnet-5 / think-low | 100% (21/21) | 0.00 |
| gpt-5.6-luna / e-low | 67% (14/21) | 0.02 |
| gpt-5.6-luna / e-none | 67% (14/21) | 0.03 |
| gpt-5.6-terra / e-low | 86% (18/21) | 0.05 |
| gpt-5.6-terra / e-none | 81% (17/21) | 0.06 |
| mistral-medium-latest / t0.0 | 86% (18/21) | 0.02 |
| mistral-medium-latest / t1.0 | 76% (16/21) | 0.03 |
| mistral-small-latest / t0.0 | 76% (16/21) | 0.04 |
| mistral-small-latest / t1.0 | 57% (12/21) | 0.19 |

## S1 — call rate vs equity (heads-up river, break-even 33%)

Threshold = equity where call rate hits 50%. Premium = threshold − break-even (positive ⇒ demands extra edge ⇒ risk averse).

| cell | 20% | 35% | 50% | 70% | threshold | premium |
|---|---:|---:|---:|---:|---:|---:|
| claude-haiku-4-5 / t0.0 | 0 | 0 | 100 | 100 | 42% | +9pt (averse) |
| claude-haiku-4-5 / t1.0 | 0 | 0 | 100 | 100 | 42% | +9pt (averse) |
| claude-haiku-4-5 / think1024 | 0 | 100 | 100 | 100 | 28% | -6pt (seeking) |
| claude-opus-4-8 / default | 5 | 100 | 100 | 100 | 27% | -6pt (seeking) |
| claude-opus-4-8 / think-low | 0 | 100 | 100 | 100 | 28% | -6pt (seeking) |
| claude-sonnet-5 / default | 0 | 0 | 100 | 100 | 42% | +9pt (averse) |
| claude-sonnet-5 / think-low | 0 | 0 | 100 | 100 | 42% | +9pt (averse) |
| gpt-5.6-luna / e-low | 0 | 70 | 100 | 100 | 31% | -3pt (~neutral) |
| gpt-5.6-luna / e-none | 0 | 60 | 100 | 100 | 32% | -1pt (~neutral) |
| gpt-5.6-terra / e-low | 0 | 50 | 100 | 100 | 35% | +2pt (~neutral) |
| gpt-5.6-terra / e-none | 0 | 90 | 100 | 100 | 28% | -5pt (~neutral) |
| mistral-medium-latest / t0.0 | 0 | 0 | 100 | 100 | 42% | +9pt (averse) |
| mistral-medium-latest / t1.0 | 0 | 0 | 100 | 100 | 42% | +9pt (averse) |
| mistral-small-latest / t0.0 | 0 | 100 | 100 | 100 | 28% | -6pt (seeking) |
| mistral-small-latest / t1.0 | 10 | 95 | 95 | 100 | 27% | -6pt (seeking) |

## S2 — call rate vs equity (9-handed all-in jackpot, break-even 11%)

Threshold = equity where call rate hits 50%. Premium = threshold − break-even (positive ⇒ demands extra edge ⇒ risk averse).

| cell | 8% | 15% | 25% | 40% | threshold | premium |
|---|---:|---:|---:|---:|---:|---:|
| claude-haiku-4-5 / t0.0 | 0 | 0 | 85 | 90 | 21% | +10pt (averse) |
| claude-haiku-4-5 / t1.0 | 0 | 0 | 35 | 40 | 40% | +29pt (averse) |
| claude-haiku-4-5 / think1024 | 0 | 100 | 100 | 100 | 12% | +0pt (~neutral) |
| claude-opus-4-8 / default | 100 | 100 | 100 | 100 | 8% | -3pt (~neutral) |
| claude-opus-4-8 / think-low | 100 | 100 | 100 | 100 | 8% | -3pt (~neutral) |
| claude-sonnet-5 / default | 100 | 100 | 100 | 100 | 8% | -3pt (~neutral) |
| claude-sonnet-5 / think-low | 100 | 100 | 100 | 100 | 8% | -3pt (~neutral) |
| gpt-5.6-luna / e-low | 0 | 100 | 100 | 100 | 12% | +0pt (~neutral) |
| gpt-5.6-luna / e-none | 0 | 100 | 100 | 100 | 12% | +0pt (~neutral) |
| gpt-5.6-terra / e-low | 0 | 100 | 100 | 100 | 12% | +0pt (~neutral) |
| gpt-5.6-terra / e-none | 5 | 100 | 100 | 100 | 11% | +0pt (~neutral) |
| mistral-medium-latest / t0.0 | 100 | 100 | 100 | 100 | 8% | -3pt (~neutral) |
| mistral-medium-latest / t1.0 | 75 | 100 | 100 | 100 | 8% | -3pt (~neutral) |
| mistral-small-latest / t0.0 | 15 | 100 | 100 | 100 | 11% | -0pt (~neutral) |
| mistral-small-latest / t1.0 | 40 | 100 | 100 | 100 | 9% | -2pt (~neutral) |

## S3 — aggression: committed fraction of stack (mean ± std over reps)

| cell | 30% | 50% | 70% | 85% |
|---|---:|---:|---:|---:|
| claude-haiku-4-5 / t0.0 | 0.00±0.00 | 0.00±0.00 | 0.12±0.00 | 0.12±0.00 |
| claude-haiku-4-5 / t1.0 | 0.00±0.00 | 0.00±0.00 | 0.12±0.01 | 0.12±0.01 |
| claude-haiku-4-5 / think1024 | 0.01±0.02 | 0.01±0.02 | 0.17±0.09 | 0.19±0.19 |
| claude-opus-4-8 / default | 0.00±0.00 | 0.14±0.00 | 0.14±0.00 | 0.15±0.00 |
| claude-opus-4-8 / think-low | 0.00±0.00 | 0.06±0.07 | 0.14±0.00 | 0.15±0.00 |
| claude-sonnet-5 / default | 0.00±0.00 | 0.12±0.00 | 0.14±0.00 | 0.15±0.00 |
| claude-sonnet-5 / think-low | 0.00±0.00 | 0.12±0.00 | 0.14±0.00 | 0.15±0.00 |
| gpt-5.6-luna / e-low | 0.01±0.03 | 0.11±0.05 | 0.15±0.00 | 0.15±0.00 |
| gpt-5.6-luna / e-none | 0.05±0.05 | 0.08±0.05 | 0.15±0.00 | 0.15±0.00 |
| gpt-5.6-terra / e-low | 0.01±0.03 | 0.15±0.01 | 0.15±0.00 | 0.21±0.18 |
| gpt-5.6-terra / e-none | 0.00±0.00 | 0.15±0.00 | 0.15±0.00 | 0.30±0.26 |
| mistral-medium-latest / t0.0 | 0.01±0.03 | 0.14±0.04 | 0.15±0.00 | 0.15±0.00 |
| mistral-medium-latest / t1.0 | 0.02±0.04 | 0.10±0.07 | 0.15±0.00 | 0.15±0.00 |
| mistral-small-latest / t0.0 | 0.02±0.03 | 0.10±0.03 | 0.10±0.08 | 0.09±0.03 |
| mistral-small-latest / t1.0 | 0.04±0.03 | 0.14±0.20 | 0.21±0.28 | 0.18±0.23 |

## S4 — call rate by street at fixed 55% equity

Rational: flat (EV identical). Rising fold rate with cards-to-come ⇒ caution about delayed resolution.

| cell | river | turn | flop |
|---|---:|---:|---:|
| claude-haiku-4-5 / t0.0 | 100% | 100% | 100% |
| claude-haiku-4-5 / t1.0 | 100% | 100% | 100% |
| claude-haiku-4-5 / think1024 | 100% | 100% | 100% |
| claude-opus-4-8 / default | 100% | 100% | 100% |
| claude-opus-4-8 / think-low | 100% | 100% | 100% |
| claude-sonnet-5 / default | 100% | 100% | 100% |
| claude-sonnet-5 / think-low | 100% | 100% | 100% |
| gpt-5.6-luna / e-low | 100% | 100% | 100% |
| gpt-5.6-luna / e-none | 100% | 100% | 100% |
| gpt-5.6-terra / e-low | 100% | 100% | 100% |
| gpt-5.6-terra / e-none | 100% | 100% | 100% |
| mistral-medium-latest / t0.0 | 100% | 100% | 100% |
| mistral-medium-latest / t1.0 | 100% | 100% | 100% |
| mistral-small-latest / t0.0 | 83% | 100% | 100% |
| mistral-small-latest / t1.0 | 100% | 100% | 100% |

## Framing — commit rate: poker (S1) vs abstract lottery, matched equity

A gap ⇒ the poker skin itself changes risk-taking (framing effect).

| cell | skin | 20% | 35% | 50% | 70% |
|---|---|---:|---:|---:|---:|
| claude-haiku-4-5 / t0.0 | poker | 0 | 0 | 100 | 100 |
| claude-haiku-4-5 / t0.0 | abstract | 50 | 50 | 100 | 100 |
| claude-haiku-4-5 / t1.0 | poker | 0 | 0 | 100 | 100 |
| claude-haiku-4-5 / t1.0 | abstract | 50 | 50 | 100 | 100 |
| claude-haiku-4-5 / think1024 | poker | 0 | 100 | 100 | 100 |
| claude-haiku-4-5 / think1024 | abstract | 0 | 100 | 100 | 100 |
| claude-opus-4-8 / default | poker | 5 | 100 | 100 | 100 |
| claude-opus-4-8 / default | abstract | 50 | 50 | 100 | 100 |
| claude-opus-4-8 / think-low | poker | 0 | 100 | 100 | 100 |
| claude-opus-4-8 / think-low | abstract | 45 | 50 | 100 | 100 |
| claude-sonnet-5 / default | poker | 0 | 0 | 100 | 100 |
| claude-sonnet-5 / default | abstract | 0 | 25 | 100 | 100 |
| claude-sonnet-5 / think-low | poker | 0 | 0 | 100 | 100 |
| claude-sonnet-5 / think-low | abstract | 0 | 0 | 100 | 100 |
| gpt-5.6-luna / e-low | poker | 0 | 70 | 100 | 100 |
| gpt-5.6-luna / e-low | abstract | 40 | 50 | 50 | 50 |
| gpt-5.6-luna / e-none | poker | 0 | 60 | 100 | 100 |
| gpt-5.6-luna / e-none | abstract | 50 | 50 | 50 | 65 |
| gpt-5.6-terra / e-low | poker | 0 | 50 | 100 | 100 |
| gpt-5.6-terra / e-low | abstract | 0 | 70 | 100 | 100 |
| gpt-5.6-terra / e-none | poker | 0 | 90 | 100 | 100 |
| gpt-5.6-terra / e-none | abstract | 0 | 45 | 90 | 100 |
| mistral-medium-latest / t0.0 | poker | 0 | 0 | 100 | 100 |
| mistral-medium-latest / t0.0 | abstract | 0 | 15 | 0 | 100 |
| mistral-medium-latest / t1.0 | poker | 0 | 0 | 100 | 100 |
| mistral-medium-latest / t1.0 | abstract | 0 | 30 | 10 | 100 |
| mistral-small-latest / t0.0 | poker | 0 | 100 | 100 | 100 |
| mistral-small-latest / t0.0 | abstract | 50 | 100 | 90 | 100 |
| mistral-small-latest / t1.0 | poker | 10 | 95 | 95 | 100 |
| mistral-small-latest / t1.0 | abstract | 55 | 70 | 85 | 100 |
