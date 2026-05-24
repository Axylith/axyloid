"""Push event handler.

On every push to a repo where the App is installed:
  1. If the push is to the default branch, regenerate the stats badge
  2. Commit the new SVG back to the repo

Skips: forks, archived repos, pushes by the bot itself (to prevent loops).
"""

import logging
import os
import tempfile
from pathlib import Path
from typing import Any

import httpx

from core.stats import fetch_repo_stats, render_repo_stats
from core.stats.github_api import GitHubAPIError

logger = logging.getLogger(__name__)


# Path within the consuming repo where we write the stats badge.
# This is the default; could be made configurable per-installation later.
DEFAULT_STATS_PATH = ".github/assets/stats.svg"


async def handle_push(payload: dict[str, Any], token: str) -> None:
    """Process a push webhook event."""
    repo = payload["repository"]
    pusher = payload.get("pusher", {}).get("name", "unknown")

    # Skip self-pushes to avoid infinite loops
    if pusher.endswith("[bot]") or pusher == "axyloid":
        logger.info(f"skipping self-push from {pusher}")
        return

    # Skip non-default-branch pushes (regenerating stats on every feature branch is overkill)
    default_branch = repo["default_branch"]
    pushed_branch = payload["ref"].replace("refs/heads/", "")
    if pushed_branch != default_branch:
        logger.info(f"skipping push to non-default branch {pushed_branch}")
        return

    # Skip archived and disabled repos
    if repo.get("archived") or repo.get("disabled"):
        logger.info(f"skipping {repo['full_name']}: archived or disabled")
        return

    owner = repo["owner"]["login"]
    name = repo["name"]
    logger.info(f"processing push to {owner}/{name}")

    # Generate the stats SVG
    try:
        stats = fetch_repo_stats(token, owner, name)
        svg = render_repo_stats(stats, owner=owner, repo=name)
    except GitHubAPIError as e:
        logger.error(f"failed to fetch stats for {owner}/{name}: {e}")
        return

    # Commit the SVG back to the repo
    await commit_file(
        token=token,
        owner=owner,
        repo=name,
        path=DEFAULT_STATS_PATH,
        content=svg,
        message="chore: regenerate stats badge",
        branch=default_branch,
    )
    logger.info(f"updated {DEFAULT_STATS_PATH} in {owner}/{name}")


async def commit_file(
        token: str,
        owner: str,
        repo: str,
        path: str,
        content: str,
        message: str,
        branch: str,
) -> None:
    """Create or update a file in a repo via the Contents API.

    The Contents API requires the file's current SHA if it already exists.
    We do a GET first to check, then a PUT with the optional sha field.
    """
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"

    # Check if the file already exists to get its sha
    sha: str | None = None
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(f"{url}?ref={branch}", headers=headers)
        if resp.status_code == 200:
            sha = resp.json()["sha"]
        elif resp.status_code != 404:
            resp.raise_for_status()

        # PUT to create or update
        import base64
        body = {
            "message": message,
            "content": base64.b64encode(content.encode()).decode(),
            "branch": branch,
        }
        if sha:
            body["sha"] = sha

        put_resp = await client.put(url, json=body, headers=headers)
        put_resp.raise_for_status()