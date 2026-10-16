"use client";

import React, { useState, useEffect, useRef } from "react";
import { Search, ArrowRight, Video, Sparkles, Terminal } from "lucide-react";
import { EditorialCamera } from "./EditorialCamera";
import {
  CameraPortalState,
  useCameraPortalTransition,
} from "./useCameraPortalTransition";

export interface CCTVGatewayProps {
  className?: string;
  onTrigger?: (query?: string) => void;
  portalState?: CameraPortalState;
  alignProgress?: number;
  isFocusing?: boolean;
  zoomProgress?: number;
}

const QUICK_SUGGESTIONS = [
  "Show tailgating on CAM_02",
  "Person down South Gate",
  "Fighting in courtyard",
  "Crowd incidents today",
];

export function CCTVGateway({
  className = "",
  onTrigger,
  portalState: propState,
  alignProgress: propAlign,
  isFocusing: propFocus,
  zoomProgress: propZoom,
}: CCTVGatewayProps) {
  const [searchInput, setSearchInput] = useState("");
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 });
  const [torchPos, setTorchPos] = useState({ x: 50, y: 50 });
  const containerRef = useRef<HTMLDivElement>(null);

  // Fallback internal transition if not coordinated by parent
  const internalTransition = useCameraPortalTransition();

  const portalState = propState ?? internalTransition.portalState;
  const alignProgress = propAlign ?? internalTransition.alignProgress;
  const isFocusing = propFocus ?? internalTransition.isFocusing;
  const zoomProgress = propZoom ?? internalTransition.zoomProgress;

  // Mouse parallax & cursor torch tracker
  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      const { innerWidth, innerHeight } = window;
      const x = (e.clientX / innerWidth) * 2 - 1;
      const y = (e.clientY / innerHeight) * 2 - 1;
      setMousePos({ x, y });
      setTorchPos({
        x: Math.round((e.clientX / innerWidth) * 100),
        y: Math.round((e.clientY / innerHeight) * 100),
      });
    };

    window.addEventListener("mousemove", handleMouseMove);
    return () => window.removeEventListener("mousemove", handleMouseMove);
  }, []);

  const handleExecute = (overrideQuery?: string) => {
    const query = (overrideQuery ?? searchInput).trim();
    if (onTrigger) {
      onTrigger(query);
    } else {
      internalTransition.triggerPortal(query);
    }
  };

  const isTransitioning = portalState !== "idle";

  return (
    <div
      ref={containerRef}
      className={`relative w-full min-h-screen bg-[#F8F9FA] text-[#17232D] flex flex-col justify-between overflow-x-hidden select-none font-sans ${className}`}
    >
      {/* Background Engineering Dot Grid */}
      <div
        className="absolute inset-0 opacity-40 pointer-events-none"
        style={{
          backgroundImage:
            "radial-gradient(#17232D 0.75px, transparent 0.75px), radial-gradient(#17232D 0.75px, #F8F9FA 0.75px)",
          backgroundSize: "36px 36px",
          backgroundPosition: "0 0, 18px 18px",
        }}
      />

      {/* Cursor Torch Ambient Glow */}
      <div
        className="absolute inset-0 pointer-events-none transition-opacity duration-300"
        style={{
          background: `radial-gradient(750px circle at ${torchPos.x}% ${torchPos.y}%, rgba(43, 127, 255, 0.05), transparent 75%)`,
        }}
      />

      {/* Top Header Rail */}
      <header className="relative z-30 w-full px-6 sm:px-12 py-4 flex items-center justify-between border-b border-zinc-200/80 bg-[#F8F9FA]/90 backdrop-blur-md">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-xl bg-[#17232D] text-white shadow-md">
            <Video className="w-5 h-5 text-[#2B7FFF]" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-base font-bold tracking-tight text-[#17232D] font-mono">
                RazorBill
              </span>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono uppercase tracking-wider bg-[#2B7FFF]/10 text-[#2B7FFF] font-semibold border border-[#2B7FFF]/20">
                Live Video AI
              </span>
            </div>
            <p className="text-[11px] text-zinc-500 font-mono hidden sm:block">
              Honeywell Video Anomaly Intelligence &amp; VLM Engine
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-mono font-medium border bg-white border-zinc-300/80 shadow-xs">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span className="text-zinc-700">OPTICAL GATEWAY ARMED</span>
          </div>
        </div>
      </header>

      {/* Hero Body Content Area */}
      <main className="relative z-20 flex-1 max-w-7xl w-full mx-auto px-6 sm:px-12 py-6 lg:py-8 flex flex-col lg:flex-row items-start justify-between overflow-visible">
        {/* Left Column: Waymark Headline & Search */}
        <div className="w-full lg:max-w-[50%] xl:max-w-[48%] flex flex-col items-start space-y-6 text-left relative z-20 py-4">
          {/* Badge Tag */}
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-white border border-zinc-300 text-xs font-mono font-semibold text-zinc-700 shadow-xs tracking-wide">
            <span className="w-1.5 h-1.5 rounded-full bg-[#FF3B00] animate-ping" />
            <span>HONEYWELL LIVE VIDEO AI // INTELLIGENT SURVEILLANCE</span>
          </div>

          {/* Big Bold Headline */}
          <h1 className="text-4xl sm:text-6xl md:text-7xl font-extrabold tracking-tight text-[#17232D] leading-[1.06]">
            Know what moves. <br />
            <span className="text-[#2B7FFF]">See what matters.</span>
          </h1>

          {/* Subtext */}
          <p className="text-base sm:text-lg text-zinc-600 leading-relaxed font-normal max-w-xl">
            Real-time edge event synthesis, open-source VLM incident classification, and conversational natural-language querying across distributed camera feeds.
          </p>

          {/* Central Pill Search & Trigger Bar */}
          <div className="w-full pt-2 space-y-3 max-w-xl">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleExecute();
              }}
              className="relative flex items-center w-full bg-white border-2 border-zinc-300 hover:border-zinc-400 focus-within:border-[#2B7FFF] focus-within:ring-4 focus-within:ring-[#2B7FFF]/10 rounded-full p-2 shadow-lg transition-all"
            >
              <Search className="w-5 h-5 text-zinc-400 ml-3 shrink-0" />
              <input
                type="text"
                value={searchInput}
                onChange={(e) => setSearchInput(e.target.value)}
                disabled={isTransitioning}
                placeholder="Search events (e.g. 'show fighting') or click camera to enter"
                className="flex-1 bg-transparent px-3 py-2 text-sm sm:text-base text-zinc-800 placeholder-zinc-400 focus:outline-none"
              />
              <button
                type="submit"
                disabled={isTransitioning}
                className="flex items-center gap-2 px-5 py-2.5 bg-[#17232D] hover:bg-black text-white text-xs sm:text-sm font-semibold rounded-full shadow-md transition-all cursor-pointer disabled:opacity-50 shrink-0"
              >
                <span>Enter Deck</span>
                <ArrowRight className="w-4 h-4 text-[#2B7FFF]" />
              </button>
            </form>

            {/* Quick Suggestion Chips */}
            <div className="flex flex-wrap items-center gap-2 pt-1 font-mono text-xs">
              <span className="text-zinc-400 flex items-center gap-1">
                <Sparkles className="w-3 h-3 text-[#2B7FFF]" />
                Try:
              </span>
              {QUICK_SUGGESTIONS.map((sug) => (
                <button
                  key={sug}
                  type="button"
                  disabled={isTransitioning}
                  onClick={() => {
                    setSearchInput(sug);
                    handleExecute(sug);
                  }}
                  className="px-2.5 py-1 rounded-md bg-white hover:bg-zinc-100 border border-zinc-300/80 text-zinc-600 hover:text-zinc-900 transition-colors cursor-pointer shadow-2xs"
                >
                  {sug}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Right Column: Suspended 3D Industrial Surveillance Camera & Optical Portal */}
        <div className="w-full lg:w-[50%] xl:w-[50%] relative flex flex-col items-center justify-start lg:items-end overflow-visible -mt-6 lg:-mt-8 pt-0 pointer-events-auto">
          <div className="relative w-full max-w-[440px] xl:max-w-[460px] flex flex-col items-center justify-start overflow-visible pt-0">
            {/* Suspended 3D Industrial Camera Component */}
            <EditorialCamera
              alignProgress={alignProgress}
              isFocusing={isFocusing}
              zoomProgress={zoomProgress}
              mousePos={mousePos}
              onClick={() => handleExecute()}
              className="w-full"
            />

            {/* Floating Technical Status Pill */}
            <div className="mt-3 z-20 pointer-events-none">
              <span className="px-3.5 py-1.5 rounded-full bg-white/95 backdrop-blur-md border border-zinc-300 text-zinc-700 font-mono text-[11px] shadow-sm flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-[#FFAA33] animate-pulse" />
                {isTransitioning ? (
                  <span className="text-[#2B7FFF] font-semibold uppercase">
                    DIVING INTO OPTICS...
                  </span>
                ) : (
                  <span>CLICK CAMERA TO DIVE</span>
                )}
              </span>
            </div>
          </div>
        </div>
      </main>

      {/* Bottom Technical Status Strip */}
      <footer className="relative z-30 w-full px-6 sm:px-12 py-3.5 flex flex-col sm:flex-row items-center justify-between border-t border-zinc-200/80 font-mono text-xs text-zinc-500 bg-[#F8F9FA]">
        <div className="flex items-center gap-4">
          <span>RAZORBILL LABS</span>
          <span>•</span>
          <span>SUSPENDED 3D INDUSTRIAL OPTICAL SENSOR 50MM F/1.2 ASPH</span>
        </div>
        <div className="mt-2 sm:mt-0 flex items-center gap-2">
          <Terminal className="w-3.5 h-3.5 text-zinc-400" />
          <span>VLM INFERENCE PIPELINE: ACTIVE</span>
        </div>
      </footer>
    </div>
  );
}
