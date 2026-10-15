from __future__ import annotations

from collections import defaultdict
from .camera_health import FrameObservation
from .schemas import CameraConfig, MarkerEvent, Track
from .temporal_rules import ready
from .zone_rules import tracks_in_zone

class MarkerEngine:
    """Single-camera state machine. Callers own frame queues and backpressure."""
    def __init__(self, config: CameraConfig):
        self.config = config; self._inside = set(); self._entered = {}; self._observations = defaultdict(int)
        self._crowd_since = {}; self._health_since = {}; self._last_alert = {}; self._active_alerts = set(); self._previous_luminance = None

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

    def source_read_failed(self, timestamp_seconds: float, reason: str) -> list[MarkerEvent]:
        return self._emit("source_read_failure", "other", timestamp_seconds, [], {"reason": reason}, 0)

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
