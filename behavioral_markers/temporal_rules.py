from __future__ import annotations

def elapsed(start: float | None, now: float) -> float:
    return 0.0 if start is None else max(0.0, now - start)

def ready(start: float | None, now: float, seconds: float) -> bool:
    return start is not None and elapsed(start, now) >= seconds
