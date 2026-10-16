"use client";

import React, { useState } from "react";
import {
  Search,
  Sparkles,
  Loader2,
  Tag,
  Camera,
  AlertCircle,
  HelpCircle,
  CornerDownLeft,
  Terminal,
} from "lucide-react";
import { Incident, QueryResponse } from "../../types/contracts";
import { submitQuery } from "../../services/api";
import { IncidentCard } from "./IncidentCard";

export interface QueryPanelProps {
  onSelectIncident: (incident: Incident) => void;
  className?: string;
}

const PRESET_QUERIES = [
  "Show all tailgating events from CAM_01",
  "Find person down incidents",
  "Show fighting incidents today",
  "Show crowd incidents across all cameras",
];

export function QueryPanel({
  onSelectIncident,
  className = "",
}: QueryPanelProps) {
  const [queryInput, setQueryInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [response, setResponse] = useState<QueryResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleExecuteQuery = async (questionToAsk?: string) => {
    const q = (questionToAsk ?? queryInput).trim();
    if (!q) return;

    if (questionToAsk) {
      setQueryInput(questionToAsk);
    }

    setIsLoading(true);
    setError(null);

    try {
      const result = await submitQuery(q);
      setResponse(result);
    } catch (err: any) {
      console.error("[QueryPanel] Error executing query:", err);
      setError("Failed to execute natural-language query. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !isLoading) {
      e.preventDefault();
      handleExecuteQuery();
    }
  };

  return (
    <div className={`flex flex-col gap-6 ${className}`}>
      {/* Search Input Box & Presets */}
      <div className="bg-zinc-950/90 border border-zinc-800/80 rounded-2xl p-5 shadow-xl backdrop-blur-md space-y-4">
        <div className="flex items-center gap-2 text-xs font-mono text-zinc-400">
          <Terminal className="w-4 h-4 text-[#2B7FFF]" />
          <span className="uppercase tracking-wider">Conversational Query Interface</span>
          <span className="text-zinc-600">•</span>
          <span className="text-zinc-500">Constrained Parameterized SQL Mapping</span>
        </div>

        {/* Input Bar */}
        <div className="relative flex items-center">
          <Search className="absolute left-4 w-5 h-5 text-zinc-500" />
          <input
            type="text"
            value={queryInput}
            onChange={(e) => setQueryInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask a question (e.g. 'Show tailgating on CAM_02', 'Any person down today?')..."
            className="w-full pl-12 pr-28 py-3.5 bg-zinc-900 border border-zinc-800 rounded-xl text-sm text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-[#2B7FFF] focus:ring-1 focus:ring-[#2B7FFF] transition"
            disabled={isLoading}
          />
          <button
            onClick={() => handleExecuteQuery()}
            disabled={isLoading || !queryInput.trim()}
            className="absolute right-2 px-4 py-2 bg-[#2B7FFF] hover:bg-blue-600 disabled:bg-zinc-800 disabled:text-zinc-500 text-white rounded-lg text-xs font-medium transition flex items-center gap-1.5 shadow-md shadow-blue-500/10 cursor-pointer disabled:cursor-not-allowed"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                <span>Searching</span>
              </>
            ) : (
              <>
                <span>Search</span>
                <CornerDownLeft className="w-3.5 h-3.5 opacity-70" />
              </>
            )}
          </button>
        </div>

        {/* Preset Prompt Suggestion Chips */}
        <div className="flex flex-wrap items-center gap-2 pt-1">
          <span className="text-xs font-mono text-zinc-500 flex items-center gap-1">
            <Sparkles className="w-3.5 h-3.5 text-[#2B7FFF]" />
            Suggestions:
          </span>
          {PRESET_QUERIES.map((preset) => (
            <button
              key={preset}
              onClick={() => handleExecuteQuery(preset)}
              disabled={isLoading}
              className="px-2.5 py-1 rounded-md bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 hover:border-zinc-700 text-xs text-zinc-300 transition cursor-pointer font-mono text-left"
            >
              {preset}
            </button>
          ))}
        </div>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 flex items-center gap-3 text-rose-400 text-sm">
          <AlertCircle className="w-5 h-5 shrink-0" />
          <p>{error}</p>
        </div>
      )}

      {/* Query Response Section */}
      {response && (
        <div className="space-y-6 animate-in fade-in duration-200">
          {/* Interpreted Filter & Answer Card */}
          <div className="bg-zinc-950/90 border border-zinc-800/80 rounded-2xl p-5 shadow-lg backdrop-blur-md space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-2 border-b border-zinc-800/80 pb-3">
              <div className="flex items-center gap-2 text-xs font-mono text-zinc-400">
                <Sparkles className="w-4 h-4 text-[#2B7FFF]" />
                <span>QUERY INTERPRETATION</span>
              </div>
              <span className="text-xs font-mono text-zinc-500 italic">
                &ldquo;{response.question}&rdquo;
              </span>
            </div>

            {/* Interpreted Filter Badges */}
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-xs font-mono text-zinc-400">Mapped Filters:</span>
              {Object.keys(response.interpreted_filters || {}).length > 0 ? (
                Object.entries(response.interpreted_filters).map(([key, val]) => (
                  <span
                    key={key}
                    className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-blue-500/10 border border-blue-500/30 text-[#2B7FFF] font-mono text-xs"
                  >
                    {key === "camera_id" && <Camera className="w-3 h-3" />}
                    {key === "category" && <Tag className="w-3 h-3" />}
                    <span className="font-semibold">{key}:</span>
                    <span>{String(val)}</span>
                  </span>
                ))
              ) : (
                <span className="px-2 py-0.5 rounded bg-zinc-900 border border-zinc-800 text-zinc-400 font-mono text-xs">
                  None (Full Database Scan or Unsupported)
                </span>
              )}
            </div>

            {/* Answer Message Box */}
            <div className="p-3.5 rounded-xl bg-zinc-900/70 border border-zinc-800/60">
              <p className="text-sm text-zinc-200 font-medium leading-relaxed">
                {response.answer}
              </p>
            </div>
          </div>

          {/* Results Grid or Empty State */}
          {response.incidents.length > 0 ? (
            <div className="space-y-3">
              <div className="flex items-center justify-between text-xs font-mono text-zinc-400 px-1">
                <span>MATCHING INCIDENTS ({response.incidents.length})</span>
                <span>Sorted by source video timestamp</span>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {response.incidents.map((incident) => (
                  <IncidentCard
                    key={incident.event_id}
                    incident={incident}
                    onSelect={onSelectIncident}
                  />
                ))}
              </div>
            </div>
          ) : (
            <div className="p-8 rounded-2xl bg-zinc-950/60 border border-dashed border-zinc-800 flex flex-col items-center justify-center text-center space-y-3">
              <HelpCircle className="w-8 h-8 text-zinc-500" />
              <h3 className="text-sm font-semibold text-zinc-300">
                No Incidents Matched Query
              </h3>
              <p className="text-xs text-zinc-500 max-w-md">
                The database returned 0 verified events for these constraints. Try refining the camera name or checking for known categories like &ldquo;tailgating&rdquo; or &ldquo;person_down&rdquo;.
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

