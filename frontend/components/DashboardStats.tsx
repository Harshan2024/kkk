"use client";

import React from "react";
import { Cloud, Target, Flame, Zap } from "lucide-react";
import { DashboardSummary } from "../services/api";
import { motion } from "framer-motion";

import { useAIStore } from "../stores/aiStore";

interface DashboardStatsProps {
  summary: DashboardSummary | null;
  xp?: number;
  level?: number;
  score?: number;
}

export default function DashboardStats({ summary, xp = 150, level = 1, score }: DashboardStatsProps) {
  const { systemHealth } = useAIStore();
  const dbStatus = systemHealth?.database;

  // 1. Error State (Database Offline)
  if (dbStatus === "offline") {
    return (
      <div className="relative grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5 w-full select-none min-h-[115px]">
        <div className="absolute inset-0 z-25 glass-card rounded-2xl flex items-center justify-center border border-rose-500/20 bg-rose-500/10">
          <span className="text-xs font-black uppercase tracking-wider text-rose-450">
            Service temporarily unavailable.
          </span>
        </div>
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="glass-card rounded-2xl h-[115px] opacity-20 border-white/5"></div>
        ))}
      </div>
    );
  }

  // 2. Loading State (no summary and health is unknown or loading)
  if (!summary && (!systemHealth || systemHealth.backend === "offline")) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5 w-full animate-pulse">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="glass-card rounded-2xl h-[115px] bg-white/5 border-white/5"></div>
        ))}
      </div>
    );
  }

  // 3. Empty State (no summary but online)
  if (!summary) {
    return (
      <div className="glass-card rounded-2xl p-6 border border-white/5 bg-white/[0.01] flex items-center justify-center min-h-[115px]">
        <span className="text-xs font-black uppercase tracking-wider text-stone-500">
          No data available.
        </span>
      </div>
    );
  }

  const showDegraded = dbStatus === "degraded";
  const {
    today_emissions = 0,
    yesterday_emissions = 0,
    weekly_emissions = 0,
    current_score = 0,
    trends = []
  } = summary ?? {};

  const finalScore = score !== undefined ? score : current_score;

  // Calculate percentage change today vs yesterday
  const getCarbonTrend = () => {
    if (yesterday_emissions === 0) return { pct: 0, improved: true };
    const diff = today_emissions - yesterday_emissions;
    const pct = (diff / yesterday_emissions) * 100;
    return {
      pct: Math.abs(pct),
      improved: diff <= 0
    };
  };

  const trend = getCarbonTrend();

  // Helper to render inline SVG sparklines
  const renderSparkline = (dataPoints: number[], strokeColor: string) => {
    if (!dataPoints || dataPoints.length < 2) return null;
    const width = 60;
    const height = 24;
    const padding = 2;
    const max = Math.max(...dataPoints, 1);
    const min = Math.min(...dataPoints, 0);
    const range = max - min;
    const points = dataPoints.map((val, index) => {
      const x = padding + (index / (dataPoints.length - 1)) * (width - padding * 2);
      const y = padding + (1 - (val - min) / (range || 1)) * (height - padding * 2);
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    });
    return (
      <svg width={width} height={height} className="overflow-visible">
        <path
          d={`M ${points.join(" L ")}`}
          fill="none"
          stroke={strokeColor}
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    );
  };

  // Circular progress helper
  const radius = 12;
  const strokeWidth = 2.5;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (Math.min(100, Math.max(0, finalScore)) / 100) * circumference;

  // XP level parameters
  const LEVEL_NAMES = [
    "",
    "Eco Beginner",
    "Eco Explorer",
    "Eco Guardian",
    "Climate Champion",
    "Sustainability Leader",
    "Carbon Warrior",
    "Net-Zero Master"
  ];
  const LEVEL_THRESHOLDS = [
    { min: 0, max: 250 },
    { min: 250, max: 650 },
    { min: 650, max: 1250 },
    { min: 1250, max: 2250 },
    { min: 2250, max: 3750 },
    { min: 3750, max: 5750 },
    { min: 5750, max: 1000000 }
  ];
  
  const safeLvl = Math.min(7, Math.max(1, level));
  const currentLvlInfo = LEVEL_THRESHOLDS[safeLvl - 1] || LEVEL_THRESHOLDS[LEVEL_THRESHOLDS.length - 1];
  const currentLevelBase = currentLvlInfo.min;
  const nextLevelXp = currentLvlInfo.max;
  const xpInCurrentLevel = Math.max(0, xp - currentLevelBase);
  const range = nextLevelXp - currentLevelBase;
  const levelProgressPct = summary?.progress_pct ?? (range > 0 ? Math.min(100, Math.max(0, (xpInCurrentLevel / range) * 100)) : 100);
  const currentLevelName = summary?.level_name ?? LEVEL_NAMES[safeLvl] ?? "Net-Zero Master";

  // Extract emissions trend array for sparklines
  const emissionsHistory = trends ? trends.map(t => t.emissions) : [0.5, 0.8, 0.4, today_emissions];
  const scoreHistory = trends ? trends.map(t => t.score) : [90, 85, 93, finalScore];

  return (
    <div className="relative w-full">
      {showDegraded && (
        <div className="absolute -top-3 left-2 z-20 px-2 py-0.5 rounded bg-amber-500/20 border border-amber-500/30 text-[8px] font-black uppercase tracking-wider text-amber-450 animate-pulse">
          Running in degraded mode.
        </div>
      )}
      <div className={`grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5 w-full select-none ${showDegraded ? "opacity-90" : ""}`}>
        {/* CARD 1: Today's CO2 */}
        <motion.div
          whileHover={{ y: -3, transition: { duration: 0.2 } }}
          className="glass-card rounded-2xl p-4.5 flex flex-col justify-between h-[115px] relative"
        >
          <div className="flex items-start justify-between">
            <div className="space-y-1">
              <span className="text-[9px] font-black uppercase tracking-wider text-stone-500 flex items-center gap-1">
                <Cloud className="w-3.5 h-3.5 text-stone-500" />
                Today's CO₂
              </span>
              <div className="text-2xl font-black text-white leading-none mt-1.5 font-sans">
                {today_emissions.toFixed(1)} <span className="text-[10px] font-semibold text-stone-500 uppercase">kg</span>
              </div>
            </div>
            {/* Sparkline on the right */}
            <div className="mt-2 opacity-85">
              {renderSparkline(emissionsHistory, "#10b981")}
            </div>
          </div>
          <div className="text-[10px] font-bold text-stone-400 flex items-center gap-1 mt-1">
            <span className={trend.improved ? "text-emerald-450" : "text-rose-500"}>
              {trend.improved ? "↓" : "↑"} {trend.pct.toFixed(0)}%
            </span>
            <span className="text-stone-500">vs Yesterday</span>
          </div>
        </motion.div>

        {/* CARD 2: Sustainability Score */}
        <motion.div
          whileHover={{ y: -3, transition: { duration: 0.2 } }}
          className="glass-card rounded-2xl p-4.5 flex flex-col justify-between h-[115px] relative"
        >
          <div className="flex items-start justify-between">
            <div className="space-y-1">
              <span className="text-[9px] font-black uppercase tracking-wider text-stone-500 flex items-center gap-1">
                <Target className="w-3.5 h-3.5 text-stone-500" />
                Sustainability Score
              </span>
              <div className="text-2xl font-black text-emerald-400 leading-none mt-1.5 font-sans">
                {finalScore.toFixed(0)}<span className="text-xs text-stone-500 font-normal">/100</span>
              </div>
            </div>

            {/* Circular progress ring on the right */}
            <div className="relative w-8 h-8 flex items-center justify-center mt-1">
              <svg className="w-full h-full transform -rotate-90">
                <circle
                  cx="16"
                  cy="16"
                  r={radius}
                  className="stroke-stone-800"
                  strokeWidth={strokeWidth}
                  fill="transparent"
                />
                <circle
                  cx="16"
                  cy="16"
                  r={radius}
                  className="stroke-emerald-400"
                  strokeWidth={strokeWidth}
                  fill="transparent"
                  strokeDasharray={circumference}
                  strokeDashoffset={strokeDashoffset}
                  strokeLinecap="round"
                />
              </svg>
            </div>
          </div>
          <div className="text-[10px] font-bold text-stone-500 mt-1">
            Great job! Keep improving 🌱
          </div>
        </motion.div>

        {/* CARD 3: Total Footprint */}
        <motion.div
          whileHover={{ y: -3, transition: { duration: 0.2 } }}
          className="glass-card rounded-2xl p-4.5 flex flex-col justify-between h-[115px] relative"
        >
          <div className="flex items-start justify-between">
            <div className="space-y-1">
              <span className="text-[9px] font-black uppercase tracking-wider text-stone-500 flex items-center gap-1">
                <Flame className="w-3.5 h-3.5 text-stone-500" />
                Total Footprint
              </span>
              <div className="text-2xl font-black text-white leading-none mt-1.5 font-sans">
                {weekly_emissions.toFixed(1)} <span className="text-[10px] font-semibold text-stone-500 uppercase">kg</span>
              </div>
            </div>
            {/* Sparkline on the right */}
            <div className="mt-2 opacity-85">
              {renderSparkline(scoreHistory.map(s => 100 - s), "#eab308")}
            </div>
          </div>
          <div className="text-[10px] font-bold text-emerald-400 mt-1">
            This Month
          </div>
        </motion.div>

        {/* CARD 4: XP / Level */}
        <motion.div
          whileHover={{ y: -3, transition: { duration: 0.2 } }}
          className="glass-card rounded-2xl p-4.5 flex flex-col justify-between h-[115px] relative"
        >
          <div className="flex items-start justify-between w-full">
            <div className="space-y-1">
              <span className="text-[9px] font-black uppercase tracking-wider text-stone-500 flex items-center gap-1">
                <Zap className="w-3.5 h-3.5 text-stone-500" />
                XP / Level
              </span>
              <div className="text-xl font-black text-purple-400 leading-none mt-1.5 font-sans">
                {xp} XP <span className="text-[9px] font-semibold text-stone-550 uppercase">• {currentLevelName}</span>
              </div>
            </div>
          </div>
          {/* Progress Bar */}
          <div className="space-y-1.5 w-full mt-2">
            <div className="w-full h-1.5 rounded-full bg-stone-900 overflow-hidden border border-white/5">
              <div
                className="h-full rounded-full bg-gradient-to-r from-purple-500 to-indigo-500 transition-all duration-300"
                style={{ width: `${levelProgressPct}%` }}
              ></div>
            </div>
            <div className="text-[8px] font-extrabold uppercase text-stone-550 tracking-wider flex justify-between">
              <span>{xpInCurrentLevel} XP In L{safeLvl}</span>
              <span>{safeLvl >= 7 ? "Max Level" : `${Math.max(0, nextLevelXp - xp)} XP to Level ${safeLvl + 1}`}</span>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
}

