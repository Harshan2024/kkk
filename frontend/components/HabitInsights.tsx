"use client";

import React, { useState, useEffect, useMemo, useCallback } from "react";
import { Brain, TrendingUp, Zap, Calendar, Flame, AlertCircle, CheckCircle2, X, ChevronRight, Activity } from "lucide-react";
import { api } from "../services/api";
import { useAIStore } from "../stores/aiStore";
import { motion, AnimatePresence } from "framer-motion";

export const HabitInsights = React.memo(function HabitInsights() {
  const { summary } = useAIStore();
  const [analysisData, setAnalysisData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);

  // Fetch analysis data once on mount
  useEffect(() => {
    let active = true;
    async function fetchAnalysis() {
      try {
        const response = await api.getHabitAnalysis();
        if (active) {
          if (response && response.success) {
            setAnalysisData(response.data);
          } else {
            setAnalysisData({ insufficient_data: true });
          }
        }
      } catch (err) {
        if (active) {
          setAnalysisData({ insufficient_data: true });
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }
    fetchAnalysis();
    return () => {
      active = false;
    };
  }, []);

  // View More toggle handlers using useCallback
  const openModal = useCallback(() => setModalOpen(true), []);
  const closeModal = useCallback(() => setModalOpen(false), []);

  const currentStreak = useMemo(() => {
    return summary?.streaks?.current_streak ?? 1;
  }, [summary?.streaks?.current_streak]);

  if (loading) {
    return (
      <div className="glass-card rounded-3xl p-5 sm:p-6 flex flex-col justify-between h-[360px] select-none">
        <div>
          <div className="flex items-center space-x-2.5 pb-3 border-b border-white/5 mb-3">
            <div className="w-6 h-6 rounded-lg bg-emerald-500/10 flex items-center justify-center border border-emerald-500/20">
              <Brain className="w-3.5 h-3.5 text-emerald-450 animate-pulse" />
            </div>
            <h3 className="font-extrabold text-xs text-stone-300 uppercase tracking-widest">
              AI Habit Analysis
            </h3>
          </div>
          <div className="flex flex-col items-center justify-center min-h-[220px] border border-dashed border-white/5 rounded-2xl bg-white/[0.01] p-4 text-center">
            <Brain className="w-8 h-8 text-amber-550 mb-2 animate-spin" />
            <span className="text-stone-400 text-[10px] font-black uppercase tracking-widest animate-pulse">
              Loading Insights...
            </span>
          </div>
        </div>
      </div>
    );
  }

  if (!analysisData || analysisData.insufficient_data || analysisData.status === "temporarily_unavailable") {
    return (
      <div className="glass-card rounded-3xl p-5 sm:p-6 flex flex-col justify-between h-[360px]">
        <div>
          <div className="flex items-center space-x-2.5 pb-3 border-b border-white/5 mb-3">
            <div className="w-6 h-6 rounded-lg bg-emerald-500/10 flex items-center justify-center border border-emerald-500/20">
              <Brain className="w-3.5 h-3.5 text-emerald-450" />
            </div>
            <h3 className="font-extrabold text-xs text-stone-300 uppercase tracking-widest">
              AI Habit Analysis
            </h3>
          </div>
          <div className="flex flex-col items-center justify-center min-h-[220px] border border-dashed border-white/5 rounded-2xl bg-white/[0.01] p-4 text-center">
            <Activity className="w-8 h-8 text-white/20 mb-2 animate-bounce" />
            <span className="text-xs font-semibold text-stone-400">
              {analysisData?.status === "temporarily_unavailable"
                ? "Habit Analysis Coming Soon"
                : "Continue logging activities to unlock AI Habit Analysis."}
            </span>
          </div>
        </div>
      </div>
    );
  }

  const { details, insights } = analysisData;

  // Derive display values from analysis payload
  const transportStatus = details?.transport?.status ?? "Stable";
  const energyStatus = details?.energy?.status ?? "Stable";
  const consistencyStatus = details?.logging_consistency?.status ?? "Good";

  return (
    <>
      <div className="glass-card rounded-3xl p-5 sm:p-6 transition-all duration-300 flex flex-col justify-between h-[360px] select-none">
        <div>
          {/* Header */}
          <div className="flex items-center space-x-2.5 pb-3 border-b border-white/5 mb-3">
            <div className="w-6 h-6 rounded-lg bg-emerald-500/10 flex items-center justify-center border border-emerald-500/20">
              <Brain className="w-3.5 h-3.5 text-emerald-450" />
            </div>
            <h3 className="font-extrabold text-xs text-stone-300 uppercase tracking-widest">
              AI Habit Analysis
            </h3>
          </div>

          {/* Quick Stats list */}
          <div className="space-y-2 max-h-[220px] overflow-y-auto pr-1">
            {/* Transport status row */}
            <div className="flex items-center justify-between p-2.5 rounded-2xl bg-white/[0.02] border border-white/5">
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 rounded-xl bg-purple-500/10 flex items-center justify-center border border-purple-500/15">
                  <TrendingUp className="w-4 h-4 text-purple-400" />
                </div>
                <div>
                  <h4 className="text-xs font-bold text-stone-200">Transport</h4>
                  <p className="text-[10px] text-stone-400">Week-to-week comparison</p>
                </div>
              </div>
              <span className={`text-[10px] px-2.5 py-1 rounded-full font-black uppercase tracking-wider ${
                transportStatus === "Improving" ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20" :
                transportStatus === "Worsening" ? "bg-rose-500/10 text-rose-400 border border-rose-500/20" :
                "bg-stone-500/10 text-stone-400 border border-stone-500/20"
              }`}>
                {transportStatus}
              </span>
            </div>

            {/* Energy status row */}
            <div className="flex items-center justify-between p-2.5 rounded-2xl bg-white/[0.02] border border-white/5">
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 rounded-xl bg-amber-500/10 flex items-center justify-center border border-amber-500/15">
                  <Zap className="w-4 h-4 text-amber-400" />
                </div>
                <div>
                  <h4 className="text-xs font-bold text-stone-200">Energy</h4>
                  <p className="text-[10px] text-stone-400">AC & appliance cycles</p>
                </div>
              </div>
              <span className={`text-[10px] px-2.5 py-1 rounded-full font-black uppercase tracking-wider ${
                energyStatus === "Stable" ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20" :
                "bg-amber-500/10 text-amber-400 border border-amber-500/20"
              }`}>
                {energyStatus}
              </span>
            </div>

            {/* Logging status row */}
            <div className="flex items-center justify-between p-2.5 rounded-2xl bg-white/[0.02] border border-white/5">
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 rounded-xl bg-blue-500/10 flex items-center justify-center border border-blue-500/15">
                  <Calendar className="w-4 h-4 text-blue-400" />
                </div>
                <div>
                  <h4 className="text-xs font-bold text-stone-200">Logging</h4>
                  <p className="text-[10px] text-stone-400">Weekly tracking status</p>
                </div>
              </div>
              <span className={`text-[10px] px-2.5 py-1 rounded-full font-black uppercase tracking-wider ${
                consistencyStatus === "Excellent" ? "bg-emerald-500/15 text-emerald-400 border border-emerald-500/30" :
                consistencyStatus === "Good" ? "bg-blue-500/10 text-blue-400 border border-blue-500/20" :
                "bg-rose-500/10 text-rose-400 border border-rose-500/20"
              }`}>
                {consistencyStatus}
              </span>
            </div>

            {/* Streak status row */}
            <div className="flex items-center justify-between p-2.5 rounded-2xl bg-white/[0.02] border border-white/5">
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 rounded-xl bg-rose-500/10 flex items-center justify-center border border-rose-500/15">
                  <Flame className="w-4 h-4 text-rose-400" />
                </div>
                <div>
                  <h4 className="text-xs font-bold text-stone-200">Current Streak</h4>
                  <p className="text-[10px] text-stone-400">Consistent logging reward</p>
                </div>
              </div>
              <span className="text-xs font-black text-rose-400 flex items-center space-x-1">
                <span>{currentStreak} Days</span>
              </span>
            </div>
          </div>
        </div>

        {/* View More Trigger */}
        <button
          onClick={openModal}
          className="w-full mt-3 py-2.5 rounded-2xl bg-white/5 hover:bg-white/10 active:bg-white/5 border border-white/5 hover:border-white/10 transition-all text-xs font-black text-stone-300 flex items-center justify-center space-x-1"
        >
          <span>View More</span>
          <ChevronRight className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Modal Popup overlay — reusing local data completely without network queries */}
      <AnimatePresence>
        {modalOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm select-none">
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 15 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 15 }}
              transition={{ duration: 0.2 }}
              className="glass-card rounded-[32px] w-full max-w-xl p-6 relative overflow-hidden border border-white/10 flex flex-col max-h-[85vh]"
            >
              {/* Modal Header */}
              <div className="flex items-center justify-between pb-4 border-b border-white/5 mb-4">
                <div className="flex items-center space-x-3">
                  <div className="w-8 h-8 rounded-xl bg-emerald-500/10 flex items-center justify-center border border-emerald-500/20">
                    <Brain className="w-4 h-4 text-emerald-450" />
                  </div>
                  <div>
                    <h3 className="text-sm font-extrabold text-stone-200 uppercase tracking-wider">
                      Detailed AI Habit Insights
                    </h3>
                    <p className="text-[10px] text-stone-400">
                      Generated at: {new Date(analysisData.generated_at).toLocaleTimeString()} {analysisData.cached ? "(Cached)" : ""}
                    </p>
                  </div>
                </div>
                <button
                  onClick={closeModal}
                  className="w-8 h-8 rounded-full bg-white/5 hover:bg-white/10 flex items-center justify-center text-stone-400 hover:text-white transition-colors"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              {/* Modal Body (Scrollable) */}
              <div className="flex-1 overflow-y-auto space-y-4 pr-1 scrollbar-thin">
                {/* 3 Dynamic Insights Block */}
                <div className="p-4 rounded-2xl bg-white/[0.02] border border-white/5 space-y-2">
                  <h4 className="text-[11px] font-black text-stone-400 uppercase tracking-widest mb-1 flex items-center space-x-1.5">
                    <span>Proactive Insights</span>
                  </h4>
                  <ul className="space-y-2.5">
                    {insights?.map((insight: string, idx: number) => (
                      <li key={idx} className="text-xs text-stone-300 flex items-start space-x-2.5 leading-relaxed">
                        <span className="mt-1 flex-shrink-0 w-1.5 h-1.5 rounded-full bg-emerald-400" />
                        <span>{insight}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                {/* Subsystem Details grid */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {/* Transport */}
                  <div className="p-4 rounded-2xl bg-white/[0.02] border border-white/5 space-y-1">
                    <span className="text-[9px] font-black text-stone-500 uppercase tracking-widest">Transport</span>
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-stone-300">{details?.transport?.status}</span>
                      <span className="text-[9px] font-bold text-stone-400 bg-white/5 px-2 py-0.5 rounded-full">Conf: {details?.transport?.confidence}</span>
                    </div>
                  </div>

                  {/* Energy */}
                  <div className="p-4 rounded-2xl bg-white/[0.02] border border-white/5 space-y-1">
                    <span className="text-[9px] font-black text-stone-500 uppercase tracking-widest">Energy</span>
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-stone-300">{details?.energy?.status}</span>
                      <span className="text-[9px] font-bold text-stone-400 bg-white/5 px-2 py-0.5 rounded-full">Conf: {details?.energy?.confidence}</span>
                    </div>
                  </div>

                  {/* Food */}
                  <div className="p-4 rounded-2xl bg-white/[0.02] border border-white/5 space-y-1">
                    <span className="text-[9px] font-black text-stone-500 uppercase tracking-widest">Food & Diet</span>
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-stone-300">{details?.food?.status}</span>
                      <span className="text-[9px] font-bold text-stone-400 bg-white/5 px-2 py-0.5 rounded-full">Conf: {details?.food?.confidence}</span>
                    </div>
                  </div>

                  {/* Score Trend */}
                  <div className="p-4 rounded-2xl bg-white/[0.02] border border-white/5 space-y-1">
                    <span className="text-[9px] font-black text-stone-500 uppercase tracking-widest">Score Trend</span>
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-stone-300">{details?.score_trend?.status}</span>
                      <span className="text-[9px] font-bold text-stone-400 bg-white/5 px-2 py-0.5 rounded-full">Conf: {details?.score_trend?.confidence}</span>
                    </div>
                  </div>
                </div>

                {/* Risk assessment and logging consistency */}
                <div className="p-4 rounded-2xl bg-white/[0.02] border border-white/5 space-y-3">
                  <div>
                    <h4 className="text-[11px] font-black text-stone-400 uppercase tracking-widest mb-2">Category Risk levels</h4>
                    <div className="grid grid-cols-4 gap-2 text-center text-[10px]">
                      <div className="p-2 rounded-xl bg-white/5">
                        <span className="block text-stone-500 font-extrabold uppercase mb-0.5">Travel</span>
                        <span className={`font-black ${
                          details?.risk_assessment?.transport === "High" ? "text-rose-400" :
                          details?.risk_assessment?.transport === "Medium" ? "text-amber-400" : "text-emerald-400"
                        }`}>{details?.risk_assessment?.transport}</span>
                      </div>
                      <div className="p-2 rounded-xl bg-white/5">
                        <span className="block text-stone-500 font-extrabold uppercase mb-0.5">Energy</span>
                        <span className={`font-black ${
                          details?.risk_assessment?.energy === "High" ? "text-rose-400" :
                          details?.risk_assessment?.energy === "Medium" ? "text-amber-400" : "text-emerald-400"
                        }`}>{details?.risk_assessment?.energy}</span>
                      </div>
                      <div className="p-2 rounded-xl bg-white/5">
                        <span className="block text-stone-500 font-extrabold uppercase mb-0.5">Food</span>
                        <span className={`font-black ${
                          details?.risk_assessment?.food === "High" ? "text-rose-400" :
                          details?.risk_assessment?.food === "Medium" ? "text-amber-400" : "text-emerald-400"
                        }`}>{details?.risk_assessment?.food}</span>
                      </div>
                      <div className="p-2 rounded-xl bg-white/5">
                        <span className="block text-stone-500 font-extrabold uppercase mb-0.5">Waste</span>
                        <span className={`font-black ${
                          details?.risk_assessment?.waste === "High" ? "text-rose-400" :
                          details?.risk_assessment?.waste === "Medium" ? "text-amber-400" : "text-emerald-400"
                        }`}>{details?.risk_assessment?.waste}</span>
                      </div>
                    </div>
                  </div>

                  <div className="pt-2 border-t border-white/5 flex items-center justify-between text-xs text-stone-300">
                    <span className="font-bold">Logging Consistency:</span>
                    <span className="font-black text-emerald-400">{details?.logging_consistency?.percentage}% ({details?.logging_consistency?.status})</span>
                  </div>
                </div>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </>
  );
});
