"""GitHub App authentication.

Two-step token flow:
  1. Sign a JWT with the App's private key. Valid 10 minutes.
  2. Exchange JWT for an installation token (per-installation, valid 1 hour).
  3. Use the installation token for API calls.

The installation token is what the bot uses to clone repos and commit results.
"""

import time
from typing import Any

import httpx
import jwt

from server.config import get_settings


def generate_app_jwt() -> str:
    """Generate a short-lived JWT signed with the App's private key.

    Used to authenticate as the App itself (not as an installation).
    Required to exchange for installation tokens.
    """
    settings = get_settings()
    now = int(time.time())

    payload = {
        "iat": now - 60,         # backdate 60s to tolerate clock skew
        "exp": now + 600,         # 10 minutes (GitHub max)
        "iss": settings.github_app_id,
    }

    return jwt.encode(payload, settings.private_key, algorithm="RS256")


async def get_installation_token(installation_id: int) -> str:
    """Exchange the App JWT for an installation access token.

    Installation tokens are valid for 1 hour. We don't cache here — the
    caller should cache per installation if making multiple calls back-to-back.
    """
    app_jwt = generate_app_jwt()
    headers = {
        "Authorization": f"Bearer {app_jwt}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    url = f"https://api.github.com/app/installations/{installation_id}/access_tokens"

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(url, headers=headers)
        response.raise_for_status()
        return response.json()["token"]


async def get_app_info() -> dict[str, Any]:
    """Get info about the registered GitHub App. Useful for health checks."""
    app_jwt = generate_app_jwt()
    headers = {
        "Authorization": f"Bearer {app_jwt}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get("https://api.github.com/app", headers=headers)
        response.raise_for_status()
        return response.json()