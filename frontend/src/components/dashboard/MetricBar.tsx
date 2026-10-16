"use client";

import React from "react";
import { ShieldAlert, Cpu, Server } from "lucide-react";
import { StatsResponse } from "../../types/contracts";

export interface MetricBarProps {
  stats: StatsResponse | null;
  isMock: boolean;
  isBackendHealthy: boolean;
  className?: string;
}

export function MetricBar({
  stats,
  isMock,
  isBackendHealthy,
  className = "",
}: MetricBarProps) {
  const total = stats?.total ?? 0;
  const recentActivity = stats?.recent_activity_count ?? 0;

  return (
    <div
      className={`w-full bg-white/70 backdrop-blur-xl border border-white/80 rounded-2xl p-4 shadow-[0_4px_24px_rgba(0,0,0,0.04)] ${className}`}
    >
      <div className="flex flex-wrap items-center justify-between gap-4">
        {/* Left: Backend / Mode Status Pill */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium border bg-white/80 border-slate-200/60 shadow-sm">
            {isMock ? (
              <>
                <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse" />
                <span className="text-amber-600 font-mono tracking-wide">MOCK DATA</span>
              </>
            ) : isBackendHealthy ? (
              <>
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                <span className="text-emerald-600 font-mono tracking-wide">LIVE API</span>
              </>
            ) : (
              <>
                <span className="w-2 h-2 rounded-full bg-rose-400 animate-pulse" />
                <span className="text-rose-600 font-mono tracking-wide">DEGRADED</span>
              </>
            )}
          </div>

          <div className="hidden sm:flex items-center gap-1.5 text-xs text-slate-400 font-mono">
            <Server className="w-3.5 h-3.5 text-slate-400" />
            <span>FastAPI:8000</span>
          </div>
        </div>

        {/* Center/Right: Key Performance Metrics */}
        <div className="flex flex-wrap items-center gap-5 sm:gap-8">
          {/* Total Incidents */}
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-blue-50 border border-blue-100 text-[#2B7FFF]">
              <ShieldAlert className="w-4 h-4" />
            </div>
            <div>
              <p className="text-[10px] font-mono text-slate-400 uppercase tracking-wider">
                Total Incidents
              </p>
              <p className="text-lg font-bold font-mono text-slate-900">
                {total}
              </p>
            </div>
          </div>

          {/* Recent activity is the only backend aggregate available here. */}
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-indigo-50 border border-indigo-100 text-indigo-500">
              <Cpu className="w-4 h-4" />
            </div>
            <div>
              <p className="text-[10px] font-mono text-slate-400 uppercase tracking-wider">
                Recent (24h)
              </p>
              <p className="text-lg font-bold font-mono text-slate-900">
                {recentActivity}
              </p>
            </div>
          </div>

          {/* Status Breakdown Pills */}
          {stats?.by_status && (
            <div className="hidden lg:flex items-center gap-1.5 pl-4 border-l border-slate-200/70 text-xs font-mono">
              <span className="px-2 py-0.5 rounded-full bg-blue-50 text-blue-600 border border-blue-100">
                {stats.by_status.classified ?? 0} classified
              </span>
              <span className="px-2 py-0.5 rounded-full bg-amber-50 text-amber-600 border border-amber-100">
                {stats.by_status.candidate ?? 0} candidate
              </span>
              <span className="px-2 py-0.5 rounded-full bg-purple-50 text-purple-600 border border-purple-100">
                {stats.by_status.needs_review ?? 0} review
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
