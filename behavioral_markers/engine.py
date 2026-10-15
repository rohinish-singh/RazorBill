from __future__ import annotations

from collections import defaultdict
from math import hypot
from .camera_health import FrameObservation
from .schemas import CameraConfig, MarkerEvent, ObjectFlag, Track
from .temporal_rules import ready
from .zone_rules import tracks_in_zone

class MarkerEngine:
    """Single-camera state machine. Callers own frame queues and backpressure."""
    def __init__(self, config: CameraConfig):
        self.config = config; self._inside = set(); self._entered = {}; self._observations = defaultdict(int)
        self._crowd_since = {}; self._health_since = {}; self._last_alert = {}; self._active_alerts = set(); self._previous_luminance = None
        self._incident_since = {}; self._previous_centres = {}

    def process_tracks(self, timestamp_seconds: float, tracks: list[Track]) -> list[MarkerEvent]:
        events = []
        for zone in self.config.zones:
            members = tracks_in_zone(tracks, zone); current = {(str(track.track_id), zone.zone_id) for track in members}
            for key in current:
                if key not in self._inside:
                    self._entered[key] = timestamp_seconds; self._observations[key] = 0
                    if zone.restricted: events += self._emit("restricted_zone_entry", "suspicious_activity", timestamp_seconds, [next(t for t in members if str(t.track_id) == key[0])], {"zone_id": zone.zone_id, "footpoint": next(t for t in members if str(t.track_id) == key[0]).footpoint}, zone.cooldown_seconds)
                self._observations[key] += 1
                if self._observations[key] >= zone.min_observations and ready(self._entered.get(key), timestamp_seconds, zone.loiter_seconds):
                    events += self._emit("loitering", "suspicious_activity", timestamp_seconds, [next(t for t in members if str(t.track_id) == key[0])], {"zone_id": zone.zone_id, "observed_dwell_seconds": timestamp_seconds - self._entered[key]}, zone.cooldown_seconds)
            for key in list(self._inside - current):
                if key[1] == zone.zone_id:
                    self._entered.pop(key, None); self._observations.pop(key, None)
                    self._reset_alert(f"restricted_zone_entry:{key[0]}"); self._reset_alert(f"loitering:{key[0]}")
            self._inside = (self._inside - {key for key in self._inside if key[1] == zone.zone_id}) | current
            crowd_key = f"crowd:{zone.zone_id}"; count = len(members)
            if count >= zone.crowd_threshold:
                self._crowd_since[crowd_key] = self._crowd_since.get(crowd_key) if self._crowd_since.get(crowd_key) is not None else timestamp_seconds
            else:
                self._crowd_since[crowd_key] = None
            if count < zone.crowd_threshold:
                self._reset_alert(f"crowd_gathering:{zone.zone_id}")
            if count >= zone.crowd_threshold and ready(self._crowd_since[crowd_key], timestamp_seconds, zone.crowd_persist_seconds):
                events += self._emit("crowd_gathering", "crowd_incident", timestamp_seconds, members, {"zone_id": zone.zone_id, "distinct_person_count": count, "persist_seconds": timestamp_seconds - self._crowd_since[crowd_key]}, zone.cooldown_seconds, f"crowd_gathering:{zone.zone_id}")
        return events

    def process_frame_observation(self, observation: FrameObservation) -> list[MarkerEvent]:
        now = observation.timestamp_seconds; events = []
        abrupt_dark = self._previous_luminance is not None and self._previous_luminance - observation.mean_luminance >= self.config.darkness_drop
        dark = observation.mean_luminance <= self.config.darkness_mean_threshold
        events += self._health("camera_dark", dark, now, {"mean_luminance": observation.mean_luminance, "abrupt_transition": abrupt_dark})
        obstructed = observation.sharpness <= self.config.obstruction_sharpness_threshold and observation.texture <= self.config.obstruction_texture_threshold
        events += self._health("camera_obstruction_candidate", obstructed, now, {"sharpness": observation.sharpness, "texture": observation.texture, "caveat": "autofocus, weather, or lighting may explain this"})
        frozen = observation.mean_absolute_difference is not None and observation.mean_absolute_difference <= self.config.freeze_mad_threshold
        events += self._health("frozen_feed_candidate", frozen, now, {"mean_absolute_difference": observation.mean_absolute_difference, "caveat": "a static scene is not proof of feed failure"}, self.config.freeze_persist_seconds)
        self._previous_luminance = observation.mean_luminance
        return events

    def process_incidents(self, timestamp_seconds: float, tracks: list[Track], object_flags: list[ObjectFlag] | None = None) -> list[MarkerEvent]:
        """Emit conservative review candidates from temporal track cues and optional object flags.

        This does not classify an incident. Weapon labels are accepted only from a
        separately supplied specialized detector; the built-in COCO person detector
        never invents them.
        """
        settings = self.config.incident
        if not settings.enabled:
            return []
        events = []
        down = {str(track.track_id): track for track in tracks if self._aspect_ratio(track) >= settings.person_down_aspect_ratio}
        events += self._sustained_incident("person_down_candidate", "person_down", timestamp_seconds, down,
                                           settings.person_down_persist_seconds,
                                           lambda item: {"track_id": item.track_id, "bbox_aspect_ratio": self._aspect_ratio(item), "caveat": "bounding-box posture cue; review required"})

        velocities = self._track_velocities(timestamp_seconds, tracks)
        pairs = {}
        for index, first in enumerate(tracks):
            for second in tracks[index + 1:]:
                pair_id = ",".join(sorted((str(first.track_id), str(second.track_id))))
                distance = hypot(first.centre[0] - second.centre[0], first.centre[1] - second.centre[1])
                motion = max(velocities.get(str(first.track_id), 0.0), velocities.get(str(second.track_id), 0.0))
                if distance <= settings.fighting_pair_distance and motion >= settings.fighting_motion_pixels_per_second:
                    pairs[pair_id] = (first, second, distance, motion)
        events += self._sustained_incident("fighting_candidate", "fighting", timestamp_seconds, pairs,
                                           settings.fighting_persist_seconds,
                                           lambda item: {"track_ids": [item[0].track_id, item[1].track_id], "centre_distance": item[2], "max_motion_pixels_per_second": item[3], "caveat": "proximity/motion cue; not proof of fighting"},
                                           lambda item: [item[0], item[1]])

        flags = [flag for flag in object_flags or [] if flag.confidence >= settings.object_confidence_threshold]
        for label, marker in (("knife", "weapon_knife_candidate"), ("firearm", "weapon_firearm_candidate")):
            matching = {str(index): flag for index, flag in enumerate(flags) if flag.label.lower() == label}
            events += self._sustained_incident(marker, "other", timestamp_seconds, matching, 0.0,
                                               lambda flag: {"object_label": flag.label, "object_confidence": flag.confidence, "object_bbox_xyxy": flag.bbox_xyxy, "caveat": "specialized detector flag; human review required"},
                                               lambda flag: self._associated_tracks(flag, tracks))
        return events

    def source_read_failed(self, timestamp_seconds: float, reason: str) -> list[MarkerEvent]:
        return self._emit("source_read_failure", "other", timestamp_seconds, [], {"reason": reason}, 0)

    def _sustained_incident(self, marker: str, category: str, now: float, items: dict, persistence: float, evidence, event_tracks=None) -> list[MarkerEvent]:
        active_keys = {f"{marker}:{item_id}" for item_id in items}
        prefix = f"{marker}:"
        for key in [key for key in self._incident_since if key.startswith(prefix) and key not in active_keys]:
            self._incident_since.pop(key, None); self._reset_alert(key)
        events = []
        for item_id, item in items.items():
            key = f"{marker}:{item_id}"
            if key not in self._incident_since:
                self._incident_since[key] = now
            if ready(self._incident_since[key], now, persistence):
                tracks = event_tracks(item) if event_tracks else [item]
                details = evidence(item) | {"persist_seconds": now - self._incident_since[key]}
                events += self._emit(marker, category, now, tracks, details, self.config.incident.cooldown_seconds, key)
        return events

    def _track_velocities(self, now: float, tracks: list[Track]) -> dict[str, float]:
        velocities = {}
        current_ids = set()
        for track in tracks:
            identifier = str(track.track_id); current_ids.add(identifier); previous = self._previous_centres.get(identifier)
            if previous is not None and now > previous[0]:
                velocities[identifier] = hypot(track.centre[0] - previous[1], track.centre[1] - previous[2]) / (now - previous[0])
            self._previous_centres[identifier] = (now, *track.centre)
        for identifier in list(self._previous_centres):
            if identifier not in current_ids:
                self._previous_centres.pop(identifier, None)
        return velocities

    @staticmethod
    def _aspect_ratio(track: Track) -> float:
        x1, y1, x2, y2 = track.bbox_xyxy
        return (x2 - x1) / max(y2 - y1, 1e-6)

    @staticmethod
    def _associated_tracks(flag: ObjectFlag, tracks: list[Track]) -> list[Track]:
        x1, y1, x2, y2 = flag.bbox_xyxy
        return [track for track in tracks if x1 <= track.centre[0] <= x2 and y1 <= track.centre[1] <= y2]

    def _health(self, marker: str, active: bool, now: float, evidence: dict, persistence: float | None = None) -> list[MarkerEvent]:
        if active:
            if self._health_since.get(marker) is None:
                self._health_since[marker] = now
        else:
            self._health_since[marker] = None
            self._reset_alert(marker)
        if active and ready(self._health_since[marker], now, persistence if persistence is not None else self.config.health_persist_seconds):
            evidence = evidence | {"persist_seconds": now - self._health_since[marker]}
            return self._emit(marker, "other", now, [], evidence, self.config.health_persist_seconds, marker)
        return []

    def _emit(self, marker: str, category: str, now: float, tracks: list[Track], evidence: dict, cooldown: float, dedupe_key: str | None = None) -> list[MarkerEvent]:
        key = dedupe_key or marker + ":" + ",".join(sorted(str(track.track_id) for track in tracks))
        # One sustained condition should create one candidate. A reset is required
        # before the same condition is eligible again, and cooldown still applies.
        if key in self._active_alerts or now - self._last_alert.get(key, float("-inf")) < cooldown: return []
        self._last_alert[key] = now; self._active_alerts.add(key)
        event_id = f"marker_{self.config.camera_id}_{marker}_{int(now * 1000)}"
        return [MarkerEvent(event_id, self.config.camera_id, self.config.video_source_id, now, marker, category, "needs_review", marker, evidence, tuple(tracks))]

    def _reset_alert(self, key: str) -> None:
        self._active_alerts.discard(key)
