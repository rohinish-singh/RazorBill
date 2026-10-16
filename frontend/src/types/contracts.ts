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
  confidence_type?: string | null;
  frame_path: string;
  source: IncidentSource;
  processing_ms?: number | null;
  status: IncidentStatus;
  evidence_notes?: string | null;
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
  total: number;
  by_category: Record<string, number>;
  by_status: Record<string, number>;
  by_camera: Record<string, number>;
  recent_activity_count: number;
}

export interface IncidentListResponse {
  items: Incident[];
  total: number;
  limit: number;
  offset: number;
}

export interface IncidentFilters {
  camera_id?: string;
  category?: IncidentCategory | "all";
  status?: IncidentStatus | "all";
  start?: string;
  end?: string;
  limit?: number;
  offset?: number;
}

