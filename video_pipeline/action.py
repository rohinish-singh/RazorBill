"""Sliding-window action adapter; action labels remain uncalibrated review cues."""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Protocol


def bgr_frames_to_rgb(frames):
    """Copy OpenCV BGR frames into the RGB order expected by VideoMAE processors."""
    return [frame[:, :, ::-1].copy() for frame in frames]


def torch_device(device: str | None, cuda_available: bool) -> str:
    """Translate the CLI's YOLO-style numeric device into a torch device."""
    if device is None:
        return "cuda:0" if cuda_available else "cpu"
    value = str(device)
    return f"cuda:{value}" if value.isdigit() and cuda_available else value


@dataclass(frozen=True)
class ActionObservation:
    label: str
    score: float
    start_seconds: float
    end_seconds: float
    class_scores: dict[str, float]
    model_id: str


@dataclass(frozen=True)
class ActionPrediction:
    label: str
    score: float
    class_scores: dict[str, float]
    model_id: str


class ActionModel(Protocol):
    def predict(self, frames) -> ActionPrediction | tuple[str, float]: ...


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
        self.device = torch_device(device, torch.cuda.is_available())
        self.model.to(self.device).eval()

    def predict(self, frames) -> tuple[str, float]:
        if not frames:
            raise ValueError("VideoMAE requires a non-empty frame window")
        rgb_frames = bgr_frames_to_rgb(frames)
        inputs = self.processor(rgb_frames, return_tensors="pt")
        inputs = {name: value.to(self.device) for name, value in inputs.items()}
        with self.torch.inference_mode():
            logits = self.model(**inputs).logits[0]
            score, index = self.torch.softmax(logits, dim=0).max(dim=0)
        return self.model.config.id2label[int(index)], float(score)


class VideoMAEViolenceModel:
    """Task-specific binary VideoMAE model with an explicit audited class map.

    The selected checkpoint does not publish ``id2label`` in config.json, so
    this adapter rejects any mapping other than the documented index mapping.
    Its scores are raw softmax outputs and must remain review evidence.
    """
    MODEL_ID = "archit11/videomae-base-finetuned-fight-nofight-subset2"
    CLASS_BY_INDEX = {0: "fight", 1: "no_fight"}

    def __init__(self, model_id: str = MODEL_ID, device: str | None = None):
        try:
            import torch
            from transformers import AutoImageProcessor, AutoModelForVideoClassification
        except ImportError as error:
            raise RuntimeError("Install optional action inference dependencies: pip install -e '.[temporal-action]'") from error
        self.torch = torch; self.model_id = model_id
        self.processor = AutoImageProcessor.from_pretrained(model_id)
        self.model, loading_info = AutoModelForVideoClassification.from_pretrained(model_id, output_loading_info=True)
        if any(loading_info[key] for key in ("missing_keys", "unexpected_keys", "mismatched_keys")):
            raise ValueError("temporal checkpoint did not load exactly; refusing unverified inference")
        if self.model.config.num_frames != 16 or self.model.config.image_size != 224 or self.model.config.num_labels != 2:
            raise ValueError("selected temporal checkpoint does not match the audited 16-frame, 224px binary configuration")
        labels = {int(index): str(label).lower().replace(" ", "_") for index, label in self.model.config.id2label.items()}
        if labels != self.CLASS_BY_INDEX:
            raise ValueError(f"temporal checkpoint class mapping is not the audited mapping: {labels}")
        self.device = torch_device(device, torch.cuda.is_available())
        self.model.to(self.device).eval()

    def predict(self, frames) -> ActionPrediction:
        if len(frames) != self.model.config.num_frames:
            raise ValueError(f"{self.model_id} requires exactly {self.model.config.num_frames} frames")
        rgb_frames = bgr_frames_to_rgb(frames)
        inputs = self.processor(rgb_frames, return_tensors="pt")
        inputs = {name: value.to(self.device) for name, value in inputs.items()}
        with self.torch.inference_mode():
            probabilities = self.torch.softmax(self.model(**inputs).logits[0], dim=0).detach().float().cpu().tolist()
        scores = {self.CLASS_BY_INDEX[index]: float(score) for index, score in enumerate(probabilities)}
        label = max(scores, key=scores.get)
        return ActionPrediction(label, scores[label], scores, self.model_id)


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
        prediction = self.model.predict(list(self._frames))
        # Tuple support preserves the CP9 injected-test-double interface.
        if isinstance(prediction, tuple):
            label, score = prediction; prediction = ActionPrediction(label, float(score), {label: float(score)}, type(self.model).__name__)
        return ActionObservation(prediction.label, prediction.score, self._timestamps[0], self._timestamps[-1],
                                 prediction.class_scores, prediction.model_id)
