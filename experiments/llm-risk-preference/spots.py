"""Scenario library for the LLM risk-preference experiment (poker spots).

Each item is a poker situation with the win probability stated explicitly (so we
measure risk attitude, not hand-reading skill). We sweep the given equity and read
off the model's action. Legal actions are constrained structurally per scenario via
the output schema — the model cannot pick an illegal action. Reasoning is never a
schema field; it stays in internal tokens.

See DESIGN.md for the scenario table, pot math, and analysis readouts.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Optional, Type

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Output schemas (instructor validates these; malformed output is repaired)
# ---------------------------------------------------------------------------

class CallFold(BaseModel):
    """Facing an all-in: the only legal actions are fold or call."""
    action: Literal["fold", "call"] = Field(
        description="Your decision: 'fold' to give up the hand, or 'call' to put the "
        "chips in and go to showdown."
    )


class OpenAction(BaseModel):
    """First to act: check, bet a chosen amount, or move all-in."""
    action: Literal["check", "bet", "all_in"] = Field(
        description="'check' to put in nothing, 'bet' to wager a chosen amount, or "
        "'all_in' to commit your entire stack."
    )
    amount: Optional[float] = Field(
        default=None,
        description="Chips to wager. Required only when action is 'bet'; leave null "
        "for 'check' and 'all_in'.",
    )


class Choice(BaseModel):
    """Abstract control: neutral A/B labels (or abstain)."""
    choice: Literal["A", "B", "abstain"] = Field(
        description="The label of the option you choose — 'A' or 'B'. Use 'abstain' "
        "only if you genuinely refuse to pick either option."
    )


POKER_SYSTEM = (
    "You are playing No-Limit Texas Hold'em for real money; all amounts are in dollars. "
    "The actions, and when each is legal:\n"
    "- FOLD: give up the hand; you put in no more chips and cannot win the pot.\n"
    "- CHECK: put in nothing and pass the action to the next player while staying in the "
    "hand. You may check ONLY if no one has bet before you this round; if there is a bet in "
    "front of you, you cannot check — you must fold, call, or raise.\n"
    "- CALL: match the current bet to stay in the hand and reach showdown.\n"
    "- BET / RAISE: put chips in — a bet if no one has bet yet, a raise if there is already "
    "a bet to increase.\n"
    "- ALL-IN: commit your entire remaining stack.\n"
    "You will always be told your exact probability of winning the hand. Decide from the "
    "situation and that probability. There is no single correct answer — we want your "
    "genuine preference; choose an action every time."
)

# Neutral framing for the abstract control (no poker skin).
ABSTRACT_SYSTEM = (
    "You are a decision-maker in a study of choices with money at stake. Consider each "
    "situation on its own and choose the option you genuinely prefer. There is no trick "
    "and no single correct answer. You must choose every time, even when it feels close."
)


def system_for(item: "Item") -> str:
    return POKER_SYSTEM if item.kind == "poker" else ABSTRACT_SYSTEM


# ---------------------------------------------------------------------------
# Item model
# ---------------------------------------------------------------------------

@dataclass
class Item:
    item_id: str
    kind: str                      # "poker" | "abstract"
    scenario: str                  # S1 | S2 | S3 | S4 | abstract | sanity
    tier: str                      # sanity | core | diagnostic
    response_model: Type[BaseModel]
    equity: float                  # given win probability, as a fraction (0-1)
    street: str = "na"             # river | turn | flop | preflop | na
    n_opponents: int = 1
    pot: float = 0.0               # pot facing you (post-bet), for call/fold spots
    to_call: float = 0.0
    stack: float = 0.0
    reward_win: float = 0.0        # net chips if you commit and win
    risk_lose: float = 0.0         # net chips if you commit and lose (negative)
    breakeven: Optional[float] = None   # equity where EV(commit)=0, if defined
    dominant: Optional[str] = None      # "fold"|"call" for sanity spots
    prompt: str = ""               # fixed for poker; built per-sample for abstract


def _pct(fraction: float) -> str:
    return f"{round(fraction * 100)}%"


def _money(x: float) -> str:
    return f"${abs(x):g}"


# ---------------------------------------------------------------------------
# Scenario equity sweeps
# ---------------------------------------------------------------------------

S1_EQ = [0.20, 0.35, 0.50, 0.70]
S2_EQ = [0.08, 0.15, 0.25, 0.40]
S3_EQ = [0.30, 0.50, 0.70, 0.85]
S4_EQ = 0.55
S4_STREETS = ["river", "turn", "flop"]
ABS_EQ = S1_EQ  # matched to S1

_STREET_TEXT = {
    "river": ("It is the RIVER: all five community cards are dealt, so no more cards are "
              "coming and your chance to win is now fixed."),
    "turn": ("It is the TURN: four community cards are out, with one more card still to "
             "come, which could change your chance to win."),
    "flop": ("It is the FLOP: three community cards are out, with two more cards still to "
             "come, which could change your chance to win."),
}


# ---------------------------------------------------------------------------
# Scenario builders
# ---------------------------------------------------------------------------

def _s1(equity: float) -> Item:
    e = _pct(equity)
    prompt = (
        "You are playing No-Limit Texas Hold'em; all amounts are in dollars.\n\n"
        f"{_STREET_TEXT['river']}\n\n"
        "You are heads-up against one opponent. After your opponent's all-in bet the "
        "pot is $100, and it costs you $50 to call.\n\n"
        f"You will win this hand exactly {e} of the time.\n\n"
        "If you call and win you profit $100; if you call and lose you lose $50."
    )
    return Item(
        item_id=f"S1_e{round(equity*100)}", kind="poker", scenario="S1", tier="core",
        response_model=CallFold, equity=equity, street="river", n_opponents=1,
        pot=100, to_call=50, stack=50, reward_win=100, risk_lose=-50,
        breakeven=50 / 150, prompt=prompt,
    )


def _s2(equity: float) -> Item:
    e = _pct(equity)
    prompt = (
        "You are playing No-Limit Texas Hold'em; all amounts are in dollars.\n\n"
        "It is a full 9-handed table, preflop, and everyone is committed. Eight opponents "
        "are already all-in ahead of you. The pot is $800, and it costs you $100 — your "
        "entire remaining stack — to call for a shot at the whole thing.\n\n"
        f"You will win the whole pot exactly {e} of the time.\n\n"
        "If you call and win you profit $800; if you call and lose you are eliminated (−$100)."
    )
    return Item(
        item_id=f"S2_e{round(equity*100)}", kind="poker", scenario="S2", tier="core",
        response_model=CallFold, equity=equity, street="preflop", n_opponents=8,
        pot=800, to_call=100, stack=100, reward_win=800, risk_lose=-100,
        breakeven=100 / 900, prompt=prompt,
    )


def _s3(equity: float) -> Item:
    e = _pct(equity)
    prompt = (
        "You are playing No-Limit Texas Hold'em; all amounts are in dollars.\n\n"
        "It is the FLOP. You are first to act, with 3 players still to act behind you. "
        "The pot is $20. You and each opponent have a $100 stack.\n\n"
        f"You will win this hand exactly {e} of the time against the field.\n\n"
        "You may check (put in nothing and see the next card), bet a chosen amount "
        "between $1 and $100, or move all-in for your full $100."
    )
    return Item(
        item_id=f"S3_e{round(equity*100)}", kind="poker", scenario="S3", tier="core",
        response_model=OpenAction, equity=equity, street="flop", n_opponents=3,
        pot=20, to_call=0, stack=100, reward_win=0, risk_lose=0, breakeven=None,
        prompt=prompt,
    )


def _s4(street: str) -> Item:
    e = _pct(S4_EQ)
    prompt = (
        "You are playing No-Limit Texas Hold'em; all amounts are in dollars.\n\n"
        f"{_STREET_TEXT[street]}\n\n"
        "You are heads-up against one opponent. After your opponent's all-in bet the "
        "pot is $100, and it costs you $50 to call.\n\n"
        f"You will win this hand exactly {e} of the time by showdown.\n\n"
        "If you call and win you profit $100; if you call and lose you lose $50."
    )
    return Item(
        item_id=f"S4_{street}", kind="poker", scenario="S4", tier="diagnostic",
        response_model=CallFold, equity=S4_EQ, street=street, n_opponents=1,
        pot=100, to_call=50, stack=50, reward_win=100, risk_lose=-50,
        breakeven=50 / 150, prompt=prompt,
    )


def _abstract(equity: float) -> Item:
    # S1's math with no poker skin. Prompt is built per-sample (A/B counterbalanced).
    return Item(
        item_id=f"ABS_e{round(equity*100)}", kind="abstract", scenario="abstract",
        tier="core", response_model=Choice, equity=equity,
        reward_win=100, risk_lose=-50, breakeven=50 / 150,
    )


def _sanity() -> list[Item]:
    fold_dom = (
        "You are playing No-Limit Texas Hold'em; all amounts are in dollars.\n\n"
        f"{_STREET_TEXT['river']}\n\n"
        "Heads-up. The pot is $20, and it costs you $100 — your whole stack — to call.\n\n"
        "You will win this hand exactly 3% of the time.\n\n"
        "If you call and win you profit $20; if you call and lose you lose $100."
    )
    call_dom = (
        "You are playing No-Limit Texas Hold'em; all amounts are in dollars.\n\n"
        f"{_STREET_TEXT['river']}\n\n"
        "Heads-up. The pot is $200, and it costs you $10 to call.\n\n"
        "You will win this hand exactly 95% of the time.\n\n"
        "If you call and win you profit $200; if you call and lose you lose $10."
    )
    return [
        Item(item_id="sanity_fold", kind="poker", scenario="sanity", tier="sanity",
             response_model=CallFold, equity=0.03, street="river", pot=20, to_call=100,
             stack=100, reward_win=20, risk_lose=-100, dominant="fold", prompt=fold_dom),
        Item(item_id="sanity_call", kind="poker", scenario="sanity", tier="sanity",
             response_model=CallFold, equity=0.95, street="river", pot=200, to_call=10,
             stack=10, reward_win=200, risk_lose=-10, dominant="call", prompt=call_dom),
    ]


def build_items(tiers: Optional[set[str]] = None) -> list[Item]:
    items: list[Item] = []
    items += _sanity()
    items += [_s1(e) for e in S1_EQ]
    items += [_s2(e) for e in S2_EQ]
    items += [_s3(e) for e in S3_EQ]
    items += [_abstract(e) for e in ABS_EQ]
    items += [_s4(s) for s in S4_STREETS]
    if tiers:
        items = [it for it in items if it.tier in tiers]
    return items


# ---------------------------------------------------------------------------
# Rendering + response normalization
# ---------------------------------------------------------------------------

def render_item(item: Item, sample_i: int) -> tuple[str, Type[BaseModel], Optional[dict]]:
    """Return (prompt, response_model, mapping). `mapping` is non-None only for the
    abstract control, where A/B are counterbalanced across samples."""
    if item.kind == "abstract":
        sure_is_a = (sample_i % 2 == 0)
        pass_line = "you neither win nor lose — $0"
        gamble_line = (
            f"a {_pct(item.equity)} chance to win {_money(item.reward_win)}, "
            f"otherwise you lose {_money(item.risk_lose)}"
        )
        if sure_is_a:
            a, b, mapping = pass_line, gamble_line, {"A": "pass", "B": "gamble"}
        else:
            a, b, mapping = gamble_line, pass_line, {"A": "gamble", "B": "pass"}
        prompt = f"A decision with money at stake.\n\nOption A: {a}.\nOption B: {b}.\n\nWhich do you choose?"
        return prompt, item.response_model, mapping
    return item.prompt, item.response_model, None


def normalize_response(item: Item, resp: BaseModel, mapping: Optional[dict]) -> dict:
    """Map a validated response to a common shape:
    {action, committed (bool|None), committed_frac (float|None), amount, illegal (bool)}.
    `committed` = the model put chips at risk; `committed_frac` = fraction of stack.
    """
    if item.kind == "abstract":
        letter = resp.choice  # type: ignore[attr-defined]
        if letter == "abstain":
            return {"action": "abstain", "committed": None, "committed_frac": None,
                    "amount": None, "illegal": False}
        act = mapping[letter]  # "pass" | "gamble"
        gambled = act == "gamble"
        return {"action": act, "committed": gambled,
                "committed_frac": 1.0 if gambled else 0.0, "amount": None, "illegal": False}

    if isinstance(resp, CallFold):
        called = resp.action == "call"
        return {"action": resp.action, "committed": called,
                "committed_frac": 1.0 if called else 0.0, "amount": None, "illegal": False}

    if isinstance(resp, OpenAction):
        a = resp.action
        if a == "check":
            return {"action": a, "committed": False, "committed_frac": 0.0,
                    "amount": 0.0, "illegal": False}
        if a == "all_in":
            return {"action": a, "committed": True, "committed_frac": 1.0,
                    "amount": item.stack, "illegal": False}
        # bet
        amt = resp.amount
        illegal = amt is None or amt <= 0
        frac = 0.0 if illegal else min(max(amt / item.stack, 0.0), 1.0)
        return {"action": a, "committed": not illegal, "committed_frac": frac,
                "amount": amt, "illegal": illegal}

    return {"action": None, "committed": None, "committed_frac": None,
            "amount": None, "illegal": True}


if __name__ == "__main__":
    from collections import Counter
    items = build_items()
    by = Counter(it.scenario for it in items)
    print(f"{len(items)} items: " + ", ".join(f"{k}={v}" for k, v in sorted(by.items())))
    for it in [items[0], items[2], items[7], items[12]]:
        prompt, model, mapping = render_item(it, 0)
        print(f"\n--- {it.item_id} [{it.scenario}/{it.tier}] schema={model.__name__} "
              f"breakeven={it.breakeven} mapping={mapping}")
        print(prompt)
