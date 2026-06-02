"use client";

/**
 * SystemStatusWidget.tsx — CarbonTracker System Health Monitor
 * =============================================================
 * Displays live backend system health in the dashboard.
 * Gracefully handles all offline/degraded states without crashing.
 */

import React, { useState, useCallback, memo } from "react";
import { Activity, Database, Cpu, Camera, Wifi, RefreshCw, CheckCircle2, AlertCircle, XCircle } from "lucide-react";
import { useAIStore } from "../stores/aiStore";

type StatusLevel = "healthy" | "degraded" | "error" | "offline" | "offline_safe_mode" | "unknown";

function getStatusConfig(status: string | undefined): {
  label: string;
  color: string;
  dot: string;
  icon: typeof CheckCircle2;
} {
  const s = (status || "unknown").toLowerCase();
  if (s === "healthy" || s === "ok" || s === "connected" || s === "working")
    return { label: "Online", color: "text-emerald-400", dot: "bg-emerald-500", icon: CheckCircle2 };
  if (s === "degraded" || s === "offline_safe_mode" || s === "unavailable")
    return { label: "Degraded", color: "text-amber-400", dot: "bg-amber-500", icon: AlertCircle };
  if (s === "offline" || s === "disconnected")
    return { label: "Offline", color: "text-stone-500", dot: "bg-stone-600", icon: XCircle };
  if (s === "error")
    return { label: "Error", color: "text-rose-400", dot: "bg-rose-500", icon: XCircle };
  return { label: "Unknown", color: "text-stone-500", dot: "bg-stone-600", icon: AlertCircle };
}

const StatusRow = memo(function StatusRow({
  icon: Icon,
  label,
  status,
}: {
  icon: React.ElementType;
  label: string;
  status: string | undefined;
}) {
  const cfg = getStatusConfig(status);
  const StatusIcon = cfg.icon;
  return (
    <div className="flex items-center justify-between py-1.5 border-b border-white/[0.03] last:border-b-0">
      <div className="flex items-center gap-2">
        <div className="w-5 h-5 rounded-md bg-white/[0.03] flex items-center justify-center">
          <Icon className="w-3 h-3 text-stone-500" />
        </div>
        <span className="text-[10px] font-bold text-stone-400 uppercase tracking-wider">{label}</span>
      </div>
      <div className="flex items-center gap-1.5">
        <div className={`w-1.5 h-1.5 rounded-full ${cfg.dot} animate-pulse`} />
        <span className={`text-[10px] font-extrabold uppercase ${cfg.color}`}>{cfg.label}</span>
      </div>
    </div>
  );
});

export default memo(function SystemStatusWidget() {
  const { systemHealth, fetchSystemHealth } = useAIStore();
  const [refreshing, setRefreshing] = useState(false);

  const handleRefresh = useCallback(async () => {
    setRefreshing(true);
    try {
      await fetchSystemHealth();
    } finally {
      setTimeout(() => setRefreshing(false), 600);
    }
  }, [fetchSystemHealth]);

  return (
    <div className="glass-card rounded-2xl p-4 select-none">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <div className="w-5 h-5 rounded-lg bg-emerald-500/10 flex items-center justify-center border border-emerald-500/20">
            <Activity className="w-3 h-3 text-emerald-400" />
          </div>
          <span className="text-[9px] font-black uppercase tracking-widest text-stone-400">
            System Status
          </span>
        </div>
        <button
          onClick={handleRefresh}
          className="p-1 rounded-lg hover:bg-white/5 transition-colors cursor-pointer"
          title="Refresh system status"
        >
          <RefreshCw className={`w-3 h-3 text-stone-500 ${refreshing ? "animate-spin" : ""}`} />
        </button>
      </div>

      <div className="space-y-0">
        <StatusRow
          icon={Cpu}
          label="Backend"
          status={systemHealth ? "healthy" : "unknown"}
        />
        <StatusRow
          icon={Database}
          label="Database"
          status={systemHealth?.database?.status}
        />
        <StatusRow
          icon={Cpu}
          label="AI Engine"
          status={systemHealth?.ai?.status}
        />
        <StatusRow
          icon={Camera}
          label="OCR"
          status={systemHealth?.ocr?.status}
        />
        <StatusRow
          icon={Wifi}
          label="IoT"
          status={systemHealth?.iot?.status}
        />
      </div>
    </div>
  );
});
