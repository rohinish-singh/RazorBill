/**
 * Central API Client for RazorBill Dashboard
 * Implements communication with Person 3's FastAPI backend
 * with automatic, graceful fallback to offline mock datasets.
 */

import {
  Incident,
  IncidentFilters,
  QueryResponse,
  StatsResponse,
} from "../types/contracts";
import {
  MOCK_INCIDENTS,
  MOCK_STATS,
  resolveMockQuery,
} from "../data/mockIncidents";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

const FORCE_MOCK =
  process.env.NEXT_PUBLIC_USE_MOCK === "true";

export const PLACEHOLDER_KEYFRAME_SVG = `data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="640" height="360" viewBox="0 0 640 360" fill="none"><rect width="640" height="360" fill="%2318181B"/><path d="M280 150H360M320 120V180" stroke="%233F3F46" stroke-width="2" stroke-linecap="round"/><circle cx="320" cy="150" r="40" stroke="%233F3F46" stroke-width="2"/><text x="50%25" y="65%25" dominant-baseline="middle" text-anchor="middle" fill="%2371717A" font-family="system-ui, sans-serif" font-size="14" font-weight="500">No Keyframe Frame Available</text><text x="50%25" y="73%25" dominant-baseline="middle" text-anchor="middle" fill="%2352525B" font-family="system-ui, sans-serif" font-size="12">Offline / Mock Evidence Mode</text></svg>`;

/**
 * Filter the mock dataset based on provided parameters
 */
function filterMockIncidents(filters?: IncidentFilters): Incident[] {
  let result = [...MOCK_INCIDENTS];

  if (filters?.camera_id && filters.camera_id !== "all") {
    result = result.filter(
      (inc) => inc.camera_id.toLowerCase() === filters.camera_id!.toLowerCase()
    );
  }

  if (filters?.category && filters.category !== "all") {
    result = result.filter((inc) => inc.category === filters.category);
  }

  if (filters?.status && filters.status !== "all") {
    result = result.filter((inc) => inc.status === filters.status);
  }

  if (filters?.start != null) {
    result = result.filter((inc) => inc.timestamp_seconds >= filters.start!);
  }

  if (filters?.end != null) {
    result = result.filter((inc) => inc.timestamp_seconds <= filters.end!);
  }

  if (filters?.offset != null && filters.offset > 0) {
    result = result.slice(filters.offset);
  }

  if (filters?.limit != null && filters.limit > 0) {
    result = result.slice(0, filters.limit);
  }

  return result;
}

/**
 * Resolves relative frame paths (e.g., 'data/frames/CAM_01/evt.jpg')
 * to an absolute backend static server URL.
 */
export function resolveKeyframeUrl(framePath?: string | null): string {
  if (!framePath || framePath.trim() === "") {
    return PLACEHOLDER_KEYFRAME_SVG;
  }

  const cleanPath = framePath.replace(/^\/+/, "");
  return `${API_BASE_URL}/${cleanPath}`;
}

/**
 * Check backend health and determine if mock fallback is active
 */
export async function checkHealth(): Promise<{ status: string; isMock: boolean }> {
  if (FORCE_MOCK) {
    return { status: "mock_enabled", isMock: true };
  }

  try {
    const res = await fetch(`${API_BASE_URL}/health`, {
      signal: AbortSignal.timeout(2500),
      cache: "no-store",
    });

    if (res.ok) {
      const data = await res.json().catch(() => ({}));
      return { status: data.status || "healthy", isMock: false };
    }

    console.warn("[RazorBill API] Backend health check returned non-200. Using mock data.");
    return { status: "backend_degraded", isMock: true };
  } catch (err) {
    console.warn("[RazorBill API] Backend unreachable at " + API_BASE_URL + ". Falling back to mock data.", err);
    return { status: "backend_offline", isMock: true };
  }
}

/**
 * Fetch incident list with optional filters and pagination
 */
export async function fetchIncidents(filters?: IncidentFilters): Promise<Incident[]> {
  if (FORCE_MOCK) {
    return filterMockIncidents(filters);
  }

  try {
    const params = new URLSearchParams();
    if (filters?.camera_id && filters.camera_id !== "all") {
      params.set("camera_id", filters.camera_id);
    }
    if (filters?.category && filters.category !== "all") {
      params.set("category", filters.category);
    }
    if (filters?.status && filters.status !== "all") {
      params.set("status", filters.status);
    }
    if (filters?.start != null) {
      params.set("start", String(filters.start));
    }
    if (filters?.end != null) {
      params.set("end", String(filters.end));
    }
    if (filters?.limit != null) {
      params.set("limit", String(filters.limit));
    }
    if (filters?.offset != null) {
      params.set("offset", String(filters.offset));
    }

    const queryStr = params.toString() ? `?${params.toString()}` : "";
    const res = await fetch(`${API_BASE_URL}/api/incidents${queryStr}`, {
      signal: AbortSignal.timeout(4000),
      cache: "no-store",
    });

    if (res.ok) {
      return await res.json();
    }

    console.warn(`[RazorBill API] /api/incidents returned status ${res.status}. Falling back to mock data.`);
    return filterMockIncidents(filters);
  } catch (err) {
    console.warn("[RazorBill API] /api/incidents fetch failed. Falling back to mock data:", err);
    return filterMockIncidents(filters);
  }
}

/**
 * Fetch a single incident record by event ID
 */
export async function fetchIncidentById(id: string): Promise<Incident | null> {
  if (FORCE_MOCK) {
    return MOCK_INCIDENTS.find((i) => i.event_id === id) || null;
  }

  try {
    const res = await fetch(`${API_BASE_URL}/api/incidents/${encodeURIComponent(id)}`, {
      signal: AbortSignal.timeout(4000),
      cache: "no-store",
    });

    if (res.ok) {
      return await res.json();
    }

    if (res.status === 404) {
      return null;
    }

    console.warn(`[RazorBill API] /api/incidents/${id} returned status ${res.status}. Falling back to mock.`);
    return MOCK_INCIDENTS.find((i) => i.event_id === id) || null;
  } catch (err) {
    console.warn(`[RazorBill API] Failed to fetch incident ${id}. Falling back to mock:`, err);
    return MOCK_INCIDENTS.find((i) => i.event_id === id) || null;
  }
}

/**
 * Fetch aggregated metrics and system statistics
 */
export async function fetchStats(): Promise<StatsResponse> {
  if (FORCE_MOCK) {
    return MOCK_STATS;
  }

  try {
    const res = await fetch(`${API_BASE_URL}/api/stats`, {
      signal: AbortSignal.timeout(3000),
      cache: "no-store",
    });

    if (res.ok) {
      return await res.json();
    }

    console.warn(`[RazorBill API] /api/stats returned status ${res.status}. Falling back to mock stats.`);
    return MOCK_STATS;
  } catch (err) {
    console.warn("[RazorBill API] Failed to fetch stats. Falling back to mock stats:", err);
    return MOCK_STATS;
  }
}

/**
 * Submit a conversational natural-language question
 */
export async function submitQuery(question: string): Promise<QueryResponse> {
  if (FORCE_MOCK) {
    return resolveMockQuery(question);
  }

  try {
    const res = await fetch(`${API_BASE_URL}/api/query`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ question }),
      signal: AbortSignal.timeout(6000),
      cache: "no-store",
    });

    if (res.ok) {
      return await res.json();
    }

    console.warn(`[RazorBill API] /api/query returned status ${res.status}. Falling back to mock query resolver.`);
    return resolveMockQuery(question);
  } catch (err) {
    console.warn("[RazorBill API] Failed to submit query. Falling back to mock query resolver:", err);
    return resolveMockQuery(question);
  }
}

