"""Top-level CLI dispatch.

Usage:
    axyloid stats user --username USER --output PATH
    axyloid stats repo --owner OWNER --repo REPO --output PATH
    axyloid axl-diff OLD.axl NEW.axl    (later)
    axyloid validate-roadmap roadmap.yml  (later)

Token comes from the GITHUB_TOKEN environment variable. In CI this is
provided automatically; locally, export it before running.
"""

import argparse
import os
import sys


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="axyloid",
        description="Maintainer automation for the Axylith ecosystem.",
    )

    subparsers = parser.add_subparsers(dest="bot", required=True, metavar="BOT")

    # ─── stats ────────────────────────────────────────────────────
    stats_parser = subparsers.add_parser(
        "stats",
        help="Generate a stats badge SVG",
    )
    stats_sub = stats_parser.add_subparsers(dest="scope", required=True, metavar="SCOPE")

    user_p = stats_sub.add_parser("user", help="User-level activity stats")
    user_p.add_argument("--username", required=True, help="GitHub username")
    user_p.add_argument("--output", required=True, help="Output SVG path")

    repo_p = stats_sub.add_parser("repo", help="Repository-level stats")
    repo_p.add_argument("--owner", required=True, help="Repository owner")
    repo_p.add_argument("--repo", required=True, help="Repository name")
    repo_p.add_argument("--output", required=True, help="Output SVG path")

    # ─── placeholder: other bots go here ──────────────────────────
    # axl_diff_parser = subparsers.add_parser("axl-diff", ...)
    # validate_parser = subparsers.add_parser("validate-roadmap", ...)

    args = parser.parse_args()

    if args.bot == "stats":
        from cli.stats import run_stats
        return run_stats(args)

    # Unknown bot — argparse should catch this, but defensive fallback:
    print(f"unknown bot: {args.bot}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())