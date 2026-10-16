"use client";

import React from "react";

export interface EditorialCameraProps {
  className?: string;
  alignProgress?: number; // 0 (isometric 3/4 resting angle) to 1 (level head-on)
  isFocusing?: boolean; // Lens focus ring mechanical dilation / flare
  zoomProgress?: number; // 0 to 1 (dive scale into lens)
  mousePos?: { x: number; y: number }; // Normalized coordinates [-1, 1]
  onClick?: () => void;
}

// 72 precision knurled barrel radial ticks (precomputed for zero runtime cost)
interface TickMark {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  stroke: string;
  strokeWidth: number;
  key: number;
}

const TICKS_72: TickMark[] = Array.from({ length: 72 }, (_, i) => {
  const angleRad = ((i * 360) / 72) * (Math.PI / 180);
  const isMajor = i % 6 === 0;
  const isMed = i % 3 === 0 && !isMajor;
  const rOuter = 217;
  const rInner = isMajor ? 202 : isMed ? 208 : 212;
  const x1 = +(280 + rInner * Math.cos(angleRad)).toFixed(2);
  const y1 = +(280 + rInner * Math.sin(angleRad)).toFixed(2);
  const x2 = +(280 + rOuter * Math.cos(angleRad)).toFixed(2);
  const y2 = +(280 + rOuter * Math.sin(angleRad)).toFixed(2);
  const stroke = isMajor ? "#94A3B8" : isMed ? "#64748B" : "#334155";
  const strokeWidth = isMajor ? 1.5 : isMed ? 1.2 : 0.75;
  return { x1, y1, x2, y2, stroke, strokeWidth, key: i };
});

// 8 curved overlapping diaphragm petals around center (280, 280)
// Closed resting state: tight swirling iris with a small pinhole opening (r ~ 26px) showing
// a hint of deep dark sapphire glass and the center red sensor reticle.
// Triggered state: entire group rotates 42deg while each petal pivots & translates outward
// by 88px, expanding the aperture to r ~ 132px to unveil the full dark sapphire glass.
interface IrisPetalData {
  key: number;
  d: string;
  angleDeg: number;
  pivotX: number;
  pivotY: number;
  dirX: number;
  dirY: number;
}

const IRIS_PETALS_8: IrisPetalData[] = Array.from({ length: 8 }, (_, i) => {
  const angleDeg = i * 45;
  const rad = (angleDeg * Math.PI) / 180;

  // Outer radius 142 (clipped to 136 by shutterBarrelClip)
  // Inner curved cutting edge sweeps down to r = 26 at angleDeg + 22.5deg
  const rOut = 142;
  const rShoulder1 = 96;
  const rShoulder2 = 86;
  const rIn = 26; // Tight closed resting pinhole opening

  const a0 = ((angleDeg - 22) * Math.PI) / 180;
  const a1 = ((angleDeg + 84) * Math.PI) / 180;
  const a2 = ((angleDeg + 68) * Math.PI) / 180;
  const a3 = ((angleDeg + 22.5) * Math.PI) / 180;
  const a4 = ((angleDeg - 16) * Math.PI) / 180;

  const x0 = +(280 + rOut * Math.cos(a0)).toFixed(2);
  const y0 = +(280 + rOut * Math.sin(a0)).toFixed(2);

  const x1 = +(280 + rOut * Math.cos(a1)).toFixed(2);
  const y1 = +(280 + rOut * Math.sin(a1)).toFixed(2);

  const x2 = +(280 + rShoulder1 * Math.cos(a2)).toFixed(2);
  const y2 = +(280 + rShoulder1 * Math.sin(a2)).toFixed(2);

  const x3 = +(280 + rIn * Math.cos(a3)).toFixed(2);
  const y3 = +(280 + rIn * Math.sin(a3)).toFixed(2);

  const x4 = +(280 + rShoulder2 * Math.cos(a4)).toFixed(2);
  const y4 = +(280 + rShoulder2 * Math.sin(a4)).toFixed(2);

  // Smooth curved petal contour forming a classic swirling diaphragm
  const d = `M ${x0} ${y0} A ${rOut} ${rOut} 0 0 1 ${x1} ${y1} Q ${x2} ${y2} ${x3} ${y3} Q ${x4} ${y4} ${x0} ${y0} Z`;

  // Pivot point positioned near the outer perimeter
  const pivotX = +(280 + 132 * Math.cos(rad)).toFixed(2);
  const pivotY = +(280 + 132 * Math.sin(rad)).toFixed(2);

  const dirX = +Math.cos(rad).toFixed(4);
  const dirY = +Math.sin(rad).toFixed(4);

  return {
    key: i,
    d,
    angleDeg,
    pivotX,
    pivotY,
    dirX,
    dirY,
  };
});

// Titanium focus ring calibration markings
const FOCUS_CALIBRATIONS = [
  { label: "0.4m", angle: -125 },
  { label: "0.6m", angle: -95 },
  { label: "0.9m", angle: -65 },
  { label: "1.4m", angle: -35 },
  { label: "2.5m", angle: -5 },
  { label: "5.0m", angle: 25 },
  { label: "∞", angle: 55 },
];

export function EditorialCamera({
  className = "",
  alignProgress = 0,
  isFocusing = false,
  zoomProgress = 0,
  mousePos = { x: 0, y: 0 },
  onClick,
}: EditorialCameraProps) {
  // Camera Resting Pose & Alignment Interpolation:
  // True 3/4 isometric surveillance angle at rest: baseYaw = -32deg, basePitch = -10deg
  // Smoothly interpolates to 0deg (level head-on) as alignProgress -> 1
  const alignDamp = Math.max(0, 1 - alignProgress);
  const currentBasePitch = -10 * alignDamp;
  const currentBaseYaw = -32 * alignDamp;

  // Aperture dilation trigger: active when focusing or diving
  const isApertureOpen = isFocusing || zoomProgress > 0;

  // Mouse Parallax Offsets (damped to 0 on align)
  const rotX = (currentBasePitch + mousePos.y * -5.5 * alignDamp).toFixed(2);
  const rotY = (currentBaseYaw + mousePos.x * 5.5 * alignDamp).toFixed(2);
  const scale = (1 + zoomProgress * 8.5).toFixed(3);

  // Optical glint refractive parallax: shifts opposite to eye cursor
  const glintX = (-mousePos.x * 8 * alignDamp).toFixed(2);
  const glintY = (-mousePos.y * 8 * alignDamp).toFixed(2);

  const isDiving = zoomProgress > 0;

  return (
    <div
      role="button"
      tabIndex={0}
      onClick={onClick}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          onClick?.();
        }
      }}
      aria-label="Enter surveillance laboratory through optical camera portal"
      className={`relative w-full flex flex-col items-center select-none cursor-pointer outline-none focus-visible:ring-2 focus-visible:ring-[#2B7FFF] focus-visible:ring-offset-4 rounded-3xl overflow-visible ${className}`}
      style={{
        perspective: "1200px",
      }}
    >
      {/* ================================================================ */}
      {/* 1. ANGLED BOOMERANG NECK                                        */}
      {/* Thick architectural arm — no labels, clean industrial elbow     */}
      {/* ================================================================ */}
      <div
        className="relative z-10 flex flex-col items-center pointer-events-none select-none transition-opacity duration-300"
        style={{
          opacity: isDiving ? Math.max(0, 1 - zoomProgress * 3.5) : 1,
        }}
      >
        {/* Ceiling anchor plate */}
        <div className="w-12 h-2.5 bg-white border border-[#CBD5E1] rounded-b shadow-sm" />

        {/* Boomerang arm SVG */}
        <svg
          viewBox="0 0 200 148"
          className="w-48 h-[142px] overflow-visible drop-shadow-lg"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          <defs>
            <linearGradient id="armBodyGrad" x1="30" y1="0" x2="170" y2="148" gradientUnits="userSpaceOnUse">
              <stop offset="0%" stopColor="#FFFFFF" />
              <stop offset="30%" stopColor="#F8FAFC" />
              <stop offset="70%" stopColor="#F1F5F9" />
              <stop offset="100%" stopColor="#E2E8F0" />
            </linearGradient>
            <linearGradient id="armSpineGrad" x1="0" y1="0" x2="1" y2="0">
              <stop offset="0%" stopColor="#CBD5E1" stopOpacity="0.9" />
              <stop offset="40%" stopColor="#FFFFFF" stopOpacity="0.5" />
              <stop offset="100%" stopColor="#94A3B8" stopOpacity="0.9" />
            </linearGradient>
          </defs>
          {/* ~28px wide boomerang silhouette */}
          <path
            d="M 84 0 L 112 0 L 112 28 C 112 46 121 60 134 72 L 160 98 C 166 104 168 112 168 120 L 168 146 L 140 146 L 140 122 C 140 116 138 110 133 105 L 107 79 C 93 66 84 51 84 32 Z"
            fill="url(#armBodyGrad)"
            stroke="#CBD5E1"
            strokeWidth="1.5"
          />
          {/* Machined elbow seam */}
          <path d="M 95 54 L 118 74" stroke="#1E242B" strokeWidth="3" strokeLinecap="round" />
          {/* Spine highlight */}
          <path
            d="M 95 2 L 95 30 C 95 46 103 59 115 70 L 141 97 C 147 103 151 111 151 119 L 151 144"
            stroke="url(#armSpineGrad)"
            strokeWidth="1.2"
            fill="none"
          />
          {/* Base collar */}
          <rect x="138" y="138" width="32" height="10" rx="2" fill="#E2E8F0" stroke="#94A3B8" strokeWidth="1" />
        </svg>
      </div>

      {/* ========================================================================= */}
      {/* 2. 3D ELONGATED CAMERA ASSEMBLY ("THE BOTTLE" + "THE CAP")                 */}
      {/* Front Square Faceplate: 180px x 180px (compact, proportioned scale)       */}
      {/* Smooth continuous ~168px matte-white hull behind faceplate (ZERO slice lines)*/}
      {/* Transform-Origin: "center center" -> Zooms straight into the optical lens!*/}
      {/* ========================================================================= */}
      <div
        className="w-[180px] h-[180px] aspect-square relative flex items-center justify-center overflow-visible -mt-1"
        style={{
          transform: `perspective(1200px) rotateX(${rotX}deg) rotateY(${rotY}deg) scale3d(${scale}, ${scale}, 1)`,
          transformOrigin: "center center",
          transformStyle: "preserve-3d",
          willChange: "transform",
          transition: isDiving
            ? "transform 60ms linear"
            : "transform 180ms cubic-bezier(0.16, 1, 0.3, 1)",
        }}
      >
        {/* ================================================================ */}
        {/* 2A. SEALED 3D BOX HULL — Strict CSS 3D Cube Math               */}
        {/* Front face: 180×180px at Z=0. Box depth: 160px.                */}
        {/* All panels use transform-origin so edges snap flush with no gap */}
        {/* ================================================================ */}

        {/* ── TOP ROOF PANEL ─────────────────────────────────────────────── */}
        {/* Width: 180px, Height: 160px (the depth)                          */}
        {/* transform-origin: top center → rotateX(-90deg) swings top edge  */}
        {/* forward, rear edge goes back 160px                               */}
        <div
          className="absolute left-0 pointer-events-none overflow-hidden"
          style={{
            width: "180px",
            height: "320px",
            top: "0px",
            transformOrigin: "top center",
            transform: "rotateX(-90deg)",
            transformStyle: "preserve-3d",
            background: "linear-gradient(to bottom, #FFFFFF 0%, #F8FAFC 35%, #F1F5F9 65%, #E8EDF3 100%)",
            borderTop: "1.2px solid #CBD5E1",
            borderLeft: "1.2px solid #CBD5E1",
            borderRight: "1.2px solid #CBD5E1",
            boxShadow: "inset 0 1px 0 rgba(255,255,255,0.9)",
          }}
        >
          {/* Subtle centre ridge highlight */}
          <div className="absolute inset-x-6 top-0 bottom-0 bg-gradient-to-r from-transparent via-white/60 to-transparent" />
          {/* Roof micro-stencil */}
          <div className="absolute top-6 left-1/2 -translate-x-1/2 font-mono text-[5px] text-zinc-400 font-semibold tracking-widest uppercase opacity-70 whitespace-nowrap">
            HONEYWELL AI VISION // RZ-S4
          </div>
          {/* Safety-orange front visor lip flush with front faceplate edge */}
          <div className="absolute top-0 left-0 right-0 h-[3px] bg-[#FF3B00] shadow-[0_0_8px_rgba(255,59,0,0.5)]" />
        </div>

        {/* ── BOTTOM BELLY PANEL ─────────────────────────────────────────── */}
        {/* transform-origin: bottom center → rotateX(90deg)                */}
        <div
          className="absolute left-0 pointer-events-none"
          style={{
            width: "180px",
            height: "320px",
            bottom: "0px",
            transformOrigin: "bottom center",
            transform: "rotateX(90deg)",
            transformStyle: "preserve-3d",
            background: "linear-gradient(to top, #C8D2DC 0%, #D8E2EA 40%, #E8EEF4 100%)",
            borderLeft: "1.2px solid #94A3B8",
            borderRight: "1.2px solid #94A3B8",
            borderBottom: "1.2px solid #94A3B8",
          }}
        />

        {/* ── RIGHT SIDE PANEL ────────────────────────────────────────────── */}
        {/* Width: 160px, Height: 180px                                       */}
        {/* transform-origin: left center → rotateY(90deg) swings right edge */}
        {/* away from viewer, left edge stays at x=180 (right of front face)  */}
        <div
          className="absolute top-0 pointer-events-none overflow-hidden"
          style={{
            width: "320px",
            height: "180px",
            left: "180px",
            transformOrigin: "left center",
            transform: "rotateY(90deg)",
            transformStyle: "preserve-3d",
            background: "linear-gradient(to right, #F8FAFC 0%, #F1F5F9 45%, #E2E8F0 80%, #D8E2EA 100%)",
            borderTop: "1.2px solid #CBD5E1",
            borderRight: "1.2px solid #CBD5E1",
            borderBottom: "1.2px solid #CBD5E1",
            boxShadow: "inset 2px 0 8px rgba(0,0,0,0.05)",
          }}
        >
          {/* Cooling vent stack — 5 bars spanning the longer hull */}
          <div className="absolute left-1/3 top-1/2 -translate-y-1/2 flex flex-col gap-2.5">
            {[0, 1, 2, 3, 4].map((v) => (
              <div
                key={v}
                className="w-28 h-1.5 bg-[#1E242B] rounded-full border border-[#334155] shadow-inner flex items-center px-1"
              >
                <div className="w-full h-[1px] bg-black/50" />
              </div>
            ))}
          </div>
          {/* Micro stencil */}
          <div className="absolute bottom-6 left-4 font-mono text-[5px] text-zinc-500 font-bold tracking-widest select-none whitespace-nowrap">
            RZ-S4 // IP67 • 50MM F/1.2
          </div>
          {/* Torx fasteners */}
          <div className="absolute bottom-2.5 right-4 flex items-center gap-3">
            {[0, 1].map((f) => (
              <div key={f} className="w-1.5 h-1.5 rounded-full bg-[#CBD5E1] border border-[#94A3B8] flex items-center justify-center">
                <div className="w-0.5 h-px bg-[#64748B]" />
              </div>
            ))}
          </div>
        </div>

        {/* ── LEFT SIDE PANEL ─────────────────────────────────────────────── */}
        {/* transform-origin: right center → rotateY(-90deg)                 */}
        <div
          className="absolute top-0 pointer-events-none"
          style={{
            width: "320px",
            height: "180px",
            left: "0px",
            transformOrigin: "right center",
            transform: "rotateY(-90deg)",
            transformStyle: "preserve-3d",
            background: "linear-gradient(to left, #F8FAFC 0%, #EEF2F7 55%, #E2E8F0 100%)",
            borderTop: "1.2px solid #CBD5E1",
            borderLeft: "1.2px solid #CBD5E1",
            borderBottom: "1.2px solid #CBD5E1",
            boxShadow: "inset -2px 0 8px rgba(0,0,0,0.05)",
          }}
        />

        {/* ── REAR TAIL CAP ───────────────────────────────────────────────── */}
        {/* Sits exactly 160px behind the front face                          */}
        <div
          className="absolute inset-0 rounded-[24px] pointer-events-none bg-[#F1F5F9] border border-[#CBD5E1] shadow-2xl flex flex-col items-center justify-between p-4 select-none"
          style={{
            transform: "translateZ(-320px)",
            transformStyle: "preserve-3d",
          }}
        >
          {/* Armored Cable Gland */}
          <div className="flex flex-col items-center mt-1">
            <div className="w-7 h-4 bg-[#CBD5E1] border border-[#94A3B8] rounded-md shadow-inner flex items-center justify-center">
              <div className="w-3 h-3 rounded-full bg-[#1E293B] border border-[#64748B] flex items-center justify-center">
                <div className="w-1.5 h-1.5 rounded-full bg-[#0F172A]" />
              </div>
            </div>
            <div className="w-3 h-3 bg-gradient-to-b from-[#1E293B] to-[#334155] border-x border-[#475569]" />
          </div>
          {/* Spec stamp */}
          <div className="w-full bg-white/90 border border-zinc-200 rounded px-1.5 py-0.5 text-center font-mono">
            <div className="text-[6.5px] text-zinc-500 font-bold tracking-wider">HONEYWELL AI // IP67</div>
            <div className="text-[5.5px] text-zinc-400 tracking-tight">RZ-S4 • 48V PoE+ 802.3at</div>
          </div>
          {/* PWR LED */}
          <div className="flex items-center gap-1.5 mb-1 font-mono text-[6px] text-zinc-500">
            <span className="w-1 h-1 rounded-full bg-[#10B981] animate-pulse" />
            <span>PWR // ONLINE</span>
          </div>
        </div>

        {/* --------------------------------------------------------------------- */}
        {/* 2B. FRONT SQUARE OPTICAL FACEPLATE ("THE CAP") at translateZ(0px)     */}
        {/* Size: 256px x 256px; Contains 100% UNTOUCHED 560x560 SVG OPTICAL CORE */}
        {/* --------------------------------------------------------------------- */}
        <div
          className="w-full h-full relative"
          style={{
            transform: "translateZ(0px)",
            transformStyle: "preserve-3d",
          }}
        >
          <svg
            viewBox="0 0 560 560"
            className="w-full h-full overflow-visible drop-shadow-2xl"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            <defs>
              {/* Outer Drop Shadow */}
              <filter id="cowlShadow" x="-20%" y="-20%" width="140%" height="140%">
                <feDropShadow
                  dx="0"
                  dy="14"
                  stdDeviation="18"
                  floodColor="#0F172A"
                  floodOpacity="0.22"
                />
              </filter>

              {/* Shutter Barrel ClipPath: Ensures petals stay inside inner barrel circle */}
              <clipPath id="shutterBarrelClip">
                <circle cx="280" cy="280" r="136" />
              </clipPath>

              {/* Optical Depth Tunnel ClipPath */}
              <clipPath id="tunnelClip">
                <circle cx="280" cy="280" r="134" />
              </clipPath>

              {/* Sculpted Shroud Bevel Daylight Gradient */}
              <linearGradient id="shroudGradient" x1="0" y1="36" x2="0" y2="524" gradientUnits="userSpaceOnUse">
                <stop offset="0%" stopColor="#FFFFFF" />
                <stop offset="12%" stopColor="#F8FAFC" />
                <stop offset="50%" stopColor="#F1F5F9" />
                <stop offset="88%" stopColor="#E2E8F0" />
                <stop offset="100%" stopColor="#CBD5E1" />
              </linearGradient>

              {/* Dark Graphite Chassis Rim */}
              <linearGradient id="chassisRim" x1="24" y1="24" x2="536" y2="536" gradientUnits="userSpaceOnUse">
                <stop offset="0%" stopColor="#22272E" />
                <stop offset="50%" stopColor="#181B20" />
                <stop offset="100%" stopColor="#0F1115" />
              </linearGradient>

              {/* Recessed Barrel Well Gradient */}
              <radialGradient id="recessedWellGrad" cx="50%" cy="50%" r="50%">
                <stop offset="70%" stopColor="#0B0D11" />
                <stop offset="92%" stopColor="#161B22" />
                <stop offset="100%" stopColor="#050608" />
              </radialGradient>

              {/* Knurled Barrel Graphite Gradient */}
              <linearGradient id="barrelGrad" x1="62" y1="62" x2="498" y2="498" gradientUnits="userSpaceOnUse">
                <stop offset="0%" stopColor="#252C36" />
                <stop offset="40%" stopColor="#161A22" />
                <stop offset="100%" stopColor="#0D1015" />
              </linearGradient>

              {/* Titanium Focus Collar Gradient */}
              <radialGradient id="focusCollarGrad" cx="48%" cy="46%" r="52%">
                <stop offset="0%" stopColor="#2A323F" />
                <stop offset="75%" stopColor="#1C212B" />
                <stop offset="100%" stopColor="#12161D" />
              </radialGradient>

              {/* Deep Sapphire Convex Glass Multi-Coating Gradient (Clean, Authentic, No Blue Glow) */}
              <radialGradient id="sapphireGlass" cx="44%" cy="40%" r="58%">
                <stop offset="0%" stopColor="#040D1A" />
                <stop offset="35%" stopColor="#0B1D36" />
                <stop offset="68%" stopColor="#071222" />
                <stop offset="90%" stopColor="#030811" />
                <stop offset="100%" stopColor="#010307" />
              </radialGradient>

              {/* Primary Specular Glint Gradient */}
              <linearGradient id="primaryGlint" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#FFFFFF" stopOpacity="0.85" />
                <stop offset="45%" stopColor="#E0F2FE" stopOpacity="0.45" />
                <stop offset="100%" stopColor="#38BDF8" stopOpacity="0" />
              </linearGradient>

              {/* Secondary Anti-Reflective Glint Gradient */}
              <linearGradient id="secondaryGlint" x1="100%" y1="100%" x2="0%" y2="0%">
                <stop offset="0%" stopColor="#A855F7" stopOpacity="0.4" />
                <stop offset="60%" stopColor="#00F0FF" stopOpacity="0.18" />
                <stop offset="100%" stopColor="#2563EB" stopOpacity="0" />
              </linearGradient>

              {/* Illuminated Halo Glow Filter */}
              <filter id="haloBloom" x="-50%" y="-50%" width="200%" height="200%">
                <feGaussianBlur in="SourceGraphic" stdDeviation={isFocusing ? "7" : "3.5"} result="blur" />
                <feMerge>
                  <feMergeNode in="blur" />
                  <feMergeNode in="SourceGraphic" />
                </feMerge>
              </filter>

              {/* Text Paths along Concentric Curves */}
              <path id="textArcTop" d="M 88,280 A 192,192 0 0,1 472,280" fill="none" />
              <path id="textArcBottom" d="M 472,280 A 192,192 0 0,1 88,280" fill="none" />

              {/* Corner Fastener Gradient */}
              <linearGradient id="screwGrad" x1="0" y1="0" x2="1" y2="1">
                <stop offset="0%" stopColor="#475569" />
                <stop offset="50%" stopColor="#1E293B" />
                <stop offset="100%" stopColor="#0F172A" />
              </linearGradient>
            </defs>

            {/* ========================================================= */}
            {/* LAYER 1: OUTER HOUSING COWL & VISOR BEZEL                 */}
            {/* ========================================================= */}
            <g id="housing-cowl" filter="url(#cowlShadow)">
              {/* Outer Dark Graphite Chassis Rim */}
              <rect
                x="24"
                y="24"
                width="512"
                height="512"
                rx="54"
                fill="url(#chassisRim)"
                stroke="#0B0D10"
                strokeWidth="2.5"
              />

              {/* Sculpted Inner Shroud (Architectural Warm Off-White) */}
              <rect
                x="36"
                y="36"
                width="488"
                height="488"
                rx="44"
                fill="url(#shroudGradient)"
                stroke="#1E232B"
                strokeWidth="1.5"
              />

              {/* Precision Machined Groove: International Safety Orange Contour */}
              <rect
                x="46"
                y="46"
                width="468"
                height="468"
                rx="36"
                fill="none"
                stroke="#FF3B00"
                strokeWidth="1.75"
                opacity="0.9"
              />

              {/* Corner Precision Torx / Hex Fasteners */}
              {[
                { cx: 70, cy: 70 },
                { cx: 490, cy: 70 },
                { cx: 70, cy: 490 },
                { cx: 490, cy: 490 },
              ].map(({ cx, cy }, idx) => (
                <g key={idx}>
                  <circle cx={cx} cy={cy} r="7.5" fill="url(#screwGrad)" stroke="#334155" strokeWidth="1" />
                  <circle cx={cx} cy={cy} r="4.2" fill="#0F1318" />
                  <path
                    d={`M ${cx - 3.2} ${cy} L ${cx + 3.2} ${cy} M ${cx} ${cy - 3.2} L ${cx} ${cy + 3.2}`}
                    stroke="#64748B"
                    strokeWidth="0.8"
                  />
                </g>
              ))}

              {/* Top Status Pill: Live Recording Telemetry */}
              <g id="top-sensor-telemetry">
                <rect
                  x="228"
                  y="52"
                  width="104"
                  height="19"
                  rx="9.5"
                  fill="#14181F"
                  stroke="#2A3342"
                  strokeWidth="1"
                />
                <circle cx="242" cy="61.5" r="3" fill="#10B981">
                  <animate
                    attributeName="opacity"
                    values="1;0.3;1"
                    dur="2s"
                    repeatCount="indefinite"
                  />
                </circle>
                <text
                  x="251"
                  y="65"
                  fill="#94A3B8"
                  fontSize="8"
                  fontFamily="monospace"
                  fontWeight="700"
                  letterSpacing="1.2"
                >
                  LIVE // OPT-01
                </text>
              </g>

              {/* Blinking Red Recording LED Indicator */}
              <g id="rec-led-indicator">
                {/* LED Housing Bezel */}
                <circle cx="456" cy="62" r="8" fill="#1A0808" stroke="#2A1010" strokeWidth="0.8" />
                {/* Intense Red LED Glow Core */}
                <circle cx="456" cy="62" r="4.5" fill="#FF2400">
                  <animate
                    attributeName="opacity"
                    values="1;0.35;1"
                    dur="1s"
                    repeatCount="indefinite"
                  />
                </circle>
                {/* Bright Specular Highlight */}
                <circle cx="454.5" cy="60.5" r="1.4" fill="#FFFFFF" opacity="0.7">
                  <animate
                    attributeName="opacity"
                    values="0.7;0.2;0.7"
                    dur="1s"
                    repeatCount="indefinite"
                  />
                </circle>
                {/* REC Label */}
                <text
                  x="456"
                  y="77"
                  textAnchor="middle"
                  fill="#EF4444"
                  fontSize="7"
                  fontFamily="monospace"
                  fontWeight="700"
                  letterSpacing="0.8"
                >
                  REC
                </text>
              </g>

              {/* Bottom Technical Micro-Engraving */}
              <text
                x="280"
                y="503"
                textAnchor="middle"
                fill="#64748B"
                fontSize="7.5"
                fontFamily="monospace"
                fontWeight="600"
                letterSpacing="2"
              >
                RAZORBILL LABS • HONEYWELL LIVE VLM VISION • IP67 SENSOR
              </text>
            </g>

            {/* ========================================================= */}
            {/* LAYER 2: RECESSED WELL & CONCENTRIC OPTICAL BARREL        */}
            {/* ========================================================= */}
            <g id="optical-barrel">
              {/* Deep Recessed Well Bevel */}
              <circle
                cx="280"
                cy="280"
                r="230"
                fill="url(#recessedWellGrad)"
                stroke="#1C212B"
                strokeWidth="2.5"
              />

              {/* Ring 1: Outer Knurled Barrel */}
              <circle
                cx="280"
                cy="280"
                r="218"
                fill="url(#barrelGrad)"
                stroke="#2A3342"
                strokeWidth="2"
              />

              {/* 72 Precision Radial Degree Ticks */}
              <g id="barrel-ticks">
                {TICKS_72.map((t) => (
                  <line
                    key={t.key}
                    x1={t.x1}
                    y1={t.y1}
                    x2={t.x2}
                    y2={t.y2}
                    stroke={t.stroke}
                    strokeWidth={t.strokeWidth}
                    strokeLinecap="round"
                  />
                ))}
              </g>

              {/* Micro-Typography Engraved along Barrel Curvature */}
              <text
                fontSize="7.5"
                fill="#94A3B8"
                fontFamily="monospace"
                letterSpacing="2.6"
                fontWeight="700"
                className="select-none pointer-events-none"
              >
                <textPath href="#textArcTop" startOffset="50%" textAnchor="middle">
                  RAZORBILL OPTICAL VLM SENSOR • 50MM F/1.2 ASPH
                </textPath>
              </text>

              <text
                fontSize="7"
                fill="#64748B"
                fontFamily="monospace"
                letterSpacing="2.2"
                fontWeight="600"
                className="select-none pointer-events-none"
              >
                <textPath href="#textArcBottom" startOffset="50%" textAnchor="middle">
                  NANO AR COATING // REALTIME EDGE CLASSIFICATION
                </textPath>
              </text>
            </g>

            {/* ========================================================= */}
            {/* LAYER 3: BRUSHED TITANIUM FOCUS COLLAR                    */}
            {/* Counter-rotates when isFocusing is active                 */}
            {/* ========================================================= */}
            <g
              id="focus-collar"
              style={{
                transform: isFocusing ? "rotate(-35deg)" : "rotate(0deg)",
                transformOrigin: "280px 280px",
                transition: "transform 800ms cubic-bezier(0.16, 1, 0.3, 1)",
              }}
            >
              {/* Base Collar Ring */}
              <circle
                cx="280"
                cy="280"
                r="182"
                fill="url(#focusCollarGrad)"
                stroke="#334155"
                strokeWidth="1.5"
              />

              {/* Machined Micro-Grooves */}
              <circle cx="280" cy="280" r="174" fill="none" stroke="#1E2633" strokeWidth="0.8" />
              <circle cx="280" cy="280" r="166" fill="none" stroke="#263142" strokeWidth="0.8" />
              <circle cx="280" cy="280" r="158" fill="none" stroke="#1E2633" strokeWidth="0.8" />

              {/* Distance Calibration Pips & Typography */}
              {FOCUS_CALIBRATIONS.map(({ label, angle }, idx) => {
                const rad = (angle * Math.PI) / 180;
                const rMark = 170;
                const rText = 155;
                const mx = 280 + rMark * Math.cos(rad);
                const my = 280 + rMark * Math.sin(rad);
                const tx = 280 + rText * Math.cos(rad);
                const ty = 280 + rText * Math.sin(rad);

                return (
                  <g key={idx}>
                    {/* Blue Calibration Line */}
                    <line
                      x1={mx}
                      y1={my}
                      x2={mx + 6 * Math.cos(rad)}
                      y2={my + 6 * Math.sin(rad)}
                      stroke="#2B7FFF"
                      strokeWidth="1.6"
                      strokeLinecap="round"
                    />
                    {/* Distance Number */}
                    <text
                      x={tx}
                      y={ty + 3}
                      textAnchor="middle"
                      fill="#E2E8F0"
                      fontSize="7"
                      fontFamily="monospace"
                      fontWeight="700"
                      transform={`rotate(${angle + 90}, ${tx}, ${ty})`}
                    >
                      {label}
                    </text>
                  </g>
                );
              })}
            </g>

            {/* ========================================================= */}
            {/* LAYER 4: ILLUMINATED OPTICAL HALO RING                    */}
            {/* Pulses at idle, flares on focus                          */}
            {/* ========================================================= */}
            <g id="halo-ring">
              {/* Halo Mounting Bezel */}
              <circle
                cx="280"
                cy="280"
                r="147"
                fill="#0D1015"
                stroke="#212834"
                strokeWidth="2"
              />

              {/* Luminous Amber Halo Core */}
              <circle
                cx="280"
                cy="280"
                r="143"
                fill="none"
                stroke={isFocusing ? "#FFAA33" : "#FF6B00"}
                strokeWidth={isFocusing ? 5 : 3}
                filter="url(#haloBloom)"
                opacity={isFocusing ? 1 : 0.85}
                style={{
                  transition:
                    "stroke-width 300ms ease, stroke 300ms ease, opacity 300ms ease",
                }}
              />

              {/* High-Contrast Halo Inner Razor Line */}
              <circle
                cx="280"
                cy="280"
                r="143"
                fill="none"
                stroke="#FFF1E0"
                strokeWidth={isFocusing ? 1.5 : 0.75}
                opacity={isFocusing ? 0.95 : 0.65}
              />
            </g>

            {/* ========================================================= */}
            {/* LAYER 5: DEEP SAPPHIRE GLASS ELEMENT & RETICLE            */}
            {/* Pure, clean dark sapphire glass (no bright blue glow)    */}
            {/* ========================================================= */}
            <g id="optical-depth-tunnel" clipPath="url(#tunnelClip)">
              {/* Convex Multi-Coated Deep Sapphire Glass Element */}
              <circle
                cx="280"
                cy="280"
                r="134"
                fill="url(#sapphireGlass)"
                stroke="#090E17"
                strokeWidth="2"
              />

              {/* Concentric Multi-Coating Optical Reflection Rings */}
              <circle cx="280" cy="280" r="104" fill="none" stroke="#2B7FFF" strokeWidth="1" opacity="0.3" />
              <circle cx="280" cy="280" r="82" fill="none" stroke="#00F0FF" strokeWidth="0.8" opacity="0.25" />
              <circle cx="280" cy="280" r="58" fill="none" stroke="#A855F7" strokeWidth="0.6" opacity="0.2" />
              <circle cx="280" cy="280" r="38" fill="none" stroke="#FF6B00" strokeWidth="0.6" opacity="0.25" />

              {/* Center Precision Sensor Die Reticle */}
              <g id="sensor-reticle">
                <line x1="268" y1="280" x2="275" y2="280" stroke="#FF3B00" strokeWidth="0.8" />
                <line x1="285" y1="280" x2="292" y2="280" stroke="#FF3B00" strokeWidth="0.8" />
                <line x1="280" y1="268" x2="280" y2="275" stroke="#FF3B00" strokeWidth="0.8" />
                <line x1="280" y1="285" x2="280" y2="292" stroke="#FF3B00" strokeWidth="0.8" />
                <circle cx="280" cy="280" r="4" fill="none" stroke="#FF3B00" strokeWidth="0.8" />
                <circle cx="280" cy="280" r="1.5" fill="#FF3B00" />
              </g>

              {/* Parallax Specular Reflections (Refractive glass depth) */}
              <g
                id="specular-glints"
                style={{
                  transform: `translate(${glintX}px, ${glintY}px)`,
                  transition: "transform 100ms ease-out",
                }}
              >
                {/* Primary Anamorphic Crescent Glint (Upper-Right) */}
                <path
                  d="M 230 220 C 265 190 325 200 355 240 C 335 220 285 210 245 230 Z"
                  fill="url(#primaryGlint)"
                />

                {/* Secondary Soft Coating Crescent Bounce (Lower-Left) */}
                <path
                  d="M 205 325 C 225 355 275 365 315 350 C 285 355 240 345 220 320 Z"
                  fill="url(#secondaryGlint)"
                />

                {/* Pinpoint Specular Highlight Star */}
                <circle cx="330" cy="225" r="2.8" fill="#FFFFFF" opacity="0.9" />
                <circle cx="338" cy="232" r="1.5" fill="#E0F2FE" opacity="0.75" />
              </g>
            </g>

            {/* ========================================================= */}
            {/* LAYER 6: 8-PETAL MECHANICAL SWIRLING IRIS SHUTTER         */}
            {/* Starts closed (r~26px pinhole), swirls & dilates to 132px */}
            {/* ========================================================= */}
            <g
              id="iris-shutter-assembly"
              clipPath="url(#shutterBarrelClip)"
              style={{
                transform: `rotate(${isApertureOpen ? 42 : 0}deg)`,
                transformOrigin: "280px 280px",
                transition: "transform 750ms cubic-bezier(0.22, 1, 0.36, 1)",
              }}
            >
              {IRIS_PETALS_8.map((petal) => {
                const tx = isApertureOpen ? +(88 * petal.dirX).toFixed(2) : 0;
                const ty = isApertureOpen ? +(88 * petal.dirY).toFixed(2) : 0;
                const rot = isApertureOpen ? 22 : 0;

                return (
                  <g
                    key={petal.key}
                    style={{
                      transform: `translate(${tx}px, ${ty}px) rotate(${rot}deg)`,
                      transformOrigin: `${petal.pivotX}px ${petal.pivotY}px`,
                      transition: "transform 750ms cubic-bezier(0.22, 1, 0.36, 1)",
                    }}
                  >
                    <path
                      d={petal.d}
                      fill="#0F1318"
                      stroke="#262C36"
                      strokeWidth="1.2"
                      strokeLinejoin="round"
                      opacity="0.98"
                    />
                  </g>
                );
              })}
            </g>
          </svg>
        </div>

        {/* --------------------------------------------------------------------- */}
        {/* 2C. SOFT VISOR DROP SHADOW ON TOP BEZEL (translateZ(1px))             */}
        {/* --------------------------------------------------------------------- */}
        <div
          className="absolute top-0 left-0 right-0 h-10 bg-gradient-to-b from-black/45 via-black/15 to-transparent pointer-events-none rounded-t-[44px]"
          style={{
            transform: "translateZ(1px)",
          }}
        />
      </div>
    </div>
  );
}
