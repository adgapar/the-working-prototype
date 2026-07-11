"""Unified structured-output call layer via `instructor`.

`call_model` returns `(validated Pydantic object, usage)` across three providers.
The instructor mode is chosen per provider:

    OpenAI     -> Mode.RESPONSES_TOOLS      (Responses API; required for gpt-5.x)
    Anthropic  -> Mode.ANTHROPIC_TOOLS  (or ANTHROPIC_REASONING_TOOLS with thinking)
    Mistral    -> instructor.from_mistral   (native, via the [mistral] extra)

A "variant" dict selects the reasoning treatment:

    {"temperature": 0.0}                          # anthropic/mistral, thinking off
    {"thinking": True, "budget": 1024}            # anthropic extended thinking (temp forced 1)
    {"reasoning_effort": "low"}                   # openai reasoning models

Reasoning is native and internal — never a field on the output schema.

`usage` is {"input_tokens", "output_tokens", "reasoning_tokens"}; any field may be
None if a provider doesn't report it. Output tokens already include reasoning tokens
(providers bill them as output), so cost is input·p_in + output·p_out.

NOTE: model ids and the OpenAI reasoning-effort passthrough come from the caller's
environment; adjust the relevant branch if a provider rejects a value.
"""

from __future__ import annotations

import os
import time
from typing import Any, Type, TypeVar

import instructor
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()

T = TypeVar("T", bound=BaseModel)

_clients: dict[Any, Any] = {}


# ---------------------------------------------------------------------------
# Client factories (instructor-patched, cached)
# ---------------------------------------------------------------------------

def _openai_client():
    if "openai" not in _clients:
        from openai import OpenAI
        _clients["openai"] = instructor.from_openai(OpenAI(), mode=instructor.Mode.RESPONSES_TOOLS)
    return _clients["openai"]


def _anthropic_client(thinking: bool):
    key = ("anthropic", thinking)
    if key not in _clients:
        from anthropic import Anthropic
        mode = (instructor.Mode.ANTHROPIC_REASONING_TOOLS if thinking
                else instructor.Mode.ANTHROPIC_TOOLS)
        _clients[key] = instructor.from_anthropic(Anthropic(), mode=mode)
    return _clients[key]


def _mistral_client():
    if "mistral" not in _clients:
        from mistralai import Mistral
        key = os.getenv("MISTRAL_API_KEY")
        if not key:
            raise ValueError("MISTRAL_API_KEY not set in .env")
        _clients["mistral"] = instructor.from_mistral(Mistral(api_key=key))
    return _clients["mistral"]


# ---------------------------------------------------------------------------
# Usage extraction
# ---------------------------------------------------------------------------

def _usage_from(raw: Any) -> dict:
    """Normalize provider-native usage to input/output/reasoning token counts."""
    empty = {"input_tokens": None, "output_tokens": None, "reasoning_tokens": None}
    try:
        u = getattr(raw, "usage", None)
        if u is None:
            return empty
        in_tok = getattr(u, "input_tokens", None) or getattr(u, "prompt_tokens", None)
        out_tok = getattr(u, "output_tokens", None) or getattr(u, "completion_tokens", None)
        reasoning = None
        details = getattr(u, "output_tokens_details", None) or getattr(u, "completion_tokens_details", None)
        if details is not None:
            reasoning = getattr(details, "reasoning_tokens", None)
        return {"input_tokens": in_tok, "output_tokens": out_tok, "reasoning_tokens": reasoning}
    except Exception:  # noqa: BLE001 — usage shapes vary; never fail the run over telemetry
        return empty


# ---------------------------------------------------------------------------
# Per-provider structured calls (return (obj, raw_completion))
#
# All use the top-level `client.create_with_completion(model=, messages=, ...)`
# (instructor 1.14+). System goes in `messages` as a system-role turn; instructor
# routes to each provider's native API (OpenAI Responses under RESPONSES_TOOLS,
# Anthropic messages, Mistral chat) and returns (obj, raw) so we can read usage.
# ---------------------------------------------------------------------------

def _messages(system: str, prompt: str) -> list[dict]:
    return [{"role": "system", "content": system}, {"role": "user", "content": prompt}]


def _call_openai(model, system, prompt, variant, response_model, max_retries):
    return _openai_client().create_with_completion(
        model=model, messages=_messages(system, prompt),
        reasoning={"effort": variant["reasoning_effort"]},  # none|low|medium|high
        response_model=response_model, max_retries=max_retries, timeout=90,
    )


def _call_anthropic(model, system, prompt, variant, response_model, max_retries):
    kwargs: dict[str, Any] = {
        "model": model, "messages": _messages(system, prompt),
        "response_model": response_model, "max_retries": max_retries,
    }
    if variant.get("thinking"):
        if "budget" in variant:   # older API (haiku-4-5): enabled + token budget
            budget = variant["budget"]
            kwargs["max_tokens"] = budget + 1024
            kwargs["thinking"] = {"type": "enabled", "budget_tokens": budget}
        else:                     # newer API (sonnet-5, opus-4-8): adaptive + effort
            kwargs["max_tokens"] = 4096
            kwargs["thinking"] = {"type": "adaptive"}
            kwargs["output_config"] = {"effort": variant.get("effort", "low")}
    else:
        kwargs["max_tokens"] = 1024
    # Newer Claude models deprecate `temperature`; pass it only when present
    # (haiku still supports it).
    if "temperature" in variant:
        kwargs["temperature"] = variant["temperature"]
    return _anthropic_client(bool(variant.get("thinking"))).create_with_completion(**kwargs)


def _call_mistral(model, system, prompt, variant, response_model, max_retries):
    return _mistral_client().create_with_completion(
        model=model, messages=_messages(system, prompt),
        response_model=response_model, temperature=variant.get("temperature", 1.0),
        max_tokens=1024, max_retries=max_retries,
    )


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def call_model(
    provider: str, model: str, system: str, prompt: str, variant: dict,
    response_model: Type[T], max_retries: int = 2, retries: int = 2, backoff: float = 2.0,
) -> tuple[T, dict]:
    """Return (validated response_model instance, usage dict).

    `max_retries` is instructor's schema-repair retry; `retries` is our transport
    retry (transient API errors) with linear backoff.
    """
    last_err: Exception | None = None
    for attempt in range(retries + 1):
        try:
            if provider == "openai":
                obj, raw = _call_openai(model, system, prompt, variant, response_model, max_retries)
            elif provider == "anthropic":
                obj, raw = _call_anthropic(model, system, prompt, variant, response_model, max_retries)
            elif provider == "mistral":
                obj, raw = _call_mistral(model, system, prompt, variant, response_model, max_retries)
            else:
                raise ValueError(f"Unknown provider: {provider}")
            return obj, _usage_from(raw)
        except Exception as e:  # noqa: BLE001
            last_err = e
            if attempt < retries:
                time.sleep(backoff * (attempt + 1))
    assert last_err is not None
    raise last_err
