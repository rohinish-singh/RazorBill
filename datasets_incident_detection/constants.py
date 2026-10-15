"""Shared, deliberately small CP1 vocabulary."""

SCHEMA_VERSION = "1.0.0"
TERMS_STATUSES = {"verified", "unverified", "restricted"}
INCIDENT_CATEGORIES = {
    "person_down", "fighting", "tailgating", "crowd_incident",
    "suspicious_activity", "other", "unknown",
}
INCIDENT_STATUSES = {"candidate", "classified", "needs_review", "failed"}
SPLITS = {"train", "validation", "test"}
