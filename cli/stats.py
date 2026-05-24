"""Stats bot CLI implementation."""

import os
import sys
from pathlib import Path

from core.stats import (
    fetch_user_stats,
    fetch_repo_stats,
    render_user_stats,
    render_repo_stats,
)
from core.stats.github_api import GitHubAPIError


def run_stats(args) -> int:
    """Dispatch to user or repo stats. Returns exit code."""
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("error: GITHUB_TOKEN environment variable not set", file=sys.stderr)
        return 1

    try:
        if args.scope == "user":
            stats = fetch_user_stats(token, args.username)
            svg = render_user_stats(stats, username=args.username)
            _summary_user(args.username, stats)
        elif args.scope == "repo":
            stats = fetch_repo_stats(token, args.owner, args.repo)
            svg = render_repo_stats(stats, owner=args.owner, repo=args.repo)
            _summary_repo(args.owner, args.repo, stats)
        else:
            print(f"error: unknown scope {args.scope}", file=sys.stderr)
            return 1
    except GitHubAPIError as e:
        print(f"GitHub API error: {e}", file=sys.stderr)
        return 2

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(svg)
    print(f"wrote {output_path}")
    return 0


def _summary_user(username: str, stats: dict) -> None:
    print(f"user: {username}")
    print(f"  commits:        {stats['commits']:,}")
    print(f"  pull requests:  {stats['prs']:,}")
    print(f"  issues:         {stats['issues']:,}")
    print(f"  reviews:        {stats['reviews']:,}")
    print(f"  total contribs: {stats['total_contribs']:,}")
    print(f"  stars earned:   {stats['stars']:,}")
    print(f"  repositories:   {stats['repos']:,}")
    if stats["languages"]:
        langs = ", ".join(f"{l['name']} {l['pct']:.0f}%" for l in stats["languages"])
        print(f"  languages:      {langs}")


def _summary_repo(owner: str, repo: str, stats: dict) -> None:
    print(f"repo: {owner}/{repo}")
    print(f"  stars:        {stats['stars']:,}")
    print(f"  forks:        {stats['forks']:,}")
    print(f"  open issues:  {stats['open_issues']:,}")
    print(f"  open PRs:     {stats['open_prs']:,}")
    print(f"  watchers:     {stats['watchers']:,}")
    if stats["primary_language"]:
        print(f"  primary lang: {stats['primary_language']}")