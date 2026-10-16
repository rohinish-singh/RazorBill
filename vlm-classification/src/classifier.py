"""Candidate packet validation and incident classification."""

from __future__ import annotations

import json
import math
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol

from .ollama_adapter import OllamaVisionAdapter

ALLOWED_CATEGORIES = {
    "person_down",
    "fighting",
    "tailgating",
    "crowd_incident",
    "suspicious_activity",
    "other",
    "unknown",
}
OUTPUT_FIELDS = {
    "event_id", "camera_id", "timestamp_seconds", "category", "summary",
    "confidence", "confidence_type", "frame_path", "source", "processing_ms",
    "status", "evidence_notes", "created_at",
}
ALLOWED_SOURCES = {"rule", "vlm", "manual"}
ALLOWED_STATUSES = {"candidate", "classified", "needs_review", "failed"}


def _is_finite_number(value: Any) -> bool:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    try:
        return math.isfinite(value)
    except OverflowError:
        return False


class CandidateError(ValueError):
    """Raised when the candidate packet is missing or has invalid fields."""


class VisionAdapter(Protocol):
    def analyze(self, image_paths: list[Path], prompt: str) -> str: ...


def validate_candidate(candidate: Any) -> dict[str, Any]:
    if not isinstance(candidate, dict):
        raise CandidateError("candidate must be a JSON object")
    for field in (
        "event_id", "camera_id", "video_source_id", "timestamp_seconds", "frame_path",
        "tracks", "trigger", "created_at",
    ):
        if field not in candidate:
            raise CandidateError(f"missing required field: {field}")
    if not isinstance(candidate["event_id"], str) or not candidate["event_id"].strip():
        raise CandidateError("event_id must be a non-empty string")
    if not isinstance(candidate["camera_id"], str) or not candidate["camera_id"].strip():
        raise CandidateError("camera_id must be a non-empty string")
    timestamp = candidate["timestamp_seconds"]
    if isinstance(timestamp, bool) or not isinstance(timestamp, (int, float)):
        raise CandidateError("timestamp_seconds must be a number")
    if not _is_finite_number(timestamp) or timestamp < 0:
        raise CandidateError("timestamp_seconds must be finite and non-negative")
    if not isinstance(candidate["frame_path"], str) or not candidate["frame_path"].strip():
        raise CandidateError("frame_path must be a non-empty string")
    if "frame_paths" in candidate and not isinstance(candidate["frame_paths"], list):
        raise CandidateError("frame_paths must be a list")
    if not isinstance(candidate["video_source_id"], str) or not candidate["video_source_id"].strip():
        raise CandidateError("video_source_id must be a non-empty string")
    if not isinstance(candidate["tracks"], list):
        raise CandidateError("tracks must be a list")
    if not isinstance(candidate["trigger"], str) or not candidate["trigger"].strip():
        raise CandidateError("trigger must be a non-empty string")
    if not isinstance(candidate["created_at"], str):
        raise CandidateError("created_at must be an ISO timestamp string")
    try:
        datetime.fromisoformat(candidate["created_at"].replace("Z", "+00:00"))
    except ValueError as exc:
        raise CandidateError("created_at must be a valid ISO timestamp") from exc
    if "frame_paths" in candidate:
        if not isinstance(candidate["frame_paths"], list):
            raise CandidateError("frame_paths must be a list")
        if any(not isinstance(path, str) or not path.strip() for path in candidate["frame_paths"]):
            raise CandidateError("every frame_paths entry must be a non-empty string")
    for index, track in enumerate(candidate["tracks"]):
        if not isinstance(track, dict):
            raise CandidateError(f"tracks[{index}] must be an object")
        track_id = track.get("track_id")
        valid_track_id = (
            isinstance(track_id, int) and not isinstance(track_id, bool)
        ) or (isinstance(track_id, str) and bool(track_id.strip()))
        if not valid_track_id:
            raise CandidateError(f"tracks[{index}].track_id must be a non-empty string or integer")
        if not isinstance(track.get("class_name"), str) or not track["class_name"].strip():
            raise CandidateError(f"tracks[{index}].class_name must be a non-empty string")
        bbox = track.get("bbox_xyxy")
        if not isinstance(bbox, list) or len(bbox) != 4 or any(not _is_finite_number(value) for value in bbox):
            raise CandidateError(f"tracks[{index}].bbox_xyxy must contain four finite numbers")
    return candidate


def validate_incident(incident: Any) -> dict[str, Any]:
    if not isinstance(incident, dict) or set(incident) != OUTPUT_FIELDS:
        raise ValueError("incident fields do not match the shared output contract")
    if not isinstance(incident["category"], str) or incident["category"] not in ALLOWED_CATEGORIES:
        raise ValueError("incident category is not allowed")
    if (not isinstance(incident["source"], str) or incident["source"] not in ALLOWED_SOURCES
            or not isinstance(incident["status"], str) or incident["status"] not in ALLOWED_STATUSES):
        raise ValueError("incident source or status is not allowed")
    if incident["confidence"] is not None or incident["confidence_type"] != "unavailable":
        raise ValueError("confidence must remain null with unavailable semantics")
    if (isinstance(incident["processing_ms"], bool) or not isinstance(incident["processing_ms"], int)
            or incident["processing_ms"] < 0):
        raise ValueError("processing_ms must be a non-negative integer")
    if not _is_finite_number(incident["timestamp_seconds"]):
        raise ValueError("timestamp_seconds must be numeric")
    if not math.isfinite(incident["timestamp_seconds"]) or incident["timestamp_seconds"] < 0:
        raise ValueError("timestamp_seconds must be finite and non-negative")
    for key in ("event_id", "camera_id", "summary", "frame_path", "evidence_notes", "created_at"):
        if not isinstance(incident[key], str) or not incident[key].strip():
            raise ValueError(f"{key} must be a non-empty string")
    try:
        datetime.fromisoformat(incident["created_at"].replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("created_at must be a valid ISO timestamp") from exc
    return incident


def _select_frames(candidate: dict[str, Any], max_frames: int) -> list[Path]:
    values = ([candidate["frame_path"]] if candidate.get("frame_path") else [])
    values.extend(candidate.get("frame_paths", []))
    seen: set[str] = set()
    selected: list[Path] = []
    for raw in values:
        if not isinstance(raw, str) or not raw:
            continue
        path = Path(raw).expanduser()
        key = str(path.resolve())
        if key in seen:
            continue
        seen.add(key)
        if path.is_file():
            selected.append(path)
        if len(selected) >= max_frames:
            break
    return selected


def _parse_model_result(raw: str) -> dict[str, str] | None:
    if not isinstance(raw, str):
        return None
    text = raw.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:].strip()
    try:
        result = json.loads(text)
    except (ValueError, TypeError):
        left, right = text.find("{"), text.rfind("}")
        if left < 0 or right <= left:
            return None
        try:
            result = json.loads(text[left : right + 1])
        except (ValueError, TypeError):
            return None
    if not isinstance(result, dict):
        return None
    category = result.get("category")
    summary = result.get("summary")
    evidence = result.get("evidence_notes")
    if not isinstance(category, str) or category not in ALLOWED_CATEGORIES:
        return None
    if not all(isinstance(x, str) and x.strip() for x in (summary, evidence)):
        return None
    return {"category": category, "summary": summary.strip(), "evidence_notes": evidence.strip()}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


class StubVisionAdapter:
    """Deterministic adapter for integration when no VLM is available."""

    source = "manual"

    def analyze(self, image_paths: list[Path], prompt: str) -> str:
        del image_paths, prompt
        return json.dumps({
            "category": "unknown",
            "summary": "The frame was received, but the deterministic stub does not classify events.",
            "evidence_notes": "Classification was not performed by a vision model.",
        })


class CandidateClassifier:
    def __init__(self, adapter: VisionAdapter | None = None, *, max_frames: int = 3):
        if max_frames < 1:
            raise ValueError("max_frames must be at least 1")
        self.adapter = adapter or StubVisionAdapter()
        self.max_frames = max_frames

    def classify_candidate(self, candidate: dict[str, Any]) -> dict[str, Any]:
        started = time.monotonic()
        packet = validate_candidate(candidate)

        frames = _select_frames(packet, self.max_frames)
        frame_path = str(frames[0]) if frames else str(packet.get("frame_path") or (packet.get("frame_paths") or [""])[0])
        if not frames:
            return self._failure(packet, "No readable frame was found in the supplied paths.", started, frame_path=frame_path)

        prompt = (
            "Inspect only what is visibly supported by the image(s). Classify into exactly one of: "
            + ", ".join(sorted(ALLOWED_CATEGORIES))
            + '. Do not infer intent. If evidence is unclear, use unknown. Return ONLY a JSON object with '
            'category, summary (one concise sentence), and evidence_notes (visible evidence).'
        )
        try:
            parsed = _parse_model_result(self.adapter.analyze(frames, prompt))
        except Exception as exc:  # adapter failures are converted into explicit records
            return self._failure(packet, f"VLM inference failed: {exc}", started, frame_path=frame_path)
        if parsed is None:
            return self._review(packet, "The VLM response was malformed or contained an unsupported category.", started, frame_path)
        status = "needs_review" if parsed["category"] == "unknown" else "classified"
        return self._record(
            packet, parsed["category"], parsed["summary"], parsed["evidence_notes"],
            frame_path, status, getattr(self.adapter, "source", "vlm"), started,
        )

    def _record(self, packet: dict[str, Any], category: str, summary: str, evidence: str,
                frame_path: str, status: str, source: str, started: float) -> dict[str, Any]:
        result = {
            "event_id": packet["event_id"],
            "camera_id": packet["camera_id"],
            "timestamp_seconds": packet["timestamp_seconds"],
            "category": category,
            "summary": summary,
            "confidence": None,
            "confidence_type": "unavailable",
            "frame_path": frame_path,
            "source": source,
            "processing_ms": max(0, int((time.monotonic() - started) * 1000)),
            "status": status,
            "evidence_notes": evidence,
            "created_at": _now_iso(),
        }
        return validate_incident(result)

    def _failure(self, packet: dict[str, Any], reason: str, started: float, frame_path: str = "") -> dict[str, Any]:
        return self._record(packet, "unknown", "Classification could not be completed.", reason,
                            frame_path, "failed", getattr(self.adapter, "source", "vlm"), started)

    def _review(self, packet: dict[str, Any], reason: str, started: float, frame_path: str) -> dict[str, Any]:
        return self._record(packet, "unknown", "The available evidence did not support a reliable classification.",
                            reason, frame_path, "needs_review", "vlm", started)


def create_ollama_classifier(*, base_url: str = "http://127.0.0.1:11434", model: str = "moondream",
                             timeout_seconds: float = 60, max_frames: int = 3,
                             max_total_image_bytes: int = 16 * 1024 * 1024) -> CandidateClassifier:
    return CandidateClassifier(
        OllamaVisionAdapter(base_url=base_url, model=model, timeout_seconds=timeout_seconds,
                            max_total_image_bytes=max_total_image_bytes),
        max_frames=max_frames,
    )
