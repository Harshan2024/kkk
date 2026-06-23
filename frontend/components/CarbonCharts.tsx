"use client";

import React, { useEffect, useState } from "react";
import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Tooltip as ChartTooltip,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  ReferenceLine,
} from "recharts";
import { DashboardSummary } from "../services/api";
import {
  PieChart as PieIcon,
  LineChart as LineIcon,
  Calendar,
  TrendingUp,
  TrendingDown,
  Minus,
  Sparkles,
  BrainCircuit,
  RefreshCw,
  Flame,
  Award,
  Leaf,
  Activity,
} from "lucide-react";
import { useAIStore } from "../stores/aiStore";
import { motion, AnimatePresence } from "framer-motion";

interface CarbonChartsProps {
  summary: DashboardSummary | null;
}

const CATEGORY_COLORS: Record<string, string> = {
  food: "#10b981",       // Emerald Green
  transport: "#0284c7",  // Sky Blue
  energy: "#eab308",     // Yellow/Gold
  waste: "#ef4444",      // Rose Red
};

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    const item = payload[0]?.payload;
    return (
      <div className="glass-card bg-stone-900/95 px-3.5 py-2.5 rounded-xl border border-white/10 text-xs shadow-xl backdrop-blur-md">
        <p className="font-extrabold text-[9px] text-stone-500 uppercase tracking-widest mb-1.5 border-b border-white/5 pb-1">
          {item?.date_full || label}
        </p>
        <div className="space-y-1 font-bold">
          {payload.map((item: any, idx: number) => (
            <div key={idx} className="flex justify-between items-center gap-4">
              <span className="text-stone-400 flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: item.stroke || item.color || item.fill }}></span>
                {item.name}:
              </span>
              <span className="text-stone-200">{Number(item.value).toFixed(2)} kg</span>
            </div>
          ))}
        </div>
      </div>
    );
  }
  return null;
};

export default function CarbonCharts({ summary }: CarbonChartsProps) {
  const [isMounted, setIsMounted] = useState(false);
  const [activeChartTab, setActiveChartTab] = useState<"historical" | "forecast">("historical");
  const [selectedModel, setSelectedModel] = useState("prophet");

  const {
    analyticsData,
    analyticsLoading,
    fetchAnalytics,
    forecastData,
    forecastLoading,
    forecastStatus,
    fetchForecast,
    systemHealth,
    forecastEnabled,
  } = useAIStore();

  const dbStatus = systemHealth?.database;
  const aiStatus = systemHealth?.ai;

  useEffect(() => {
    setIsMounted(true);
  }, []);

  // Fetch forecast when forecast tab is active
  useEffect(() => {
    if (isMounted && activeChartTab === "forecast" && aiStatus !== "offline") {
      fetchForecast(selectedModel, 30, true);
    }
  }, [selectedModel, activeChartTab, isMounted, aiStatus]);

  // Reset tab to historical if forecast gets disabled
  useEffect(() => {
    if (!forecastEnabled && activeChartTab === "forecast") {
      setActiveChartTab("historical");
    }
  }, [forecastEnabled, activeChartTab]);

  if (dbStatus === "offline") {
    return (
      <div className="relative w-full min-h-[420px] glass-card rounded-3xl flex flex-col items-center justify-center border border-rose-500/20 bg-rose-500/10 p-6 select-none">
        <Flame className="w-10 h-10 text-rose-400 mb-3 animate-pulse" />
        <span className="text-xs font-black uppercase tracking-wider text-rose-400">
          Analytics service temporarily offline.
        </span>
        <p className="text-[10px] text-rose-300/70 font-semibold mt-1">
          Unable to calculate statistics. Please check database connection.
        </p>
      </div>
    );
  }

  if (analyticsLoading || !analyticsData || !isMounted || !summary) {
    return (
      <div className="space-y-6 w-full animate-pulse">
        {/* KPI Cards Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="glass-card rounded-3xl h-[120px] bg-white/5 border-white/5"></div>
          ))}
        </div>
        {/* Visual Analytics Row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="glass-card rounded-3xl h-[380px] bg-white/5 border-white/5"></div>
          <div className="glass-card rounded-3xl h-[380px] bg-white/5 border-white/5"></div>
        </div>
        {/* Rankings & Suggestions Row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="glass-card rounded-3xl h-[280px] bg-white/5 border-white/5"></div>
          <div className="glass-card rounded-3xl h-[280px] bg-white/5 border-white/5"></div>
        </div>
      </div>
    );
  }

  const isAnalyticsEmpty = 
    !analyticsData || 
    ((analyticsData.daily?.activities ?? analyticsData.daily_summary?.activities ?? 0) === 0 &&
     (analyticsData.weekly?.weekly_total ?? analyticsData.weekly_summary?.weekly_total ?? 0) === 0 &&
     (analyticsData.monthly?.monthly_total ?? analyticsData.monthly_summary?.monthly_total ?? 0) === 0 &&
     Object.values(analyticsData.category_breakdown ?? {}).every(v => v === 0));

  if (isAnalyticsEmpty) {
    return (
      <div className="w-full flex flex-col items-center justify-center min-h-[400px] border border-dashed border-white/5 rounded-3xl bg-white/[0.01] p-6 text-center select-none">
        <Leaf className="w-10 h-10 text-emerald-500/40 mb-3 animate-pulse" />
        <span className="text-sm font-bold text-stone-300">
          No analytics data available yet.
        </span>
        <p className="text-xs text-stone-500 mt-1">
          Start logging activities.
        </p>
      </div>
    );
  }

  // 1. Map Category Breakdown Pie Chart data safely
  const pieData = Object.entries(
    analyticsData?.category_breakdown ?? {}
  )
    .filter(([_, value]) => typeof value === "number" && value > 0)
    .map(([key, value]) => ({
      name: key.toUpperCase(),
      value: value as number,
      color: CATEGORY_COLORS[key] || "#10b981",
    }));

  const trends = summary?.trends ?? [];
  const showDegraded = dbStatus === "degraded" || aiStatus === "degraded";

  // Trend indicator builder helper
  const renderTrendBadge = (val: number, status: string) => {
    const isDecreasing = status === "decreasing";
    const isStable = status === "stable";

    let Icon = Minus;
    let badgeClass = "bg-white/5 text-stone-400 border-white/5";
    let text = "Stable";

    if (isDecreasing) {
      Icon = TrendingDown;
      badgeClass = "bg-emerald-500/10 text-emerald-400 border-emerald-500/10";
      text = `${Math.abs(val)}% decrease`;
    } else if (status === "increasing") {
      Icon = TrendingUp;
      badgeClass = "bg-rose-500/10 text-rose-450 border-rose-500/10";
      text = `+${val}% increase`;
    }

    return (
      <div className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-lg border text-[9px] font-black uppercase tracking-wider ${badgeClass}`}>
        <Icon className="w-3 h-3" />
        <span>{text}</span>
      </div>
    );
  };

  // Grade color helper
  const getGradeColor = (grade: string) => {
    if (grade.startsWith("A")) return "text-emerald-400 bg-emerald-500/10 border-emerald-500/15";
    if (grade.startsWith("B") || grade.startsWith("C")) return "text-amber-400 bg-amber-500/10 border-amber-500/15";
    return "text-rose-400 bg-rose-500/10 border-rose-500/15";
  };

  return (
    <div className="space-y-6 w-full">
      {/* ───────────────────────────────────────────────────────────────────────
          SUMMARY CARDS GRID
      ─────────────────────────────────────────────────────────────────────── */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 select-none">
        {/* Card 1: Today's Emissions */}
        <div className="glass-card rounded-3xl p-5 border border-white/5 bg-white/[0.01] hover:border-emerald-500/10 transition-all duration-300 flex flex-col justify-between min-h-[120px]">
          <div>
            <span className="text-[10px] font-black uppercase tracking-widest text-stone-500 flex items-center gap-1.5">
              <Activity className="w-3.5 h-3.5 text-emerald-500" />
              Today's Footprint
            </span>
            <div className="mt-2.5 flex items-baseline gap-1.5">
              <span className="text-2xl font-black text-white">{(analyticsData?.daily?.total_carbon ?? analyticsData?.daily_summary?.total_carbon ?? 0).toFixed(2)}</span>
              <span className="text-[10px] font-extrabold text-stone-400 uppercase">kg CO2e</span>
            </div>
          </div>
          <div className="mt-4 flex items-center justify-between border-t border-white/5 pt-2.5">
            <span className="text-[9px] font-bold text-stone-500">
              {analyticsData?.daily?.activities ?? analyticsData?.daily_summary?.activities ?? 0} logs • Avg: {analyticsData?.daily?.average ?? analyticsData?.daily_summary?.average ?? 0} kg
            </span>
            {renderTrendBadge(analyticsData?.daily?.trend_value ?? 0, analyticsData?.daily?.trend_status ?? analyticsData?.trend?.status ?? "stable")}
          </div>
        </div>

        {/* Card 2: Weekly Emissions */}
        <div className="glass-card rounded-3xl p-5 border border-white/5 bg-white/[0.01] hover:border-sky-500/10 transition-all duration-300 flex flex-col justify-between min-h-[120px]">
          <div>
            <span className="text-[10px] font-black uppercase tracking-widest text-stone-500 flex items-center gap-1.5">
              <Calendar className="w-3.5 h-3.5 text-sky-550" />
              Weekly Footprint
            </span>
            <div className="mt-2.5 flex items-baseline gap-1.5">
              <span className="text-2xl font-black text-white">{(analyticsData?.weekly?.weekly_total ?? analyticsData?.weekly_summary?.weekly_total ?? 0).toFixed(2)}</span>
              <span className="text-[10px] font-extrabold text-sky-400 uppercase">kg CO2e</span>
            </div>
          </div>
          <div className="mt-4 flex items-center justify-between border-t border-white/5 pt-2.5">
            <span className="text-[9px] font-bold text-stone-500">
              Daily Avg: {analyticsData?.weekly?.daily_average ?? 0} kg
            </span>
            {renderTrendBadge(analyticsData?.weekly?.trend_value ?? 0, analyticsData?.weekly?.trend_status ?? "stable")}
          </div>
        </div>

        {/* Card 3: Monthly Emissions */}
        <div className="glass-card rounded-3xl p-5 border border-white/5 bg-white/[0.01] hover:border-amber-500/10 transition-all duration-300 flex flex-col justify-between min-h-[120px]">
          <div>
            <span className="text-[10px] font-black uppercase tracking-widest text-stone-500 flex items-center gap-1.5">
              <LineIcon className="w-3.5 h-3.5 text-amber-550" />
              Monthly Footprint
            </span>
            <div className="mt-2.5 flex items-baseline gap-1.5">
              <span className="text-2xl font-black text-white">{(analyticsData?.monthly?.monthly_total ?? analyticsData?.monthly_summary?.monthly_total ?? 0).toFixed(2)}</span>
              <span className="text-[10px] font-extrabold text-amber-500 uppercase">kg CO2e</span>
            </div>
          </div>
          <div className="mt-4 flex items-center justify-between border-t border-white/5 pt-2.5">
            <span className="text-[9px] font-bold text-stone-500">
              Daily Avg: {analyticsData?.monthly?.daily_average ?? 0} kg
            </span>
            {renderTrendBadge(analyticsData?.monthly?.trend_value ?? 0, analyticsData?.monthly?.trend_status ?? "stable")}
          </div>
        </div>

        {/* Card 4: Sustainability Grade */}
        <div className="glass-card rounded-3xl p-5 border border-white/5 bg-white/[0.01] hover:border-emerald-500/10 transition-all duration-300 flex flex-col justify-between min-h-[120px]">
          <div>
            <span className="text-[10px] font-black uppercase tracking-widest text-stone-500 flex items-center gap-1.5">
              <Award className="w-3.5 h-3.5 text-emerald-400" />
              Sustainability Rating
            </span>
            <div className="mt-2.5 flex items-center gap-3">
              <span className="text-2xl font-black text-white">{analyticsData?.sustainability?.score ?? analyticsData?.sustainability_score?.score ?? 0}</span>
              <span className="text-[9px] font-extrabold text-stone-400 uppercase">Score</span>
              <span className={`px-2 py-0.5 rounded-lg border text-xs font-black uppercase tracking-wide ml-auto ${getGradeColor(analyticsData?.sustainability?.grade ?? analyticsData?.sustainability_score?.grade ?? "N/A")}`}>
                Grade {analyticsData?.sustainability?.grade ?? analyticsData?.sustainability_score?.grade ?? "N/A"}
              </span>
            </div>
          </div>
          <div className="mt-4 border-t border-white/5 pt-2.5 flex items-center justify-between text-[9px] font-bold text-stone-500">
            <span>Composite eco performance index</span>
            <span className="text-emerald-450 uppercase font-black">active</span>
          </div>
        </div>
      </div>

      {/* ───────────────────────────────────────────────────────────────────────
          VISUAL ANALYTICS ROW
      ─────────────────────────────────────────────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 w-full">
        {/* CHART 1: Historical Trend or AI Forecasting (Tabbed Card) */}
        <div className="glass-card rounded-3xl p-5 sm:p-6 flex flex-col justify-between h-[400px] relative">
          {showDegraded && (
            <div className="absolute top-2 right-2 z-20 px-2 py-0.5 rounded bg-amber-500/20 border border-amber-500/30 text-[8px] font-black uppercase tracking-wider text-amber-450 animate-pulse">
              Running in degraded mode.
            </div>
          )}
          <div>
            {/* Tabs header */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-3 border-b border-white/5 mb-4 gap-3">
              <div className="flex space-x-1 bg-black/20 p-1 rounded-xl border border-white/5 self-start">
                <button
                  onClick={() => setActiveChartTab("historical")}
                  className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center space-x-1.5 cursor-pointer ${
                    activeChartTab === "historical"
                      ? "bg-forest-600 text-white shadow-md shadow-forest-650/20"
                      : "text-stone-400 hover:text-stone-200"
                  }`}
                >
                  <LineIcon className="w-3.5 h-3.5" />
                  <span>Historical Trend</span>
                </button>
                {forecastEnabled && (
                  <button
                    onClick={() => setActiveChartTab("forecast")}
                    className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center space-x-1.5 cursor-pointer ${
                      activeChartTab === "forecast"
                        ? "bg-forest-600 text-white shadow-md shadow-forest-650/20"
                        : "text-stone-400 hover:text-stone-200"
                    }`}
                  >
                    <BrainCircuit className="w-3.5 h-3.5 text-amber-400" />
                    <span>AI 30D Forecast</span>
                  </button>
                )}
              </div>

              {/* Model Selector (Visible during Forecast Mode) */}
              {activeChartTab === "forecast" && (
                <div className="flex items-center space-x-1.5">
                  <span className="text-[10px] text-stone-500 uppercase tracking-wider font-bold">Model:</span>
                  <select
                    value={selectedModel}
                    onChange={(e) => setSelectedModel(e.target.value)}
                    className="bg-stone-900 border border-white/10 rounded-lg text-stone-300 text-[10px] font-bold px-2 py-1 focus:outline-none focus:border-forest-500 cursor-pointer"
                  >
                    <option value="prophet">Seasonal Prophet (Default)</option>
                    <option value="lstm">Cyclical LSTM RNN</option>
                    <option value="moving_average">Moving Average Walk</option>
                  </select>
                </div>
              )}

              {activeChartTab === "historical" && (
                <span className="text-[10px] bg-forest-600/15 border border-forest-500/20 text-forest-750 dark:text-forest-400 font-extrabold px-2 py-0.5 rounded-full uppercase self-start sm:self-auto">
                  Budget Limit: 5.0 kg
                </span>
              )}
            </div>

            {/* Historical Trend Chart Panel */}
            {activeChartTab === "historical" ? (
              <div className="h-64 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={trends} margin={{ top: 10, right: 5, left: -25, bottom: 0 }}>
                    <defs>
                      <linearGradient id="colorCarbon" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#10b981" stopOpacity={0.4} />
                        <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(255,255,255,0.05)" />
                    <XAxis dataKey="date" stroke="#64748b" fontSize={11} tickLine={false} />
                    <YAxis stroke="#64748b" fontSize={11} tickLine={false} />
                    <ChartTooltip content={<CustomTooltip />} />
                    <Area
                      type="monotone"
                      dataKey="emissions"
                      name="Emissions (kg CO2e)"
                      stroke="#10b981"
                      strokeWidth={2.5}
                      fillOpacity={1}
                      fill="url(#colorCarbon)"
                    />
                    <ReferenceLine
                      y={5.0}
                      stroke="#ef4444"
                      strokeDasharray="4 4"
                      label={{
                        value: "Limit (5.0kg)",
                        position: "top",
                        fill: "#ef4444",
                        fontSize: 9,
                        fontWeight: "bold",
                      }}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            ) : (
              /* AI Forecasting Chart Panel */
              <div className="h-64 w-full relative">
                {forecastLoading ? (
                  <div className="absolute inset-0 flex items-center justify-center bg-black/10 rounded-2xl z-10">
                    <div className="flex flex-col items-center space-y-2">
                      <RefreshCw className="w-6 h-6 animate-spin text-amber-500" />
                      <span className="text-[10px] text-amber-500 uppercase tracking-widest font-black animate-pulse">Loading Forecast...</span>
                    </div>
                  </div>
                ) : null}
                {forecastStatus === "disabled_intentionally" ? (
                  <div className="absolute inset-0 flex flex-col items-center justify-center bg-stone-950/40 rounded-2xl border border-dashed border-white/5 p-4 text-center z-10">
                    <BrainCircuit className="w-10 h-10 text-amber-550 mb-2 animate-pulse" />
                    <p className="text-xs font-semibold text-stone-300">
                      Forecast Engine will be available after Habit Analysis is completed.
                    </p>
                  </div>
                ) : forecastStatus === "pending" ? (
                  <div className="absolute inset-0 flex flex-col items-center justify-center bg-stone-950/40 rounded-2xl border border-dashed border-white/5 p-4 text-center z-10">
                    <BrainCircuit className="w-10 h-10 text-amber-550 mb-2 animate-pulse" />
                    <p className="text-xs font-bold text-stone-300 mb-4">Forecast has not been generated yet.</p>
                    <button
                      onClick={() => fetchForecast(selectedModel, 30, true)}
                      className="px-4 py-2 bg-amber-500 hover:bg-amber-600 text-black font-extrabold text-[10px] uppercase rounded-xl tracking-wider transition-all cursor-pointer active:scale-95 shadow shadow-amber-500/10"
                    >
                      Generate Forecast
                    </button>
                  </div>
                ) : aiStatus === "offline" || (!forecastLoading && (!forecastData || forecastData.length === 0)) ? (
                  <div className="absolute inset-0 flex flex-col items-center justify-center bg-stone-950/40 rounded-2xl border border-dashed border-white/5">
                    <span className="text-xs font-black text-rose-400 uppercase tracking-widest">AI service temporarily unavailable.</span>
                  </div>
                ) : (
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={forecastData} margin={{ top: 10, right: 5, left: -25, bottom: 0 }}>
                      <defs>
                        <linearGradient id="colorForecast" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#d97706" stopOpacity={0.25} />
                          <stop offset="95%" stopColor="#d97706" stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(255,255,255,0.05)" />
                      <XAxis dataKey="date" stroke="#64748b" fontSize={9} tickLine={false} />
                      <YAxis stroke="#64748b" fontSize={11} tickLine={false} />
                      <ChartTooltip content={<CustomTooltip />} />
                      {/* Pessimistic Boundary */}
                      <Area
                        type="monotone"
                        dataKey="pessimistic"
                        name="Pessimistic Forecast"
                        stroke="#f43f5e"
                        strokeWidth={1.5}
                        strokeDasharray="4 4"
                        fill="none"
                      />
                      {/* Expected Path */}
                      <Area
                        type="monotone"
                        dataKey="expected"
                        name="Expected Path"
                        stroke="#d97706"
                        strokeWidth={2.5}
                        fillOpacity={1}
                        fill="url(#colorForecast)"
                      />
                      {/* Optimistic Boundary */}
                      <Area
                        type="monotone"
                        dataKey="optimistic"
                        name="Optimistic Target"
                        stroke="#10b981"
                        strokeWidth={1.5}
                        strokeDasharray="4 4"
                        fill="none"
                      />
                      <ReferenceLine
                        y={5.0}
                        stroke="#ef4444"
                        strokeDasharray="4 4"
                        label={{
                          value: "Limit (5kg)",
                          position: "top",
                          fill: "#ef4444",
                          fontSize: 9,
                          fontWeight: "bold",
                        }}
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                )}
              </div>
            )}
          </div>
        </div>

        {/* CHART 2: Mapped Category Breakdown Pie Chart */}
        <div className="glass-card rounded-3xl p-5 sm:p-6 flex flex-col justify-between h-[400px] relative">
          <div>
            <div className="flex items-center justify-between mb-4 border-b border-white/5 pb-3">
              <div className="flex items-center space-x-2">
                <PieIcon className="w-4.5 h-4.5 text-forest-500" />
                <h3 className="font-bold text-forest-100">
                  Category Breakdown
                </h3>
              </div>
              <span className="text-[10px] text-stone-400 font-bold uppercase tracking-wider">
                Last 30 Days
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 items-center">
              {pieData.length > 0 ? (
                <>
                  {/* Recharts Pie */}
                  <div className="h-44 w-full">
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={pieData}
                          cx="50%"
                          cy="50%"
                          innerRadius={50}
                          outerRadius={70}
                          paddingAngle={4}
                          dataKey="value"
                        >
                          {pieData.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={entry.color} />
                          ))}
                        </Pie>
                        <ChartTooltip content={<CustomTooltip />} />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>

                  {/* Legend list */}
                  <div className="space-y-2 max-h-44 overflow-y-auto pr-1">
                    {pieData.map((entry) => (
                      <div key={entry.name} className="flex items-center justify-between text-xs">
                        <div className="flex items-center space-x-2 text-stone-300 font-semibold">
                          <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: entry.color }}></span>
                          <span className="capitalize">{entry.name.toLowerCase()}</span>
                        </div>
                        <span className="font-bold text-white">
                          {entry.value.toFixed(0)}%
                        </span>
                      </div>
                    ))}
                  </div>
                </>
              ) : (
                <div className="col-span-2 text-center py-10 text-xs text-stone-500">
                  No activity logs in the last 30 days.
                </div>
              )}
            </div>
          </div>

          {/* Habit Heatmap Calendar Row */}
          <div className="border-t border-white/5 pt-4 mt-4 select-none">
            <div className="flex items-center space-x-2 mb-2 text-xs font-bold text-stone-400">
              <Calendar className="w-3.5 h-3.5 text-forest-550" />
              <span>CLIMATE HABIT MATRIX (PAST 7 DAYS)</span>
            </div>
            <div className="flex items-center justify-between gap-1 sm:gap-2">
              {trends.map((day) => {
                const getGridColor = (score: number) => {
                  if (score >= 90) return "bg-emerald-600 border-emerald-500/50 shadow-emerald-500/20";
                  if (score >= 75) return "bg-emerald-500/60 border-emerald-500/30";
                  if (score >= 50) return "bg-amber-500/60 border-amber-500/30";
                  return "bg-rose-500/60 border-rose-500/30 shadow-rose-500/20";
                };
                return (
                  <div
                    key={day.date_full}
                    className="flex-1 flex flex-col items-center p-1.5 sm:p-2 rounded-xl border border-white/5 bg-white/5"
                    title={`${day.date_full}: ${day.emissions.toFixed(2)} kg CO2e, Score: ${day.score.toFixed(0)}`}
                  >
                    <div className={`w-full aspect-square rounded-lg border ${getGridColor(day.score)} flex items-center justify-center text-[10px] font-bold text-white shadow-sm`}>
                      {day.score.toFixed(0)}
                    </div>
                    <span className="text-[10px] text-stone-400 mt-1 font-bold">{day.date}</span>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>

      {/* ───────────────────────────────────────────────────────────────────────
          RANKINGS & RECOMMENDATIONS ROW
      ─────────────────────────────────────────────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 w-full">
        {/* Card 1: Activity Rankings */}
        <div className="glass-card rounded-3xl p-5 sm:p-6 border border-white/5 bg-white/[0.01] flex flex-col min-h-[300px]">
          <div className="border-b border-white/5 pb-3 mb-4 flex items-center justify-between">
            <h3 className="font-bold text-forest-100 flex items-center gap-1.5">
              <Flame className="w-4 h-4 text-rose-500" />
              Source Rankings
            </h3>
            <span className="text-[9px] font-black uppercase tracking-widest text-stone-500">
              last 30 days
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 flex-1">
            {/* Top Carbon Sources */}
            <div>
              <h4 className="text-[10px] font-black uppercase tracking-widest text-stone-400 mb-2.5">
                Top Carbon Sources
              </h4>
              {(analyticsData?.rankings?.top_sources ?? []).length > 0 ? (
                <div className="space-y-3">
                  {(analyticsData?.rankings?.top_sources ?? []).map((item, idx) => (
                    <div key={idx} className="space-y-1">
                      <div className="flex justify-between text-xs font-bold text-stone-300">
                        <span className="truncate max-w-[130px]">{item.activity}</span>
                        <span className="text-white font-extrabold">{item.carbon.toFixed(1)} kg</span>
                      </div>
                      {/* Realistic Progress Bar */}
                      <div className="w-full h-1.5 rounded-full bg-white/5 overflow-hidden">
                        <div
                          className="h-full bg-gradient-to-r from-rose-500 to-rose-600 rounded-full"
                          style={{
                            width: `${Math.min(
                              100,
                              (item.carbon / ((analyticsData?.rankings?.top_sources ?? [])[0]?.carbon || 1)) * 100
                            )}%`,
                          }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-stone-550 italic">No significant sources.</p>
              )}
            </div>

            {/* Most Frequent Activities */}
            <div>
              <h4 className="text-[10px] font-black uppercase tracking-widest text-stone-400 mb-2.5">
                Most Frequent Activities
              </h4>
              {(analyticsData?.rankings?.most_frequent ?? []).length > 0 ? (
                <div className="space-y-2.5">
                  {(analyticsData?.rankings?.most_frequent ?? []).map((item, idx) => (
                    <div key={idx} className="flex justify-between items-center bg-white/[0.02] border border-white/5 px-3 py-2 rounded-xl text-xs">
                      <span className="font-bold text-stone-350 truncate max-w-[120px]">{item.activity}</span>
                      <span className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/10 text-[9px] font-black uppercase tracking-wider">
                        {item.count} times
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-stone-550 italic">No logs recorded.</p>
              )}
            </div>
          </div>
        </div>

        {/* Card 2: AI Sustainability Coaching suggestions */}
        <div className="glass-card rounded-3xl p-5 sm:p-6 border border-white/5 bg-white/[0.01] flex flex-col justify-between min-h-[300px]">
          <div>
            <div className="border-b border-white/5 pb-3 mb-4 flex items-center justify-between">
              <h3 className="font-bold text-forest-100 flex items-center gap-1.5">
                <Sparkles className="w-4 h-4 text-emerald-400 animate-pulse" />
                AI Sustainability Coach
              </h3>
              <span className="text-[9px] font-black uppercase tracking-widest text-stone-500">
                active advice
              </span>
            </div>

            <div className="space-y-3.5">
              {(analyticsData?.recommendations ?? []).map((rec, idx) => (
                <div key={idx} className="flex items-start gap-3 bg-emerald-950/5 border border-emerald-550/10 p-3.5 rounded-2xl">
                  <span className="w-6 h-6 rounded-lg bg-emerald-500/15 flex items-center justify-center border border-emerald-500/20 mt-0.5">
                    <Leaf className="w-3.5 h-3.5 text-emerald-400" />
                  </span>
                  <div>
                    <p className="text-xs font-bold text-stone-250 leading-relaxed">
                      {rec}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="text-[9px] font-bold text-stone-500 uppercase tracking-wider border-t border-white/5 pt-3 mt-4">
            Suggestions update automatically as activity patterns change.
          </div>
        </div>
      </div>
    </div>
  );
}
