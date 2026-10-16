"use client";

import React, { useEffect, useState } from "react";
import {
  X,
  Camera,
  Clock,
  Cpu,
  ShieldAlert,
  FileText,
  Calendar,
  Sparkles,
  Code2,
} from "lucide-react";
import { Incident } from "../../types/contracts";
import { resolveKeyframeUrl, PLACEHOLDER_KEYFRAME_SVG } from "../../services/api";

export interface IncidentDetailModalProps {
  incident: Incident | null;
  onClose: () => void;
  className?: string;
}

function formatVideoTimestamp(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  const ms = Math.floor((seconds % 1) * 10);
  return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}.${ms} (${seconds}s)`;
}

export function IncidentDetailModal({
  incident,
  onClose,
  className = "",
}: IncidentDetailModalProps) {
  const [showJson, setShowJson] = useState(false);
  const [imgSrc, setImgSrc] = useState<string>(
    incident?.frame_path ? resolveKeyframeUrl(incident.frame_path) : PLACEHOLDER_KEYFRAME_SVG
  );
  const [hasImageError, setHasImageError] = useState(false);

  useEffect(() => {
    if (incident) {
      const resolved = resolveKeyframeUrl(incident.frame_path);
      setImgSrc(resolved || PLACEHOLDER_KEYFRAME_SVG);
      setHasImageError(false);
      setShowJson(false);
    }
  }, [incident]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    if (incident) {
      window.addEventListener("keydown", handleKeyDown);
      document.body.style.overflow = "hidden";
    }
    return () => {
      window.removeEventListener("keydown", handleKeyDown);
      document.body.style.overflow = "";
    };
  }, [incident, onClose]);

  if (!incident) return null;

  const handleImageError = () => {
    setHasImageError(true);
    setImgSrc(PLACEHOLDER_KEYFRAME_SVG);
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-incident-title"
      className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 bg-slate-900/40 backdrop-blur-md animate-in fade-in duration-200"
      onClick={onClose}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        className={`relative w-full max-w-4xl max-h-[92vh] flex flex-col bg-white/90 backdrop-blur-xl border border-white/80 rounded-2xl shadow-[0_20px_60px_rgba(0,0,0,0.12)] overflow-hidden ${className}`}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100 bg-white/70">
          <div className="flex items-center gap-3">
            <span className="p-2 rounded-xl bg-blue-50 border border-blue-100 text-[#2B7FFF]">
              <ShieldAlert className="w-5 h-5" />
            </span>
            <div>
              <div className="flex items-center gap-2">
                <h2 id="modal-incident-title" className="text-base font-semibold text-slate-900">
                  Incident Evidence Record
                </h2>
                <span className="px-2 py-0.5 rounded-full font-mono text-[11px] bg-slate-100 text-slate-600 border border-slate-200">
                  {incident.event_id}
                </span>
              </div>
              <p className="text-xs text-slate-400 font-mono">
                Source: {incident.source.toUpperCase()} • Status: {incident.status}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowJson(!showJson)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-white hover:bg-slate-50 border border-slate-200/70 text-xs text-slate-600 font-mono transition shadow-sm"
            >
              <Code2 className="w-3.5 h-3.5" />
              <span>{showJson ? "View Details" : "Inspect JSON"}</span>
            </button>
            <button
              onClick={onClose}
              aria-label="Close incident details"
              className="p-2 rounded-xl bg-white hover:bg-slate-50 text-slate-400 hover:text-slate-700 border border-slate-200/70 transition shadow-sm"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Scrollable Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-5 bg-slate-50/40">
          {showJson ? (
            <div className="rounded-2xl bg-slate-900 border border-slate-800 p-4 font-mono text-xs text-emerald-400 overflow-x-auto">
              <pre>{JSON.stringify(incident, null, 2)}</pre>
            </div>
          ) : (
            <>
              {/* Keyframe */}
              <div className="relative aspect-video w-full rounded-2xl overflow-hidden bg-slate-100 border border-slate-200/70 shadow-inner">
                <img
                  src={imgSrc && imgSrc.trim() !== "" ? imgSrc : PLACEHOLDER_KEYFRAME_SVG}
                  alt={`Keyframe for incident ${incident.event_id}`}
                  onError={handleImageError}
                  className="w-full h-full object-contain bg-slate-900"
                />
                <div className="absolute top-3 left-3 flex items-center gap-2">
                  <span className="px-2.5 py-1 rounded-md bg-white/90 backdrop-blur-md border border-white/60 text-slate-800 font-mono text-xs flex items-center gap-1.5 shadow-sm">
                    <Camera className="w-3.5 h-3.5 text-[#2B7FFF]" />
                    {incident.camera_id}
                  </span>
                  <span className="px-2.5 py-1 rounded-md bg-white/90 backdrop-blur-md border border-white/60 text-slate-600 font-mono text-xs flex items-center gap-1.5 shadow-sm">
                    <Clock className="w-3.5 h-3.5 text-slate-400" />
                    {formatVideoTimestamp(incident.timestamp_seconds)}
                  </span>
                </div>
                <div className="absolute bottom-3 left-3 px-2 py-0.5 rounded-md bg-white/80 backdrop-blur-xs text-[10px] text-slate-500 font-mono border border-white/60">
                  {incident.frame_path}
                </div>
              </div>

              {/* Summary & Notes */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="p-4 rounded-2xl bg-white/80 backdrop-blur-xl border border-slate-200/70 shadow-[0_2px_12px_rgba(0,0,0,0.04)]">
                  <div className="flex items-center gap-2 text-xs font-mono text-slate-400 mb-2">
                    <Sparkles className="w-3.5 h-3.5 text-[#2B7FFF]" />
                    <span className="uppercase tracking-wider">VLM Event Summary</span>
                  </div>
                  <p className="text-sm font-medium text-slate-800 leading-relaxed">
                    {incident.summary}
                  </p>
                </div>

                <div className="p-4 rounded-2xl bg-white/80 backdrop-blur-xl border border-slate-200/70 shadow-[0_2px_12px_rgba(0,0,0,0.04)]">
                  <div className="flex items-center gap-2 text-xs font-mono text-slate-400 mb-2">
                    <FileText className="w-3.5 h-3.5 text-indigo-400" />
                    <span className="uppercase tracking-wider">Visual Evidence Notes</span>
                  </div>
                  <p className="text-sm text-slate-600 leading-relaxed">
                    {incident.evidence_notes || "No additional visual evidence notes recorded."}
                  </p>
                </div>
              </div>

              {/* Technical Specs */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="p-3 rounded-xl bg-white/80 border border-slate-200/70 shadow-[0_2px_8px_rgba(0,0,0,0.03)]">
                  <p className="text-[11px] font-mono uppercase text-slate-400">Category</p>
                  <p className="text-sm font-semibold font-mono text-slate-800 mt-1">
                    {incident.category}
                  </p>
                </div>

                <div className="p-3 rounded-xl bg-white/80 border border-slate-200/70 shadow-[0_2px_8px_rgba(0,0,0,0.03)]">
                  <p className="text-[11px] font-mono uppercase text-slate-400">Confidence</p>
                  <p className="text-sm font-mono text-slate-800 mt-1">
                    {incident.confidence !== null
                      ? `${(incident.confidence * 100).toFixed(1)}%`
                      : "Unavailable"}
                    <span className="text-[10px] text-slate-400 block font-normal">
                      ({incident.confidence_type})
                    </span>
                  </p>
                </div>

                <div className="p-3 rounded-xl bg-white/80 border border-slate-200/70 shadow-[0_2px_8px_rgba(0,0,0,0.03)]">
                  <p className="text-[11px] font-mono uppercase text-slate-400">Inference Latency</p>
                  <div className="flex items-center gap-1.5 mt-1">
                    <Cpu className="w-3.5 h-3.5 text-slate-400" />
                    <span className="text-sm font-semibold font-mono text-slate-800">
                      {incident.processing_ms != null ? `${incident.processing_ms} ms` : "Unavailable"}
                    </span>
                  </div>
                </div>

                <div className="p-3 rounded-xl bg-white/80 border border-slate-200/70 shadow-[0_2px_8px_rgba(0,0,0,0.03)]">
                  <p className="text-[11px] font-mono uppercase text-slate-400">Recorded At</p>
                  <div className="flex items-center gap-1.5 mt-1">
                    <Calendar className="w-3.5 h-3.5 text-slate-400" />
                    <span className="text-xs font-mono text-slate-800 truncate" title={incident.created_at}>
                      {new Date(incident.created_at).toLocaleTimeString()}
                    </span>
                  </div>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
