"""CP1 dataset catalog, contract compatibility, and evaluation helpers."""

from .catalog import validate_manifest, make_split_plan
from .contracts import validate_candidate_packet

__all__ = ["make_split_plan", "validate_candidate_packet", "validate_manifest"]
