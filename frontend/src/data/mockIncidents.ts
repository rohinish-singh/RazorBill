import { Incident, QueryResponse, StatsResponse } from "../types/contracts";

export const MOCK_INCIDENTS: Incident[] = [
  {
    event_id: "evt_20261015_001",
    camera_id: "CAM_01",
    timestamp_seconds: 134.5,
    category: "person_down",
    summary: "Individual collapsed near South Gate entrance walkway.",
    confidence: null,
    confidence_type: "unavailable",
    frame_path: "data/frames/CAM_01/evt_20261015_001.jpg",
    source: "vlm",
    processing_ms: 740,
    status: "classified",
    evidence_notes: "Visible horizontal posture on walkway; no movement observed over 8 sampled frames.",
    created_at: "2026-10-15T10:02:14Z",
  },
  {
    event_id: "evt_20261015_002",
    camera_id: "CAM_02",
    timestamp_seconds: 218.0,
    category: "tailgating",
    summary: "Two individuals traversed secure turnstile on single badge credential swipe.",
    confidence: null,
    confidence_type: "unavailable",
    frame_path: "data/frames/CAM_02/evt_20261015_002.jpg",
    source: "vlm",
    processing_ms: 680,
    status: "classified",
    evidence_notes: "Second person entered turnstile within 0.4s of first person before barrier reset.",
    created_at: "2026-10-15T10:14:30Z",
  },
  {
    event_id: "evt_20261015_003",
    camera_id: "CAM_03",
    timestamp_seconds: 412.3,
    category: "fighting",
    summary: "Physical altercation with rapid grappling detected between two subjects in courtyard.",
    confidence: null,
    confidence_type: "unavailable",
    frame_path: "data/frames/CAM_03/evt_20261015_003.jpg",
    source: "vlm",
    processing_ms: 1150,
    status: "classified",
    evidence_notes: "Aggressive upper-limb contact and sudden trajectory changes detected across multiple tracks.",
    created_at: "2026-10-15T10:28:45Z",
  },
  {
    event_id: "evt_20261015_004",
    camera_id: "CAM_01",
    timestamp_seconds: 589.1,
    category: "crowd_incident",
    summary: "Dense congregation formed abruptly near corridor exit blocking transit pathway.",
    confidence: null,
    confidence_type: "unavailable",
    frame_path: "data/frames/CAM_01/evt_20261015_004.jpg",
    source: "vlm",
    processing_ms: 890,
    status: "classified",
    evidence_notes: "Subject count exceeded threshold (14 subjects in 5m radius) with near-zero directional flow.",
    created_at: "2026-10-15T10:45:12Z",
  },
  {
    event_id: "evt_20261015_005",
    camera_id: "CAM_04",
    timestamp_seconds: 730.0,
    category: "suspicious_activity",
    summary: "Subject loitering around restricted server access perimeter door for extended duration.",
    confidence: null,
    confidence_type: "unavailable",
    frame_path: "data/frames/CAM_04/evt_20261015_005.jpg",
    source: "vlm",
    processing_ms: 420,
    status: "needs_review",
    evidence_notes: "Dwell time > 90 seconds without door badge attempt. Lighting occludes facial features.",
    created_at: "2026-10-15T11:05:00Z",
  },
  {
    event_id: "evt_20261015_006",
    camera_id: "CAM_02",
    timestamp_seconds: 895.4,
    category: "unknown",
    summary: "Rule-based anomaly detected from rapid motion vector change; awaiting VLM classification.",
    confidence: null,
    confidence_type: "unavailable",
    frame_path: "data/frames/CAM_02/evt_20261015_006.jpg",
    source: "rule",
    processing_ms: 180,
    status: "candidate",
    evidence_notes: "Optical flow acceleration spike on bounding track 24. Queued for visual inference.",
    created_at: "2026-10-15T11:18:22Z",
  },
];

export const MOCK_STATS: StatsResponse = {
  total: 6,
  by_category: {
    person_down: 1,
    tailgating: 1,
    fighting: 1,
    crowd_incident: 1,
    suspicious_activity: 1,
    other: 0,
    unknown: 1,
  },
  by_status: {
    classified: 4,
    candidate: 1,
    needs_review: 1,
    failed: 0,
  },
  by_camera: {
    CAM_01: 2,
    CAM_02: 2,
    CAM_03: 1,
    CAM_04: 1,
  },
  recent_activity_count: 0,
};

export const MOCK_QUERY_RESPONSES: Record<string, QueryResponse> = {
  "tailgating": {
    question: "Show all tailgating events from camera 2 today",
    interpreted_filters: { camera_id: "CAM_02", category: "tailgating" },
    answer: "Found 1 matching incident on CAM_02 involving unauthorized turnstile entry.",
    incidents: [MOCK_INCIDENTS[1]],
  },
  "person down": {
    question: "Show any person down incidents",
    interpreted_filters: { category: "person_down" },
    answer: "Found 1 confirmed person down incident near South Gate entrance on CAM_01.",
    incidents: [MOCK_INCIDENTS[0]],
  },
  "fighting": {
    question: "Show fighting or altercations",
    interpreted_filters: { category: "fighting" },
    answer: "Found 1 fighting incident in courtyard recorded on CAM_03.",
    incidents: [MOCK_INCIDENTS[2]],
  },
  "crowd": {
    question: "Show crowd incidents or blockages",
    interpreted_filters: { category: "crowd_incident" },
    answer: "Found 1 crowd congestion incident blocking transit pathway on CAM_01.",
    incidents: [MOCK_INCIDENTS[3]],
  },
};

/**
 * Safe mock query resolver matching backend's constrained query parser behavior
 */
export function resolveMockQuery(question: string): QueryResponse {
  const normalized = question.toLowerCase();

  for (const [key, response] of Object.entries(MOCK_QUERY_RESPONSES)) {
    if (normalized.includes(key)) {
      return {
        ...response,
        question,
      };
    }
  }

  // Camera filter search
  const cameraMatch = normalized.match(/cam(?:era)?[_\s-]?0?([1-4])/i);
  if (cameraMatch) {
    const camId = `CAM_0${cameraMatch[1]}`;
    const matched = MOCK_INCIDENTS.filter((inc) => inc.camera_id === camId);
    return {
      question,
      interpreted_filters: { camera_id: camId },
      answer: `Found ${matched.length} incidents recorded on ${camId}.`,
      incidents: matched,
    };
  }

  // Fallback / unsupported query response (never fabricate results as per contract)
  return {
    question,
    interpreted_filters: {},
    answer:
      "Query could not be mapped to supported filters. Try asking by category (e.g., 'tailgating', 'person down', 'fighting') or camera ID (e.g., 'CAM_01').",
    incidents: [],
  };
}

