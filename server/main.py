"""FastAPI app entry point.

Routes:
  POST /webhook  — receive GitHub webhook events
  GET  /health   — health check for monitoring and the status badge
  GET  /         — landing page (minimal)
"""

import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, PlainTextResponse

from server.auth import get_app_info, get_installation_token
from server.config import get_settings
from server.handlers.push import handle_push
from server.webhook import verify_and_parse

logger = logging.getLogger("axyloid")


# Dispatch table: webhook event type → handler function
# Each handler signature: async def(payload: dict, token: str) -> None
HANDLERS = {
    "push": handle_push,
    # Future: pull_request, installation, etc.
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown hooks."""
    settings = get_settings()
    logging.basicConfig(
        level=settings.log_level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    logger.info(f"axyloid starting up, app_id={settings.github_app_id}")

    # Verify the App credentials work at startup
    try:
        info = await get_app_info()
        logger.info(f"authenticated as GitHub App: {info['slug']}")
    except Exception as e:
        logger.error(f"failed to authenticate at startup: {e}")
        # Don't fail startup — Cloud Run health checks need us to come up.
        # But this is logged so we'll see it in monitoring.

    yield
    logger.info("axyloid shutting down")


app = FastAPI(
    title="axyloid",
    description="Maintainer automation toolkit for the Axylith ecosystem",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/", response_class=PlainTextResponse)
async def root() -> str:
    """Minimal landing page."""
    return "axyloid · https://github.com/Axylith/axyloid"


@app.get("/health")
async def health() -> dict[str, Any]:
    """Health check endpoint.

    Returns 200 with basic status. Used by:
      - Cloud Run health probes
      - The status-badge workflow in this repo
      - External uptime monitoring
    """
    return {
        "status": "ok",
        "service": "axyloid",
        "version": "0.1.0",
    }


@app.post("/webhook")
async def webhook(request: Request) -> JSONResponse:
    """Receive and dispatch GitHub webhook events."""
    event_type, payload = await verify_and_parse(request)

    handler = HANDLERS.get(event_type)
    if not handler:
        logger.info(f"ignoring unhandled event type: {event_type}")
        return JSONResponse({"status": "ignored", "event": event_type})

    # Get an installation token for this event
    installation_id = payload.get("installation", {}).get("id")
    if not installation_id:
        logger.error(f"no installation id in {event_type} payload")
        raise HTTPException(status_code=400, detail="Missing installation id")

    try:
        token = await get_installation_token(installation_id)
    except Exception as e:
        logger.error(f"failed to get installation token: {e}")
        raise HTTPException(status_code=500, detail="Auth failed") from e

    try:
        await handler(payload, token)
    except Exception as e:
        logger.exception(f"handler {event_type} failed")
        raise HTTPException(status_code=500, detail=str(e)) from e

    return JSONResponse({"status": "ok", "event": event_type})