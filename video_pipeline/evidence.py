"""Bounded local evidence buffering; evidence stays outside shared packets."""
from __future__ import annotations

import json
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class _PendingEvidence:
    event_id: str
    start: float
    end: float
    frames: list[tuple[float, object]] = field(default_factory=list)


class EvidenceBuffer:
    def __init__(self, pre_seconds: float, post_seconds: float, fps: float, max_pending: int = 16):
        if pre_seconds < 0 or post_seconds < 0:
            raise ValueError("evidence durations must be non-negative")
        if fps <= 0:
            raise ValueError("evidence fps must be positive")
        self.pre_seconds, self.post_seconds, self.fps, self.max_pending = pre_seconds, post_seconds, fps, max_pending
        self._frames: deque[tuple[float, object]] = deque(maxlen=max(1, int((pre_seconds + 1) * max(fps, 1))))
        self._pending: list[_PendingEvidence] = []

    def add(self, timestamp_seconds: float, frame) -> None:
        copied = frame.copy(); self._frames.append((timestamp_seconds, copied))
        for pending in self._pending:
            if timestamp_seconds <= pending.end:
                pending.frames.append((timestamp_seconds, copied))

    def register(self, event_id: str, timestamp_seconds: float) -> None:
        if len(self._pending) >= self.max_pending:
            return
        start, end = timestamp_seconds - self.pre_seconds, timestamp_seconds + self.post_seconds
        frames = [(timestamp, frame) for timestamp, frame in self._frames if timestamp >= start]
        self._pending.append(_PendingEvidence(event_id, start, end, frames))

    def write(self, output_root: Path, relative_root: Path, cv2) -> list[dict]:
        output_root.mkdir(parents=True, exist_ok=True); index = []
        for pending in self._pending:
            if not pending.frames:
                continue
            path = output_root / f"{pending.event_id}.mp4"
            height, width = pending.frames[0][1].shape[:2]
            writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), self.fps, (width, height))
            if not writer.isOpened():
                continue
            try:
                for _, frame in pending.frames:
                    writer.write(frame)
            finally:
                writer.release()
            index.append({"event_id": pending.event_id, "clip_path": str(relative_root / path.name),
                          "start_seconds": pending.start, "end_seconds": pending.end, "output_fps": self.fps,
                          "frame_count": len(pending.frames)})
        if index:
            with (output_root / "index.jsonl").open("w", encoding="utf-8") as handle:
                for item in index:
                    handle.write(json.dumps(item) + "\n")
        return index
