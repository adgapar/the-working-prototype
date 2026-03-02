#!/usr/bin/env python3
"""
Full analysis of promptfoo red-team results with conversation transcript support.

Replaces analyze_results.py with richer per-turn analysis, crack-turn detection,
strategy efficiency reporting, and optional markdown output.

Usage:
    uv run python analyze_full.py output/results-excessive-agency.json
    uv run python analyze_full.py output/results-*.json --transcripts-dir output/transcripts/
    uv run python analyze_full.py output/results-*.json --transcripts-dir output/transcripts/ --report output/report.md
"""

import json
import sys
import glob
import argparse
from collections import defaultdict
from pathlib import Path
from typing import Optional

# Maps promptfoo provider labels → approach codes used in transcript state_keys
LABEL_TO_APPROACH = {
    "Approach A: Text Transcript": "json_history",
    "Approach B: Message Array": "multi_message",
}


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_results(paths: list[str]) -> list[dict]:
    """Load and merge results from one or more promptfoo result JSON files."""
    all_results = []
    for path in paths:
        for expanded in glob.glob(path):
            with open(expanded) as f:
                data = json.load(f)
            results_obj = data.get('results', {})
            if isinstance(results_obj, dict):
                results = results_obj.get('results', [])
            else:
                results = []
            all_results.extend(results)
    return all_results


def load_transcripts(transcripts_dir: str) -> dict[str, dict]:
    """Load all transcript JSON files, keyed by state_key."""
    transcripts = {}
    p = Path(transcripts_dir)
    if not p.exists():
        return transcripts
    for f in p.glob("**/*.json"):
        try:
            with open(f) as fh:
                t = json.load(fh)
            state_key = t.get("state_key")
            if state_key:
                transcripts[state_key] = t
        except (json.JSONDecodeError, KeyError):
            pass
    return transcripts


# ---------------------------------------------------------------------------
# Crack-turn detection
# ---------------------------------------------------------------------------

def find_crack_turn(result: dict, transcript: Optional[dict]) -> Optional[int]:
    """Return the 1-indexed turn number at which Maya first failed.

    Uses the final response.output to locate the matching maya turn in the
    transcript. Returns None if the test passed or no transcript is available.
    """
    if result.get('success', True):
        return None
    if transcript is None:
        return None

    response_output = result.get('response', {}).get('output', '').strip()
    if not response_output:
        return None

    for turn in transcript.get('conversation', []):
        maya_text = turn.get('maya', '').strip()
        # Match on the first 120 chars to handle minor whitespace differences
        if maya_text[:120] == response_output[:120]:
            return turn['turn']

    # Fallback: if we couldn't match exactly, return the last turn
    conversation = transcript.get('conversation', [])
    if conversation:
        return conversation[-1]['turn']
    return None


# ---------------------------------------------------------------------------
# Summaries
# ---------------------------------------------------------------------------

def _provider_label(result: dict) -> str:
    provider = result.get('provider', {})
    if isinstance(provider, dict):
        return provider.get('label', 'Unknown')
    return str(provider)


def _meta(result: dict) -> dict:
    return result.get('testCase', {}).get('metadata', {})


def _state_key_for_result(result: dict) -> str:
    """Reconstruct the transcript state_key that chat.py would have written.

    Mirrors the logic in chat.py:
        state_key = f"{approach}_{plugin_id}_{strategy_id}_{session_id}"
    """
    label = _provider_label(result)
    approach = LABEL_TO_APPROACH.get(label, label)
    meta = _meta(result)
    plugin_id = meta.get('pluginId', 'unknown')
    strategy_id = meta.get('strategyId', 'none')
    session_id = result.get('vars', {}).get('sessionId', '')
    if session_id:
        return f"{approach}_{plugin_id}_{strategy_id}_{session_id}"
    return f"{approach}_{plugin_id}_{strategy_id}"


def summarize_by_strategy(results: list[dict], transcripts: dict) -> dict:
    """Group results by strategyId, compute crack rate and avg crack turn."""
    stats = defaultdict(lambda: {'total': 0, 'passed': 0, 'failed': 0, 'crack_turns': []})

    for r in results:
        sid = _meta(r).get('strategyId', 'none')
        stats[sid]['total'] += 1
        if r.get('success', True):
            stats[sid]['passed'] += 1
        else:
            stats[sid]['failed'] += 1
            transcript = transcripts.get(_state_key_for_result(r))
            ct = find_crack_turn(r, transcript)
            if ct is not None:
                stats[sid]['crack_turns'].append(ct)

    summary = {}
    for sid, s in stats.items():
        crack_turns = s['crack_turns']
        summary[sid] = {
            'total': s['total'],
            'passed': s['passed'],
            'failed': s['failed'],
            'crack_rate': round(s['failed'] / s['total'] * 100) if s['total'] else 0,
            'avg_crack_turn': round(sum(crack_turns) / len(crack_turns), 1) if crack_turns else None,
        }
    return summary


def summarize_by_plugin_approach(results: list[dict]) -> dict:
    """Group results by pluginId × provider label, compute pass rates."""
    stats = defaultdict(lambda: defaultdict(lambda: {'total': 0, 'passed': 0}))

    for r in results:
        plugin = _meta(r).get('pluginId', 'unknown')
        label = _provider_label(r)
        stats[plugin][label]['total'] += 1
        if r.get('success', True):
            stats[plugin][label]['passed'] += 1

    # Convert to plain dict with pass_rate
    summary = {}
    for plugin, approaches in stats.items():
        summary[plugin] = {}
        for label, s in approaches.items():
            total = s['total']
            passed = s['passed']
            summary[plugin][label] = {
                'passed': passed,
                'total': total,
                'pass_rate': round(passed / total * 100) if total else 0,
            }
    return summary


# ---------------------------------------------------------------------------
# Printing
# ---------------------------------------------------------------------------

def print_summary(strategy_summary: dict, plugin_summary: dict, has_transcripts: bool) -> None:
    print()
    print("=" * 65)
    print("STRATEGY EFFICIENCY")
    print("=" * 65)
    crack_col = "Avg Crack Turn" if has_transcripts else "Avg Crack Turn*"
    print(f"{'Strategy':<20} {'Tests':>6} {'Passed':>7} {'Failed':>7} {'Crack%':>7}  {crack_col}")
    print("-" * 65)
    for sid in sorted(strategy_summary):
        s = strategy_summary[sid]
        avg = f"{s['avg_crack_turn']:.1f}" if s['avg_crack_turn'] is not None else "N/A"
        print(f"{sid:<20} {s['total']:>6} {s['passed']:>7} {s['failed']:>7} {s['crack_rate']:>6}%  {avg}")
    if not has_transcripts:
        print()
        print("  * Run with --transcripts-dir to show crack turns")

    print()
    print("=" * 65)
    print("PLUGIN × APPROACH")
    print("=" * 65)

    # Collect all approach labels in a stable order
    all_labels = []
    for approaches in plugin_summary.values():
        for label in approaches:
            if label not in all_labels:
                all_labels.append(label)
    all_labels.sort()

    col_w = 22
    header = f"{'Plugin':<20}" + "".join(f"  {lbl[:col_w-2]:<{col_w}}" for lbl in all_labels)
    print(header)
    print("-" * 65)
    for plugin in sorted(plugin_summary):
        row = f"{plugin:<20}"
        for label in all_labels:
            s = plugin_summary[plugin].get(label, {})
            if s:
                cell = f"{s['passed']}/{s['total']} ({s['pass_rate']}%)"
            else:
                cell = "N/A"
            row += f"  {cell:<{col_w}}"
        print(row)
    print()


# ---------------------------------------------------------------------------
# Markdown report
# ---------------------------------------------------------------------------

def write_markdown_report(
    strategy_summary: dict,
    plugin_summary: dict,
    path: str,
    has_transcripts: bool,
    source_files: list[str],
) -> None:
    lines = [
        "# Red-Team Analysis Report",
        "",
        f"**Source files:** {', '.join(source_files)}",
        f"**Transcripts:** {'yes' if has_transcripts else 'no (run with --transcripts-dir for crack-turn data)'}",
        "",
        "---",
        "",
        "## Strategy Efficiency",
        "",
    ]

    crack_col = "Avg Crack Turn" if has_transcripts else "Avg Crack Turn*"
    lines.append(f"| Strategy | Tests | Passed | Failed | Crack% | {crack_col} |")
    lines.append("|----------|------:|-------:|-------:|-------:|" + "-" * 16 + "|")
    for sid in sorted(strategy_summary):
        s = strategy_summary[sid]
        avg = f"{s['avg_crack_turn']:.1f}" if s['avg_crack_turn'] is not None else "N/A"
        lines.append(f"| `{sid}` | {s['total']} | {s['passed']} | {s['failed']} | {s['crack_rate']}% | {avg} |")

    if not has_transcripts:
        lines.append("")
        lines.append("*\\* Crack turn data requires `--transcripts-dir`*")

    lines += ["", "---", "", "## Plugin × Approach", ""]

    all_labels = sorted({lbl for approaches in plugin_summary.values() for lbl in approaches})
    header = "| Plugin | " + " | ".join(all_labels) + " |"
    sep = "|--------|" + "|".join(["-" * max(len(lbl), 10) for lbl in all_labels]) + "|"
    lines.append(header)
    lines.append(sep)
    for plugin in sorted(plugin_summary):
        cells = []
        for label in all_labels:
            s = plugin_summary[plugin].get(label, {})
            if s:
                cells.append(f"{s['passed']}/{s['total']} ({s['pass_rate']}%)")
            else:
                cells.append("N/A")
        lines.append(f"| `{plugin}` | " + " | ".join(cells) + " |")

    lines += ["", "---", ""]
    output = "\n".join(lines)

    with open(path, "w") as f:
        f.write(output)
    print(f"Report written to: {path}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Analyze promptfoo red-team results with optional transcript support."
    )
    parser.add_argument(
        "results",
        nargs="+",
        help="Path(s) to promptfoo result JSON files (supports globs)",
    )
    parser.add_argument(
        "--transcripts-dir",
        default=None,
        help="Directory containing transcript JSON files from chat.py",
    )
    parser.add_argument(
        "--report",
        default=None,
        help="Write a markdown report to this path",
    )
    args = parser.parse_args()

    results = load_results(args.results)
    if not results:
        print("Error: no results found in the provided files.")
        sys.exit(1)
    print(f"Loaded {len(results)} test results.")

    transcripts = {}
    if args.transcripts_dir:
        transcripts = load_transcripts(args.transcripts_dir)
        print(f"Loaded {len(transcripts)} transcripts from {args.transcripts_dir}")
    has_transcripts = bool(transcripts)

    strategy_summary = summarize_by_strategy(results, transcripts)
    plugin_summary = summarize_by_plugin_approach(results)

    print_summary(strategy_summary, plugin_summary, has_transcripts)

    if args.report:
        write_markdown_report(
            strategy_summary,
            plugin_summary,
            args.report,
            has_transcripts,
            args.results,
        )


if __name__ == "__main__":
    main()
