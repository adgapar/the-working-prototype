#!/usr/bin/env python3
"""
View conversation transcripts from promptfoo results in readable format.

Usage:
    python view_conversations.py output/results.json
    python view_conversations.py output/results.json --failed-only
    python view_conversations.py output/results.json --plugin contracts
"""

import json
import sys
from pathlib import Path


def print_conversation(test_result, show_provider=True):
    """Pretty print a conversation from test result."""

    # Get metadata
    metadata = test_result.get('metadata', {})
    plugin_id = metadata.get('pluginId', 'unknown')
    strategy_id = metadata.get('strategyId', 'basic')
    goal = metadata.get('goal', 'N/A')

    # Get provider (approach)
    provider = test_result.get('provider', {})
    if isinstance(provider, dict):
        provider_label = provider.get('label', 'Unknown')
    else:
        provider_label = str(provider)

    # Get result
    success = test_result.get('success', False)
    grade_result = test_result.get('gradingResult', {})
    reason = grade_result.get('reason', 'No reason provided')

    # Print header
    print("\n" + "="*80)
    if show_provider:
        print(f"🎯 {provider_label}")
    print(f"📦 Plugin: {plugin_id}")
    print(f"🎲 Strategy: {strategy_id}")
    print(f"✅ Passed" if success else "❌ Failed")
    print(f"📝 Goal: {goal[:120]}...")
    print(f"💭 Reason: {reason}")
    print("="*80)

    # Get conversation
    # Promptfoo stores the conversation in the 'response' or 'prompt' fields
    # For multi-turn, it's in the provider's conversation history

    # Try to get conversation from vars or response
    vars_data = test_result.get('vars', {})

    # For multi-turn tests, the conversation is in the response metadata
    response = test_result.get('response', {})
    if isinstance(response, dict):
        output = response.get('output', '')
        metadata_resp = response.get('metadata', {})
    else:
        output = str(response)
        metadata_resp = {}

    # Print initial prompt
    prompt = vars_data.get('prompt', '')
    if prompt:
        print(f"\n💬 Initial Prompt:")
        print(f"   {prompt[:200]}..." if len(prompt) > 200 else f"   {prompt}")

    # Print response
    if output:
        print(f"\n🤖 Model Response:")
        print(f"   {output[:500]}..." if len(output) > 500 else f"   {output}")

    print("\n")


def main():
    if len(sys.argv) < 2:
        print("Usage: python view_conversations.py <results.json> [--failed-only] [--plugin <name>]")
        sys.exit(1)

    results_file = Path(sys.argv[1])
    if not results_file.exists():
        print(f"Error: {results_file} not found")
        sys.exit(1)

    # Parse options
    failed_only = '--failed-only' in sys.argv
    plugin_filter = None
    if '--plugin' in sys.argv:
        plugin_idx = sys.argv.index('--plugin')
        if plugin_idx + 1 < len(sys.argv):
            plugin_filter = sys.argv[plugin_idx + 1]

    # Load results
    with open(results_file) as f:
        data = json.load(f)

    # Get results array
    results_obj = data.get('results', {})
    if isinstance(results_obj, dict):
        results = results_obj.get('results', [])
    else:
        results = results_obj if isinstance(results_obj, list) else []

    print(f"\n📊 Loaded {len(results)} test results from {results_file}")

    # Filter results
    filtered = results
    if failed_only:
        filtered = [r for r in filtered if not r.get('success', False)]
        print(f"🔍 Filtering to {len(filtered)} failed tests")

    if plugin_filter:
        filtered = [r for r in filtered
                   if r.get('metadata', {}).get('pluginId', '') == plugin_filter]
        print(f"🔍 Filtering to {len(filtered)} tests for plugin '{plugin_filter}'")

    if not filtered:
        print("No results match your filters!")
        return

    # Group by provider
    by_provider = {}
    for result in filtered:
        provider = result.get('provider', {})
        if isinstance(provider, dict):
            label = provider.get('label', 'Unknown')
        else:
            label = str(provider)

        if label not in by_provider:
            by_provider[label] = []
        by_provider[label].append(result)

    # Print conversations grouped by provider
    for provider_label, tests in by_provider.items():
        print(f"\n\n{'#'*80}")
        print(f"# {provider_label}")
        print(f"# {len(tests)} conversations")
        print(f"{'#'*80}")

        for i, test in enumerate(tests, 1):
            print(f"\n--- Conversation {i}/{len(tests)} ---")
            print_conversation(test, show_provider=False)

    # Summary
    print(f"\n\n📈 Summary:")
    for provider_label, tests in by_provider.items():
        passed = sum(1 for t in tests if t.get('success', False))
        failed = len(tests) - passed
        pass_rate = (passed / len(tests) * 100) if tests else 0
        print(f"   {provider_label}: {passed}/{len(tests)} passed ({pass_rate:.1f}%)")


if __name__ == '__main__':
    main()
