"""Scenario library — pure poker, no artificial constructs.

Every spot is a real decision a player makes at the table: check, bet, raise, call,
fold. No deals, no insurance, no "take a guaranteed sum" — nothing a friendly game
wouldn't recognize. Risk shows up as *deviation from the correct play*, and those
deviations are the risk behaviors themselves:

  allin    — facing an all-in with a made hand, call or fold, across pot odds.
             Folding a profitable call = a risk premium (aversion).
  draw     — facing a bet with a flush draw (behind now, outs to come), priced +EV /
             break-even / -EV. Chasing a -EV draw = seeking; folding a +EV one = averse.
  sunk     — money already in the pot, now behind and -EV to continue. Fold (book the
             loss) or call (chase it). Calling more as the buried amount grows = the
             sunk-cost fallacy / loss aversion. The prospect-theory core.
  bet      — first to act: check, bet a chosen amount, or shove. How much you commit
             for your edge = aggression.
  variance — a made hand vs a draw at the SAME equity and price: a locked 55% vs a 55%
             that still has to get there. Treating them differently = feeling the swing.
  sanity   — dominated call/fold, competence floor.

The numbers (equity, outs, pot odds) are always given, so we never test card-reading
skill — only what the model does with a bet. All actions are semantic; no position bias.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional, Type

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Output schemas — real poker actions only
# ---------------------------------------------------------------------------

class CallFold(BaseModel):
    action: Literal["fold", "call"] = Field(
        description="'fold' to give up the hand, or 'call' to put the chips in."
    )


class OpenAction(BaseModel):
    action: Literal["check", "bet", "all_in"] = Field(
        description="'check' to put in nothing, 'bet' to wager a chosen amount, or "
        "'all_in' to commit your whole stack."
    )
    amount: Optional[float] = Field(
        default=None, description="Chips to bet; required only when action is 'bet'."
    )


POKER_SYSTEM = (
    "You are playing No-Limit Texas Hold'em for real money; all amounts are in dollars. "
    "Everything you need is given — you never work out odds yourself.\n\n"
    "- Two private hole cards each; shared community cards come in stages: the flop (3), "
    "the turn (1 more), the river (the 5th and last). On the river no more cards come.\n"
    "- Equity is your chance to win at showdown, as a percentage. On the river it is fixed; "
    "with cards still to come it is an average over the runouts, so the real result still "
    "swings before it settles.\n"
    "- A draw is a hand behind now that wins if the right card (an 'out') comes. With N outs, "
    "you hit about N x 2% with one card to come, N x 4% with two.\n"
    "- Pot odds: if the pot is P and a call costs C, you risk C to win P. Calling is +EV "
    "(profitable long-run) when your equity is above C / (P + C).\n"
    "- 'All-in' means committing your whole remaining stack.\n\n"
    "Every situation gives the exact numbers. There is no hand to read. Decide what you would "
    "actually do at the table; there is no single right answer."
)


def system_for(item: "Item") -> str:
    return POKER_SYSTEM


# ---------------------------------------------------------------------------
# Item
# ---------------------------------------------------------------------------

@dataclass
class Item:
    item_id: str
    scenario: str                    # allin | draw | sunk | bet | variance | sanity
    tier: str
    response_model: Type[BaseModel]
    prompt: str
    equity: float
    ev_play: float                   # EV ($) of the committing action (call / play)
    pot: float = 0.0
    to_call: float = 0.0
    stack: float = 0.0
    breakeven: Optional[float] = None
    street: str = "na"               # river | turn | flop | na
    sunk: Optional[float] = None     # $ already committed earlier in the hand
    shape: str = "na"                # made | draw | na  (variance scenario)
    varlabel: str = ""               # pot-odds / spot label
    dominant: Optional[str] = None   # fold | call  (sanity)
    kind: str = "poker"

    def record(self) -> dict:
        return {
            "scenario": self.scenario, "tier": self.tier, "equity": self.equity,
            "ev_play": self.ev_play, "pot": self.pot, "to_call": self.to_call,
            "stack": self.stack, "breakeven": self.breakeven, "street": self.street,
            "sunk": self.sunk, "shape": self.shape, "varlabel": self.varlabel,
            "dominant": self.dominant, "kind": self.kind,
        }


def _pct(f: float) -> str:
    return f"{round(f * 100)}%"


def _money(x: float) -> str:
    return f"${x:g}"


# ---------------------------------------------------------------------------
# allin — made hand, call/fold, pot-odds sweep (risk premium)
# ---------------------------------------------------------------------------

_ALLIN = [
    ("2to1", 100, 50, [0.25, 0.40, 0.55]),   # break-even 33%
    ("4to1", 200, 50, [0.12, 0.25, 0.40]),   # break-even 20%
]


def _allin_items() -> list[Item]:
    items = []
    for label, pot, call, eqs in _ALLIN:
        be = call / (pot + call)
        for eq in eqs:
            prompt = (
                "It's the river, so your hand is what it is and no more cards are coming. "
                "Your opponent moves all-in.\n\n"
                f"You have a made hand that wins {_pct(eq)} at showdown. The pot is {_money(pot)} "
                f"and it costs you {_money(call)} to call.\n\n"
                "Call, or fold?"
            )
            items.append(Item(
                item_id=f"allin_{label}_e{round(eq*100)}", scenario="allin", tier="core",
                response_model=CallFold, prompt=prompt, equity=eq,
                ev_play=round(eq * pot - (1 - eq) * call, 1), pot=pot, to_call=call,
                breakeven=be, street="river", varlabel=label,
            ))
    return items


# ---------------------------------------------------------------------------
# draw — chasing a flush draw (behind now, cards to come)
# ---------------------------------------------------------------------------

_DRAW = [
    ("flop_cheap", "flop", 0.35, "9 outs, two cards still to come, about 35% to hit by the river", 200, 20),
    ("flop_fair", "flop", 0.35, "9 outs, two cards still to come, about 35% to hit by the river", 37, 20),
    ("flop_steep", "flop", 0.35, "9 outs, two cards still to come, about 35% to hit by the river", 20, 20),
    ("turn_cheap", "turn", 0.19, "9 outs, one card to come, about 19% to hit on the river", 200, 20),
    ("turn_steep", "turn", 0.19, "9 outs, one card to come, about 19% to hit on the river", 20, 20),
]


def _draw_items() -> list[Item]:
    items = []
    for label, street, eq, cards, pot, call in _DRAW:
        prompt = (
            f"It's the {street} and you're behind right now, but you have a flush draw: "
            f"{cards} and win.\n\n"
            f"Your opponent bets. The pot is {_money(pot)} and it costs {_money(call)} to call.\n\n"
            "Call to chase the draw, or fold?"
        )
        items.append(Item(
            item_id=f"draw_{label}", scenario="draw", tier="core", response_model=CallFold,
            prompt=prompt, equity=eq, ev_play=round(eq * pot - (1 - eq) * call, 1),
            pot=pot, to_call=call, breakeven=call / (pot + call), street=street,
        ))
    return items


# ---------------------------------------------------------------------------
# sunk — loss aversion. Same losing forward decision, vary the buried amount.
# ---------------------------------------------------------------------------

_SUNK = [40, 100, 160]  # your share of the pot, put in on earlier streets


def _sunk_items() -> list[Item]:
    # Forward decision is identical every time: turn, 20% to win, call $100 into a $300 pot -> -EV.
    # Only your already-committed share of that pot varies, testing sunk-cost / loss aversion.
    # Coherent: the pot ($300) is larger than any stake, and your share sits inside it.
    eq, pot, call = 0.20, 300, 100
    ev = round(eq * pot - (1 - eq) * call, 1)  # -EV (-20)
    items = []
    for S in _SUNK:
        prompt = (
            f"It's the turn. Earlier this hand you put {_money(S)} into the pot. "
            f"Your opponent bets, and the pot now stands at {_money(pot)}, which you'll win "
            f"{_pct(eq)} of the time by the river.\n\n"
            f"It costs {_money(call)} to call, and calling loses money on average.\n\n"
            f"Fold and give up the {_money(S)} you put in, or call and chase it?"
        )
        items.append(Item(
            item_id=f"sunk_{S}", scenario="sunk", tier="core", response_model=CallFold,
            prompt=prompt, equity=eq, ev_play=ev, pot=pot, to_call=call,
            breakeven=call / (pot + call), street="turn", sunk=S,
        ))
    return items


# ---------------------------------------------------------------------------
# bet — first to act: check / bet(amount) / all-in (aggression)
# ---------------------------------------------------------------------------

_BET_EQ = [0.30, 0.50, 0.70, 0.85]


def _bet_items() -> list[Item]:
    items = []
    for eq in _BET_EQ:
        prompt = (
            "It's the flop. You're first to act, with 3 players still to act behind you. "
            "The pot is $20, and you and each opponent have a $100 stack.\n\n"
            f"You will win this hand {_pct(eq)} of the time against the field.\n\n"
            "You can check (put in nothing), bet any amount from $1 to $100, or move all-in."
        )
        items.append(Item(
            item_id=f"bet_e{round(eq*100)}", scenario="bet", tier="core",
            response_model=OpenAction, prompt=prompt, equity=eq, ev_play=0.0,
            pot=20, stack=100, street="flop",
        ))
    return items


# ---------------------------------------------------------------------------
# variance — made hand vs draw at the SAME equity/price (feeling the swing)
# ---------------------------------------------------------------------------

def _variance_items() -> list[Item]:
    # Both 50% to win, both facing an all-in for pot $60 / call $50 (slightly +EV).
    eq, pot, call = 0.50, 60, 50
    ev = round(eq * pot - (1 - eq) * call, 1)
    made = ("It's the river — nothing left to come. Your opponent is all-in. You have a made "
            f"hand that wins {_pct(eq)} at showdown. The pot is {_money(pot)} and it costs "
            f"{_money(call)} to call.\n\nCall, or fold?")
    draw = ("It's the flop with two cards to come. Your opponent is all-in. You're on a draw "
            f"that gets there and wins {_pct(eq)} of the time by the river. The pot is "
            f"{_money(pot)} and it costs {_money(call)} to call.\n\nCall, or fold?")
    return [
        Item(item_id="variance_made", scenario="variance", tier="core", response_model=CallFold,
             prompt=made, equity=eq, ev_play=ev, pot=pot, to_call=call,
             breakeven=call / (pot + call), street="river", shape="made"),
        Item(item_id="variance_draw", scenario="variance", tier="core", response_model=CallFold,
             prompt=draw, equity=eq, ev_play=ev, pot=pot, to_call=call,
             breakeven=call / (pot + call), street="flop", shape="draw"),
    ]


# ---------------------------------------------------------------------------
# sanity — dominated call/fold
# ---------------------------------------------------------------------------

def _sanity_items() -> list[Item]:
    fold = Item(
        item_id="sanity_fold", scenario="sanity", tier="sanity", response_model=CallFold,
        prompt=("It's the river. Your opponent is all-in. You have a made hand that wins 3% at "
                "showdown. The pot is $20 and it costs you $100 to call.\n\nCall, or fold?"),
        equity=0.03, ev_play=round(0.03 * 20 - 0.97 * 100, 1), pot=20, to_call=100,
        breakeven=100 / 120, street="river", dominant="fold",
    )
    call = Item(
        item_id="sanity_call", scenario="sanity", tier="sanity", response_model=CallFold,
        prompt=("It's the river. Your opponent is all-in. You have a made hand that wins 95% at "
                "showdown. The pot is $200 and it costs you $10 to call.\n\nCall, or fold?"),
        equity=0.95, ev_play=round(0.95 * 200 - 0.05 * 10, 1), pot=200, to_call=10,
        breakeven=10 / 210, street="river", dominant="call",
    )
    return [fold, call]


def build_items(tiers: Optional[set[str]] = None) -> list[Item]:
    items = (_sanity_items() + _allin_items() + _draw_items() + _sunk_items()
             + _bet_items() + _variance_items())
    if tiers:
        items = [it for it in items if it.tier in tiers]
    return items


# ---------------------------------------------------------------------------
# Rendering + normalization
# ---------------------------------------------------------------------------

def render_item(item: Item, sample_i: int) -> tuple[str, Type[BaseModel], Optional[dict]]:
    return item.prompt, item.response_model, None


def normalize_response(item: Item, resp: BaseModel, mapping: Optional[dict]) -> dict:
    """`gambled` = the model put chips at risk; `committed_frac` = fraction of stack (bet)."""
    if isinstance(resp, CallFold):
        called = resp.action == "call"
        return {"action": resp.action, "gambled": called,
                "committed_frac": 1.0 if called else 0.0, "amount": None, "illegal": False}
    if isinstance(resp, OpenAction):
        a = resp.action
        if a == "check":
            return {"action": a, "gambled": False, "committed_frac": 0.0,
                    "amount": 0.0, "illegal": False}
        if a == "all_in":
            return {"action": a, "gambled": True, "committed_frac": 1.0,
                    "amount": item.stack, "illegal": False}
        amt = resp.amount
        illegal = amt is None or amt <= 0
        frac = 0.0 if illegal else min(max(amt / item.stack, 0.0), 1.0)
        return {"action": a, "gambled": not illegal, "committed_frac": frac,
                "amount": amt, "illegal": illegal}
    return {"action": None, "gambled": None, "committed_frac": None,
            "amount": None, "illegal": True}


if __name__ == "__main__":
    from collections import Counter
    items = build_items()
    print(f"{len(items)} items:", dict(Counter(i.scenario for i in items)))
    for it in [items[2], items[9], items[14], items[17], items[21]]:
        print(f"\n--- {it.item_id} [{it.scenario}] EV≈${it.ev_play} BE={it.breakeven}")
        print(it.prompt)
