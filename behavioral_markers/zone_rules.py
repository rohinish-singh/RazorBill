from __future__ import annotations

from .schemas import ZoneConfig

def point_in_polygon(point: tuple[float, float], polygon: tuple[tuple[float, float], ...]) -> bool:
    x, y = point; inside = False
    for index, (x1, y1) in enumerate(polygon):
        x2, y2 = polygon[(index + 1) % len(polygon)]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / ((y2 - y1) or 1e-12) + x1:
            inside = not inside
    return inside

def tracks_in_zone(tracks, zone: ZoneConfig):
    return [track for track in tracks if track.class_name == "person" and point_in_polygon(track.footpoint, zone.polygon)]
