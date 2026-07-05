"use client";

import React, { useState, useMemo, useCallback, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Sparkles, MessageSquare, Compass, ShieldCheck, Sun, CloudRain } from "lucide-react";
import { useRouter } from "next/navigation";

import Sidebar from "../components/Sidebar";
import Topbar from "../components/Topbar";
import EarthPanel from "../components/EarthPanel";
import dynamic from "next/dynamic";

const WeeklyFootprintChart = dynamic(() => import("../components/WeeklyFootprintChart"), {
  loading: () => <div className="glass-premium rounded-3xl h-[280px] animate-pulse" />,
  ssr: false
});
const CategoryDonutChart = dynamic(() => import("../components/CategoryDonutChart"), {
  loading: () => <div className="glass-premium rounded-3xl h-[360px] animate-pulse" />,
  ssr: false
});
const DailyQuests = dynamic(() => import("../components/DailyQuests"), {
  loading: () => <div className="glass-premium rounded-3xl h-[320px] animate-pulse" />,
  ssr: false
});
const StreakFooter = dynamic(() => import("../components/StreakFooter"), { ssr: false });
const IoTDashboard = dynamic(() => import("../components/IoTDashboard"), {
  loading: () => <div className="glass-premium rounded-3xl h-[240px] animate-pulse" />,
  ssr: false
});
import ActivityInput from "../components/ActivityInput";
import DashboardStats from "../components/DashboardStats";
const CarbonCharts = dynamic(() => import("../components/CarbonCharts"), {
  loading: () => <div className="glass-premium rounded-3xl h-[420px] animate-pulse" />,
  ssr: false
});
const AIRecommendations = dynamic(() => import("../components/AIRecommendations"), {
  loading: () => <div className="glass-premium rounded-3xl h-[300px] animate-pulse" />,
  ssr: false
});
const Achievements = dynamic(() => import("../components/Achievements"), {
  loading: () => <div className="glass-premium rounded-3xl h-[260px] animate-pulse" />,
  ssr: false
});

const ActivityHistory = dynamic(() => import("../components/ActivityHistory"), { ssr: false });
const CoachDashboard = dynamic(() => import("../components/CoachDashboard"), { ssr: false });
const Marketplace = dynamic(() => import("../components/Marketplace"), { ssr: false });
const Settings = dynamic(() => import("../components/Settings"), { ssr: false });
import api, { GamificationProfile } from "../services/api";

const CopilotChat = dynamic(() => import("../components/CopilotChat"), {
  loading: () => null,
  ssr: false,
});
const HabitInsights = dynamic(() => import("../components/HabitInsights").then(mod => mod.HabitInsights), {
  loading: () => <div className="glass-premium rounded-3xl h-[360px] animate-pulse" />,
  ssr: false,
});
import MultimodalUpload from "../components/MultimodalUpload";
import SystemStatusWidget from "../components/SystemStatusWidget";
import ErrorBoundary from "../components/ErrorBoundary";
import { useAIStore } from "../stores/aiStore";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";
import PremiumCursor from "../components/PremiumCursor";
import { ProfileSkeleton, KpiSkeleton, CardSkeleton, ListSkeleton } from "../components/ui/Skeleton";

// ─── Animation Configs ────────────────────────────────────────────────────────

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.05, delayChildren: 0.02 },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 12 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { type: "spring", stiffness: 100, damping: 16 },
  },
};

// ─── Toast Error Component ───────────────────────────────────────────────────

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
          <div className="glass-premium rounded-2xl p-4 border border-amber-500/30 bg-amber-500/10 shadow-xl flex items-start gap-3">
            <div className="flex-1">
              <p className="text-[11px] font-bold text-amber-300 leading-relaxed">{toastError}</p>
            </div>
            <button
              onClick={clearToastError}
              className="text-theme-muted hover:text-theme-primary transition-colors cursor-pointer mt-0.5"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

// ─── Time aware Greeting Helper ──────────────────────────────────────────────

function getTimeGreeting(username: string) {
  if (typeof window === "undefined") return `Hello, ${username}`;
  const hours = new Date().getHours();
  let greeting = "Good morning";
  if (hours >= 12 && hours < 17) greeting = "Good afternoon";
  else if (hours >= 17) greeting = "Good evening";
  return `${greeting}, ${username}`;
}


// ─── Dashboard Skeleton ──────────────────────────────────────────────────────

function DashboardSkeleton() {
  return (
    <div className="space-y-6 animate-pulse select-none">
      {/* Hero Greeting Skeleton */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5 items-stretch">
        <div className="lg:col-span-2 glass-premium rounded-3xl p-6 h-[170px] space-y-4">
          <div className="h-4 bg-white/5 rounded w-1/4" />
          <div className="h-8 bg-white/5 rounded w-1/2" />
          <div className="h-3 bg-white/5 rounded w-3/4" />
        </div>
        <div className="glass-premium rounded-3xl p-6 h-[170px] flex flex-col justify-between">
          <div className="h-4 bg-white/5 rounded w-1/3" />
          <div className="h-10 bg-white/5 rounded w-full" />
        </div>
      </div>

      {/* KPI Skeletons */}
      <KpiSkeleton count={4} />

      {/* Main Grid Skeletons */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        <div className="xl:col-span-2 space-y-6">
          <CardSkeleton lines={4} className="h-[380px]" />
          <CardSkeleton lines={3} className="h-[250px]" />
        </div>
        <div className="xl:col-span-1 space-y-6">
          <div className="glass-premium rounded-3xl p-5 h-[320px] space-y-4">
            <div className="h-3.5 bg-white/5 rounded w-1/3" />
            <ListSkeleton rows={3} />
          </div>
          <div className="glass-premium rounded-3xl p-5 h-[310px] space-y-4">
            <div className="h-3.5 bg-white/5 rounded w-1/3" />
            <ListSkeleton rows={3} />
          </div>
        </div>
      </div>
    </div>
  );
}


// ─── Error Banner Component ──────────────────────────────────────────────────

interface ErrorBannerProps {
  error: string;
  loadDashboardData: () => void;
  router: any;
}

const ErrorBanner = React.memo(function ErrorBanner({
  error,
  loadDashboardData,
  router,
}: ErrorBannerProps) {
  const isAuth = error.toLowerCase().includes("session expired") || error.toLowerCase().includes("login");
  const isNetwork = error.toLowerCase().includes("unable to connect") || error.toLowerCase().includes("timed out");
  const isReconnecting = error === "Reconnecting to database...";
  const isServer = error.toLowerCase().includes("server error") || error.toLowerCase().includes("http ");

  const bannerClass = isReconnecting
    ? "border-amber-500/30 bg-amber-500/10 text-amber-400"
    : isAuth
      ? "border-sky-500/30 bg-sky-500/10 text-sky-400"
      : isNetwork
        ? "border-rose-500/30 bg-rose-500/10 text-rose-400"
        : "border-amber-500/30 bg-amber-500/10 text-amber-400";

  return (
    <div className={`p-4 rounded-2xl border flex items-center justify-between shadow-lg transition-all duration-300 ${bannerClass}`}>
      <div className="flex items-center gap-3">
        {isReconnecting && (
          <span className="w-3.5 h-3.5 border-2 border-amber-400 border-t-transparent rounded-full animate-spin flex-shrink-0" />
        )}
        <span className="text-xs font-bold">{error}</span>
      </div>
      <div className="flex items-center gap-2">
        {isAuth && (
          <Button variant="primary" size="xs" onClick={() => router.push("/login")}>
            Login
          </Button>
        )}
        {isNetwork && (
          <Button variant="danger" size="xs" onClick={loadDashboardData}>
            Retry Connection
          </Button>
        )}
        {isServer && !isReconnecting && (
          <Button variant="danger" size="xs" onClick={loadDashboardData}>
            Retry
          </Button>
        )}
      </div>
    </div>
  );
});

// ─── Home Content Component ───────────────────────────────────────────────────

const HomeContent = React.memo(function HomeContent() {
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
    smartDevicesEnabled,
    startupPhase,
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
    } catch (err) {
      console.error("Failed to fetch gamification profile", err);
    }
  }, []);

  useEffect(() => {
    if (isAuthenticated) {
      fetchGamificationProfile();
    }
  }, [fetchGamificationProfile, activities?.length, isAuthenticated]);

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

  useEffect(() => {
    if (typeof window !== "undefined") {
      const params = new URLSearchParams(window.location.search);
      const tabParam = params.get("tab");
      if (tabParam) {
        setCurrentTab(tabParam);
      }
    }
  }, []);

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

  const handleTabChange = useCallback((tab: string) => {
    if (tab === "profile") {
      router.push("/profile");
    } else {
      setCurrentTab(tab);
    }
  }, [router]);

  const greeting = useMemo(() => getTimeGreeting(user?.username || "Eco Warrior"), [user]);

  const loadingMessage = useMemo(() => {
    switch (startupPhase) {
      case "init":
        return "Checking Session...";
      case "validating":
        return "Connecting Backend...";
      case "loading":
        return "Loading Dashboard...";
      default:
        return "Loading User...";
    }
  }, [startupPhase]);

  // Loading Screen using Premium Styles
  if (loading && !isAuthenticated) {
    return (
      <div className="fixed inset-0 bg-theme-base z-50 flex items-center justify-center select-none">
        <div className="flex flex-col items-center space-y-4">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-emerald-400 to-emerald-700 flex items-center justify-center shadow-lg animate-spin-slow">
            <span className="text-white font-black text-sm">CT</span>
          </div>
          <p className="text-[10px] font-black text-theme-brand animate-pulse uppercase tracking-widest">
            {loadingMessage}
          </p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  return (
    <div className="min-h-screen bg-theme-base text-theme-primary font-sans relative overflow-x-hidden transition-colors duration-300">
      {/* Background Dot Matrix Accent */}
      <div className="absolute inset-0 dot-matrix pointer-events-none z-0" />

      {/* Atmospheric glowing brand orbs */}
      <div className="absolute top-[-10%] left-[-5%] w-[45%] aspect-square rounded-full bg-theme-brand-muted opacity-25 blur-[130px] pointer-events-none z-0" />
      <div className="absolute bottom-[-10%] right-[-5%] w-[45%] aspect-square rounded-full bg-theme-brand-muted opacity-20 blur-[130px] pointer-events-none z-0" />

      {/* Premium Cursor Integration */}
      <PremiumCursor />

      {/* Sidebar Section */}
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
        <ErrorBoundary>
          <Topbar onRefresh={loadDashboardData} region={region} onRegionChange={setRegion} />
        </ErrorBoundary>

        <main className="flex-1 px-4 sm:px-6 lg:px-8 py-6 space-y-6">
          {/* Error Banner — context-aware per error type */}
          {error && (
            <ErrorBanner
              error={error}
              loadDashboardData={loadDashboardData}
              router={router}
            />
          )}


          {/* Mobile Drawer Trigger Bar */}
          <div className="lg:hidden flex items-center justify-between p-3 bg-white/[0.02] border border-white/5 rounded-2xl select-none">
            <Button
              variant="secondary"
              size="sm"
              icon={<span>☰</span>}
              onClick={() => setSidebarOpen(true)}
            >
              Menu
            </Button>
            <span className="text-[9px] text-theme-muted uppercase font-black tracking-widest">
              CarbonTracker AI
            </span>
          </div>

          {loading && !summary ? (
            <DashboardSkeleton />
          ) : (
            <>
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
              {/* Greeting Hero Grid */}
              <motion.div
                variants={itemVariants}
                className="grid grid-cols-1 lg:grid-cols-3 gap-5 items-stretch select-none"
              >
                {/* Greeting Card */}
                <Card className="lg:col-span-2 relative overflow-hidden flex flex-col justify-between p-6 h-full min-h-[170px]" gradientBorder>
                  <div className="absolute inset-0 pointer-events-none bg-gradient-to-r from-transparent via-white/[0.01] to-emerald-500/[0.03]" />
                  <div className="space-y-2 relative z-10">
                    <div className="flex items-center gap-2">
                      <Badge variant="success" size="xs" dot>Live Session</Badge>
                      <span className="text-[10px] text-theme-muted font-bold flex items-center gap-1">
                        <Compass className="w-3 h-3" /> Paris Accord Target: 2.0 tonnes/yr
                      </span>
                    </div>
                    <h1 className="text-xl sm:text-3xl font-black tracking-tight text-theme-heading leading-tight font-display">
                      {greeting}
                    </h1>
                    <p className="text-xs text-theme-secondary font-medium leading-relaxed max-w-xl">
                      Your current daily activities are driving a high-impact index change. Log activities below or upload scans to recalibrate your footprint.
                    </p>
                  </div>
                  
                  <div className="mt-4 flex items-center gap-3 relative z-10 pt-3 border-t border-white/5">
                    <Button
                      variant="primary"
                      size="sm"
                      onClick={() => handleTabChange("logger")}
                      icon={<Sparkles className="w-3.5 h-3.5" />}
                    >
                      Analyze Daily Footprint
                    </Button>
                    <span className="text-[9px] text-theme-muted font-bold uppercase tracking-wider hidden sm:inline-block">
                      Telemetry Synced: 100% Accurate
                    </span>
                  </div>
                </Card>

                {/* System Status Widget */}
                <div className="lg:col-span-1 h-full">
                  <ErrorBoundary>
                    <SystemStatusWidget />
                  </ErrorBoundary>
                </div>
              </motion.div>

              {/* Quick Actions Panel */}
              <motion.div
                variants={itemVariants}
                className="flex flex-wrap items-center gap-2.5 bg-white/[0.01] border border-white/5 p-3 rounded-2xl select-none"
              >
                <span className="text-[10px] font-black text-theme-muted uppercase tracking-widest mr-1.5 pl-1.5">
                  Quick Panel:
                </span>
                <Button variant="outline" size="sm" onClick={() => handleTabChange("logger")}>
                  + Log Activity
                </Button>
                <Button variant="secondary" size="sm" onClick={() => handleTabChange("logger")}>
                  📷 Scan Receipt
                </Button>
                {smartDevicesEnabled && (
                  <Button variant="secondary" size="sm" onClick={() => handleTabChange("devices")}>
                    🔌 Connect IoT
                  </Button>
                )}
                <Button variant="ghost" size="sm" onClick={() => window.dispatchEvent(new Event("open-copilot"))}>
                  🤖 Chat with Coach
                </Button>
              </motion.div>

              {/* KPI Cards */}
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
                  <Card className="lg:col-span-2 relative overflow-hidden flex flex-col justify-between min-h-[140px] border-emerald-500/10 bg-gradient-to-br from-emerald-950/5 via-theme-surface to-theme-base">
                    <div className="absolute top-0 right-0 w-32 h-32 bg-emerald-500/5 blur-[55px] pointer-events-none rounded-full" />
                    <div>
                      <div className="flex items-center gap-2 mb-2.5">
                        <span className="w-5 h-5 rounded-lg bg-emerald-500/15 flex items-center justify-center border border-emerald-500/35">
                          <Sparkles className="w-3 h-3 text-theme-brand animate-pulse" />
                        </span>
                        <h3 className="text-[10px] font-black uppercase tracking-wider text-theme-brand">
                          AI Recommendations
                        </h3>
                      </div>
                      <p className="text-xs font-semibold text-theme-secondary leading-relaxed max-w-2xl">
                        {summary.ai_dashboard.personalized_sustainability_summary}
                      </p>
                    </div>
                    <div className="flex flex-wrap gap-x-6 gap-y-2 mt-4 text-[9px] font-black text-theme-muted uppercase tracking-wider border-t border-white/5 pt-3">
                      <div>
                        Top Source: <span className="text-theme-brand">{summary.ai_dashboard.top_emission_source}</span>
                      </div>
                      <div>
                        Weekly Trend: <span className="text-theme-brand">{summary.ai_dashboard.weekly_trend}</span>
                      </div>
                      <div>
                        Suggestion: <span className="text-theme-brand">{summary.ai_dashboard.behavior_change}</span>
                      </div>
                      <div>
                        Predicted Monthly: <span className="text-theme-brand">{summary.ai_dashboard.predicted_monthly_emissions} kg</span>
                      </div>
                    </div>
                  </Card>

                  {/* Right part: Live Insight Feed */}
                  <Card className="lg:col-span-1 flex flex-col justify-between min-h-[140px]">
                    <div>
                      <h3 className="text-[10px] font-black uppercase tracking-wider text-theme-secondary mb-3.5 flex items-center gap-1.5">
                        <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-ping" />
                        Live Eco Feed
                      </h3>
                      <div className="space-y-2.5 max-h-[105px] overflow-y-auto pr-1">
                        {summary.insight_feed?.map((item, idx) => (
                          <div key={idx} className="text-[10px] font-bold text-theme-secondary flex items-start gap-2 leading-tight">
                            <span className="text-[8px] uppercase px-1.5 py-0.5 rounded bg-white/5 text-theme-muted mt-0.5 flex-shrink-0 font-extrabold">
                              {item.type}
                            </span>
                            <span className="line-clamp-2">{item.text}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </Card>
                </motion.div>
              )}

              {/* Center Row: Earth + Activity Input + Weekly Chart */}
              <motion.div variants={itemVariants} className="grid grid-cols-1 xl:grid-cols-3 gap-5">
                <div className="xl:col-span-1 space-y-4">
                  <ErrorBoundary>
                    <EarthPanel score={score ?? summary?.current_score ?? 93} />
                  </ErrorBoundary>
                </div>
                <div className="xl:col-span-2 space-y-5 min-w-0">
                  <ErrorBoundary>
                    <ActivityInput onActivityLogged={loadDashboardData} region={region} />
                  </ErrorBoundary>
                  <ErrorBoundary>
                    <WeeklyFootprintChart summary={summary} />
                  </ErrorBoundary>
                </div>
              </motion.div>

              {/* Bottom Row: Quests + Donut + AI Insights + Habit Insights */}
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
              <div className="flex items-center justify-between border-b pb-3 border-white/5">
                <h2 className="text-md font-black uppercase tracking-wider text-theme-heading">
                  Activity Logging Studio
                </h2>
                <Badge variant="sky" size="sm">OCR Scanner Ready</Badge>
              </div>
              <ErrorBoundary>
                <ActivityInput onActivityLogged={loadDashboardData} region={region} />
              </ErrorBoundary>
              <ErrorBoundary>
                <Card className="space-y-3">
                  <h3 className="text-xs font-black uppercase tracking-widest text-theme-secondary">
                    Multimodal Scans (OCR Scan Receipt)
                  </h3>
                  <MultimodalUpload onUploadSuccess={loadDashboardData} region={region} />
                </Card>
              </ErrorBoundary>
            </motion.div>
          )}

          {/* ═══════════════════════════════════════════════════════════════
              ANALYTICS TAB
          ═══════════════════════════════════════════════════════════════ */}
          {currentTab === "analytics" && (
            <motion.div variants={itemVariants} className="space-y-6">
              <h2 className="text-md font-black uppercase tracking-wider text-theme-heading">
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
          {currentTab === "devices" && smartDevicesEnabled && (
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
              <h2 className="text-md font-black uppercase tracking-wider text-theme-heading">
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
              <h2 className="text-md font-black uppercase tracking-wider text-theme-heading">
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
              SETTINGS TAB
          ═══════════════════════════════════════════════════════════════ */}
          {currentTab === "settings" && (
            <motion.div variants={itemVariants} className="max-w-4xl mx-auto space-y-6">
              <ErrorBoundary>
                <Settings />
              </ErrorBoundary>
            </motion.div>
          )}

          {/* ═══════════════════════════════════════════════════════════════
              FALLBACK
          ═══════════════════════════════════════════════════════════════ */}
          {!["dashboard", "logger", "analytics", "coach", "devices", "quests", "marketplace", "history", "settings"].includes(
            currentTab
          ) && (
            <motion.div
              variants={itemVariants}
              className="flex flex-col items-center justify-center min-h-[400px] border border-dashed border-white/5 rounded-3xl bg-white/[0.01] select-none text-center p-6"
            >
              <span className="text-xs text-theme-muted font-extrabold uppercase tracking-widest animate-pulse">
                {currentTab} view coming soon
              </span>
              <Button
                variant="outline"
                size="md"
                onClick={() => handleTabChange("dashboard")}
                className="mt-5"
              >
                Return to Cockpit
              </Button>
            </motion.div>
          )}
        </>
      )}
    </main>
      </div>

      {/* Floating AI Copilot Trigger */}
      {!isCopilotOpen && (
        <div className="fixed bottom-6 right-6 z-40">
          <motion.button
            whileHover={{ scale: 1.06 }}
            whileTap={{ scale: 0.94 }}
            onClick={() => setIsCopilotOpen(true)}
            className="relative flex items-center justify-center w-14 h-14 rounded-full bg-theme-brand text-white shadow-xl cursor-pointer overflow-hidden border border-white/10 glow-btn"
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

      <ToastError />
    </div>
  );
});

// ─── Root Wrapped Export ──────────────────────────────────────────────────────

export default function Home() {
  return (
    <ErrorBoundary>
      <HomeContent />
    </ErrorBoundary>
  );
}
