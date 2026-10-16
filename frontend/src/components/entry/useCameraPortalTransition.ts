"use client";

import { useState, useRef, useCallback, useEffect } from "react";

export type CameraPortalState =
  | "idle"
  | "aligning"
  | "focusing"
  | "diving"
  | "revealed";

export interface UseCameraPortalTransitionOptions {
  onComplete?: (query?: string) => void;
}

export function useCameraPortalTransition(
  options?: UseCameraPortalTransitionOptions
) {
  const [portalState, setPortalState] = useState<CameraPortalState>("idle");
  const [alignProgress, setAlignProgress] = useState(0); // 0 to 1
  const [isFocusing, setIsFocusing] = useState(false);
  const [zoomProgress, setZoomProgress] = useState(0); // 0 to 1
  const [submittedQuery, setSubmittedQuery] = useState<string>("");

  const stateRef = useRef<CameraPortalState>("idle");
  const onCompleteRef = useRef(options?.onComplete);

  useEffect(() => {
    stateRef.current = portalState;
  }, [portalState]);

  useEffect(() => {
    onCompleteRef.current = options?.onComplete;
  }, [options?.onComplete]);

  // Main trigger: glides -> focuses -> dives -> reveals
  const triggerPortal = useCallback((query?: string) => {
    if (stateRef.current !== "idle") return;

    if (query) {
      setSubmittedQuery(query);
    }

    const prefersReducedMotion =
      typeof window !== "undefined" &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    if (prefersReducedMotion) {
      setAlignProgress(1);
      setZoomProgress(1);
      setPortalState("revealed");
      onCompleteRef.current?.(query);
      return;
    }

    // Phase 1: Camera smoothly glides to center & levels head-on (600ms ease-out)
    setPortalState("aligning");
    const alignStartTime = performance.now();
    const alignDuration = 600;

    const animateAlign = (now: number) => {
      const elapsed = now - alignStartTime;
      const progress = Math.min(elapsed / alignDuration, 1);
      // Ease out cubic: 1 - (1 - t)^3
      const easeOut = 1 - Math.pow(1 - progress, 3);
      setAlignProgress(easeOut);

      if (progress < 1) {
        requestAnimationFrame(animateAlign);
      } else {
        setAlignProgress(1);

        // Phase 2: Lens focus rings dilate/spin (1000ms focusing state)
        setPortalState("focusing");
        setIsFocusing(true);

        setTimeout(() => {
          setIsFocusing(false);

          // Phase 3: Camera dollies forward into the lens (1200ms ease-in-out)
          setPortalState("diving");
          const diveStartTime = performance.now();
          const diveDuration = 1200;

          const animateDive = (diveNow: number) => {
            const diveElapsed = diveNow - diveStartTime;
            const diveProgress = Math.min(diveElapsed / diveDuration, 1);

            // Ease in-out cubic
            const easeInOut =
              diveProgress < 0.5
                ? 4 * diveProgress * diveProgress * diveProgress
                : 1 - Math.pow(-2 * diveProgress + 2, 3) / 2;

            setZoomProgress(easeInOut);

            if (diveProgress < 1) {
              requestAnimationFrame(animateDive);
            } else {
              setZoomProgress(1);

              // Phase 4: Fully revealed
              setPortalState("revealed");
              onCompleteRef.current?.(query);
            }
          };

          requestAnimationFrame(animateDive);
        }, 1000);
      }
    };

    requestAnimationFrame(animateAlign);
  }, []);

  const resetPortal = useCallback(() => {
    setPortalState("idle");
    setAlignProgress(0);
    setIsFocusing(false);
    setZoomProgress(0);
    setSubmittedQuery("");
  }, []);

  return {
    portalState,
    alignProgress,
    isFocusing,
    zoomProgress,
    submittedQuery,
    triggerPortal,
    resetPortal,
  };
}

