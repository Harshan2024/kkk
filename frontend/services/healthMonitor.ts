/**
 * healthMonitor.ts — CarbonTracker Background Health Monitor
 * ===========================================================
 * Lightweight singleton that polls /api/system/status every 45 seconds.
 *
 * Features:
 *  - Pauses polling when the browser tab is hidden (visibilitychange)
 *  - Resumes immediately when tab becomes visible
 *  - Dispatches "carbontracker:health" CustomEvent with SystemHealth payload
 *  - Never blocks the UI thread
 *  - Single interval even if start() is called multiple times
 *
 * Usage:
 *   healthMonitor.start();   // called once in AIStoreProvider
 *   healthMonitor.stop();    // called on logout / unmount
 *
 * Listen for updates anywhere:
 *   window.addEventListener("carbontracker:health", (e) => {
 *     const health = (e as CustomEvent).detail;
 *   });
 */

import type { SystemHealth } from "./api";

const HOST = process.env.NEXT_PUBLIC_API_URL || "https://kkk-harshan-sona.onrender.com";
const POLL_INTERVAL_MS = 45_000;
const PROBE_TIMEOUT_MS = 10_000;

class HealthMonitor {
  private _intervalId: ReturnType<typeof setInterval> | null = null;
  private _started = false;

  /** Start polling. Safe to call multiple times — only one interval runs. */
  start(): void {
    if (this._started) return;
    this._started = true;

    // Poll immediately on start, then every POLL_INTERVAL_MS
    this._poll();
    this._intervalId = setInterval(() => this._poll(), POLL_INTERVAL_MS);

    // Pause/resume based on tab visibility
    if (typeof document !== "undefined") {
      document.addEventListener("visibilitychange", this._handleVisibility);
    }
  }

  /** Stop polling and clean up. */
  stop(): void {
    if (this._intervalId !== null) {
      clearInterval(this._intervalId);
      this._intervalId = null;
    }
    this._started = false;
    if (typeof document !== "undefined") {
      document.removeEventListener("visibilitychange", this._handleVisibility);
    }
  }

  private _handleVisibility = (): void => {
    if (document.visibilityState === "visible") {
      // Tab became visible — probe immediately then restart interval
      this._poll();
      if (this._intervalId !== null) clearInterval(this._intervalId);
      this._intervalId = setInterval(() => this._poll(), POLL_INTERVAL_MS);
    } else {
      // Tab hidden — pause polling to save resources
      if (this._intervalId !== null) {
        clearInterval(this._intervalId);
        this._intervalId = null;
      }
    }
  };

  private async _poll(): Promise<void> {
    if (typeof window === "undefined") return;
    try {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), PROBE_TIMEOUT_MS);

      const response = await fetch(`${HOST}/api/system/status`, {
        signal: controller.signal,
        cache: "no-store",
      });
      clearTimeout(timeout);

      let health: SystemHealth;

      if (!response.ok) {
        const status = response.status;
        if (status === 401 || status === 403) {
          // Reachable but auth issue on public endpoint — treat as online
          health = { backend: "online", database: "unknown", ai: "online", ocr: "online", cache: "online", iot: "online", failed: false };
        } else if (status === 404) {
          health = { backend: "degraded", database: "degraded", ai: "degraded", ocr: "degraded", cache: "degraded", iot: "degraded", failed: false };
        } else {
          health = { backend: "error", database: "unknown", ai: "unknown", ocr: "unknown", cache: "unknown", iot: "unknown", failed: true };
        }
      } else {
        const data = await response.json();
        const d = ("data" in data ? data.data : data) as Partial<SystemHealth>;
        health = {
          backend:  d.backend  || "online",
          database: d.database || "online",
          ai:       d.ai       || "online",
          ocr:      d.ocr      || "online",
          cache:    d.cache    || "online",
          iot:      d.iot      || "online",
          failed:   false,
        };
      }

      window.dispatchEvent(new CustomEvent<SystemHealth>("carbontracker:health", { detail: health }));
    } catch {
      // Network/timeout — backend unreachable
      const offlineHealth: SystemHealth = {
        backend: "offline", database: "offline", ai: "offline",
        ocr: "offline", cache: "offline", iot: "offline", failed: true,
      };
      window.dispatchEvent(new CustomEvent<SystemHealth>("carbontracker:health", { detail: offlineHealth }));
    }
  }
}

/** Singleton export — import this anywhere in the app. */
export const healthMonitor = new HealthMonitor();
