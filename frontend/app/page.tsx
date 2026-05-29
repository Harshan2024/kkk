"use client";

import React, { useState } from "react";
import Sidebar from "../components/Sidebar";
import Topbar from "../components/Topbar";
import EarthPanel from "../components/EarthPanel";
import WeeklyFootprintChart from "../components/WeeklyFootprintChart";
import CategoryDonutChart from "../components/CategoryDonutChart";
import DailyQuests from "../components/DailyQuests";
import StreakFooter from "../components/StreakFooter";

import ActivityInput from "../components/ActivityInput";
import DashboardStats from "../components/DashboardStats";
import CarbonCharts from "../components/CarbonCharts";
import AIRecommendations from "../components/AIRecommendations";
import Achievements from "../components/Achievements";
import ActivityHistory from "../components/ActivityHistory";
import CopilotChat from "../components/CopilotChat";
import MultimodalUpload from "../components/MultimodalUpload";
import { AIStoreProvider, useAIStore } from "../stores/aiStore";
import ErrorBoundary from "../components/ErrorBoundary";
import { motion } from "framer-motion";

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.05,
      delayChildren: 0.02
    }
  }
};

const itemVariants = {
  hidden: { opacity: 0, y: 10 },
  visible: {
    opacity: 1,
    y: 0,
    transition: {
      type: "spring",
      stiffness: 100,
      damping: 15
    }
  }
};

function HomeContent() {
  const {
    summary,
    insights,
    achievements,
    activities,
    loading,
    error,
    region,
    setRegion,
    loadDashboardData
  } = useAIStore();

  const [currentTab, setCurrentTab] = useState("dashboard");
  const [sidebarOpen, setSidebarOpen] = useState(false);

  // Dynamic calculations for gamification parameters
  const achievementsCount = summary?.achievements_count || achievements?.length || 0;
  const xp = 150 + (activities?.length || 0) * 20 + achievementsCount * 100;
  const level = Math.floor(xp / 200) + 1;
  const streak = summary?.trends ? Math.max(1, summary.trends.filter(t => t.emissions > 0).length) : 1;

  return (
    <div className="min-h-screen bg-[#080d0a] text-stone-100 font-sans relative overflow-x-hidden transition-colors duration-300">
      {/* Background Dot Matrix Accent */}
      <div className="absolute inset-0 dot-matrix pointer-events-none z-0"></div>

      {/* Atmospheric glowing green orbs */}
      <div className="absolute top-[-10%] left-[-5%] w-[45%] aspect-square rounded-full bg-emerald-600/5 blur-[120px] pointer-events-none z-0"></div>
      <div className="absolute bottom-[-10%] right-[-5%] w-[45%] aspect-square rounded-full bg-emerald-700/5 blur-[120px] pointer-events-none z-0"></div>

      {/* Sidebar fixed menu */}
      <Sidebar 
        currentTab={currentTab}
        onTabChange={setCurrentTab}
        username="Harshan R"
        xp={xp}
        level={level}
        streak={streak}
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />

      {/* Main viewport */}
      <div className="lg:pl-64 flex flex-col min-h-screen relative z-10">
        {/* Floating Header topbar */}
        <Topbar onRefresh={loadDashboardData} region={region} onRegionChange={setRegion} />

        <main className="flex-1 px-4 sm:px-6 lg:px-8 py-6 space-y-6">
          <ErrorBoundary>
            {/* Error Alert banner */}
            {error && (
              <div className="p-4.5 rounded-2xl border border-rose-500/30 bg-rose-500/10 text-rose-450 text-xs font-bold flex items-center justify-between shadow-lg shadow-rose-500/5 animate-in fade-in">
                <span>{error}</span>
                <button
                  onClick={loadDashboardData}
                  className="px-3 py-1.5 bg-rose-500/20 hover:bg-rose-500/30 rounded-xl transition-all text-[10px] font-black uppercase"
                >
                  Retry Connection
                </button>
              </div>
            )}

            {/* Mobile Layout Menu Button */}
            <div className="lg:hidden flex items-center justify-between p-3 bg-white/[0.02] border border-white/5 rounded-2xl mb-4.5 select-none">
              <button 
                onClick={() => setSidebarOpen(true)}
                className="flex items-center space-x-2 px-3 py-1.5 bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 rounded-xl text-[10px] font-extrabold uppercase"
              >
                <span>☰</span>
                <span>Menu</span>
              </button>
              <span className="text-[9px] text-stone-500 uppercase font-black tracking-widest">CarbonTracker AI</span>
            </div>

            {/* VIEWS CONTROLLER */}
            {currentTab === "dashboard" ? (
              <motion.div 
                variants={containerVariants}
                initial="hidden"
                animate="visible"
                className="space-y-6"
              >
                {/* Top greeting area */}
                <motion.div variants={itemVariants} className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 select-none">
                  <div>
                    <h1 className="text-xl sm:text-2xl font-black tracking-tight text-white flex items-center gap-1.5">
                      Good evening, <span className="text-emerald-400">Harshan R</span> 👋
                    </h1>
                    <p className="text-[11px] font-bold text-stone-500 mt-1">
                      "Small choices today, a better planet tomorrow." 🌿
                    </p>
                  </div>
                  <button 
                    onClick={() => alert("Grid map telemetry synced. Loading Carbon Density overlays...")}
                    className="px-4 py-2 border border-amber-500/25 bg-amber-500/5 hover:bg-amber-500/10 rounded-xl text-[10px] font-black uppercase text-amber-400 tracking-wider transition-all flex items-center gap-1.5 cursor-pointer active:scale-95 shadow shadow-amber-500/5"
                  >
                    🗺️ View Heatmap
                  </button>
                </motion.div>

                {/* KPI Cards Row */}
                <motion.div variants={itemVariants}>
                  <DashboardStats summary={summary} xp={xp} level={level} />
                </motion.div>

                {/* Center Row: Earth Visualizer & Conversational Inputs */}
                <motion.div variants={itemVariants} className="grid grid-cols-1 xl:grid-cols-3 gap-5">
                  <div className="xl:col-span-1">
                    <EarthPanel score={summary?.current_score || 93} />
                  </div>
                  <div className="xl:col-span-2 space-y-5">
                    <ActivityInput onActivityLogged={loadDashboardData} region={region} />
                    <WeeklyFootprintChart summary={summary} />
                  </div>
                </motion.div>

                {/* Bottom Row: Daily Quests, Donut Breakdown, AI Insights */}
                <motion.div variants={itemVariants} className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
                  <DailyQuests />
                  <CategoryDonutChart summary={summary} />
                  <AIRecommendations insights={insights} loading={loading} />
                </motion.div>

                {/* Streak timeline footer */}
                <motion.div variants={itemVariants}>
                  <StreakFooter streak={streak} />
                </motion.div>
              </motion.div>
            ) : currentTab === "logger" ? (
              <motion.div variants={itemVariants} className="max-w-3xl mx-auto space-y-6">
                <h2 className="text-lg font-black uppercase tracking-wider text-white">Activity Logging Studio</h2>
                <ActivityInput onActivityLogged={loadDashboardData} region={region} />
                <div className="glass-card rounded-3xl p-6">
                  <h3 className="text-xs font-black uppercase tracking-widest text-stone-400 mb-3">Multimodal Scans (OCR Scan Receipt)</h3>
                  <MultimodalUpload onUploadSuccess={loadDashboardData} region={region} />
                </div>
              </motion.div>
            ) : currentTab === "analytics" ? (
              <motion.div variants={itemVariants} className="space-y-6">
                <h2 className="text-lg font-black uppercase tracking-wider text-white">Footprint Analytics Dashboard</h2>
                <CarbonCharts summary={summary} />
              </motion.div>
            ) : currentTab === "quests" ? (
              <motion.div variants={itemVariants} className="max-w-4xl mx-auto space-y-6">
                <h2 className="text-lg font-black uppercase tracking-wider text-white">Daily Quests & Achievements</h2>
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                  <div className="lg:col-span-1">
                    <DailyQuests />
                  </div>
                  <div className="lg:col-span-2">
                    <Achievements unlockedList={achievements} loading={loading} />
                  </div>
                </div>
              </motion.div>
            ) : currentTab === "history" ? (
              <motion.div variants={itemVariants} className="max-w-4xl mx-auto space-y-6">
                <h2 className="text-lg font-black uppercase tracking-wider text-white">Emission Log Ledger</h2>
                <ActivityHistory activities={activities} loading={loading} />
              </motion.div>
            ) : (
              <motion.div variants={itemVariants} className="flex flex-col items-center justify-center min-h-[400px] border border-dashed border-white/5 rounded-3xl bg-white/[0.01] select-none text-center p-6">
                <span className="text-xs text-stone-500 font-extrabold uppercase tracking-widest animate-pulse">
                  {currentTab} view is synchronized to cloud
                </span>
                <p className="text-[10px] text-stone-600 mt-2 max-w-[280px]">
                  Real-time IoT database connectors will populate this screen once active.
                </p>
                <button 
                  onClick={() => setCurrentTab("dashboard")} 
                  className="mt-5 px-4 py-2 bg-emerald-500/10 text-emerald-400 hover:text-emerald-350 border border-emerald-500/20 rounded-xl text-[10px] font-black uppercase transition-all active:scale-95 cursor-pointer"
                >
                  Return to Cockpit
                </button>
              </motion.div>
            )}
          </ErrorBoundary>
        </main>
      </div>

      {/* Slide-out AI Copilot Panel */}
      <CopilotChat />

      {/* Loading overlay spinner */}
      {loading && !summary && (
        <div className="fixed inset-0 bg-[#080d0a]/80 backdrop-blur-sm z-50 flex items-center justify-center select-none">
          <div className="flex flex-col items-center space-y-4">
            <div className="w-10 h-10 rounded-2xl bg-emerald-600 flex items-center justify-center animate-spin">
              <span className="w-5 h-5 border-2 border-white border-t-transparent rounded-full"></span>
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

export default function Home() {
  return (
    <AIStoreProvider>
      <HomeContent />
    </AIStoreProvider>
  );
}
