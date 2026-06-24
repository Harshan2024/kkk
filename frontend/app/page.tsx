"use client";

import React, { useState, useMemo, useCallback, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Sparkles, MessageSquare } from "lucide-react";
import { useRouter } from "next/navigation";

import Sidebar from "../components/Sidebar";
import Topbar from "../components/Topbar";
import EarthPanel from "../components/EarthPanel";
import WeeklyFootprintChart from "../components/WeeklyFootprintChart";
import CategoryDonutChart from "../components/CategoryDonutChart";
import DailyQuests from "../components/DailyQuests";
import StreakFooter from "../components/StreakFooter";
import IoTDashboard from "../components/IoTDashboard";
import ActivityInput from "../components/ActivityInput";
import DashboardStats from "../components/DashboardStats";
import CarbonCharts from "../components/CarbonCharts";
import AIRecommendations from "../components/AIRecommendations";
import Achievements from "../components/Achievements";
import ActivityHistory from "../components/ActivityHistory";
import CoachDashboard from "../components/CoachDashboard";
import Marketplace from "../components/Marketplace";
import api, { GamificationProfile } from "../services/api";
import dynamic from "next/dynamic";
const CopilotChat = dynamic(() => import("../components/CopilotChat"), {
  loading: () => null,
  ssr: false,
});
const HabitInsights = dynamic(() => import("../components/HabitInsights").then(mod => mod.HabitInsights), {
  loading: () => <div className="glass-card rounded-3xl h-[360px] animate-pulse bg-white/5" />,
  ssr: false,
});
import MultimodalUpload from "../components/MultimodalUpload";
import SystemStatusWidget from "../components/SystemStatusWidget";
import ErrorBoundary from "../components/ErrorBoundary";
import { AIStoreProvider, useAIStore } from "../stores/aiStore";

// ─────────────────────────────────────────────────────────────────────────────
// ANIMATION VARIANTS
// ─────────────────────────────────────────────────────────────────────────────

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.05, delayChildren: 0.02 },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 10 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { type: "spring", stiffness: 100, damping: 15 },
  },
};

// ─────────────────────────────────────────────────────────────────────────────
// TOAST NOTIFICATION — non-blocking, auto-dismisses
// ─────────────────────────────────────────────────────────────────────────────

function ToastError() {
  const { toastError, clearToastError } = useAIStore();
  return (
    <AnimatePresence>
      {toastError && (
        <motion.div
          initial={{ opacity: 0, y: 40, scale: 0.95 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: 20, scale: 0.95 }}
          className="fixed bottom-6 right-6 z-[100] max-w-sm"
        >
          <div className="glass-card rounded-2xl p-4 border border-amber-500/30 bg-amber-500/10 shadow-xl shadow-amber-500/10 flex items-start gap-3">
            <div className="flex-1">
              <p className="text-[11px] font-bold text-amber-300 leading-relaxed">{toastError}</p>
            </div>
            <button
              onClick={clearToastError}
              className="text-stone-500 hover:text-white transition-colors cursor-pointer mt-0.5"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// MAIN DASHBOARD CONTENT
// ─────────────────────────────────────────────────────────────────────────────

function HomeContent() {
  const {
    summary,
    insights,
    insightsLoading,
    achievements,
    activities,
    loading,
    error,
    region,
    setRegion,
    loadDashboardData,
    metrics,
    fetchAnalytics,
    isAuthenticated,
    user,
  } = useAIStore();

  const router = useRouter();

  useEffect(() => {
    if (!loading && !isAuthenticated) {
      router.push("/login");
    }
  }, [loading, isAuthenticated, router]);

  const [currentTab, setCurrentTab] = useState("dashboard");
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [isCopilotOpen, setIsCopilotOpen] = useState(false);
  const [gamificationProfile, setGamificationProfile] = useState<GamificationProfile | null>(null);

  const fetchGamificationProfile = useCallback(async () => {
    try {
      const profileData = await api.getGamificationProfile();
      setGamificationProfile(profileData);
      console.log("[CarbonTracker] Fetched gamification profile:", profileData);
    } catch (err) {
      console.error("Failed to fetch gamification profile", err);
    }
  }, []);

  useEffect(() => {
    fetchGamificationProfile();
  }, [fetchGamificationProfile, activities?.length, currentTab]);

  useEffect(() => {
    const handleOpen = () => setIsCopilotOpen(true);
    window.addEventListener("open-copilot", handleOpen);
    return () => window.removeEventListener("open-copilot", handleOpen);
  }, []);

  useEffect(() => {
    if (currentTab === "analytics") {
      fetchAnalytics();
    }
  }, [currentTab, fetchAnalytics]);

  // Memoized gamification values — prefer backend profile, fallback to computed if null
  const { xp, level, streak, score } = useMemo(() => {
    if (gamificationProfile) {
      return {
        xp: gamificationProfile.total_xp,
        level: gamificationProfile.level,
        streak: gamificationProfile.streak,
        score: gamificationProfile.sustainability_score
      };
    }
    const achievementsCount = summary?.achievements_count ?? achievements?.length ?? 0;
    const xpVal = summary?.xp ?? (150 + (activities?.length ?? 0) * 20 + achievementsCount * 100);
    const levelVal = summary?.level ?? (Math.floor(xpVal / 200) + 1);
    const streakVal = summary?.streaks?.current_streak ?? (summary?.trends
      ? Math.max(1, summary.trends.filter((t) => t.emissions > 0).length)
      : 1);
    const scoreVal = summary?.current_score ?? 0;
    return { xp: xpVal, level: levelVal, streak: streakVal, score: scoreVal };
  }, [gamificationProfile, summary, achievements, activities]);

  const handleTabChange = useCallback((tab: string) => setCurrentTab(tab), []);

  return (
    <div className="min-h-screen bg-[#080d0a] text-stone-100 font-sans relative overflow-x-hidden transition-colors duration-300">
      {/* Background Dot Matrix Accent */}
      <div className="absolute inset-0 dot-matrix pointer-events-none z-0" />

      {/* Atmospheric glowing green orbs */}
      <div className="absolute top-[-10%] left-[-5%] w-[45%] aspect-square rounded-full bg-emerald-600/5 blur-[120px] pointer-events-none z-0" />
      <div className="absolute bottom-[-10%] right-[-5%] w-[45%] aspect-square rounded-full bg-emerald-700/5 blur-[120px] pointer-events-none z-0" />

      {/* Sidebar — isolated error boundary */}
      <ErrorBoundary>
        <Sidebar
          currentTab={currentTab}
          onTabChange={handleTabChange}
          username={user?.username || "Guest"}
          xp={xp}
          level={level}
          streak={streak}
          isOpen={sidebarOpen}
          onClose={() => setSidebarOpen(false)}
        />
      </ErrorBoundary>

      {/* Main viewport */}
      <div className="lg:pl-64 flex flex-col min-h-screen relative z-10">
        {/* Topbar — isolated error boundary */}
        <ErrorBoundary>
          <Topbar onRefresh={loadDashboardData} region={region} onRegionChange={setRegion} />
        </ErrorBoundary>

        <main className="flex-1 px-4 sm:px-6 lg:px-8 py-6 space-y-6">

          {/* Error Alert banner */}
          {error && (
            error === "Reconnecting to database..." ? (
              <div className="p-4 rounded-2xl border border-amber-500/30 bg-amber-500/10 text-amber-400 text-xs font-bold flex items-center gap-3 shadow-lg shadow-amber-500/5 animate-in fade-in select-none">
                <span className="w-3.5 h-3.5 border-2 border-amber-400 border-t-transparent rounded-full animate-spin flex-shrink-0" />
                <span>Reconnecting to database... Running in read-only mode.</span>
              </div>
            ) : (
              <div className="p-4 rounded-2xl border border-rose-500/30 bg-rose-500/10 text-rose-400 text-xs font-bold flex items-center justify-between shadow-lg shadow-rose-500/5 animate-in fade-in">
                <span>{error}</span>
                <button
                  onClick={loadDashboardData}
                  className="px-3 py-1.5 bg-rose-500/20 hover:bg-rose-500/30 rounded-xl transition-all text-[10px] font-black uppercase cursor-pointer"
                >
                  Retry Connection
                </button>
              </div>
            )
          )}

          {/* Mobile Layout Menu Button */}
          <div className="lg:hidden flex items-center justify-between p-3 bg-white/[0.02] border border-white/5 rounded-2xl select-none">
            <button
              onClick={() => setSidebarOpen(true)}
              className="flex items-center space-x-2 px-3 py-1.5 bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 rounded-xl text-[10px] font-extrabold uppercase cursor-pointer"
            >
              <span>☰</span>
              <span>Menu</span>
            </button>
            <span className="text-[9px] text-stone-500 uppercase font-black tracking-widest">
              CarbonTracker AI
            </span>
          </div>

          {/* ═══════════════════════════════════════════════════════════════
              DASHBOARD TAB
          ═══════════════════════════════════════════════════════════════ */}
          {currentTab === "dashboard" && (
            <motion.div
              variants={containerVariants}
              initial="hidden"
              animate="visible"
              className="space-y-6"
            >
              {/* Greeting row */}
              <motion.div
                variants={itemVariants}
                className="grid grid-cols-1 md:grid-cols-3 gap-4 items-start select-none"
              >
                <div className="md:col-span-2">
                  <h1 className="text-xl sm:text-2xl font-black tracking-tight text-white flex items-center gap-1.5">
                    Good evening, <span className="text-emerald-450">{user?.username || "Guest"}</span> 👋
                  </h1>
                  <p className="text-[11px] font-bold text-stone-500 mt-1">
                    &ldquo;Small choices today, a better planet tomorrow.&rdquo; 🌿
                  </p>
                  <div className="mt-4">
                    <button
                      onClick={() => alert("Grid map telemetry synced. Loading Carbon Density overlays...")}
                      className="px-4 py-2 border border-amber-500/25 bg-amber-500/5 hover:bg-amber-500/10 rounded-xl text-[10px] font-black uppercase text-amber-400 tracking-wider transition-all flex items-center gap-1.5 cursor-pointer active:scale-95 shadow shadow-amber-500/5"
                    >
                      🗺️ View Heatmap
                    </button>
                  </div>
                </div>
                <div className="md:col-span-1">
                  <ErrorBoundary>
                    <SystemStatusWidget />
                  </ErrorBoundary>
                </div>
              </motion.div>

              {/* Quick Actions Bar */}
              <motion.div
                variants={itemVariants}
                className="flex flex-wrap items-center gap-2.5 bg-white/[0.01] border border-white/5 p-3 rounded-2xl select-none"
              >
                <span className="text-[10px] font-black text-stone-500 uppercase tracking-widest mr-1.5 pl-1.5">
                  Quick Actions:
                </span>
                {[
                  { label: "+ Log Activity", tab: "logger", color: "emerald" },
                  { label: "📷 Upload Bill", tab: "logger", color: "purple" },
                  { label: "🔌 Connect Device", tab: "devices", color: "indigo" },
                ].map((action) => (
                  <button
                    key={action.label}
                    onClick={() => handleTabChange(action.tab)}
                    className={`px-3 py-1.5 rounded-xl bg-${action.color}-500/10 hover:bg-${action.color}-500/15 text-${action.color}-400 border border-${action.color}-500/15 text-[10px] font-extrabold uppercase transition-all flex items-center gap-1.5 cursor-pointer active:scale-95`}
                  >
                    {action.label}
                  </button>
                ))}
                <button
                  onClick={() => handleTabChange("logger")}
                  className="px-3 py-1.5 rounded-xl bg-sky-500/10 hover:bg-sky-500/15 text-sky-400 border border-sky-500/15 text-[10px] font-extrabold uppercase transition-all flex items-center gap-1.5 cursor-pointer active:scale-95"
                >
                  🎤 Voice Log
                </button>
                <button
                  onClick={() => window.dispatchEvent(new Event("open-copilot"))}
                  className="px-3 py-1.5 rounded-xl bg-amber-500/10 hover:bg-amber-500/15 text-amber-400 border border-amber-500/15 text-[10px] font-extrabold uppercase transition-all flex items-center gap-1.5 cursor-pointer active:scale-95"
                >
                  🤖 Ask AI
                </button>
              </motion.div>

              {/* KPI Cards — isolated boundary */}
              <motion.div variants={itemVariants}>
                <ErrorBoundary>
                  <DashboardStats summary={summary} xp={xp} level={level} score={score} />
                </ErrorBoundary>
              </motion.div>

              {/* AI Dashboard Intelligence Feed */}
              {summary?.ai_dashboard && (
                <motion.div
                  variants={itemVariants}
                  className="grid grid-cols-1 lg:grid-cols-3 gap-5 select-none"
                >
                  {/* Left part: Personalized intelligence summary banner */}
                  <div className="lg:col-span-2 glass-card rounded-3xl p-5 border border-emerald-500/10 bg-gradient-to-br from-emerald-950/5 via-[#080d0a]/40 to-[#080d0a]/10 relative overflow-hidden flex flex-col justify-between min-h-[140px]">
                    <div className="absolute top-0 right-0 w-32 h-32 bg-emerald-500/5 blur-[50px] pointer-events-none rounded-full" />
                    <div>
                      <div className="flex items-center gap-2 mb-2">
                        <span className="w-5 h-5 rounded-lg bg-emerald-500/15 flex items-center justify-center border border-emerald-500/35">
                          <Sparkles className="w-3 h-3 text-emerald-450 animate-pulse" />
                        </span>
                        <h3 className="text-xs font-black uppercase tracking-widest text-emerald-400">
                          AI Sustainability Recommendations
                        </h3>
                      </div>
                      <p className="text-xs font-bold text-stone-300 leading-relaxed max-w-2xl">
                        {summary.ai_dashboard.personalized_sustainability_summary}
                      </p>
                    </div>
                    <div className="flex flex-wrap gap-x-6 gap-y-2 mt-4 text-[9px] font-black text-stone-500 uppercase tracking-widest border-t border-white/5 pt-3">
                      <div>
                        Top Source: <span className="text-emerald-450">{summary.ai_dashboard.top_emission_source}</span>
                      </div>
                      <div>
                        Weekly Trend: <span className="text-emerald-450">{summary.ai_dashboard.weekly_trend}</span>
                      </div>
                      <div>
                        Behavior Suggestion: <span className="text-emerald-450">{summary.ai_dashboard.behavior_change}</span>
                      </div>
                      <div>
                        Predicted Monthly: <span className="text-emerald-450">{summary.ai_dashboard.predicted_monthly_emissions} kg</span>
                      </div>
                    </div>
                  </div>

                  {/* Right part: Live Insight Feed */}
                  <div className="lg:col-span-1 glass-card rounded-3xl p-5 border border-white/5 bg-white/[0.01] flex flex-col justify-between min-h-[140px]">
                    <div>
                      <h3 className="text-xs font-black uppercase tracking-widest text-stone-400 mb-3 flex items-center gap-1.5">
                        <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-ping" />
                        Live Eco Feed
                      </h3>
                      <div className="space-y-2.5 max-h-[100px] overflow-y-auto pr-1">
                        {summary.insight_feed?.map((item, idx) => (
                          <div key={idx} className="text-[10px] font-bold text-stone-300 flex items-start gap-2 leading-tight">
                            <span className="text-[8px] uppercase px-1.5 py-0.5 rounded bg-white/5 text-stone-550 mt-0.5 flex-shrink-0 font-extrabold">
                              {item.type}
                            </span>
                            <span className="line-clamp-2">{item.text}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </motion.div>
              )}

              {/* Center Row: Earth + Activity Input + Weekly Chart */}
              <motion.div variants={itemVariants} className="grid grid-cols-1 xl:grid-cols-3 gap-5">
                <div className="xl:col-span-1 space-y-4">
                  <ErrorBoundary>
                    <EarthPanel score={score ?? summary?.current_score ?? 93} />
                  </ErrorBoundary>
                </div>
                <div className="xl:col-span-2 space-y-5">
                  <ErrorBoundary>
                    <ActivityInput onActivityLogged={loadDashboardData} region={region} />
                  </ErrorBoundary>
                  <ErrorBoundary>
                    <WeeklyFootprintChart summary={summary} />
                  </ErrorBoundary>
                </div>
              </motion.div>

              {/* Bottom Row: Quests + Donut + AI Insights + Habit Insights — each isolated */}
              <motion.div
                variants={itemVariants}
                className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-5"
              >
                <ErrorBoundary>
                  <DailyQuests />
                </ErrorBoundary>
                <ErrorBoundary>
                  <CategoryDonutChart summary={summary} />
                </ErrorBoundary>
                <ErrorBoundary>
                  <AIRecommendations insights={insights} loading={insightsLoading} />
                </ErrorBoundary>
                <ErrorBoundary>
                  <HabitInsights />
                </ErrorBoundary>
              </motion.div>

              {/* Streak Footer */}
              <motion.div variants={itemVariants}>
                <ErrorBoundary>
                  <StreakFooter streak={streak} />
                </ErrorBoundary>
              </motion.div>
            </motion.div>
          )}

          {/* ═══════════════════════════════════════════════════════════════
              LOGGER TAB
          ═══════════════════════════════════════════════════════════════ */}
          {currentTab === "logger" && (
            <motion.div variants={itemVariants} className="max-w-3xl mx-auto space-y-6">
              <h2 className="text-lg font-black uppercase tracking-wider text-white">
                Activity Logging Studio
              </h2>
              <ErrorBoundary>
                <ActivityInput onActivityLogged={loadDashboardData} region={region} />
              </ErrorBoundary>
              <ErrorBoundary>
                <div className="glass-card rounded-3xl p-6">
                  <h3 className="text-xs font-black uppercase tracking-widest text-stone-400 mb-3">
                    Multimodal Scans (OCR Scan Receipt)
                  </h3>
                  <MultimodalUpload onUploadSuccess={loadDashboardData} region={region} />
                </div>
              </ErrorBoundary>
            </motion.div>
          )}

          {/* ═══════════════════════════════════════════════════════════════
              ANALYTICS TAB
          ═══════════════════════════════════════════════════════════════ */}
          {currentTab === "analytics" && (
            <motion.div variants={itemVariants} className="space-y-6">
              <h2 className="text-lg font-black uppercase tracking-wider text-white">
                Footprint Analytics Dashboard
              </h2>
              <ErrorBoundary>
                <CarbonCharts summary={summary} />
              </ErrorBoundary>
            </motion.div>
          )}

          {/* ═══════════════════════════════════════════════════════════════
              DEVICES TAB
          ═══════════════════════════════════════════════════════════════ */}
          {currentTab === "devices" && (
            <motion.div variants={itemVariants}>
              <ErrorBoundary>
                <IoTDashboard />
              </ErrorBoundary>
            </motion.div>
          )}

          {/* ═══════════════════════════════════════════════════════════════
              QUESTS TAB
          ═══════════════════════════════════════════════════════════════ */}
          {currentTab === "quests" && (
            <motion.div variants={itemVariants} className="max-w-4xl mx-auto space-y-6">
              <h2 className="text-lg font-black uppercase tracking-wider text-white">
                Daily Quests & Achievements
              </h2>
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-1">
                  <ErrorBoundary>
                    <DailyQuests />
                  </ErrorBoundary>
                </div>
                <div className="lg:col-span-2">
                  <ErrorBoundary>
                    <Achievements unlockedList={achievements} loading={loading} />
                  </ErrorBoundary>
                </div>
              </div>
            </motion.div>
          )}

          {/* ═══════════════════════════════════════════════════════════════
              HISTORY TAB
          ═══════════════════════════════════════════════════════════════ */}
          {currentTab === "history" && (
            <motion.div variants={itemVariants} className="max-w-4xl mx-auto space-y-6">
              <h2 className="text-lg font-black uppercase tracking-wider text-white">
                Emission Log Ledger
              </h2>
              <ErrorBoundary>
                <ActivityHistory activities={activities} loading={loading} />
              </ErrorBoundary>
            </motion.div>
          )}

          {/* ═══════════════════════════════════════════════════════════════
              COACH TAB
          ═══════════════════════════════════════════════════════════════ */}
          {currentTab === "coach" && (
            <motion.div variants={itemVariants} className="max-w-4xl mx-auto space-y-6">
              <ErrorBoundary>
                <CoachDashboard />
              </ErrorBoundary>
            </motion.div>
          )}

          {/* ═══════════════════════════════════════════════════════════════
              MARKETPLACE TAB
          ═══════════════════════════════════════════════════════════════ */}
          {currentTab === "marketplace" && (
            <motion.div variants={itemVariants} className="max-w-4xl mx-auto space-y-6">
              <ErrorBoundary>
                <Marketplace />
              </ErrorBoundary>
            </motion.div>
          )}

          {/* ═══════════════════════════════════════════════════════════════
              FALLBACK (unknown tab)
          ═══════════════════════════════════════════════════════════════ */}
          {!["dashboard", "logger", "analytics", "coach", "devices", "quests", "marketplace", "history"].includes(
            currentTab
          ) && (
            <motion.div
              variants={itemVariants}
              className="flex flex-col items-center justify-center min-h-[400px] border border-dashed border-white/5 rounded-3xl bg-white/[0.01] select-none text-center p-6"
            >
              <span className="text-xs text-stone-500 font-extrabold uppercase tracking-widest animate-pulse">
                {currentTab} view coming soon
              </span>
              <button
                onClick={() => handleTabChange("dashboard")}
                className="mt-5 px-4 py-2 bg-emerald-500/10 text-emerald-400 hover:text-emerald-300 border border-emerald-500/20 rounded-xl text-[10px] font-black uppercase transition-all active:scale-95 cursor-pointer"
              >
                Return to Cockpit
              </button>
            </motion.div>
          )}
        </main>
      </div>

      {/* Floating AI Copilot Toggle & Lazy-loaded Panel */}
      {!isCopilotOpen && (
        <div className="fixed bottom-6 right-6 z-40">
          <motion.button
            whileHover={{ scale: 1.06 }}
            whileTap={{ scale: 0.94 }}
            onClick={() => setIsCopilotOpen(true)}
            className="relative flex items-center justify-center w-14 h-14 rounded-full bg-forest-600 hover:bg-forest-500 text-white shadow-xl shadow-forest-600/35 cursor-pointer overflow-hidden border border-forest-500/30 glow-btn"
          >
            <MessageSquare className="w-6 h-6" />
            {metrics && metrics.total_user_corrections > 0 && (
              <span className="absolute top-1 right-1 bg-amber-500 text-black text-[10px] font-black w-4 h-4 rounded-full flex items-center justify-center">
                {metrics.total_user_corrections}
              </span>
            )}
          </motion.button>
        </div>
      )}

      <ErrorBoundary>
        <AnimatePresence>
          {isCopilotOpen && (
            <CopilotChat onClose={() => setIsCopilotOpen(false)} />
          )}
        </AnimatePresence>
      </ErrorBoundary>

      {/* Non-blocking toast error notification */}
      <ToastError />

      {/* Loading overlay spinner — only on initial cold load */}
      {loading && !summary && (
        <div className="fixed inset-0 bg-[#080d0a]/80 backdrop-blur-sm z-50 flex items-center justify-center select-none">
          <div className="flex flex-col items-center space-y-4">
            <div className="w-10 h-10 rounded-2xl bg-emerald-600 flex items-center justify-center">
              <span className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
            </div>
            <p className="text-[10px] font-black text-emerald-400 animate-pulse uppercase tracking-widest">
              Connecting to CarbonTracker Engine...
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// ROOT EXPORT — wraps in provider with top-level error boundary
// ─────────────────────────────────────────────────────────────────────────────

export default function Home() {
  return (
    <ErrorBoundary>
      <AIStoreProvider>
        <HomeContent />
      </AIStoreProvider>
    </ErrorBoundary>
  );
}
