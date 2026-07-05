"use client";

import React, { useState, useEffect, useMemo } from "react";
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as ChartTooltip
} from "recharts";
import { TrendingDown, Calendar } from "lucide-react";
import { DashboardSummary } from "../services/api";
import { useAIStore } from "../stores/aiStore";

interface WeeklyFootprintChartProps {
  summary: DashboardSummary | null;
}

const CustomChartTooltip = ({ active, payload }: any) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div className="glass-premium px-3.5 py-2.5 rounded-xl text-xs border border-theme shadow-2xl">
        <p className="font-extrabold text-[9px] text-theme-muted uppercase tracking-widest mb-1.5 border-b border-white/5 pb-1">
          {data?.date_full || "Activity Date"}
        </p>
        <div className="flex justify-between items-center gap-4 font-bold">
          <span className="text-theme-secondary flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: "var(--brand-primary)" }} />
            Emissions:
          </span>
          <span className="text-theme-brand">{Number(data?.emissions ?? 0.0).toFixed(1)} kg</span>
        </div>
      </div>
    );
  }
  return null;
};

export default function WeeklyFootprintChart({ summary: rawSummary }: WeeklyFootprintChartProps) {
  const [isMounted, setIsMounted] = useState(false);
  const { loading, error } = useAIStore();

  useEffect(() => {
    setIsMounted(true);
  }, []);

  const trends = rawSummary?.trends || [];

  // Pad trends for mockup/aesthetic default
  const formattedTrends = useMemo(() => {
    return Array.isArray(trends) && trends.length > 0 ? trends : [
      { date: "Mon", emissions: 0.5, date_full: "Monday" },
      { date: "Tue", emissions: 0.8, date_full: "Tuesday" },
      { date: "Wed", emissions: 0.4, date_full: "Wednesday" },
      { date: "Thu", emissions: 1.2, date_full: "Thursday" },
      { date: "Fri", emissions: 0.6, date_full: "Friday" },
      { date: "Sat", emissions: 0.9, date_full: "Saturday" },
      { date: "Sun", emissions: 0.7, date_full: "Sunday" }
    ];
  }, [trends]);

  if (error && !loading && !rawSummary) {
    return (
      <div className="glass-premium rounded-3xl p-5 h-[280px] flex flex-col items-center justify-center border border-rose-500/20 text-center p-6 select-none">
        <span className="text-xs text-rose-455 font-bold uppercase tracking-wider mb-2">Failed to load Chart Data</span>
        <span className="text-[10px] text-theme-muted font-semibold max-w-[220px]">{error}</span>
      </div>
    );
  }

  if (!isMounted || (loading && !rawSummary)) {
    return (
      <div className="glass-premium rounded-3xl p-5 h-[280px] flex items-center justify-center animate-pulse">
        <span className="text-xs text-theme-muted font-bold uppercase tracking-wider">Loading Chart Data...</span>
      </div>
    );
  }

  const summary = rawSummary || {
    today_emissions: 0,
    yesterday_emissions: 0,
    weekly_emissions: 0,
    current_score: 100,
    avg_weekly_score: 100,
    daily_budget: 10,
    breakdown: [],
    trends: [],
    achievements_count: 0,
    quests: [],
  };

  return (
    <div className="glass-premium rounded-3xl p-5 sm:p-6 transition-all duration-300 flex flex-col justify-between h-[280px]">
      <div>
        {/* Header */}
        <div className="flex items-center justify-between pb-3 border-b border-white/5 mb-4">
          <div className="flex items-center space-x-2.5">
            <div className="w-6 h-6 rounded-lg bg-emerald-500/10 flex items-center justify-center border border-emerald-500/20">
              <TrendingDown className="w-3.5 h-3.5 text-emerald-400" />
            </div>
            <h3 className="font-extrabold text-xs text-theme-secondary uppercase tracking-widest">
              Weekly Footprint (kg CO₂)
            </h3>
          </div>

          <div className="relative flex items-center bg-white/[0.02] border border-white/5 rounded-lg px-2.5 py-1 text-[10px] font-bold select-none cursor-pointer">
            <span className="text-theme-brand">This Week</span>
            <select
              disabled
              className="absolute inset-0 opacity-0 cursor-not-allowed w-full"
            >
              <option>This Week</option>
            </select>
          </div>
        </div>

        {/* Line Chart Panel */}
        <div className="h-44 w-full select-none">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={formattedTrends} margin={{ top: 10, right: 10, left: -25, bottom: 0 }}>
              <defs>
                <linearGradient id="chartGradientWeekly" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="var(--brand-primary)" stopOpacity={0.25} />
                  <stop offset="95%" stopColor="var(--brand-primary)" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(255,255,255,0.03)" />
              <XAxis 
                dataKey="date" 
                stroke="var(--text-muted)" 
                fontSize={10} 
                tickLine={false} 
                axisLine={false}
                dy={6}
                style={{ fontWeight: "bold" }}
              />
              <YAxis 
                stroke="var(--text-muted)" 
                fontSize={10} 
                tickLine={false} 
                axisLine={false}
                dx={-4}
                style={{ fontWeight: "bold" }}
              />
              <ChartTooltip content={<CustomChartTooltip />} />
              <Area
                type="monotone"
                dataKey="emissions"
                stroke="var(--brand-primary)"
                strokeWidth={2.5}
                fillOpacity={1}
                fill="url(#chartGradientWeekly)"
                activeDot={{ r: 6, fill: "var(--brand-primary)", stroke: "var(--bg-surface)", strokeWidth: 2 }}
                dot={{ r: 3.5, fill: "var(--brand-primary)", stroke: "transparent" }}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
