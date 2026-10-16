"use client";

import React, { useState } from "react";
import { Camera, Clock, Cpu, Eye, AlertCircle } from "lucide-react";
import { Incident, IncidentCategory, IncidentStatus } from "../../types/contracts";
import { resolveKeyframeUrl, PLACEHOLDER_KEYFRAME_SVG } from "../../services/api";

export interface IncidentCardProps {
  incident: Incident;
  onSelect: (incident: Incident) => void;
  className?: string;
}

function formatVideoTimestamp(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  const ms = Math.floor((seconds % 1) * 10);
  return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}.${ms}`;
}

const CATEGORY_STYLES: Record<IncidentCategory, { label: string; badgeClass: string; dot: string }> = {
  person_down: {
    label: "Person Down",
    badgeClass: "bg-rose-50 text-rose-600 border-rose-200",
    dot: "bg-rose-500",
  },
  fighting: {
    label: "Fighting",
    badgeClass: "bg-orange-50 text-orange-600 border-orange-200",
    dot: "bg-orange-500",
  },
  tailgating: {
    label: "Tailgating",
    badgeClass: "bg-amber-50 text-amber-600 border-amber-200",
    dot: "bg-amber-400",
  },
  crowd_incident: {
    label: "Crowd Incident",
    badgeClass: "bg-purple-50 text-purple-600 border-purple-200",
    dot: "bg-purple-500",
  },
  suspicious_activity: {
    label: "Suspicious Activity",
    badgeClass: "bg-cyan-50 text-cyan-700 border-cyan-200",
    dot: "bg-cyan-500",
  },
  other: {
    label: "Other",
    badgeClass: "bg-slate-50 text-slate-500 border-slate-200",
    dot: "bg-slate-400",
  },
  unknown: {
    label: "Unknown / Queued",
    badgeClass: "bg-slate-50 text-slate-400 border-slate-200",
    dot: "bg-slate-300",
  },
};

const STATUS_STYLES: Record<IncidentStatus, { label: string; badgeClass: string; dotClass: string }> = {
  candidate: {
    label: "Candidate",
    badgeClass: "bg-amber-50 text-amber-600 border-amber-200",
    dotClass: "bg-amber-400",
  },
  classified: {
    label: "Classified",
    badgeClass: "bg-blue-50 text-[#2B7FFF] border-blue-200",
    dotClass: "bg-[#2B7FFF]",
  },
  needs_review: {
    label: "Needs Review",
    badgeClass: "bg-purple-50 text-purple-600 border-purple-200",
    dotClass: "bg-purple-500",
  },
  failed: {
    label: "Failed",
    badgeClass: "bg-rose-50 text-rose-600 border-rose-200",
    dotClass: "bg-rose-500",
  },
};

export function IncidentCard({
  incident,
  onSelect,
  className = "",
}: IncidentCardProps) {
  const initialUrl = resolveKeyframeUrl(incident.frame_path);
  const [imgSrc, setImgSrc] = useState<string>(initialUrl);
  const [hasImageError, setHasImageError] = useState<boolean>(false);

  const categoryMeta =
    CATEGORY_STYLES[incident.category] || CATEGORY_STYLES.unknown;
  const statusMeta =
    STATUS_STYLES[incident.status] || STATUS_STYLES.candidate;

  const handleImageError = () => {
    if (!hasImageError) {
      setHasImageError(true);
      setImgSrc(PLACEHOLDER_KEYFRAME_SVG);
    }
  };

  return (
    <div
      onClick={() => onSelect(incident)}
      className={`group relative flex flex-col bg-white/70 hover:bg-white/90 backdrop-blur-xl border border-white/80 hover:border-slate-200/80 rounded-2xl overflow-hidden shadow-[0_4px_24px_rgba(0,0,0,0.04)] hover:shadow-[0_8px_32px_rgba(0,0,0,0.08)] transition-all duration-200 cursor-pointer ${className}`}
    >
      {/* Media Preview */}
      <div className="relative aspect-video w-full bg-slate-100 overflow-hidden border-b border-slate-100/80">
        <img
          src={imgSrc && imgSrc.trim() !== "" ? imgSrc : PLACEHOLDER_KEYFRAME_SVG}
          alt={incident.summary}
          onError={handleImageError}
          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
          loading="lazy"
        />

        {/* Camera & Time overlays */}
        <div className="absolute top-2.5 left-2.5 flex items-center gap-1.5">
          <span className="flex items-center gap-1 px-2 py-0.5 rounded-md bg-white/85 backdrop-blur-md border border-white/60 text-slate-700 font-mono text-[11px] font-semibold shadow-sm">
            <Camera className="w-3 h-3 text-[#2B7FFF]" />
            {incident.camera_id}
          </span>
          <span className="flex items-center gap-1 px-2 py-0.5 rounded-md bg-white/85 backdrop-blur-md border border-white/60 text-slate-500 font-mono text-[11px] shadow-sm">
            <Clock className="w-3 h-3 text-slate-400" />
            {formatVideoTimestamp(incident.timestamp_seconds)}
          </span>
        </div>

        {/* Status Pill */}
        <div className="absolute top-2.5 right-2.5">
          <span
            className={`flex items-center gap-1.5 px-2.5 py-0.5 rounded-full backdrop-blur-md border text-[11px] font-mono font-medium ${statusMeta.badgeClass} shadow-sm`}
          >
            <span className={`w-1.5 h-1.5 rounded-full ${statusMeta.dotClass}`} />
            {statusMeta.label}
          </span>
        </div>

        {/* Keyframe fallback banner */}
        {hasImageError && (
          <div className="absolute inset-x-0 bottom-0 py-1 bg-white/80 backdrop-blur-xs flex items-center justify-center gap-1.5 text-[10px] text-slate-400 font-mono border-t border-slate-100">
            <AlertCircle className="w-3 h-3 text-amber-400" />
            <span>Keyframe rendered from fallback</span>
          </div>
        )}
      </div>

      {/* Card Content */}
      <div className="flex-1 flex flex-col p-4 justify-between gap-3">
        <div>
          {/* Category Badge & Source */}
          <div className="flex items-center justify-between gap-2 mb-2">
            <span
              className={`flex items-center gap-1.5 px-2.5 py-0.5 rounded-full border text-xs font-medium tracking-wide ${categoryMeta.badgeClass}`}
            >
              <span className={`w-1.5 h-1.5 rounded-full ${categoryMeta.dot}`} />
              {categoryMeta.label}
            </span>

            <span className="text-[11px] font-mono uppercase text-slate-400 bg-slate-50 px-2 py-0.5 rounded-md border border-slate-200/70">
              {incident.source}
            </span>
          </div>

          {/* Summary */}
          <p className="text-sm font-medium text-slate-800 line-clamp-2 leading-relaxed">
            {incident.summary}
          </p>
        </div>

        {/* Footer */}
        <div className="pt-2.5 border-t border-slate-100 flex items-center justify-between text-xs font-mono text-slate-400">
          <div className="flex items-center gap-1.5">
            <Cpu className="w-3.5 h-3.5 text-slate-300" />
            <span>{incident.processing_ms ?? "Unavailable"}{incident.processing_ms != null ? " ms" : ""}</span>
          </div>

          <div className="flex items-center gap-1 text-[#2B7FFF] group-hover:translate-x-0.5 transition-transform font-sans font-medium text-[11px]">
            <Eye className="w-3.5 h-3.5" />
            <span>Inspect</span>
          </div>
        </div>
      </div>
    </div>
  );
}
