"""Stats bot: generates SVG badges of repo activity."""

from core.stats.github_api import fetch_user_stats, fetch_repo_stats
from core.stats.renderer import render_user_stats, render_repo_stats

__all__ = [
    "fetch_user_stats",
    "fetch_repo_stats",
    "render_user_stats",
    "render_repo_stats",
]