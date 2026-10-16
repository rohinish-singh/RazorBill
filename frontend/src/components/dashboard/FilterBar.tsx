"use client";

import React from "react";
import { Search, RotateCcw, Camera, Tag, Layers, X } from "lucide-react";
import { IncidentCategory, IncidentFilters, IncidentStatus } from "../../types/contracts";

export interface FilterBarProps {
  filters: IncidentFilters;
  onFilterChange: (filters: IncidentFilters) => void;
  onReset: () => void;
  searchQuery: string;
  onSearchChange: (query: string) => void;
  availableCameras?: string[];
  totalResults?: number;
  className?: string;
}

const CATEGORIES: { label: string; value: IncidentCategory | "all" }[] = [
  { label: "All Categories", value: "all" },
  { label: "Person Down", value: "person_down" },
  { label: "Fighting", value: "fighting" },
  { label: "Tailgating", value: "tailgating" },
  { label: "Crowd Incident", value: "crowd_incident" },
  { label: "Suspicious Activity", value: "suspicious_activity" },
  { label: "Other", value: "other" },
  { label: "Unknown", value: "unknown" },
];

const STATUSES: { label: string; value: IncidentStatus | "all" }[] = [
  { label: "All Statuses", value: "all" },
  { label: "Candidate", value: "candidate" },
  { label: "Classified", value: "classified" },
  { label: "Needs Review", value: "needs_review" },
  { label: "Failed", value: "failed" },
];

const DEFAULT_CAMERAS = ["all", "CAM_01", "CAM_02", "CAM_03", "CAM_04"];

export function FilterBar({
  filters,
  onFilterChange,
  onReset,
  searchQuery,
  onSearchChange,
  availableCameras = DEFAULT_CAMERAS,
  totalResults,
  className = "",
}: FilterBarProps) {
  const hasActiveFilters =
    Boolean(searchQuery) ||
    (filters.camera_id && filters.camera_id !== "all") ||
    (filters.category && filters.category !== "all") ||
    (filters.status && filters.status !== "all");

  return (
    <div
      className={`w-full bg-white/70 backdrop-blur-xl border border-white/80 rounded-2xl p-3.5 shadow-[0_4px_24px_rgba(0,0,0,0.04)] ${className}`}
    >
      <div className="flex flex-col lg:flex-row items-stretch lg:items-center justify-between gap-3">
        {/* Search input */}
        <div className="relative flex-1 min-w-[240px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            placeholder="Search summaries, notes, or event IDs..."
            className="w-full pl-9 pr-8 py-2.5 bg-white/80 border border-slate-200/70 rounded-xl text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:border-[#2B7FFF] focus:ring-1 focus:ring-[#2B7FFF]/40 transition shadow-sm"
          />
          {searchQuery && (
            <button
              onClick={() => onSearchChange("")}
              className="absolute right-2.5 top-1/2 -translate-y-1/2 p-0.5 rounded text-slate-400 hover:text-slate-600"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>

        {/* Dropdown selectors */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Camera Selector */}
          <div className="flex items-center gap-1.5 px-2.5 py-2 bg-white/80 border border-slate-200/70 rounded-xl text-xs shadow-sm">
            <Camera className="w-3.5 h-3.5 text-slate-400" />
            <select
              value={filters.camera_id || "all"}
              onChange={(e) =>
                onFilterChange({
                  ...filters,
                  camera_id: e.target.value === "all" ? undefined : e.target.value,
                })
              }
              className="bg-transparent text-slate-700 font-mono text-xs focus:outline-none cursor-pointer"
            >
              <option value="all">All Cameras</option>
              {availableCameras
                .filter((c) => c !== "all")
                .map((cam) => (
                  <option key={cam} value={cam}>
                    {cam}
                  </option>
                ))}
            </select>
          </div>

          {/* Category Selector */}
          <div className="flex items-center gap-1.5 px-2.5 py-2 bg-white/80 border border-slate-200/70 rounded-xl text-xs shadow-sm">
            <Tag className="w-3.5 h-3.5 text-slate-400" />
            <select
              value={filters.category || "all"}
              onChange={(e) =>
                onFilterChange({
                  ...filters,
                  category: e.target.value as IncidentCategory | "all",
                })
              }
              className="bg-transparent text-slate-700 text-xs focus:outline-none cursor-pointer"
            >
              {CATEGORIES.map((cat) => (
                <option key={cat.value} value={cat.value}>
                  {cat.label}
                </option>
              ))}
            </select>
          </div>

          {/* Status Selector */}
          <div className="flex items-center gap-1.5 px-2.5 py-2 bg-white/80 border border-slate-200/70 rounded-xl text-xs shadow-sm">
            <Layers className="w-3.5 h-3.5 text-slate-400" />
            <select
              value={filters.status || "all"}
              onChange={(e) =>
                onFilterChange({
                  ...filters,
                  status: e.target.value as IncidentStatus | "all",
                })
              }
              className="bg-transparent text-slate-700 text-xs focus:outline-none cursor-pointer"
            >
              {STATUSES.map((st) => (
                <option key={st.value} value={st.value}>
                  {st.label}
                </option>
              ))}
            </select>
          </div>

          {/* Reset Filters */}
          {hasActiveFilters && (
            <button
              onClick={onReset}
              className="flex items-center gap-1.5 px-3 py-2 bg-white/80 hover:bg-white text-slate-600 hover:text-slate-900 border border-slate-200/70 rounded-xl text-xs transition font-mono shadow-sm"
              title="Reset all filters"
            >
              <RotateCcw className="w-3 h-3" />
              <span>Reset</span>
            </button>
          )}

          {/* Results count */}
          {totalResults !== undefined && (
            <div className="px-2.5 py-2 rounded-xl bg-slate-50 border border-slate-200/70 text-slate-500 font-mono text-xs">
              <span className="text-slate-800 font-semibold">{totalResults}</span> incidents
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
