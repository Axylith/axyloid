"""Tests for the stats bot.

These tests use mock data — we don't make real API calls in unit tests.
Integration tests against the real GitHub API live elsewhere (and require
a token to run).
"""

import pytest
from core.stats.renderer import render_user_stats, render_repo_stats


@pytest.fixture
def mock_user_stats():
    return {
        "commits": 487,
        "prs": 32,
        "issues": 14,
        "reviews": 8,
        "total_contribs": 1247,
        "stars": 89,
        "repos": 23,
        "languages": [
            {"name": "C++", "pct": 62.4, "color": "#f34b7d"},
            {"name": "Python", "pct": 21.7, "color": "#3572A5"},
            {"name": "CUDA", "pct": 8.3, "color": "#3A4E3A"},
            {"name": "GLSL", "pct": 4.2, "color": "#5686a5"},
            {"name": "CMake", "pct": 3.4, "color": "#DA3434"},
        ],
    }


@pytest.fixture
def mock_repo_stats():
    return {
        "stars": 142,
        "forks": 18,
        "open_issues": 7,
        "open_prs": 3,
        "watchers": 28,
        "primary_language": "C++",
        "languages": [
            {"name": "C++", "pct": 78.2, "color": "#f34b7d"},
            {"name": "Python", "pct": 15.4, "color": "#3572A5"},
            {"name": "CMake", "pct": 6.4, "color": "#DA3434"},
        ],
    }


def test_render_user_stats_produces_valid_svg(mock_user_stats):
    svg = render_user_stats(mock_user_stats, username="testuser")
    assert svg.startswith("<svg")
    assert svg.endswith("</svg>\n")
    assert 'viewBox="0 0 900 240"' in svg


def test_render_user_stats_includes_numeric_values(mock_user_stats):
    svg = render_user_stats(mock_user_stats)
    assert "487" in svg       # commits
    assert "32" in svg        # prs
    assert "89" in svg        # stars
    assert "1,247" in svg     # total_contribs (formatted)


def test_render_user_stats_includes_languages(mock_user_stats):
    svg = render_user_stats(mock_user_stats)
    for lang in mock_user_stats["languages"]:
        assert lang["name"] in svg
        assert lang["color"] in svg


def test_render_user_stats_handles_empty_languages():
    stats = {
        "commits": 10, "prs": 0, "issues": 0, "reviews": 0,
        "total_contribs": 10, "stars": 0, "repos": 1,
        "languages": [],
    }
    svg = render_user_stats(stats)
    assert svg.startswith("<svg")
    # Should not crash, just render with no language segments


def test_render_repo_stats_produces_valid_svg(mock_repo_stats):
    svg = render_repo_stats(mock_repo_stats, owner="Axylith", repo="axle")
    assert svg.startswith("<svg")
    assert svg.endswith("</svg>\n")
    assert "AXYLITH/AXLE" in svg.upper()


def test_render_repo_stats_includes_numeric_values(mock_repo_stats):
    svg = render_repo_stats(mock_repo_stats, "Axylith", "axle")
    assert "142" in svg   # stars
    assert "18" in svg    # forks
    assert "7" in svg     # open_issues


def test_render_repo_stats_includes_primary_language(mock_repo_stats):
    svg = render_repo_stats(mock_repo_stats, "Axylith", "axle")
    assert "C++" in svg