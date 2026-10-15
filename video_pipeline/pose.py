"""Optional pose inference and conservative association to Person 1 tracks."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from behavioral_markers.schemas import PoseCue, Track


@dataclass(frozen=True)
class PoseObservation:
    bbox_xyxy: tuple[float, float, float, float]
    keypoints_xy_conf: tuple[tuple[float, float, float], ...]


class PoseEstimator(Protocol):
    def poses(self, frame) -> list[PoseObservation]: ...


class UltralyticsPoseEstimator:
    """YOLO11 pose adapter; model weights are local-only and intentionally lazy."""
    def __init__(self, model: str = "yolo11n-pose.pt", confidence: float = 0.30, device: str | None = None):
        try:
            from ultralytics import YOLO
        except ImportError as error:
            raise RuntimeError("Install the optional Person 1 dependency: pip install -e '.[person1]'") from error
        self.model, self.confidence, self.device = YOLO(model), confidence, device

    def poses(self, frame) -> list[PoseObservation]:
        result = self.model.predict(frame, conf=self.confidence, device=self.device, verbose=False)[0]
        if result.boxes is None or result.keypoints is None:
            return []
        boxes = result.boxes.xyxy.cpu().tolist()
        points = result.keypoints.data.cpu().tolist()
        return [PoseObservation(tuple(map(float, box)), tuple(tuple(map(float, point)) for point in pose))
                for box, pose in zip(boxes, points)]


def associate_pose_cues(tracks: list[Track], poses: list[PoseObservation], min_iou: float = 0.30,
                         min_keypoint_confidence: float = 0.30, min_keypoints: int = 6) -> list[PoseCue]:
    """Return one-to-one spatial matches; ambiguous/low-quality poses are rejected."""
    pairs = sorted(((_iou(track.bbox_xyxy, pose.bbox_xyxy), index, pose_index)
                    for index, track in enumerate(tracks) for pose_index, pose in enumerate(poses)), reverse=True)
    used_tracks, used_poses, cues = set(), set(), []
    for overlap, track_index, pose_index in pairs:
        if overlap < min_iou or track_index in used_tracks or pose_index in used_poses:
            continue
        pose = poses[pose_index]
        visible = [point for point in pose.keypoints_xy_conf if point[2] >= min_keypoint_confidence]
        if len(visible) < min_keypoints:
            continue
        min_x, max_x = min(point[0] for point in visible), max(point[0] for point in visible)
        min_y, max_y = min(point[1] for point in visible), max(point[1] for point in visible)
        cues.append(PoseCue(tracks[track_index].track_id, (max_x - min_x) / max(max_y - min_y, 1e-6), len(visible)))
        used_tracks.add(track_index); used_poses.add(pose_index)
    return cues


def _iou(first: tuple[float, float, float, float], second: tuple[float, float, float, float]) -> float:
    left, top = max(first[0], second[0]), max(first[1], second[1])
    right, bottom = min(first[2], second[2]), min(first[3], second[3])
    intersection = max(0.0, right - left) * max(0.0, bottom - top)
    if not intersection:
        return 0.0
    first_area = max(0.0, first[2] - first[0]) * max(0.0, first[3] - first[1])
    second_area = max(0.0, second[2] - second[0]) * max(0.0, second[3] - second[1])
    return intersection / max(first_area + second_area - intersection, 1e-6)
