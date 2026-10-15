from __future__ import annotations

from dataclasses import dataclass
from typing import Any

try:
    import numpy as np
except ImportError:  # pragma: no cover
    np = None

@dataclass(frozen=True)
class FrameObservation:
    timestamp_seconds: float
    mean_luminance: float
    sharpness: float
    texture: float
    mean_absolute_difference: float | None

def observe_frame(frame: Any, timestamp_seconds: float, previous: Any = None) -> FrameObservation:
    if np is None:
        raise RuntimeError("numpy is required for frame health observations")
    image = np.asarray(frame, dtype=float)
    gray = image.mean(axis=2) if image.ndim == 3 else image
    gy, gx = np.gradient(gray)
    sharpness = float(np.var(gx) + np.var(gy))
    texture = float(np.mean(np.abs(gx)) + np.mean(np.abs(gy)))
    previous_gray = None if previous is None else (np.asarray(previous, dtype=float).mean(axis=2) if np.asarray(previous).ndim == 3 else np.asarray(previous, dtype=float))
    mad = None if previous_gray is None or previous_gray.shape != gray.shape else float(np.mean(np.abs(gray - previous_gray)))
    return FrameObservation(timestamp_seconds, float(np.mean(gray)), sharpness, texture, mad)
