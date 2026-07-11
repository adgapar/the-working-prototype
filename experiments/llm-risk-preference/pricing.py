"""Token pricing for cost estimation.

PLACEHOLDER prices — set the real $ per 1M tokens for your models/deployment before
trusting the dollar figures. Token *counts* are logged from the API regardless, so
you can always recompute cost after the fact by fixing these numbers.

Output price covers reasoning/thinking tokens too (providers bill them as output),
so we never add reasoning tokens separately.
"""

# model id -> (input $/1M, output $/1M). All rows confirmed.
# Caching isn't modeled: our prompts (~400-1000 tokens) sit below the providers'
# ~1024-token automatic-cache threshold, so cached-read/write prices never apply here
# (luna's cached read/write would be $0.10 / $1.25 per 1M if it did).
PRICING: dict[str, tuple[float, float]] = {
    "claude-haiku-4-5": (1.00, 5.00),      # confirmed (cache read $0.10)
    "claude-sonnet-5": (2.00, 10.00),      # confirmed (cache read $0.20)
    "claude-opus-4-8": (5.00, 25.00),      # confirmed (cache read $0.50; not modeled)
    "gpt-5.6-luna": (1.00, 6.00),          # confirmed
    "gpt-5.6-terra": (2.50, 15.00),        # confirmed
    "mistral-small-latest": (0.15, 0.60),   # confirmed
    "mistral-medium-latest": (1.50, 7.50),  # confirmed
}


def cost_of(model: str, input_tokens, output_tokens) -> float | None:
    """Dollar cost of one call, or None if price/usage is unknown."""
    if model not in PRICING or input_tokens is None or output_tokens is None:
        return None
    p_in, p_out = PRICING[model]
    return (input_tokens * p_in + output_tokens * p_out) / 1_000_000
