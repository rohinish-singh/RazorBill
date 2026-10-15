"""Sliding-window action adapter; action labels remain uncalibrated review cues."""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ActionObservation:
    label: str
    score: float
    start_seconds: float
    end_seconds: float


class ActionModel(Protocol):
    def predict(self, frames) -> tuple[str, float]: ...


class VideoMAEActionModel:
    """Optional local VideoMAE Kinetics adapter.

    Returned scores are raw softmax outputs, not calibrated incident confidence.
    The caller must keep generic Kinetics labels as review evidence.
    """
    def __init__(self, model_id: str = "MCG-NJU/videomae-base-finetuned-kinetics", device: str | None = None):
        try:
            import torch
            from transformers import AutoImageProcessor, AutoModelForVideoClassification
        except ImportError as error:
            raise RuntimeError("Install optional action inference dependencies: pip install transformers") from error
        self.torch = torch; self.processor = AutoImageProcessor.from_pretrained(model_id)
        self.model = AutoModelForVideoClassification.from_pretrained(model_id)
        self.device = device or ("cuda:0" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device).eval()

    def predict(self, frames) -> tuple[str, float]:
        if not frames:
            raise ValueError("VideoMAE requires a non-empty frame window")
        rgb_frames = [frame[:, :, ::-1] for frame in frames]
        inputs = self.processor(rgb_frames, return_tensors="pt")
        inputs = {name: value.to(self.device) for name, value in inputs.items()}
        with self.torch.inference_mode():
            logits = self.model(**inputs).logits[0]
            score, index = self.torch.softmax(logits, dim=0).max(dim=0)
        return self.model.config.id2label[int(index)], float(score)


class SlidingWindowActionAdapter:
    def __init__(self, model: ActionModel, window_frames: int = 16, stride_frames: int = 8):
        if window_frames < 2 or stride_frames < 1:
            raise ValueError("window_frames must be >= 2 and stride_frames must be >= 1")
        self.model, self.window_frames, self.stride_frames = model, window_frames, stride_frames
        self._frames = deque(maxlen=window_frames); self._timestamps = deque(maxlen=window_frames); self._seen = 0

    def observe(self, timestamp_seconds: float, frame) -> ActionObservation | None:
        self._frames.append(frame.copy()); self._timestamps.append(timestamp_seconds); self._seen += 1
        if len(self._frames) < self.window_frames or (self._seen - self.window_frames) % self.stride_frames:
            return None
        label, score = self.model.predict(list(self._frames))
        return ActionObservation(label, float(score), self._timestamps[0], self._timestamps[-1])
