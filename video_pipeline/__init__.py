"""Person 1 local video ingestion, detection/tracking, marker, and packet pipeline."""

from .pipeline import PipelineConfig, process_video

__all__ = ["PipelineConfig", "process_video"]
