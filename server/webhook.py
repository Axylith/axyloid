"""Webhook signature verification and event parsing."""

import hashlib
import hmac
import json
from typing import Any

from fastapi import HTTPException, Request

from server.config import get_settings


async def verify_and_parse(request: Request) -> tuple[str, dict[str, Any]]:
    """Verify the webhook signature and return (event_type, payload).

    GitHub signs each webhook delivery with HMAC-SHA256 using our shared
    secret. We must verify before processing anything; an unverified request
    can be forged.

    Returns:
        (event_type, payload) — e.g. ("push", {...full webhook body...})

    Raises:
        HTTPException(400) if headers are missing
        HTTPException(401) if signature doesn't match
    """
    settings = get_settings()

    # Required headers per GitHub webhook spec
    sig_header = request.headers.get("X-Hub-Signature-256")
    event_type = request.headers.get("X-GitHub-Event")
    delivery_id = request.headers.get("X-GitHub-Delivery")

    if not sig_header or not event_type:
        raise HTTPException(
            status_code=400,
            detail="Missing required webhook headers",
        )

    if not sig_header.startswith("sha256="):
        raise HTTPException(
            status_code=400,
            detail="Invalid signature format",
        )

    body = await request.body()

    # Compute expected signature
    expected_sig = "sha256=" + hmac.new(
        settings.github_webhook_secret.encode(),
        body,
        hashlib.sha256,
    ).hexdigest()

    # Constant-time comparison to prevent timing attacks
    if not hmac.compare_digest(sig_header, expected_sig):
        raise HTTPException(
            status_code=401,
            detail="Signature verification failed",
        )

    try:
        payload = json.loads(body)
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid JSON payload: {e}",
        ) from e

    return event_type, payload