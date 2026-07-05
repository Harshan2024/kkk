"use client";

import React, { useEffect, useRef, useState } from "react";

/**
 * PremiumCursor — custom cursor overlay
 * - Disabled automatically on touch devices (pointer: coarse)
 * - Dot follows mouse immediately, ring follows with lag
 * - Grows on hoverable elements, shrinks on click
 */
export default function PremiumCursor() {
  const dotRef = useRef<HTMLDivElement>(null);
  const ringRef = useRef<HTMLDivElement>(null);
  const [visible, setVisible] = useState(false);
  const pos = useRef({ x: -100, y: -100 });
  const ringPos = useRef({ x: -100, y: -100 });
  const rafId = useRef<number>(0);

  useEffect(() => {
    // Bail on touch devices
    if (typeof window === "undefined") return;
    if (window.matchMedia("(pointer: coarse)").matches) return;

    setVisible(true);

    const onMouseMove = (e: MouseEvent) => {
      pos.current = { x: e.clientX, y: e.clientY };
    };

    const onMouseDown = () => {
      ringRef.current?.classList.add("cursor-click");
    };
    const onMouseUp = () => {
      ringRef.current?.classList.remove("cursor-click");
    };

    const onMouseEnterInteractive = () => {
      ringRef.current?.classList.add("cursor-hover");
    };
    const onMouseLeaveInteractive = () => {
      ringRef.current?.classList.remove("cursor-hover");
    };

    const addInteractiveListeners = () => {
      document.querySelectorAll("button, a, [role='button'], input, select, textarea, label[for]").forEach(el => {
        el.addEventListener("mouseenter", onMouseEnterInteractive);
        el.addEventListener("mouseleave", onMouseLeaveInteractive);
      });
    };

    // Smooth ring lag animation
    const animate = () => {
      const lag = 0.12;
      ringPos.current.x += (pos.current.x - ringPos.current.x) * lag;
      ringPos.current.y += (pos.current.y - ringPos.current.y) * lag;

      if (dotRef.current) {
        dotRef.current.style.transform = `translate(${pos.current.x - 4}px, ${pos.current.y - 4}px)`;
      }
      if (ringRef.current) {
        ringRef.current.style.transform = `translate(${ringPos.current.x - 16}px, ${ringPos.current.y - 16}px)`;
      }

      rafId.current = requestAnimationFrame(animate);
    };

    document.addEventListener("mousemove", onMouseMove);
    document.addEventListener("mousedown", onMouseDown);
    document.addEventListener("mouseup", onMouseUp);
    addInteractiveListeners();

    rafId.current = requestAnimationFrame(animate);

    // Re-attach on DOM changes for dynamic elements
    const observer = new MutationObserver(addInteractiveListeners);
    observer.observe(document.body, { childList: true, subtree: true });

    return () => {
      document.removeEventListener("mousemove", onMouseMove);
      document.removeEventListener("mousedown", onMouseDown);
      document.removeEventListener("mouseup", onMouseUp);
      cancelAnimationFrame(rafId.current);
      observer.disconnect();
    };
  }, []);

  if (!visible) return null;

  return (
    <>
      <div ref={dotRef} className="premium-cursor-dot" aria-hidden="true" />
      <div ref={ringRef} className="premium-cursor-ring" aria-hidden="true" />
    </>
  );
}
