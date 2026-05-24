"""GitHub GraphQL API client for stats collection.

Two functions:
  - fetch_user_stats(token, username): for profile stats
  - fetch_repo_stats(token, owner, repo): for repo-level stats

Both return a plain dict — no Pydantic model overhead since these are
single-pass consumed by the renderer.
"""

import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


GITHUB_GRAPHQL = "https://api.github.com/graphql"


# Languages excluded from stats. These typically dominate byte-counts
# due to generated files, but don't reflect what the author "does."
# Repos with authored content in these languages should use
# .gitattributes (linguist-generated=true) to fix at the source instead.
EXCLUDED_LANGUAGES = {
    "HTML", "CSS", "SCSS", "Sass", "Less",
    "TeX", "Roff",
    "JavaScript", "Svelte",  # often Emscripten / vendored
}


class GitHubAPIError(Exception):
    """Raised when the GitHub API returns an error or is unreachable."""


def _gql(token: str, query: str) -> dict[str, Any]:
    """Run a GraphQL query. Returns the `data` field on success."""
    req = Request(
        GITHUB_GRAPHQL,
        data=json.dumps({"query": query}).encode(),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "axyloid",
        },
    )

    try:
        with urlopen(req, timeout=30) as r:
            payload = json.loads(r.read())
    except HTTPError as e:
        raise GitHubAPIError(f"HTTP {e.code}: {e.reason}") from e
    except URLError as e:
        raise GitHubAPIError(f"network error: {e.reason}") from e

    if "errors" in payload:
        raise GitHubAPIError(f"GraphQL errors: {payload['errors']}")

    return payload["data"]


def fetch_user_stats(token: str, username: str) -> dict[str, Any]:
    """Collect 12-month activity stats for a GitHub user.

    Returns:
        {
            "commits": int,
            "prs": int,
            "issues": int,
            "reviews": int,
            "total_contribs": int,
            "stars": int,
            "repos": int,
            "languages": [{"name": str, "pct": float, "color": str}, ...]
        }
    """
    query = """
    query {
      user(login: "%s") {
        contributionsCollection {
          totalCommitContributions
          totalPullRequestContributions
          totalIssueContributions
          totalPullRequestReviewContributions
          contributionCalendar { totalContributions }
        }
        repositories(first: 100, ownerAffiliations: OWNER, isFork: false,
                     orderBy: {field: STARGAZERS, direction: DESC}) {
          totalCount
          nodes {
            stargazerCount
            languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
              edges {
                size
                node { name color }
              }
            }
          }
        }
      }
    }
    """ % username

    data = _gql(token, query)
    user = data["user"]
    if user is None:
        raise GitHubAPIError(f"user not found: {username}")

    contrib = user["contributionsCollection"]
    repos = user["repositories"]["nodes"]

    lang_bytes: dict[str, int] = {}
    lang_colors: dict[str, str] = {}
    total_stars = 0

    for repo in repos:
        total_stars += repo["stargazerCount"]
        for edge in repo["languages"]["edges"]:
            name = edge["node"]["name"]
            if name in EXCLUDED_LANGUAGES:
                continue
            lang_bytes[name] = lang_bytes.get(name, 0) + edge["size"]
            lang_colors[name] = edge["node"]["color"] or "#888888"

    sorted_langs = sorted(lang_bytes.items(), key=lambda kv: -kv[1])[:5]
    total = sum(b for _, b in sorted_langs) or 1
    languages = [
        {"name": name, "pct": 100.0 * b / total, "color": lang_colors[name]}
        for name, b in sorted_langs
    ]

    return {
        "commits": contrib["totalCommitContributions"],
        "prs": contrib["totalPullRequestContributions"],
        "issues": contrib["totalIssueContributions"],
        "reviews": contrib["totalPullRequestReviewContributions"],
        "total_contribs": contrib["contributionCalendar"]["totalContributions"],
        "stars": total_stars,
        "repos": user["repositories"]["totalCount"],
        "languages": languages,
    }


def fetch_repo_stats(token: str, owner: str, repo: str) -> dict[str, Any]:
    """Collect activity stats for a single repository.

    Returns:
        {
            "stars": int,
            "forks": int,
            "open_issues": int,
            "open_prs": int,
            "watchers": int,
            "primary_language": str | None,
            "languages": [{"name": str, "pct": float, "color": str}, ...]
        }
    """
    query = """
    query {
      repository(owner: "%s", name: "%s") {
        stargazerCount
        forkCount
        watchers { totalCount }
        issues(states: OPEN) { totalCount }
        pullRequests(states: OPEN) { totalCount }
        primaryLanguage { name color }
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
          edges {
            size
            node { name color }
          }
        }
      }
    }
    """ % (owner, repo)

    data = _gql(token, query)
    r = data["repository"]
    if r is None:
        raise GitHubAPIError(f"repo not found: {owner}/{repo}")

    lang_bytes: dict[str, int] = {}
    lang_colors: dict[str, str] = {}
    for edge in r["languages"]["edges"]:
        name = edge["node"]["name"]
        if name in EXCLUDED_LANGUAGES:
            continue
        lang_bytes[name] = edge["size"]
        lang_colors[name] = edge["node"]["color"] or "#888888"

    sorted_langs = sorted(lang_bytes.items(), key=lambda kv: -kv[1])[:5]
    total = sum(b for _, b in sorted_langs) or 1
    languages = [
        {"name": name, "pct": 100.0 * b / total, "color": lang_colors[name]}
        for name, b in sorted_langs
    ]

    primary = r["primaryLanguage"]
    return {
        "stars": r["stargazerCount"],
        "forks": r["forkCount"],
        "open_issues": r["issues"]["totalCount"],
        "open_prs": r["pullRequests"]["totalCount"],
        "watchers": r["watchers"]["totalCount"],
        "primary_language": primary["name"] if primary else None,
        "languages": languages,
    }