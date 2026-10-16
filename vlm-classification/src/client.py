"""Minimal standard-library client for Person 3's incident endpoint."""

from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .classifier import validate_incident


class BackendError(RuntimeError):
    pass


def post_incident(incident: dict, *, base_url: str = "http://127.0.0.1:8000", timeout_seconds: float = 5) -> dict:
    """POST one contract-shaped incident to the documented backend route."""
    validate_incident(incident)
    request = Request(
        base_url.rstrip("/") + "/api/incidents",
        data=json.dumps(incident).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            body = response.read().decode("utf-8")
    except HTTPError as exc:
        raise BackendError(f"backend returned HTTP {exc.code}") from exc
    except (URLError, TimeoutError, OSError) as exc:
        raise BackendError(f"backend is unavailable or timed out: {exc}") from exc
    try:
        parsed = json.loads(body) if body else {}
    except json.JSONDecodeError as exc:
        raise BackendError("backend returned invalid JSON") from exc
    if not isinstance(parsed, dict):
        raise BackendError("backend response must be a JSON object")
    return parsed
