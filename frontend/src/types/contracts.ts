/**
 * Data contracts matching SHARED_CONTRACTS.md
 * Source of truth across video pipeline, VLM inference, FastAPI backend, and React dashboard.
 */

export type IncidentCategory =
  | "person_down"
  | "fighting"
  | "tailgating"
  | "crowd_incident"
  | "suspicious_activity"
  | "other"
  | "unknown";

export type IncidentStatus =
  | "candidate"
  | "classified"
  | "needs_review"
  | "failed";

export type IncidentSource =
  | "rule"
  | "vlm"
  | "manual";

export interface Incident {
  event_id: string;
  camera_id: string;
  timestamp_seconds: number;
  category: IncidentCategory;
  summary: string;
  confidence: number | null;
  confidence_type: string;
  frame_path: string;
  source: IncidentSource;
  processing_ms: number;
  status: IncidentStatus;
  evidence_notes: string;
  created_at: string;
}

export interface QueryRequest {
  question: string;
}

export interface QueryResponse {
  question: string;
  interpreted_filters: Record<string, any>;
  answer: string;
  incidents: Incident[];
}

export interface StatsResponse {
  total_incidents: number;
  category_counts: Record<IncidentCategory, number> | Record<string, number>;
  status_counts: Record<IncidentStatus, number> | Record<string, number>;
  avg_processing_ms: number;
  dropped_count: number;
}

export interface IncidentFilters {
  camera_id?: string;
  category?: IncidentCategory | "all";
  status?: IncidentStatus | "all";
  start?: number;
  end?: number;
  limit?: number;
  offset?: number;
}

