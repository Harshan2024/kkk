"use client";

import { useState, useEffect } from "react";
import { Shield, Users, Activity, Server, Database, Cpu, RefreshCw, AlertTriangle, CheckCircle, Clock, BarChart3 } from "lucide-react";

interface ComponentStatus {
  status: string;
  indicator: "green" | "yellow" | "red";
  [key: string]: unknown;
}

interface HealthDashboard {
  status: string;
  timestamp: string;
  uptime_seconds: number;
  components: {
    backend: ComponentStatus;
    database: ComponentStatus;
    cache: ComponentStatus;
    ai_engine: ComponentStatus;
    circuit_breakers: ComponentStatus;
    resources: ComponentStatus & {
      cpu_pct?: number;
      memory_pct?: number;
      disk_pct?: number;
    };
  };
  metrics: Record<string, number>;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

const INDICATOR_COLORS: Record<string, string> = {
  green:  "bg-emerald-500",
  yellow: "bg-amber-400",
  red:    "bg-red-500",
};

const INDICATOR_RING: Record<string, string> = {
  green:  "ring-emerald-500/30",
  yellow: "ring-amber-400/30",
  red:    "ring-red-500/30",
};

const STATUS_EMOJI: Record<string, string> = {
  healthy:  "🟢",
  warning:  "🟡",
  critical: "🔴",
};

function StatusBadge({ indicator, label }: { indicator: string; label: string }) {
  const color = INDICATOR_COLORS[indicator] || "bg-gray-500";
  const ring  = INDICATOR_RING[indicator] || "ring-gray-500/30";
  return (
    <div className={`flex items-center gap-2 px-3 py-1 rounded-full ring-1 ${ring} bg-white/5`}>
      <span className={`w-2 h-2 rounded-full ${color} shadow-lg`} style={{ boxShadow: `0 0 6px var(--tw-shadow-color)` }} />
      <span className="text-xs font-medium text-gray-300 capitalize">{label}</span>
    </div>
  );
}

function MetricCard({
  icon: Icon,
  title,
  value,
  sub,
  indicator,
}: {
  icon: React.ElementType;
  title: string;
  value: string | number;
  sub?: string;
  indicator?: string;
}) {
  const color = INDICATOR_COLORS[indicator || "green"];
  return (
    <div className="relative bg-white/5 border border-white/10 rounded-2xl p-5 hover:bg-white/8 transition-all">
      <div className="flex items-start justify-between mb-3">
        <div className="p-2 rounded-xl bg-emerald-500/15">
          <Icon className="w-5 h-5 text-emerald-400" />
        </div>
        {indicator && (
          <span className={`w-2.5 h-2.5 rounded-full mt-1 ${color}`} />
        )}
      </div>
      <div className="text-2xl font-bold text-white mb-1">{value}</div>
      <div className="text-sm text-gray-400">{title}</div>
      {sub && <div className="text-xs text-gray-500 mt-1">{sub}</div>}
    </div>
  );
}

function formatUptime(seconds: number): string {
  const d = Math.floor(seconds / 86400);
  const h = Math.floor((seconds % 86400) / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = Math.floor(seconds % 60);
  if (d > 0) return `${d}d ${h}h ${m}m`;
  if (h > 0) return `${h}h ${m}m ${s}s`;
  return `${m}m ${s}s`;
}

export default function AdminPage() {
  const [dashboard, setDashboard] = useState<HealthDashboard | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);

  const fetchDashboard = async () => {
    try {
      const token = typeof window !== "undefined"
        ? localStorage.getItem("carbon_access_token") || sessionStorage.getItem("carbon_access_token")
        : null;

      const res = await fetch(`${API_BASE}/api/v1/admin/health-dashboard`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });

      if (!res.ok) {
        throw new Error(res.status === 403 ? "Admin access required" : `HTTP ${res.status}`);
      }

      const data = await res.json();
      setDashboard(data);
      setError(null);
      setLastRefresh(new Date());
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load dashboard");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboard();
    if (!autoRefresh) return;
    const interval = setInterval(fetchDashboard, 30000);
    return () => clearInterval(interval);
  }, [autoRefresh]);

  return (
    <div className="min-h-screen bg-gray-950 text-white p-6 md:p-10">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
        <div className="flex items-center gap-3">
          <div className="p-3 rounded-2xl bg-emerald-500/15">
            <Shield className="w-7 h-7 text-emerald-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">Admin Dashboard</h1>
            <p className="text-sm text-gray-400">CarbonTracker AI — System Health Monitor</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {lastRefresh && (
            <span className="text-xs text-gray-500 flex items-center gap-1">
              <Clock className="w-3 h-3" />
              {lastRefresh.toLocaleTimeString()}
            </span>
          )}
          <button
            onClick={() => setAutoRefresh(v => !v)}
            className={`text-xs px-3 py-1.5 rounded-lg border transition-all ${
              autoRefresh
                ? "border-emerald-500/50 text-emerald-400 bg-emerald-500/10"
                : "border-white/10 text-gray-400"
            }`}
          >
            {autoRefresh ? "Auto ✓" : "Auto"}
          </button>
          <button
            onClick={() => { setLoading(true); fetchDashboard(); }}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-emerald-500/15 text-emerald-400 hover:bg-emerald-500/25 transition-all text-sm"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>
        </div>
      </div>

      {/* Error state */}
      {error && (
        <div className="mb-6 flex items-center gap-3 p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400">
          <AlertTriangle className="w-5 h-5 shrink-0" />
          <span className="text-sm">{error}</span>
        </div>
      )}

      {/* Loading skeleton */}
      {loading && !dashboard && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="h-32 rounded-2xl bg-white/5 animate-pulse" />
          ))}
        </div>
      )}

      {/* Dashboard */}
      {dashboard && (
        <>
          {/* Overall Status Banner */}
          <div className={`mb-6 p-4 rounded-2xl border flex items-center gap-4 ${
            dashboard.status === "healthy"
              ? "border-emerald-500/30 bg-emerald-500/10"
              : dashboard.status === "warning"
              ? "border-amber-400/30 bg-amber-400/10"
              : "border-red-500/30 bg-red-500/10"
          }`}>
            <span className="text-3xl">{STATUS_EMOJI[dashboard.status] || "⚪"}</span>
            <div>
              <div className="font-bold text-white capitalize">System {dashboard.status}</div>
              <div className="text-xs text-gray-400">
                Uptime: {formatUptime(dashboard.uptime_seconds)} •{" "}
                Last checked: {new Date(dashboard.timestamp).toLocaleTimeString()}
              </div>
            </div>
          </div>

          {/* Component Status Grid */}
          <div className="mb-8">
            <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4">
              Component Health
            </h2>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
              {Object.entries(dashboard.components).map(([name, comp]) => (
                <div
                  key={name}
                  className="flex flex-col items-center gap-2 p-4 rounded-xl bg-white/5 border border-white/10 hover:bg-white/8 transition-all"
                >
                  <span className={`w-3 h-3 rounded-full ${INDICATOR_COLORS[comp.indicator] || "bg-gray-500"} shadow-lg`} />
                  <span className="text-xs text-gray-300 text-center capitalize">
                    {name.replace(/_/g, " ")}
                  </span>
                  <StatusBadge indicator={comp.indicator} label={comp.status || comp.indicator} />
                </div>
              ))}
            </div>
          </div>

          {/* Resource Metrics */}
          <div className="mb-8">
            <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4">
              System Resources
            </h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <MetricCard
                icon={Cpu}
                title="CPU Usage"
                value={`${dashboard.components.resources?.cpu_pct?.toFixed(1) ?? "—"}%`}
                indicator={
                  (dashboard.components.resources?.cpu_pct ?? 0) > 80 ? "red"
                  : (dashboard.components.resources?.cpu_pct ?? 0) > 60 ? "yellow"
                  : "green"
                }
              />
              <MetricCard
                icon={Server}
                title="Memory Usage"
                value={`${dashboard.components.resources?.memory_pct?.toFixed(1) ?? "—"}%`}
                indicator={
                  (dashboard.components.resources?.memory_pct ?? 0) > 85 ? "red"
                  : (dashboard.components.resources?.memory_pct ?? 0) > 70 ? "yellow"
                  : "green"
                }
              />
              <MetricCard
                icon={Database}
                title="Database"
                value={dashboard.components.database.status}
                indicator={dashboard.components.database.indicator}
              />
              <MetricCard
                icon={Activity}
                title="AI Engine"
                value={dashboard.components.ai_engine.status}
                indicator={dashboard.components.ai_engine.indicator}
              />
            </div>
          </div>

          {/* Error Metrics */}
          <div className="mb-8">
            <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4">
              Reliability Counters
            </h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <MetricCard icon={BarChart3}  title="DB Retries"          value={dashboard.metrics.db_retries ?? 0}           />
              <MetricCard icon={AlertTriangle} title="Circuit Breaker Opens" value={dashboard.metrics.circuit_breaker_opens ?? 0} />
              <MetricCard icon={Activity}   title="AI Failures"         value={dashboard.metrics.ai_failures ?? 0}          />
              <MetricCard icon={RefreshCw}  title="Rate Limit Hits"     value={dashboard.metrics.rate_limit_hits ?? 0}      />
            </div>
          </div>

          {/* Admin Actions placeholder */}
          <div className="border border-white/10 rounded-2xl p-6 bg-white/5">
            <div className="flex items-center gap-3 mb-4">
              <Users className="w-5 h-5 text-emerald-400" />
              <h2 className="text-sm font-semibold text-white">User Management</h2>
              <span className="ml-auto px-2 py-0.5 rounded-full bg-amber-400/15 text-amber-400 text-xs">Coming v1.3.0</span>
            </div>
            <p className="text-sm text-gray-500">
              Full user management (suspend, role assignment, data export) will be available in v1.3.0.
              RBAC enforcement is already implemented in the backend via <code className="text-emerald-400 text-xs">rbac.py</code>.
            </p>
          </div>
        </>
      )}
    </div>
  );
}
