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
  Legend
} from "recharts";
import { DashboardSummary } from "../services/api";
import { PieChart as PieIcon, LineChart as LineIcon, Calendar, TrendingUp, Sparkles, BrainCircuit, RefreshCw } from "lucide-react";
import { useAIStore } from "../stores/aiStore";
import { getSafeCategory } from "../utils/safeCategory";
import { motion, AnimatePresence } from "framer-motion";

interface CarbonChartsProps {
  summary: DashboardSummary | null;
}

const CATEGORY_COLORS: Record<string, string> = {
  food: "#10b981",       // Emerald Green
  transport: "#0284c7",  // Sky Blue
  electricity: "#eab308",// Yellow
  appliances: "#6366f1", // Indigo
  shopping: "#a855f7",   // Purple
  waste: "#f43f5e",      // Rose Red
  water: "#06b6d4",      // Cyan
  lifestyle: "#64748b",  // Slate
};

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    const item = payload[0]?.payload;
    return (
      <div className="glass-card bg-stone-900/95 dark:bg-black/90 px-3.5 py-2.5 rounded-xl border border-white/10 text-xs shadow-xl backdrop-blur-md">
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
  const [activeTab, setActiveTab] = useState<"historical" | "forecast">("historical");
  const [selectedModel, setSelectedModel] = useState("prophet");
  
  const { forecastData, forecastLoading, fetchForecast } = useAIStore();

  // Prevent SSR hydration errors with Recharts SVG rendering
  useEffect(() => {
    setIsMounted(true);
  }, []);

  // Fetch forecast when model changes
  useEffect(() => {
    if (isMounted && activeTab === "forecast") {
      fetchForecast(selectedModel);
    }
  }, [selectedModel, activeTab, isMounted]);

  if (!summary || !isMounted) {
    return (
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 w-full animate-pulse">
        <div className="glass-card rounded-3xl h-96 bg-white/5"></div>
        <div className="glass-card rounded-3xl h-96 bg-white/5"></div>
      </div>
    );
  }

  // Safely extract arrays — always default to [] even if API returns null
  const breakdown = summary.breakdown ?? [];
  const trends = summary.trends ?? [];

  // Format pie chart data — safe to call .filter on guaranteed array
  const pieData = breakdown
    .filter((cat) => cat.total_carbon > 0)
    .map((cat) => {
      const safeCategory = getSafeCategory(cat.category);
      return {
        name: safeCategory.toUpperCase(),
        value: cat.total_carbon,
        percentage: cat.percentage,
        color: CATEGORY_COLORS[safeCategory] || "#10b981",
      };
    });


  // Format habit grid grid cells (past 7 days)
  const getGridColor = (score: number) => {
    if (score >= 90) return "bg-emerald-600 border-emerald-500/50 shadow-emerald-500/20";
    if (score >= 75) return "bg-emerald-500/60 border-emerald-500/30";
    if (score >= 50) return "bg-amber-500/60 border-amber-500/30";
    return "bg-rose-500/60 border-rose-500/30 shadow-rose-500/20";
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 w-full">
      {/* CHART 1: Historical Trend or AI Forecasting (Tabbed Card) */}
      <div className="glass-card rounded-3xl p-5 sm:p-6 transition-all duration-300 flex flex-col justify-between h-[420px]">
        <div>
          {/* Tabs header */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-3 border-b border-white/10 dark:border-white/5 mb-4 gap-3">
            <div className="flex space-x-1 bg-black/20 p-1 rounded-xl border border-white/5 self-start">
              <button
                onClick={() => setActiveTab("historical")}
                className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center space-x-1.5 cursor-pointer ${
                  activeTab === "historical"
                    ? "bg-forest-600 text-white shadow-md shadow-forest-650/20"
                    : "text-stone-400 hover:text-stone-200"
                }`}
              >
                <LineIcon className="w-3.5 h-3.5" />
                <span>Historical Trend</span>
              </button>
              <button
                onClick={() => setActiveTab("forecast")}
                className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center space-x-1.5 cursor-pointer ${
                  activeTab === "forecast"
                    ? "bg-forest-600 text-white shadow-md shadow-forest-650/20"
                    : "text-stone-400 hover:text-stone-200"
                }`}
              >
                <BrainCircuit className="w-3.5 h-3.5 text-amber-400" />
                <span>AI 30D Forecast</span>
              </button>
            </div>

            {/* Model Selector (Visible during Forecast Mode) */}
            {activeTab === "forecast" && (
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

            {activeTab === "historical" && (
              <span className="text-[10px] bg-forest-600/15 border border-forest-500/20 text-forest-700 dark:text-forest-400 font-extrabold px-2 py-0.5 rounded-full uppercase self-start sm:self-auto">
                Budget Limit: 5.0 kg
              </span>
            )}
          </div>

          {/* Historical Trend Chart Panel */}
          {activeTab === "historical" ? (
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
                <div className="absolute inset-0 flex items-center justify-center bg-black/10 rounded-2xl">
                  <div className="flex flex-col items-center space-y-2">
                    <RefreshCw className="w-6 h-6 animate-spin text-amber-500" />
                    <span className="text-[10px] text-amber-500 uppercase tracking-widest font-black animate-pulse">Running Calculations...</span>
                  </div>
                </div>
              ) : null}
              
              {!forecastLoading && (!forecastData || forecastData.length === 0) ? (
                <div className="absolute inset-0 flex flex-col items-center justify-center bg-stone-950/40 rounded-2xl border border-dashed border-white/5">
                  <span className="text-xs font-black text-amber-550 uppercase tracking-widest">AI service temporarily unavailable</span>
                  <span className="text-[9px] text-stone-500 font-bold uppercase tracking-wider mt-1">Please try again later</span>
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

      {/* CHART 2: Category Breakdown Pie Chart & Habit Grid */}
      <div className="glass-card rounded-3xl p-5 sm:p-6 transition-all duration-300 flex flex-col justify-between h-[420px]">
        <div>
          <div className="flex items-center justify-between mb-4 border-b border-white/10 dark:border-white/5 pb-3">
            <div className="flex items-center space-x-2">
              <PieIcon className="w-4.5 h-4.5 text-forest-500" />
              <h3 className="font-bold text-earth-800 dark:text-forest-100">
                Source Breakdown
              </h3>
            </div>
            <span className="text-[10px] text-stone-400 font-bold uppercase tracking-wider">
              Lifetime stats
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
                      <div className="flex items-center space-x-2 text-earth-700 dark:text-stone-300 font-semibold">
                        <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: entry.color }}></span>
                        <span className="capitalize">{entry.name.toLowerCase()}</span>
                      </div>
                      <span className="font-bold text-earth-900 dark:text-white">
                        {entry.percentage.toFixed(0)}%
                      </span>
                    </div>
                  ))}
                </div>
              </>
            ) : (
              <div className="col-span-2 text-center py-10 text-xs text-stone-500">
                No carbon data logged yet.
              </div>
            )}
          </div>
        </div>

        {/* Habit Heatmap Calendar Row */}
        <div className="border-t border-white/10 dark:border-white/5 pt-4 mt-4">
          <div className="flex items-center space-x-2 mb-2 text-xs font-bold text-earth-500 dark:text-stone-400">
            <Calendar className="w-3.5 h-3.5 text-forest-500" />
            <span>CLIMATE HABIT MATRIX (PAST 7 DAYS)</span>
          </div>
          <div className="flex items-center justify-between gap-1 sm:gap-2">
            {trends.map((day) => (
              <div
                key={day.date_full}
                className="flex-1 flex flex-col items-center p-1.5 sm:p-2 rounded-xl border border-white/5 bg-white/5 dark:bg-black/5"
                title={`${day.date_full}: ${day.emissions.toFixed(2)} kg CO2e, Score: ${day.score.toFixed(0)}`}
              >
                <div className={`w-full aspect-square rounded-lg border ${getGridColor(day.score)} flex items-center justify-center text-[10px] font-bold text-white shadow-sm`}>
                  {day.score.toFixed(0)}
                </div>
                <span className="text-[10px] text-stone-400 mt-1 font-bold">{day.date}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
