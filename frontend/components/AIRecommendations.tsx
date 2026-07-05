"use client";

import React, { useState } from "react";
import { 
  Sparkles, Leaf, Car, Snowflake, ChevronRight, Info, BarChart2, Check 
} from "lucide-react";
import { AIInsight } from "../services/api";
import { getSafeCategory } from "../utils/safeCategory";
import { motion, AnimatePresence } from "framer-motion";
import { useAIStore } from "../stores/aiStore";
import { Card } from "./ui/Card";
import { Badge } from "./ui/Badge";
import { Button } from "./ui/Button";

interface AIRecommendationsProps {
  insights: AIInsight[];
  loading: boolean;
}

const INSIGHT_ICONS: Record<string, { icon: any; color: string; bg: string }> = {
  transport: { icon: Car, color: "text-purple-400", bg: "bg-purple-950/20 border-purple-500/20" },
  transportation: { icon: Car, color: "text-purple-400", bg: "bg-purple-950/20 border-purple-500/20" },
  energy: { icon: Snowflake, color: "text-sky-400", bg: "bg-sky-950/20 border-sky-500/20" },
  electricity: { icon: Snowflake, color: "text-sky-400", bg: "bg-sky-950/20 border-sky-500/20" },
  appliances: { icon: Snowflake, color: "text-sky-400", bg: "bg-sky-950/20 border-sky-500/20" },
  lifestyle: { icon: Leaf, color: "text-emerald-450", bg: "bg-emerald-950/20 border-emerald-500/20" },
  food: { icon: Leaf, color: "text-emerald-450", bg: "bg-emerald-950/20 border-emerald-500/20" }
};

export default function AIRecommendations({ insights, loading }: AIRecommendationsProps) {
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const { systemHealth } = useAIStore();
  const dbStatus = systemHealth?.database;
  const aiStatus = systemHealth?.ai;

  const toggleExpand = (id: number) => {
    setExpandedId(expandedId === id ? null : id);
  };

  if (dbStatus === "offline" || aiStatus === "offline") {
    return (
      <Card className="flex flex-col justify-between h-[360px] select-none" hover={false}>
        <div>
          <div className="flex items-center space-x-2.5 pb-3 border-b border-white/5 mb-3">
            <div className="w-6 h-6 rounded-lg bg-emerald-500/10 flex items-center justify-center border border-emerald-500/20">
              <Sparkles className="w-3.5 h-3.5 text-emerald-450" />
            </div>
            <h3 className="font-extrabold text-xs text-theme-secondary uppercase tracking-widest">
              AI Insights
            </h3>
          </div>
          <div className="flex flex-col items-center justify-center min-h-[200px] border border-dashed border-theme-subtle rounded-2xl bg-white/[0.01]">
            <span className="text-xs font-black uppercase tracking-wider text-rose-455">
              AI Service Offline
            </span>
          </div>
        </div>
      </Card>
    );
  }

  const defaultInsights = [
    {
      id: 101,
      content: "Your transportation emissions are lower than 72% of users this week. Great job! 🚲",
      category: "lifestyle",
      impact_estimate: "Praise",
      why_explanation: "Using low-emission options like bicycling has lowered your footprint relative to your peers.",
      how_calculation: "Calculated based on 25km of active commuting.",
      confidence_score: 0.95,
      weighted_priority_score: 85.5,
      feasibility: "HIGH",
      difficulty: "EASY",
      impact_value: 0.0
    },
    {
      id: 102,
      content: "Using public transport 2 more times can reduce 1.3 kg CO₂ this week.",
      category: "transport",
      impact_estimate: "1.3 kg CO₂",
      why_explanation: "Buses and trains share emissions across passengers, making them much cleaner per passenger-km.",
      how_calculation: "Saving 10km driving by swapping to metro transit.",
      confidence_score: 0.90,
      weighted_priority_score: 72.0,
      feasibility: "HIGH",
      difficulty: "EASY",
      impact_value: 1.3
    },
    {
      id: 103,
      content: "Try reducing AC usage by 1 hour daily to save 0.8 kg CO₂ weekly.",
      category: "energy",
      impact_estimate: "0.8 kg CO₂",
      why_explanation: "Air conditioning draws substantial electric loads from regional fossil-powered grids.",
      how_calculation: "Savings from 7 hours of AC runtime reduction.",
      confidence_score: 0.88,
      weighted_priority_score: 64.2,
      feasibility: "MEDIUM",
      difficulty: "MEDIUM",
      impact_value: 0.8
    }
  ];

  const activeInsights = Array.isArray(insights) && insights.length > 0 ? insights.slice(0, 3) : defaultInsights;
  const showDegraded = dbStatus === "degraded" || aiStatus === "degraded";

  return (
    <Card className="flex flex-col justify-between h-[360px] select-none" hover={false}>
      <div>
        {/* Header */}
        <div className="flex items-center justify-between pb-3 border-b border-white/5 mb-3">
          <div className="flex items-center space-x-2.5">
            <div className="w-6 h-6 rounded-lg bg-emerald-500/10 flex items-center justify-center border border-emerald-500/20">
              <Sparkles className="w-3.5 h-3.5 text-emerald-450" />
            </div>
            <h3 className="font-extrabold text-xs text-theme-secondary uppercase tracking-widest">
              AI Insights
            </h3>
          </div>
          {showDegraded ? (
            <Badge variant="warning" size="xs" dot>degraded</Badge>
          ) : (
            <Badge variant="success" size="xs" dot>New</Badge>
          )}
        </div>

        {/* Recommendations list */}
        {loading ? (
          <div className="space-y-2 animate-pulse flex flex-col justify-center items-center min-h-[220px]">
            <Sparkles className="w-6 h-6 text-amber-500 animate-spin mb-2" />
            <span className="text-theme-muted text-[10px] font-black uppercase tracking-widest">Loading Insights...</span>
          </div>
        ) : activeInsights.length === 0 ? (
          <div className="flex items-center justify-center min-h-[200px]">
            <span className="text-xs font-black uppercase tracking-wider text-theme-muted">
              No insights compiled.
            </span>
          </div>
        ) : (
          <div className="space-y-2 max-h-[220px] overflow-y-auto pr-1">
            {activeInsights.map((insight) => {
              const safeCat = getSafeCategory(insight.category);
              const { icon: Icon, color, bg } = INSIGHT_ICONS[safeCat] || INSIGHT_ICONS.lifestyle;
              const isExpanded = expandedId === insight.id;

              return (
                <div key={insight.id} className="group flex flex-col">
                  <motion.div
                    whileHover={{ x: 2 }}
                    onClick={() => toggleExpand(insight.id)}
                    className="flex items-center justify-between p-2.5 rounded-2xl border border-theme-subtle bg-white/[0.01] hover:bg-white/[0.02] transition-all cursor-pointer"
                  >
                    <div className="flex items-center space-x-3 min-w-0 flex-1">
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center border flex-shrink-0 ${bg}`}>
                        <Icon className={`w-4 h-4 ${color}`} />
                      </div>
                      
                      <div className="min-w-0 pr-2">
                        <p className="text-[11px] font-bold text-theme-secondary leading-normal line-clamp-2">
                          {insight.content}
                        </p>
                      </div>
                    </div>

                    <div className="flex-shrink-0 text-theme-muted pr-1 group-hover:text-theme-primary">
                      <ChevronRight className={`w-4 h-4 transition-transform duration-300 ${isExpanded ? "rotate-90 text-theme-brand" : ""}`} />
                    </div>
                  </motion.div>

                  <AnimatePresence initial={false}>
                    {isExpanded && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: "auto", opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.2 }}
                        className="overflow-hidden bg-[#070b09] border-x border-b border-theme-subtle rounded-b-2xl -mt-2 p-3 space-y-2 text-[10px] text-theme-muted font-bold"
                      >
                        {insight.why_explanation && (
                          <div>
                            <span className="text-[8px] uppercase tracking-widest text-theme-brand block mb-0.5">AI Reasoning</span>
                            <p className="text-theme-secondary font-medium leading-relaxed">{insight.why_explanation}</p>
                          </div>
                        )}
                        {insight.how_calculation && (
                          <div>
                            <span className="text-[8px] uppercase tracking-widest text-sky-400 block mb-0.5">Calculation Formula</span>
                            <p className="text-theme-secondary font-medium leading-relaxed">{insight.how_calculation}</p>
                          </div>
                        )}
                        <div className="grid grid-cols-2 gap-x-4 gap-y-1 border-t border-white/5 pt-1.5 mt-1.5 text-[9px] text-theme-muted font-bold">
                          {typeof insight.weighted_priority_score === "number" && (
                            <div className="flex justify-between">
                              <span>Priority Score:</span>
                              <span className="text-theme-brand">{insight.weighted_priority_score.toFixed(1)}</span>
                            </div>
                          )}
                          {(insight.impact_estimate || insight.impact_value !== undefined) && (
                            <div className="flex justify-between">
                              <span>Carbon Saved:</span>
                              <span className="text-theme-brand">
                                {insight.impact_estimate && insight.impact_estimate !== "Praise" 
                                  ? insight.impact_estimate 
                                  : `${insight.impact_value || 0} kg CO₂`}
                              </span>
                            </div>
                          )}
                          {insight.feasibility && (
                            <div className="flex justify-between">
                              <span>Feasibility:</span>
                              <span className="text-theme-secondary">{insight.feasibility}</span>
                            </div>
                          )}
                          {insight.difficulty && (
                            <div className="flex justify-between">
                              <span>Difficulty:</span>
                              <span className="text-theme-secondary">{insight.difficulty}</span>
                            </div>
                          )}
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              );
            })}
          </div>
        )}
      </div>

      <button className="w-full py-2 bg-white/[0.02] hover:bg-white/[0.04] border border-white/5 rounded-xl text-[10px] font-extrabold uppercase text-theme-muted hover:text-theme-primary transition-all flex items-center justify-center gap-1 cursor-pointer">
        <span>Get More Insights</span>
        <ChevronRight className="w-3.5 h-3.5" />
      </button>
    </Card>
  );
}
