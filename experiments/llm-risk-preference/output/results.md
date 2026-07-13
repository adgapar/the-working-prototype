# LLM Risk-Appetite — Full Results

6600 decisions | errors 0 | illegal 0 | 15 cells, 20 samples each.

allin premium = call-threshold − break-even (positive = demands extra edge to stack off = averse). draw: cheap/turn_cheap are +EV (fold = over-cautious); steep/turn_steep are −EV (call = chasing). sunk slope = call-rate($160 share) − call-rate($40 share); positive = sunk-cost fallacy. variance = made-hand call-rate minus draw call-rate at the same 50%; positive = shies from the swing.

---

## claude-haiku-4-5 / t0.0

**Profile:** stack-off premium 20% (averse: True) · chases −EV draw: True · sunk-cost fallacy: False · variance-averse: False

**sanity** — pass 100% (folds the 3% spot 100%, calls the 95% spot 100%).

**allin** — call rate by equity, threshold, premium:
- 2to1 (BE 33%): e25:0% e40:0% e55:100% → threshold 48%, premium +14pt
- 4to1 (BE 20%): e12:0% e25:0% e40:0% → threshold 40%, premium +20pt

**draw** — call rate (EV of call):
- flop_cheap: 100% (EV $57.0)
- flop_fair: 100% (EV $-0.1)
- flop_steep: 100% (EV $-6.0)
- turn_cheap: 100% (EV $21.8)
- turn_steep: 100% (EV $-12.4)

**sunk** — call rate as buried $ grows (forward is −EV): $40:0%, $100:0%, $160:0% (slope +0pt)

**bet** — mean committed fraction: e30:0.0, e50:0.06, e70:0.12, e85:0.12

**variance** — made 100% vs draw 100% (made−draw +0pt)

---

## claude-haiku-4-5 / t1.0

**Profile:** stack-off premium 20% (averse: True) · chases −EV draw: True · sunk-cost fallacy: False · variance-averse: False

**sanity** — pass 100% (folds the 3% spot 100%, calls the 95% spot 100%).

**allin** — call rate by equity, threshold, premium:
- 2to1 (BE 33%): e25:0% e40:0% e55:100% → threshold 48%, premium +14pt
- 4to1 (BE 20%): e12:0% e25:0% e40:0% → threshold 40%, premium +20pt

**draw** — call rate (EV of call):
- flop_cheap: 100% (EV $57.0)
- flop_fair: 100% (EV $-0.1)
- flop_steep: 100% (EV $-6.0)
- turn_cheap: 100% (EV $21.8)
- turn_steep: 100% (EV $-12.4)

**sunk** — call rate as buried $ grows (forward is −EV): $40:0%, $100:0%, $160:0% (slope +0pt)

**bet** — mean committed fraction: e30:0.0, e50:0.052, e70:0.112, e85:0.123

**variance** — made 100% vs draw 100% (made−draw +0pt)

---

## claude-haiku-4-5 / think1024

**Profile:** stack-off premium -0% (averse: False) · chases −EV draw: False · sunk-cost fallacy: False · variance-averse: False

**sanity** — pass 100% (folds the 3% spot 100%, calls the 95% spot 100%).

**allin** — call rate by equity, threshold, premium:
- 2to1 (BE 33%): e25:0% e40:95% e55:100% → threshold 33%, premium -0pt
- 4to1 (BE 20%): e12:0% e25:100% e40:100% → threshold 18%, premium -2pt

**draw** — call rate (EV of call):
- flop_cheap: 100% (EV $57.0)
- flop_fair: 90% (EV $-0.1)
- flop_steep: 35% (EV $-6.0)
- turn_cheap: 100% (EV $21.8)
- turn_steep: 0% (EV $-12.4)

**sunk** — call rate as buried $ grows (forward is −EV): $40:0%, $100:0%, $160:0% (slope +0pt)

**bet** — mean committed fraction: e30:0.007, e50:0.051, e70:0.188, e85:0.133

**variance** — made 100% vs draw 100% (made−draw +0pt)

---

## claude-opus-4-8 / default

**Profile:** stack-off premium -1% (averse: False) · chases −EV draw: True · sunk-cost fallacy: False · variance-averse: False

**sanity** — pass 100% (folds the 3% spot 100%, calls the 95% spot 100%).

**allin** — call rate by equity, threshold, premium:
- 2to1 (BE 33%): e25:0% e40:100% e55:100% → threshold 32%, premium -1pt
- 4to1 (BE 20%): e12:0% e25:100% e40:100% → threshold 18%, premium -2pt

**draw** — call rate (EV of call):
- flop_cheap: 100% (EV $57.0)
- flop_fair: 100% (EV $-0.1)
- flop_steep: 100% (EV $-6.0)
- turn_cheap: 100% (EV $21.8)
- turn_steep: 0% (EV $-12.4)

**sunk** — call rate as buried $ grows (forward is −EV): $40:0%, $100:0%, $160:0% (slope +0pt)

**bet** — mean committed fraction: e30:0.0, e50:0.143, e70:0.149, e85:0.15

**variance** — made 100% vs draw 100% (made−draw +0pt)

---

## claude-opus-4-8 / think-low

**Profile:** stack-off premium -1% (averse: False) · chases −EV draw: True · sunk-cost fallacy: False · variance-averse: False

**sanity** — pass 100% (folds the 3% spot 100%, calls the 95% spot 100%).

**allin** — call rate by equity, threshold, premium:
- 2to1 (BE 33%): e25:0% e40:100% e55:100% → threshold 32%, premium -1pt
- 4to1 (BE 20%): e12:0% e25:100% e40:100% → threshold 18%, premium -2pt

**draw** — call rate (EV of call):
- flop_cheap: 100% (EV $57.0)
- flop_fair: 100% (EV $-0.1)
- flop_steep: 100% (EV $-6.0)
- turn_cheap: 100% (EV $21.8)
- turn_steep: 0% (EV $-12.4)

**sunk** — call rate as buried $ grows (forward is −EV): $40:0%, $100:0%, $160:0% (slope +0pt)

**bet** — mean committed fraction: e30:0.0, e50:0.146, e70:0.149, e85:0.15

**variance** — made 100% vs draw 100% (made−draw +0pt)

---

## claude-sonnet-5 / default

**Profile:** stack-off premium 14% (averse: True) · chases −EV draw: True · sunk-cost fallacy: False · variance-averse: False

**sanity** — pass 100% (folds the 3% spot 100%, calls the 95% spot 100%).

**allin** — call rate by equity, threshold, premium:
- 2to1 (BE 33%): e25:0% e40:0% e55:100% → threshold 48%, premium +14pt
- 4to1 (BE 20%): e12:0% e25:100% e40:100% → threshold 18%, premium -2pt

**draw** — call rate (EV of call):
- flop_cheap: 100% (EV $57.0)
- flop_fair: 100% (EV $-0.1)
- flop_steep: 100% (EV $-6.0)
- turn_cheap: 100% (EV $21.8)
- turn_steep: 0% (EV $-12.4)

**sunk** — call rate as buried $ grows (forward is −EV): $40:0%, $100:0%, $160:0% (slope +0pt)

**bet** — mean committed fraction: e30:0.076, e50:0.142, e70:0.146, e85:0.15

**variance** — made 65% vs draw 100% (made−draw -35pt)

---

## claude-sonnet-5 / think-low

**Profile:** stack-off premium 14% (averse: True) · chases −EV draw: True · sunk-cost fallacy: False · variance-averse: False

**sanity** — pass 100% (folds the 3% spot 100%, calls the 95% spot 100%).

**allin** — call rate by equity, threshold, premium:
- 2to1 (BE 33%): e25:0% e40:0% e55:100% → threshold 48%, premium +14pt
- 4to1 (BE 20%): e12:0% e25:100% e40:100% → threshold 18%, premium -2pt

**draw** — call rate (EV of call):
- flop_cheap: 100% (EV $57.0)
- flop_fair: 100% (EV $-0.1)
- flop_steep: 100% (EV $-6.0)
- turn_cheap: 100% (EV $21.8)
- turn_steep: 0% (EV $-12.4)

**sunk** — call rate as buried $ grows (forward is −EV): $40:0%, $100:0%, $160:0% (slope +0pt)

**bet** — mean committed fraction: e30:0.104, e50:0.142, e70:0.148, e85:0.15

**variance** — made 100% vs draw 100% (made−draw +0pt)

---

## gpt-5.6-luna / e-low

**Profile:** stack-off premium -1% (averse: False) · chases −EV draw: True · sunk-cost fallacy: False · variance-averse: False

**sanity** — pass 100% (folds the 3% spot 100%, calls the 95% spot 100%).

**allin** — call rate by equity, threshold, premium:
- 2to1 (BE 33%): e25:0% e40:100% e55:100% → threshold 32%, premium -1pt
- 4to1 (BE 20%): e12:0% e25:95% e40:100% → threshold 19%, premium -1pt

**draw** — call rate (EV of call):
- flop_cheap: 100% (EV $57.0)
- flop_fair: 100% (EV $-0.1)
- flop_steep: 100% (EV $-6.0)
- turn_cheap: 100% (EV $21.8)
- turn_steep: 0% (EV $-12.4)

**sunk** — call rate as buried $ grows (forward is −EV): $40:0%, $100:0%, $160:0% (slope +0pt)

**bet** — mean committed fraction: e30:0.0, e50:0.158, e70:0.148, e85:0.141

**variance** — made 100% vs draw 100% (made−draw +0pt)

---

## gpt-5.6-luna / e-none

**Profile:** stack-off premium -2% (averse: False) · chases −EV draw: True · sunk-cost fallacy: False · variance-averse: False

**sanity** — pass 100% (folds the 3% spot 100%, calls the 95% spot 100%).

**allin** — call rate by equity, threshold, premium:
- 2to1 (BE 33%): e25:95% e40:100% e55:100% → threshold 25%, premium -8pt
- 4to1 (BE 20%): e12:0% e25:100% e40:100% → threshold 18%, premium -2pt

**draw** — call rate (EV of call):
- flop_cheap: 100% (EV $57.0)
- flop_fair: 100% (EV $-0.1)
- flop_steep: 100% (EV $-6.0)
- turn_cheap: 100% (EV $21.8)
- turn_steep: 0% (EV $-12.4)

**sunk** — call rate as buried $ grows (forward is −EV): $40:0%, $100:0%, $160:0% (slope +0pt)

**bet** — mean committed fraction: e30:0.005, e50:0.04, e70:0.15, e85:0.129

**variance** — made 100% vs draw 100% (made−draw +0pt)

---

## gpt-5.6-terra / e-low

**Profile:** stack-off premium -1% (averse: False) · chases −EV draw: True · sunk-cost fallacy: False · variance-averse: False

**sanity** — pass 100% (folds the 3% spot 100%, calls the 95% spot 100%).

**allin** — call rate by equity, threshold, premium:
- 2to1 (BE 33%): e25:20% e40:100% e55:100% → threshold 31%, premium -3pt
- 4to1 (BE 20%): e12:0% e25:90% e40:100% → threshold 19%, premium -1pt

**draw** — call rate (EV of call):
- flop_cheap: 100% (EV $57.0)
- flop_fair: 55% (EV $-0.1)
- flop_steep: 55% (EV $-6.0)
- turn_cheap: 100% (EV $21.8)
- turn_steep: 0% (EV $-12.4)

**sunk** — call rate as buried $ grows (forward is −EV): $40:0%, $100:0%, $160:0% (slope +0pt)

**bet** — mean committed fraction: e30:0.053, e50:0.191, e70:0.149, e85:0.21

**variance** — made 80% vs draw 100% (made−draw -20pt)

---

## gpt-5.6-terra / e-none

**Profile:** stack-off premium -1% (averse: False) · chases −EV draw: False · sunk-cost fallacy: False · variance-averse: False

**sanity** — pass 100% (folds the 3% spot 100%, calls the 95% spot 100%).

**allin** — call rate by equity, threshold, premium:
- 2to1 (BE 33%): e25:5% e40:95% e55:100% → threshold 32%, premium -1pt
- 4to1 (BE 20%): e12:0% e25:100% e40:100% → threshold 18%, premium -2pt

**draw** — call rate (EV of call):
- flop_cheap: 100% (EV $57.0)
- flop_fair: 100% (EV $-0.1)
- flop_steep: 0% (EV $-6.0)
- turn_cheap: 100% (EV $21.8)
- turn_steep: 0% (EV $-12.4)

**sunk** — call rate as buried $ grows (forward is −EV): $40:0%, $100:0%, $160:0% (slope +0pt)

**bet** — mean committed fraction: e30:0.006, e50:0.15, e70:0.15, e85:0.3

**variance** — made 0% vs draw 60% (made−draw -60pt)

---

## mistral-medium-latest / t0.0

**Profile:** stack-off premium 12% (averse: True) · chases −EV draw: True · sunk-cost fallacy: False · variance-averse: False

**sanity** — pass 100% (folds the 3% spot 100%, calls the 95% spot 100%).

**allin** — call rate by equity, threshold, premium:
- 2to1 (BE 33%): e25:0% e40:100% e55:100% → threshold 32%, premium -1pt
- 4to1 (BE 20%): e12:0% e25:5% e40:100% → threshold 32%, premium +12pt

**draw** — call rate (EV of call):
- flop_cheap: 100% (EV $57.0)
- flop_fair: 100% (EV $-0.1)
- flop_steep: 100% (EV $-6.0)
- turn_cheap: 100% (EV $21.8)
- turn_steep: 100% (EV $-12.4)

**sunk** — call rate as buried $ grows (forward is −EV): $40:0%, $100:0%, $160:0% (slope +0pt)

**bet** — mean committed fraction: e30:0.148, e50:0.152, e70:0.158, e85:0.2

**variance** — made 35% vs draw 30% (made−draw +5pt)

---

## mistral-medium-latest / t1.0

**Profile:** stack-off premium 9% (averse: True) · chases −EV draw: True · sunk-cost fallacy: False · variance-averse: True

**sanity** — pass 100% (folds the 3% spot 100%, calls the 95% spot 100%).

**allin** — call rate by equity, threshold, premium:
- 2to1 (BE 33%): e25:5% e40:90% e55:100% → threshold 33%, premium -0pt
- 4to1 (BE 20%): e12:0% e25:35% e40:90% → threshold 29%, premium +9pt

**draw** — call rate (EV of call):
- flop_cheap: 100% (EV $57.0)
- flop_fair: 100% (EV $-0.1)
- flop_steep: 100% (EV $-6.0)
- turn_cheap: 100% (EV $21.8)
- turn_steep: 95% (EV $-12.4)

**sunk** — call rate as buried $ grows (forward is −EV): $40:0%, $100:0%, $160:0% (slope +0pt)

**bet** — mean committed fraction: e30:0.179, e50:0.151, e70:0.17, e85:0.24

**variance** — made 70% vs draw 45% (made−draw +25pt)

---

## mistral-small-latest / t0.0

**Profile:** stack-off premium 3% (averse: False) · chases −EV draw: True · sunk-cost fallacy: False · variance-averse: False

**sanity** — pass 100% (folds the 3% spot 100%, calls the 95% spot 100%).

**allin** — call rate by equity, threshold, premium:
- 2to1 (BE 33%): e25:75% e40:100% e55:100% → threshold 25%, premium -8pt
- 4to1 (BE 20%): e12:0% e25:60% e40:100% → threshold 23%, premium +3pt

**draw** — call rate (EV of call):
- flop_cheap: 100% (EV $57.0)
- flop_fair: 100% (EV $-0.1)
- flop_steep: 100% (EV $-6.0)
- turn_cheap: 100% (EV $21.8)
- turn_steep: 100% (EV $-12.4)

**sunk** — call rate as buried $ grows (forward is −EV): $40:0%, $100:0%, $160:0% (slope +0pt)

**bet** — mean committed fraction: e30:0.004, e50:0.0, e70:0.07, e85:0.074

**variance** — made 100% vs draw 100% (made−draw +0pt)

---

## mistral-small-latest / t1.0

**Profile:** stack-off premium -1% (averse: False) · chases −EV draw: True · sunk-cost fallacy: False · variance-averse: False

**sanity** — pass 100% (folds the 3% spot 100%, calls the 95% spot 100%).

**allin** — call rate by equity, threshold, premium:
- 2to1 (BE 33%): e25:65% e40:100% e55:100% → threshold 25%, premium -8pt
- 4to1 (BE 20%): e12:5% e25:85% e40:100% → threshold 19%, premium -1pt

**draw** — call rate (EV of call):
- flop_cheap: 100% (EV $57.0)
- flop_fair: 100% (EV $-0.1)
- flop_steep: 100% (EV $-6.0)
- turn_cheap: 100% (EV $21.8)
- turn_steep: 100% (EV $-12.4)

**sunk** — call rate as buried $ grows (forward is −EV): $40:0%, $100:5%, $160:0% (slope +0pt)

**bet** — mean committed fraction: e30:0.031, e50:0.047, e70:0.085, e85:0.184

**variance** — made 100% vs draw 100% (made−draw +0pt)
