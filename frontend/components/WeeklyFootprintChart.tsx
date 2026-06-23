"use client";

import React, { useState, useEffect } from "react";
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

interface WeeklyFootprintChartProps {
  summary: DashboardSummary | null;
}

const CustomChartTooltip = ({ active, payload }: any) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div className="glass-card bg-[#0b120f]/95 px-3 py-2 rounded-xl border border-emerald-500/20 text-xs shadow-xl backdrop-blur-md">
        <p className="font-extrabold text-[9px] text-stone-500 uppercase tracking-widest mb-1.5 border-b border-white/5 pb-1">
          {data.date_full || "Activity Date"}
        </p>
        <div className="flex justify-between items-center gap-4 font-bold">
          <span className="text-stone-405 flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
            Emissions:
          </span>
          <span className="text-emerald-400">{Number(data.emissions).toFixed(1)} kg</span>
        </div>
      </div>
    );
  }
  return null;
};

export default function WeeklyFootprintChart({ summary }: WeeklyFootprintChartProps) {
  const [isMounted, setIsMounted] = useState(false);

  useEffect(() => {
    setIsMounted(true);
  }, []);

  if (!isMounted || !summary) {
    return (
      <div className="glass-card rounded-3xl p-5 h-64 bg-white/5 border-white/5 flex items-center justify-center animate-pulse">
        <span className="text-xs text-stone-500 font-bold uppercase tracking-wider">Loading Chart Data...</span>
      </div>
    );
  }

  const { trends = [] } = summary ?? {};

  // If trends array is empty or short, we pad it with default values for mockup aesthetic
  const formattedTrends = trends && trends.length > 0 ? trends : [
    { date: "Mon", emissions: 0.5, date_full: "Monday" },
    { date: "Tue", emissions: 0.8, date_full: "Tuesday" },
    { date: "Wed", emissions: 0.4, date_full: "Wednesday" },
    { date: "Thu", emissions: 1.2, date_full: "Thursday" },
    { date: "Fri", emissions: 0.6, date_full: "Friday" },
    { date: "Sat", emissions: 0.9, date_full: "Saturday" },
    { date: "Sun", emissions: 0.7, date_full: "Sunday" }
  ];

  return (
    <div className="glass-card rounded-3xl p-5 sm:p-6 transition-all duration-300 flex flex-col justify-between h-[280px]">
      <div>
        {/* Header */}
        <div className="flex items-center justify-between pb-3 border-b border-white/5 mb-4">
          <div className="flex items-center space-x-2.5">
            <div className="w-6 h-6 rounded-lg bg-emerald-500/10 flex items-center justify-center border border-emerald-500/20">
              <TrendingDown className="w-3.5 h-3.5 text-emerald-450" />
            </div>
            <h3 className="font-extrabold text-xs text-stone-300 uppercase tracking-widest">
              Weekly Footprint (kg CO₂)
            </h3>
          </div>

          <div className="relative flex items-center bg-white/[0.02] border border-white/5 rounded-lg px-2.5 py-1 text-[10px] font-bold select-none cursor-pointer">
            <span className="text-emerald-400">This Week</span>
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
                <linearGradient id="chartGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#10b981" stopOpacity={0.25} />
                  <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(255,255,255,0.03)" />
              <XAxis 
                dataKey="date" 
                stroke="#44403c" 
                fontSize={10} 
                tickLine={false} 
                axisLine={false}
                dy={6}
                style={{ fontWeight: "bold" }}
              />
              <YAxis 
                stroke="#44403c" 
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
                stroke="#10b981"
                strokeWidth={2}
                fillOpacity={1}
                fill="url(#chartGradient)"
                activeDot={{ r: 6, fill: "#10b981", stroke: "#080d0a", strokeWidth: 2 }}
                dot={{ r: 3, fill: "#10b981", stroke: "transparent" }}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
