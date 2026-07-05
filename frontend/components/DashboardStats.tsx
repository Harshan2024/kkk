"use client";

import React, { useEffect, useState } from "react";
import { Cloud, Target, Flame, Zap } from "lucide-react";
import { DashboardSummary } from "../services/api";
import { motion } from "framer-motion";
import { useAIStore } from "../stores/aiStore";
import { KpiCard } from "./ui/Card";
import { KpiSkeleton } from "./ui/Skeleton";

interface DashboardStatsProps {
  summary: DashboardSummary | null;
  xp?: number;
  level?: number;
  score?: number;
}

export default function DashboardStats({ summary, xp = 150, level = 1, score }: DashboardStatsProps) {
  const { systemHealth } = useAIStore();
  const dbStatus = systemHealth?.database;
  const [animatedScore, setAnimatedScore] = useState(0);
  const [animatedToday, setAnimatedToday] = useState(0);
  const [animatedWeekly, setAnimatedWeekly] = useState(0);

  const finalScore = score !== undefined ? score : (summary?.current_score ?? 0);
  const today_emissions = summary?.today_emissions ?? 0;
  const weekly_emissions = summary?.weekly_emissions ?? 0;

  // Simple count-up micro-animation
  useEffect(() => {
    if (!summary) return;
    const duration = 800; // ms
    const startTime = performance.now();

    const animate = (now: number) => {
      const elapsed = now - startTime;
      const progress = Math.min(elapsed / duration, 1);
      // Ease out quad
      const ease = progress * (2 - progress);

      setAnimatedScore(Math.round(ease * finalScore));
      setAnimatedToday(parseFloat((ease * today_emissions).toFixed(1)));
      setAnimatedWeekly(parseFloat((ease * weekly_emissions).toFixed(1)));

      if (progress < 1) {
        requestAnimationFrame(animate);
      }
    };

    requestAnimationFrame(animate);
  }, [summary, finalScore, today_emissions, weekly_emissions]);

  // 1. Error State (Database Offline)
  if (dbStatus === "offline") {
    return (
      <div className="relative grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5 w-full select-none min-h-[115px]">
        <div className="absolute inset-0 z-20 glass-premium rounded-3xl flex items-center justify-center border border-rose-500/20 bg-rose-500/10 backdrop-blur-md">
          <span className="text-xs font-black uppercase tracking-wider text-rose-400">
            Database Connection Offline — Running in Local Sandbox Mode
          </span>
        </div>
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="glass-premium rounded-2xl h-[115px] opacity-20"></div>
        ))}
      </div>
    );
  }

  // 2. Loading State
  if (!summary && (!systemHealth || systemHealth.backend === "offline")) {
    return <KpiSkeleton count={4} />;
  }

  // 3. Empty State
  if (!summary) {
    return (
      <div className="glass-premium rounded-3xl p-8 flex items-center justify-center min-h-[115px] border border-theme-subtle">
        <span className="text-xs font-black uppercase tracking-wider text-theme-muted">
          Waiting for activity metrics...
        </span>
      </div>
    );
  }

  const showDegraded = dbStatus === "degraded";
  const { yesterday_emissions = 0, trends = [] } = summary ?? {};

  // Calculate percentage change today vs yesterday
  const getCarbonTrend = () => {
    if (yesterday_emissions === 0) return { pct: 0, improved: true };
    const diff = today_emissions - yesterday_emissions;
    const pct = (diff / yesterday_emissions) * 100;
    return {
      pct: Math.abs(pct),
      improved: diff <= 0,
    };
  };

  const trend = getCarbonTrend();

  // Helper to render inline SVG sparklines with smooth glow
  const renderSparkline = (dataPoints: number[], strokeColor: string, id: string) => {
    if (!dataPoints || dataPoints.length < 2) return null;
    const width = 68;
    const height = 28;
    const padding = 3;
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
        <defs>
          <linearGradient id={`glow-${id}`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={strokeColor} stopOpacity="0.4" />
            <stop offset="100%" stopColor={strokeColor} stopOpacity="0.0" />
          </linearGradient>
        </defs>
        <path
          d={`M ${points[0]} L ${points.slice(1).join(" L ")}`}
          fill="none"
          stroke={strokeColor}
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          style={{ filter: `drop-shadow(0px 2px 4px ${strokeColor}40)` }}
        />
        {/* Under area */}
        <path
          d={`M ${padding},${height} L ${points.join(" L ")} L ${width - padding},${height} Z`}
          fill={`url(#glow-${id})`}
        />
      </svg>
    );
  };

  // Circular progress helper
  const radius = 13;
  const strokeWidth = 3;
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
    "Net-Zero Master",
  ];
  const LEVEL_THRESHOLDS = [
    { min: 0, max: 250 },
    { min: 250, max: 650 },
    { min: 650, max: 1250 },
    { min: 1250, max: 2250 },
    { min: 2250, max: 3750 },
    { min: 3750, max: 5750 },
    { min: 5750, max: 1000000 },
  ];

  const safeLvl = Math.min(7, Math.max(1, level));
  const currentLvlInfo = LEVEL_THRESHOLDS[safeLvl - 1] || LEVEL_THRESHOLDS[LEVEL_THRESHOLDS.length - 1];
  const currentLevelBase = currentLvlInfo.min;
  const nextLevelXp = currentLvlInfo.max;
  const xpInCurrentLevel = Math.max(0, xp - currentLevelBase);
  const totalLevelRange = nextLevelXp - currentLevelBase;
  const levelProgressPct =
    summary?.progress_pct ??
    (totalLevelRange > 0 ? Math.min(100, Math.max(0, (xpInCurrentLevel / totalLevelRange) * 100)) : 100);
  const currentLevelName = summary?.level_name ?? LEVEL_NAMES[safeLvl] ?? "Net-Zero Master";

  // Extract emissions trend array for sparklines
  const emissionsHistory = trends && trends.length > 0 ? trends.map((t) => t.emissions) : [0.5, 0.8, 0.4, today_emissions];
  const scoreHistory = trends && trends.length > 0 ? trends.map((t) => t.score) : [90, 85, 93, finalScore];

  return (
    <div className="relative w-full">
      {showDegraded && (
        <div className="absolute -top-3 left-2 z-20 px-2 py-0.5 rounded bg-amber-500/20 border border-amber-500/30 text-[8px] font-black uppercase tracking-wider text-amber-400 animate-pulse">
          Database Degraded — Serving Cached Metrics
        </div>
      )}
      <div className={`grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5 w-full select-none ${showDegraded ? "opacity-90" : ""}`}>
        {/* CARD 1: Today's CO2 */}
        <KpiCard
          label="Today's CO₂"
          value={animatedToday.toFixed(1)}
          unit="kg"
          icon={<Cloud className="w-3.5 h-3.5 text-sky-400" />}
          iconBg="bg-sky-500/10 border border-sky-500/25"
          trend={{ value: trend.pct, improved: trend.improved }}
          sparkline={renderSparkline(emissionsHistory, "var(--brand-primary)", "today")}
        />

        {/* CARD 2: Sustainability Score */}
        <motion.div
          whileHover={{ y: -3 }}
          transition={{ duration: 0.2 }}
          className="glass-premium rounded-2xl p-4.5 flex flex-col justify-between min-h-[115px]"
        >
          <div className="flex items-start justify-between">
            <div className="space-y-1.5">
              <span className="text-[10px] font-black uppercase tracking-wider text-theme-muted flex items-center gap-1.5">
                <span className="w-6 h-6 rounded-lg flex items-center justify-center bg-emerald-500/10 border border-emerald-500/25">
                  <Target className="w-3.5 h-3.5 text-emerald-400" />
                </span>
                Sustainability Score
              </span>
              <div className="flex items-baseline gap-1 mt-1.5">
                <span className="text-2xl font-black text-theme-brand leading-none font-display">
                  {animatedScore}
                </span>
                <span className="text-[10px] font-semibold text-theme-muted uppercase">/100</span>
              </div>
            </div>

            {/* Circular Progress Ring */}
            <div className="relative w-8 h-8 flex items-center justify-center mt-1">
              <svg className="w-full h-full transform -rotate-90">
                <circle
                  cx="16"
                  cy="16"
                  r={radius}
                  className="stroke-stone-850"
                  style={{ stroke: "rgba(255,255,255,0.05)" }}
                  strokeWidth={strokeWidth}
                  fill="transparent"
                />
                <circle
                  cx="16"
                  cy="16"
                  r={radius}
                  style={{
                    stroke: "var(--brand-primary)",
                    strokeDasharray: circumference,
                    strokeDashoffset: strokeDashoffset,
                  }}
                  strokeWidth={strokeWidth}
                  fill="transparent"
                  strokeLinecap="round"
                />
              </svg>
              <span className="absolute text-[8px] font-extrabold text-theme-brand">
                {finalScore.toFixed(0)}
              </span>
            </div>
          </div>
          <div className="text-[10px] font-bold text-theme-muted mt-2">
            Excellent index! Lower than regional avg.
          </div>
        </motion.div>

        {/* CARD 3: Weekly Footprint */}
        <KpiCard
          label="Weekly Footprint"
          value={animatedWeekly.toFixed(1)}
          unit="kg"
          icon={<Flame className="w-3.5 h-3.5 text-orange-400" />}
          iconBg="bg-orange-500/10 border border-orange-500/25"
          sparkline={renderSparkline(scoreHistory.map((s) => 100 - s), "#f59e0b", "weekly")}
          footer={
            <span className="text-[10px] text-theme-brand font-bold">
              Active tracking session
            </span>
          }
        />

        {/* CARD 4: XP / Level */}
        <motion.div
          whileHover={{ y: -3 }}
          transition={{ duration: 0.2 }}
          className="glass-premium rounded-2xl p-4.5 flex flex-col justify-between min-h-[115px]"
        >
          <div className="space-y-1.5">
            <span className="text-[10px] font-black uppercase tracking-wider text-theme-muted flex items-center gap-1.5">
              <span className="w-6 h-6 rounded-lg flex items-center justify-center bg-purple-500/10 border border-purple-500/25">
                <Zap className="w-3.5 h-3.5 text-purple-400" />
              </span>
              XP / Level Info
            </span>
            <div className="text-lg font-black text-purple-400 leading-none mt-1.5 font-display">
              {xp} XP <span className="text-[9px] font-extrabold text-theme-muted uppercase tracking-wide">• {currentLevelName}</span>
            </div>
          </div>

          <div className="space-y-1.5 w-full mt-2">
            <div className="w-full h-1 rounded-full bg-stone-900 overflow-hidden border border-white/5 relative">
              <div
                className="h-full rounded-full bg-gradient-to-r from-purple-500 to-indigo-500 transition-all duration-300"
                style={{ width: `${levelProgressPct}%` }}
              ></div>
            </div>
            <div className="text-[8px] font-extrabold uppercase text-theme-muted tracking-wider flex justify-between">
              <span>{xpInCurrentLevel} XP in L{safeLvl}</span>
              <span>{safeLvl >= 7 ? "Max Lvl" : `${Math.max(0, nextLevelXp - xp)} XP to L${safeLvl + 1}`}</span>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
