"use client";

import React, { useEffect, useState, useMemo, useCallback, useRef } from "react";
import {
  ShieldAlert,
  Radio,
  Search,
  RotateCcw,
  Sparkles,
  Inbox,
  Video,
  Clock,
  RefreshCw,
  Camera,
} from "lucide-react";
import {
  Incident,
  IncidentFilters,
  StatsResponse,
} from "../types/contracts";
import {
  checkHealth,
  fetchIncidentById,
  fetchIncidents,
  fetchStats,
} from "../services/api";
import { MetricBar } from "../components/dashboard/MetricBar";
import { FilterBar } from "../components/dashboard/FilterBar";
import { IncidentCard } from "../components/dashboard/IncidentCard";
import { IncidentDetailModal } from "../components/dashboard/IncidentDetailModal";
import { QueryPanel } from "../components/dashboard/QueryPanel";
import { IrisReveal } from "../components/entry/IrisReveal";
import { CameraPortalState } from "../components/entry/useCameraPortalTransition";

export default function DashboardPage() {
  // Application Data States
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [selectedIncident, setSelectedIncident] = useState<Incident | null>(null);

  // System & Connection States
  const [isBackendHealthy, setIsBackendHealthy] = useState<boolean>(true);
  const [isMockMode, setIsMockMode] = useState<boolean>(true);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [lastSyncTime, setLastSyncTime] = useState<Date | null>(null);

  // Gateway & Iris State
  const [gatewayState, setGatewayState] = useState<CameraPortalState>("idle");
  const resetGatewayRef = useRef<() => void>(() => {});

  // Navigation & Filtering States
  const [activeTab, setActiveTab] = useState<"stream" | "query">("stream");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [filters, setFilters] = useState<IncidentFilters>({
    camera_id: undefined,
    category: "all",
    status: "all",
  });

  const loadData = useCallback(async () => {
    setIsLoading(true);
    setLoadError(null);
    try {
      const health = await checkHealth();
      setIsBackendHealthy(health.status === "healthy" || health.status === "ok");
      setIsMockMode(health.isMock);

      const [loadedIncidents, loadedStats] = await Promise.all([
        fetchIncidents(filters),
        fetchStats(),
      ]);

      setIncidents(loadedIncidents);
      setStats(loadedStats);
      setLastSyncTime(new Date());
    } catch (err) {
      console.error("[Dashboard] Error loading data:", err);
      setIsBackendHealthy(false);
      setLoadError(err instanceof Error ? err.message : "Unable to load the incident API.");
    } finally {
      setIsLoading(false);
    }
  }, [filters]);

  const handleSelectIncident = useCallback(async (incident: Incident) => {
    try {
      const detail = await fetchIncidentById(incident.event_id);
      setSelectedIncident(detail || incident);
    } catch (err) {
      setLoadError(err instanceof Error ? err.message : "Unable to load incident details.");
      setSelectedIncident(incident);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const filteredIncidents = useMemo(() => {
    if (!searchQuery.trim()) return incidents;
    const q = searchQuery.toLowerCase().trim();
    return incidents.filter((inc) =>
      inc.summary.toLowerCase().includes(q) ||
      (inc.evidence_notes ?? "").toLowerCase().includes(q) ||
      inc.camera_id.toLowerCase().includes(q) ||
      inc.event_id.toLowerCase().includes(q) ||
      inc.category.toLowerCase().includes(q)
    );
  }, [incidents, searchQuery]);

  const handleResetFilters = () => {
    setFilters({ camera_id: undefined, category: "all", status: "all" });
    setSearchQuery("");
  };

  const handleHeroQuery = (query: string) => {
    if (query.trim()) {
      setSearchQuery(query);
      setActiveTab("query");
    }
  };

  return (
    /* ── Root Canvas: crisp white dotted-grid background matching the entry page ── */
    <div
      className="min-h-screen flex flex-col font-sans selection:bg-[#2B7FFF] selection:text-white"
      style={{
        background: "radial-gradient(circle at 1px 1px, #E2E8F0 1px, transparent 0)",
        backgroundSize: "28px 28px",
        backgroundColor: "#F8FAFC",
      }}
    >
      {/* ── Sticky Top Application Header ── */}
      <header className="sticky top-0 z-50 w-full bg-white/80 backdrop-blur-xl border-b border-slate-200/70 px-4 sm:px-8 py-3.5 shadow-[0_1px_12px_rgba(0,0,0,0.04)]">
        <div className="max-w-7xl mx-auto flex items-center justify-between gap-4">
          {/* Brand */}
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-[#2B7FFF]/10 border border-[#2B7FFF]/20 text-[#2B7FFF]">
              <Video className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-base font-bold tracking-tight text-slate-900 font-mono">
                  RazorBill
                </h1>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-mono uppercase tracking-wider bg-blue-50 text-[#2B7FFF] border border-blue-100">
                  Video AI
                </span>
              </div>
              <p className="text-xs text-slate-400 font-mono hidden sm:block">
                Honeywell Live Video Summarization &amp; Querying
              </p>
            </div>
          </div>

          {/* Controls */}
          <div className="flex items-center gap-3">
            {lastSyncTime && (
              <span className="text-[11px] font-mono text-slate-400 hidden md:inline">
                Synced {lastSyncTime.toLocaleTimeString()}
              </span>
            )}

            {gatewayState === "revealed" && (
              <button
                onClick={() => resetGatewayRef.current?.()}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-white hover:bg-slate-50 border border-slate-200/70 text-xs font-mono text-slate-600 hover:text-slate-900 transition cursor-pointer shadow-sm"
                title="Replay 3D Camera Entry"
              >
                <Camera className="w-3.5 h-3.5 text-[#2B7FFF]" />
                <span className="hidden sm:inline">Exit to Camera</span>
              </button>
            )}

            <button
              onClick={() => loadData()}
              disabled={isLoading}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-white hover:bg-slate-50 border border-slate-200/70 text-xs font-mono text-slate-600 hover:text-slate-900 transition cursor-pointer disabled:opacity-50 shadow-sm"
              title="Refresh incidents and stats"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? "animate-spin text-[#2B7FFF]" : "text-slate-400"}`} />
              <span>{isLoading ? "Syncing..." : "Sync"}</span>
            </button>
          </div>
        </div>
      </header>

      {/* ── Iris Transition Orchestrator ── */}
      <IrisReveal
        onStateChange={(state) => setGatewayState(state)}
        onQuerySubmitted={handleHeroQuery}
        registerReset={(resetFn) => {
          resetGatewayRef.current = resetFn;
        }}
      >
        {/* ── Main Dashboard Content ── */}
        <main className="max-w-7xl w-full mx-auto px-4 sm:px-8 py-6 space-y-5">
          {/* Telemetry Bar */}
          <MetricBar
            stats={stats}
            isMock={isMockMode}
            isBackendHealthy={isBackendHealthy}
          />

          {loadError && (
            <div role="alert" className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
              <span>{loadError}</span>
              <button onClick={loadData} className="rounded-lg border border-rose-200 bg-white px-3 py-1.5 text-xs font-mono hover:bg-rose-50">Retry</button>
            </div>
          )}

          {/* Tab Navigation */}
          <div className="flex items-center justify-between border-b border-slate-200/70 pb-1">
            <div className="flex items-center gap-2">
              <button
                onClick={() => setActiveTab("stream")}
                className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition cursor-pointer ${
                  activeTab === "stream"
                    ? "bg-[#2B7FFF] text-white shadow-[0_4px_12px_rgba(43,127,255,0.25)]"
                    : "bg-white/70 hover:bg-white text-slate-500 hover:text-slate-800 border border-slate-200/70 shadow-sm backdrop-blur-xl"
                }`}
              >
                <Radio className="w-4 h-4" />
                <span>Live Incident Stream</span>
                <span
                  className={`ml-1 px-1.5 py-0.5 rounded-full text-xs font-mono ${
                    activeTab === "stream"
                      ? "bg-white/20 text-white"
                      : "bg-slate-100 text-slate-500"
                  }`}
                >
                  {filteredIncidents.length}
                </span>
              </button>

              <button
                onClick={() => setActiveTab("query")}
                className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition cursor-pointer ${
                  activeTab === "query"
                    ? "bg-[#2B7FFF] text-white shadow-[0_4px_12px_rgba(43,127,255,0.25)]"
                    : "bg-white/70 hover:bg-white text-slate-500 hover:text-slate-800 border border-slate-200/70 shadow-sm backdrop-blur-xl"
                }`}
              >
                <Sparkles className="w-4 h-4" />
                <span>Conversational Query Search</span>
              </button>
            </div>
          </div>

          {/* Tab Content */}
          {activeTab === "stream" ? (
            <div className="space-y-5">
              {/* Filter Bar */}
              <FilterBar
                filters={filters}
                onFilterChange={(newFilters) => setFilters(newFilters)}
                onReset={handleResetFilters}
                searchQuery={searchQuery}
                onSearchChange={(q) => setSearchQuery(q)}
                totalResults={filteredIncidents.length}
              />

              {/* Bento Incident Grid */}
              {filteredIncidents.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {filteredIncidents.map((incident) => (
                    <IncidentCard
                      key={incident.event_id}
                      incident={incident}
                      onSelect={handleSelectIncident}
                    />
                  ))}
                </div>
              ) : (
                /* Empty State */
                <div className="p-14 rounded-2xl bg-white/70 backdrop-blur-xl border border-white/80 shadow-[0_4px_24px_rgba(0,0,0,0.04)] flex flex-col items-center justify-center text-center space-y-3">
                  <div className="p-3.5 rounded-2xl bg-slate-50 border border-slate-200/70 text-slate-400">
                    <Inbox className="w-8 h-8" />
                  </div>
                  <h3 className="text-sm font-semibold text-slate-700">
                    No matching incidents found
                  </h3>
                  <p className="text-xs text-slate-400 max-w-sm leading-relaxed">
                    No video events match your current filter parameters or search keywords.
                  </p>
                  <button
                    onClick={handleResetFilters}
                    className="mt-1 flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-white hover:bg-slate-50 text-slate-600 border border-slate-200/70 text-xs font-mono transition cursor-pointer shadow-sm"
                  >
                    <RotateCcw className="w-3.5 h-3.5" />
                    <span>Reset All Filters</span>
                  </button>
                </div>
              )}
            </div>
          ) : (
            /* Query Panel */
            <QueryPanel
              onSelectIncident={handleSelectIncident}
            />
          )}
        </main>
      </IrisReveal>

      {/* Incident Detail Modal */}
      <IncidentDetailModal
        incident={selectedIncident}
        onClose={() => setSelectedIncident(null)}
      />
    </div>
  );
}
