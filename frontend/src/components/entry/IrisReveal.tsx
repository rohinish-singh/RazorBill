"use client";

import React, { useEffect } from "react";
import { CCTVGateway } from "./CCTVGateway";
import {
  CameraPortalState,
  useCameraPortalTransition,
} from "./useCameraPortalTransition";

export interface IrisRevealProps {
  children: React.ReactNode;
  onStateChange?: (state: CameraPortalState) => void;
  onQuerySubmitted?: (query: string) => void;
  registerReset?: (resetFn: () => void) => void;
  className?: string;
}

export function IrisReveal({
  children,
  onStateChange,
  onQuerySubmitted,
  registerReset,
  className = "",
}: IrisRevealProps) {
  const transition = useCameraPortalTransition({
    onComplete: (query) => {
      if (query && onQuerySubmitted) {
        onQuerySubmitted(query);
      }
    },
  });

  const { portalState, alignProgress, isFocusing, zoomProgress, resetPortal, triggerPortal } =
    transition;

  // Notify parent of state changes
  useEffect(() => {
    onStateChange?.(portalState);
  }, [portalState, onStateChange]);

  // Expose reset trigger to parent
  useEffect(() => {
    registerReset?.(resetPortal);
  }, [registerReset, resetPortal]);

  const isRevealed = portalState === "revealed";
  const isDiving = portalState === "diving";

  // Circular iris radius opens as camera dives through the lens
  const irisProgress = Math.min(Math.max((zoomProgress - 0.2) / 0.8, 0), 1);
  const radiusPercent = irisProgress * 150;

  const dashboardClipPath = isRevealed
    ? "none"
    : isDiving
    ? `circle(${radiusPercent.toFixed(1)}% at 50% 50%)`
    : "circle(0% at 50% 50%)";

  return (
    <div className={`relative w-full min-h-[calc(100vh-65px)] overflow-hidden ${className}`}>
      {/* Background/Base Layer: CCTV Gateway (unmounts completely when revealed) */}
      {!isRevealed && (
        <div
          className="absolute inset-0 z-10 w-full h-full pointer-events-auto"
          style={{
            opacity: isDiving ? Math.max(0, 1 - irisProgress * 1.15) : 1,
            transition: "opacity 120ms ease-out",
          }}
        >
          <CCTVGateway
            portalState={portalState}
            alignProgress={alignProgress}
            isFocusing={isFocusing}
            zoomProgress={zoomProgress}
            onTrigger={(q) => triggerPortal(q)}
            className="w-full h-full"
          />
        </div>
      )}

      {/* Foreground/Revealed Layer: Main Industrial Dashboard */}
      <div
        className={`w-full min-h-full transition-[clip-path] duration-75 ease-out ${
          isRevealed ? "relative z-20 pointer-events-auto" : "absolute inset-0 z-20 pointer-events-none"
        }`}
        style={{
          clipPath: dashboardClipPath,
          WebkitClipPath: dashboardClipPath,
        }}
      >
        {children}
      </div>
    </div>
  );
}
