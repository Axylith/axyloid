"""SVG renderers for stats badges.

Output matches the warm-amber-on-dark Axylith aesthetic:
  background: #0d0e10 → #13151a
  accent:     #c89858 → #b88848
  text:       #e8dcc8 (primary), #8b8275 (muted), #5a5249 (label)
  font:       JetBrains Mono
"""

import datetime
from typing import Any


def _legend_segment(lang: dict[str, Any], x: int) -> tuple[str, int]:
    """Build one legend item (dot + name + pct). Returns (svg, next_x)."""
    name_width = len(lang["name"]) * 6.5 + 50  # rough text width estimate
    svg = (
        f'<circle cx="{x + 5}" cy="200" r="3.5" '
        f'fill="{lang["color"]}" opacity="0.85"/>'
        f'<text x="{x + 15}" y="204" font-family="JetBrains Mono, monospace" '
        f'font-size="10" fill="#a8a098">'
        f'{lang["name"]} '
        f'<tspan fill="#5a5249">{lang["pct"]:.0f}%</tspan>'
        f'</text>'
    )
    return svg, x + int(name_width)


def render_user_stats(stats: dict[str, Any], username: str = "") -> str:
    """Generate SVG for user-level GitHub activity stats."""

    bar_x = 80
    bar_y = 175
    bar_w = 740
    bar_h = 8

    # Stacked language bar segments
    segments = []
    cursor = bar_x
    for i, lang in enumerate(stats["languages"]):
        seg_w = bar_w * (lang["pct"] / 100.0)
        segments.append(
            f'<rect x="{cursor:.1f}" y="{bar_y}" '
            f'width="{seg_w:.1f}" height="{bar_h}" '
            f'fill="{lang["color"]}" opacity="0.85"/>'
        )
        cursor += seg_w

    # Legend below bar
    legend_parts = []
    legend_x = bar_x
    for lang in stats["languages"]:
        svg, legend_x = _legend_segment(lang, legend_x)
        legend_parts.append(svg)

    segments_svg = "\n  ".join(segments)
    legend_svg = "\n  ".join(legend_parts)
    today = datetime.datetime.utcnow().strftime("%Y-%m-%d")
    header = f"GITHUB ACTIVITY · LAST 12 MONTHS · UPDATED {today.upper()}"

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 240" width="900" height="240" role="img" aria-label="GitHub stats">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#0d0e10"/>
      <stop offset="100%" stop-color="#13151a"/>
    </linearGradient>
    <linearGradient id="acc" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#c89858"/>
      <stop offset="100%" stop-color="#b88848"/>
    </linearGradient>
    <pattern id="grid" width="20" height="20" patternUnits="userSpaceOnUse">
      <path d="M 20 0 L 0 0 0 20" fill="none" stroke="#1f2126" stroke-width="0.5"/>
    </pattern>
  </defs>

  <rect width="900" height="240" fill="url(#bg)" rx="6"/>
  <rect width="900" height="240" fill="url(#grid)" opacity="0.4"/>

  <text x="30" y="32" font-family="JetBrains Mono, monospace" font-size="10" fill="#5a5249" letter-spacing="2">
    {header}
  </text>
  <line x1="30" y1="42" x2="870" y2="42" stroke="#2a2d34" stroke-width="1"/>

  <g font-family="JetBrains Mono, monospace">
    <g transform="translate(30, 60)">
      <text x="0" y="14" font-size="9" fill="#5a5249" letter-spacing="1.5">COMMITS</text>
      <text x="0" y="48" font-size="32" fill="url(#acc)" font-weight="500">{stats['commits']:,}</text>
    </g>
    <g transform="translate(240, 60)">
      <text x="0" y="14" font-size="9" fill="#5a5249" letter-spacing="1.5">PULL REQUESTS</text>
      <text x="0" y="48" font-size="32" fill="url(#acc)" font-weight="500">{stats['prs']:,}</text>
    </g>
    <g transform="translate(450, 60)">
      <text x="0" y="14" font-size="9" fill="#5a5249" letter-spacing="1.5">STARS EARNED</text>
      <text x="0" y="48" font-size="32" fill="url(#acc)" font-weight="500">{stats['stars']:,}</text>
    </g>
    <g transform="translate(660, 60)">
      <text x="0" y="14" font-size="9" fill="#5a5249" letter-spacing="1.5">REPOSITORIES</text>
      <text x="0" y="48" font-size="32" fill="url(#acc)" font-weight="500">{stats['repos']:,}</text>
    </g>
  </g>

  <g font-family="JetBrains Mono, monospace" font-size="11" fill="#8b8275">
    <text x="30"  y="135"><tspan fill="#5a5249">issues opened</tspan><tspan dx="8" fill="#e8dcc8">{stats['issues']:,}</tspan></text>
    <text x="240" y="135"><tspan fill="#5a5249">PRs reviewed</tspan><tspan dx="8" fill="#e8dcc8">{stats['reviews']:,}</tspan></text>
    <text x="450" y="135"><tspan fill="#5a5249">total contributions</tspan><tspan dx="8" fill="#e8dcc8">{stats['total_contribs']:,}</tspan></text>
  </g>

  <text x="30" y="165" font-family="JetBrains Mono, monospace" font-size="10" fill="#5a5249" letter-spacing="1.5">
    LANGUAGES
  </text>

  <rect x="{bar_x}" y="{bar_y}" width="{bar_w}" height="{bar_h}" rx="3" fill="#1a1c20" stroke="#2a2d34" stroke-width="0.5"/>
  {segments_svg}

  {legend_svg}

  <rect x="897" y="20" width="3" height="200" fill="url(#acc)" opacity="0.3"/>
</svg>
"""


def render_repo_stats(stats: dict[str, Any], owner: str = "", repo: str = "") -> str:
    """Generate SVG for repo-level stats."""

    bar_x = 80
    bar_y = 155
    bar_w = 740
    bar_h = 8

    segments = []
    cursor = bar_x
    for lang in stats["languages"]:
        seg_w = bar_w * (lang["pct"] / 100.0)
        segments.append(
            f'<rect x="{cursor:.1f}" y="{bar_y}" '
            f'width="{seg_w:.1f}" height="{bar_h}" '
            f'fill="{lang["color"]}" opacity="0.85"/>'
        )
        cursor += seg_w

    legend_parts = []
    legend_x = bar_x
    for lang in stats["languages"]:
        # Adjusted Y for repo card (different layout)
        svg = (
            f'<circle cx="{legend_x + 5}" cy="180" r="3.5" '
            f'fill="{lang["color"]}" opacity="0.85"/>'
            f'<text x="{legend_x + 15}" y="184" font-family="JetBrains Mono, monospace" '
            f'font-size="10" fill="#a8a098">'
            f'{lang["name"]} '
            f'<tspan fill="#5a5249">{lang["pct"]:.0f}%</tspan>'
            f'</text>'
        )
        legend_parts.append(svg)
        legend_x += len(lang["name"]) * 7 + 50

    segments_svg = "\n  ".join(segments)
    legend_svg = "\n  ".join(legend_parts)
    title = f"{owner}/{repo}" if owner and repo else "repo stats"
    today = datetime.datetime.utcnow().strftime("%Y-%m-%d")

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 220" width="900" height="220" role="img" aria-label="{title} stats">
  <defs>
    <linearGradient id="bg-r" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#0d0e10"/>
      <stop offset="100%" stop-color="#13151a"/>
    </linearGradient>
    <linearGradient id="acc-r" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#c89858"/>
      <stop offset="100%" stop-color="#b88848"/>
    </linearGradient>
    <pattern id="grid-r" width="20" height="20" patternUnits="userSpaceOnUse">
      <path d="M 20 0 L 0 0 0 20" fill="none" stroke="#1f2126" stroke-width="0.5"/>
    </pattern>
  </defs>

  <rect width="900" height="220" fill="url(#bg-r)" rx="6"/>
  <rect width="900" height="220" fill="url(#grid-r)" opacity="0.4"/>

  <text x="30" y="32" font-family="JetBrains Mono, monospace" font-size="10" fill="#5a5249" letter-spacing="2">
    REPOSITORY · {title.upper()} · UPDATED {today.upper()}
  </text>
  <line x1="30" y1="42" x2="870" y2="42" stroke="#2a2d34" stroke-width="1"/>

  <g font-family="JetBrains Mono, monospace">
    <g transform="translate(30, 60)">
      <text x="0" y="14" font-size="9" fill="#5a5249" letter-spacing="1.5">STARS</text>
      <text x="0" y="48" font-size="32" fill="url(#acc-r)" font-weight="500">{stats['stars']:,}</text>
    </g>
    <g transform="translate(240, 60)">
      <text x="0" y="14" font-size="9" fill="#5a5249" letter-spacing="1.5">FORKS</text>
      <text x="0" y="48" font-size="32" fill="url(#acc-r)" font-weight="500">{stats['forks']:,}</text>
    </g>
    <g transform="translate(450, 60)">
      <text x="0" y="14" font-size="9" fill="#5a5249" letter-spacing="1.5">OPEN ISSUES</text>
      <text x="0" y="48" font-size="32" fill="url(#acc-r)" font-weight="500">{stats['open_issues']:,}</text>
    </g>
    <g transform="translate(660, 60)">
      <text x="0" y="14" font-size="9" fill="#5a5249" letter-spacing="1.5">OPEN PRS</text>
      <text x="0" y="48" font-size="32" fill="url(#acc-r)" font-weight="500">{stats['open_prs']:,}</text>
    </g>
  </g>

  <text x="30" y="145" font-family="JetBrains Mono, monospace" font-size="10" fill="#5a5249" letter-spacing="1.5">
    LANGUAGES
  </text>

  <rect x="{bar_x}" y="{bar_y}" width="{bar_w}" height="{bar_h}" rx="3" fill="#1a1c20" stroke="#2a2d34" stroke-width="0.5"/>
  {segments_svg}

  {legend_svg}

  <rect x="897" y="20" width="3" height="180" fill="url(#acc-r)" opacity="0.3"/>
</svg>
"""