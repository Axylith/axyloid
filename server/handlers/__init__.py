"""Event handlers for webhook dispatches.

Each handler is an async function that receives the parsed webhook payload
and an installation token. Returns None on success, raises on error.

Dispatch table in server/main.py maps event types to handlers.
"""