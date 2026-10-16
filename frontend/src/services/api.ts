/** Browser client for the FastAPI incident API.
 * Mock data is available only with NEXT_PUBLIC_USE_MOCK=true. Normal mode
 * never substitutes invented records when the backend is unavailable.
 */
import { Incident, IncidentFilters, IncidentListResponse, QueryResponse, StatsResponse } from "../types/contracts";
import { MOCK_INCIDENTS, MOCK_STATS, resolveMockQuery } from "../data/mockIncidents";

const API_BASE_URL = (process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000").replace(/\/$/, "");
const USE_MOCK = process.env.NEXT_PUBLIC_USE_MOCK === "true";

export class ApiError extends Error {
  constructor(message: string, public readonly status?: number) {
    super(message);
    this.name = "ApiError";
  }
}

export const PLACEHOLDER_KEYFRAME_SVG = `data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="640" height="360" viewBox="0 0 640 360" fill="none"><rect width="640" height="360" fill="%2318181B"/><circle cx="320" cy="150" r="40" stroke="%233F3F46" stroke-width="2"/><text x="50%25" y="65%25" dominant-baseline="middle" text-anchor="middle" fill="%2371717A" font-family="system-ui, sans-serif" font-size="14">No Keyframe Available</text></svg>`;

function filterMockIncidents(filters?: IncidentFilters): Incident[] {
  let result = [...MOCK_INCIDENTS];
  if (filters?.camera_id && filters.camera_id !== "all") result = result.filter((item) => item.camera_id === filters.camera_id);
  if (filters?.category && filters.category !== "all") result = result.filter((item) => item.category === filters.category);
  if (filters?.status && filters.status !== "all") result = result.filter((item) => item.status === filters.status);
  const offset = filters?.offset || 0;
  return result.slice(offset, filters?.limit ? offset + filters.limit : undefined);
}

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, { ...init, cache: "no-store", signal: AbortSignal.timeout(6000) });
  } catch {
    throw new ApiError("The FastAPI service is unreachable. Start the backend and retry.");
  }
  if (!response.ok) {
    const detail = await response.json().catch(() => null) as { detail?: string } | null;
    throw new ApiError(detail?.detail || `API request failed (${response.status}).`, response.status);
  }
  return response.json() as Promise<T>;
}

/** Never expose a Windows/local path: request only backend-served evidence. */
export function resolveKeyframeUrl(framePath?: string | null): string {
  if (!framePath || /^[a-zA-Z]:[\\/]/.test(framePath) || framePath.includes("..")) return PLACEHOLDER_KEYFRAME_SVG;
  const path = framePath.replace(/\\/g, "/").replace(/^\/+/, "").replace(/^(data\/)?frames\//, "");
  if (!path) return PLACEHOLDER_KEYFRAME_SVG;
  return `${API_BASE_URL}/api/evidence/${path.split("/").map(encodeURIComponent).join("/")}`;
}

export async function checkHealth(): Promise<{ status: string; isMock: boolean }> {
  if (USE_MOCK) return { status: "mock_enabled", isMock: true };
  const health = await requestJson<{ status: string }>("/health");
  return { status: health.status, isMock: false };
}

export async function fetchIncidents(filters?: IncidentFilters): Promise<Incident[]> {
  if (USE_MOCK) return filterMockIncidents(filters);
  const params = new URLSearchParams();
  if (filters?.camera_id && filters.camera_id !== "all") params.set("camera_id", filters.camera_id);
  if (filters?.category && filters.category !== "all") params.set("category", filters.category);
  if (filters?.status && filters.status !== "all") params.set("status", filters.status);
  if (filters?.start) params.set("start", filters.start);
  if (filters?.end) params.set("end", filters.end);
  if (filters?.limit) params.set("limit", String(filters.limit));
  if (filters?.offset) params.set("offset", String(filters.offset));
  const response = await requestJson<IncidentListResponse>(`/api/incidents${params.size ? `?${params}` : ""}`);
  if (!Array.isArray(response.items)) throw new ApiError("API returned an invalid incident-list response.");
  return response.items;
}

export async function fetchIncidentById(id: string): Promise<Incident | null> {
  if (USE_MOCK) return MOCK_INCIDENTS.find((item) => item.event_id === id) || null;
  try {
    return await requestJson<Incident>(`/api/incidents/${encodeURIComponent(id)}`);
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) return null;
    throw error;
  }
}

export async function fetchStats(): Promise<StatsResponse> {
  return USE_MOCK ? MOCK_STATS : requestJson<StatsResponse>("/api/stats");
}

export async function submitQuery(question: string): Promise<QueryResponse> {
  if (USE_MOCK) return resolveMockQuery(question);
  return requestJson<QueryResponse>("/api/query", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ question }) });
}
