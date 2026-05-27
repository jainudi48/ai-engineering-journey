"""
demo.py — GitHub Repo Health Checker: Tool Use Rings

Runs all 5 tool-use patterns against a GitHub repo (default: anthropics/anthropic-sdk-python).
Each ring demonstrates a distinct layer of complexity in the Anthropic SDK.

Usage:
    python demo.py                                    # all 5 rings, default repo
    python demo.py --repo torvalds/linux              # target a different repo
    python demo.py --ring 3                           # parallel tools only
    python demo.py --ring 3 --repo pallets/flask      # specific ring + repo
    python demo.py --quiet                            # final answers only, no step logs

Requirements:
    export ANTHROPIC_API_KEY=sk-ant-...
    pip install -r requirements.txt
"""

import argparse
import sys
import time

DEFAULT_REPO = "anthropics/anthropic-sdk-python"


def banner(text: str) -> None:
    width = 62
    print("\n" + "▓" * width)
    print(f"  {text}")
    print("▓" * width)


def run_ring(n: int, verbose: bool, repo: str) -> str:
    if n == 1:
        from rings.ring1_single_tool   import run
    elif n == 2:
        from rings.ring2_agentic_loop  import run
    elif n == 3:
        from rings.ring3_parallel_tools import run
    elif n == 4:
        from rings.ring4_error_handling import run
    elif n == 5:
        from rings.ring5_beta_sdk      import run
    else:
        raise ValueError(f"Unknown ring: {n}")
    return run(verbose=verbose, repo=repo)


def main():
    parser = argparse.ArgumentParser(
        description="Tool Use Rings — GitHub Repo Health Checker"
    )
    parser.add_argument(
        "--ring", type=int, choices=[1, 2, 3, 4, 5],
        help="Run a single ring (1–5). Omit to run all."
    )
    parser.add_argument(
        "--repo", type=str, default=DEFAULT_REPO,
        metavar="OWNER/REPO",
        help=f"GitHub repo to analyse (default: {DEFAULT_REPO})."
    )
    parser.add_argument(
        "--quiet", action="store_true",
        help="Suppress per-step logging; only print final answers."
    )
    args = parser.parse_args()

    if "/" not in args.repo or args.repo.count("/") != 1:
        print(f"Error: --repo must be in OWNER/REPO format (got: {args.repo!r})", file=sys.stderr)
        sys.exit(1)

    verbose = not args.quiet
    rings_to_run = [args.ring] if args.ring else [1, 2, 3, 4, 5]

    ring_titles = {
        1: "Single Tool, Single Run",
        2: "Agentic Loop",
        3: "Parallel Multi-Tool Run",
        4: "Error Handling",
        5: "Beta SDK ToolRunner Abstraction",
    }

    banner("GitHub Repo Health Checker — Tool Use Rings (Rings 1–5)")
    print(f"  Target: {args.repo}")
    print("  Model:  claude-sonnet-4-6")
    print(f"  Rings:  {rings_to_run}\n")

    results = {}

    for n in rings_to_run:
        banner(f"Ring {n} — {ring_titles[n]}")
        start = time.time()
        try:
            answer = run_ring(n, verbose=verbose, repo=args.repo)
            elapsed = time.time() - start
            results[n] = ("✓", elapsed, answer)
        except Exception as e:
            elapsed = time.time() - start
            results[n] = ("✗", elapsed, str(e))
            print(f"  [ERROR] Ring {n} failed: {e}", file=sys.stderr)

    # ── Summary ───────────────────────────────────────────────────────────────
    banner("Summary")
    for n, (status, elapsed, answer) in results.items():
        short = answer[:100].replace("\n", " ")
        print(f"  Ring {n} {status}  ({elapsed:.1f}s) — {short}…")

    all_ok = all(s == "✓" for s, _, _ in results.values())
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
