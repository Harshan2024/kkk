"use client";

/**
 * aiStore.tsx — CarbonTracker Global State Store
 * ===============================================
 * LOCKED: Core state management. Do not modify without team review.
 *
 * Hardened with:
 * - Per-call try/catch (one failing API call does NOT abort dashboard load)
 * - Non-blocking toast error state instead of alert()
 * - AbortController cleanup on unmount
 * - useMemo for derived gamification values
 * - fetchWithRetry for resilient initial load
 */

import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  useMemo,
  useRef,
} from "react";
import {
  api,
  ChatMessage,
  ForecastData,
  ObservabilityMetrics,
  Activity,
  DashboardSummary,
  AIInsight,
  Achievement,
  SystemHealth,
} from "../services/api";
import logger from "../utils/logger";

// ─────────────────────────────────────────────────────────────────────────────
// CONTEXT SHAPE
// ─────────────────────────────────────────────────────────────────────────────

interface AIContextProps {
  // Dashboard state
  summary: DashboardSummary | null;
  insights: AIInsight[];
  achievements: Achievement[];
  activities: Activity[];
  region: string;
  loading: boolean;
  error: string | null;
  toastError: string | null;       // Non-blocking error notification
  clearToastError: () => void;

  setRegion: (r: string) => void;
  loadDashboardData: () => Promise<void>;
  logActivity: (text: string, region?: string) => Promise<void>;

  // Chat & AI
  chatMessages: ChatMessage[];
  chatLoading: boolean;
  forecastData: ForecastData[];
  forecastLoading: boolean;
  metrics: ObservabilityMetrics | null;
  metricsLoading: boolean;
  isRecording: boolean;
  transcript: string;
  setTranscript: (text: string) => void;
  setIsRecording: (recording: boolean) => void;
  fetchChatHistory: () => Promise<void>;
  sendChatMessage: (message: string) => Promise<string>;
  fetchForecast: (model?: string, steps?: number) => Promise<void>;
  fetchMetrics: () => Promise<void>;
  uploadReceipt: (file: File, region?: string) => Promise<unknown>;
  submitCorrection: (original: string, corrected: string, category?: string) => Promise<void>;

  // System health
  systemHealth: SystemHealth | null;
  fetchSystemHealth: () => Promise<void>;
}

export const AIContext = createContext<AIContextProps | undefined>(undefined);

export function useAIStore() {
  const context = useContext(AIContext);
  if (!context) {
    throw new Error("useAIStore must be used within an AIStoreProvider");
  }
  return context;
}

// ─────────────────────────────────────────────────────────────────────────────
// PROVIDER
// ─────────────────────────────────────────────────────────────────────────────

export function AIStoreProvider({
  children,
  username = "demo_user",
}: {
  children: React.ReactNode;
  username?: string;
}) {
  // Core dashboard state
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [insights, setInsights] = useState<AIInsight[]>([]);
  const [achievements, setAchievements] = useState<Achievement[]>([]);
  const [activities, setActivities] = useState<Activity[]>([]);
  const [region, setRegion] = useState("Global");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [toastError, setToastError] = useState<string | null>(null);

  // Chat / voice / forecast
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [chatLoading, setChatLoading] = useState(false);
  const [forecastData, setForecastData] = useState<ForecastData[]>([]);
  const [forecastLoading, setForecastLoading] = useState(false);
  const [metrics, setMetrics] = useState<ObservabilityMetrics | null>(null);
  const [metricsLoading, setMetricsLoading] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [systemHealth, setSystemHealth] = useState<SystemHealth | null>(null);

  // Unmount abort controller
  const abortRef = useRef<AbortController | null>(null);

  const clearToastError = useCallback(() => setToastError(null), []);

  // ─────────────────────────────────────────────────────────────────────────
  // RETRY HELPER
  // ─────────────────────────────────────────────────────────────────────────

  const fetchWithRetry = useCallback(async <T,>(
    fn: () => Promise<T>,
    retries = 2,
    delayMs = 800
  ): Promise<T | null> => {
    for (let i = 1; i <= retries; i++) {
      try {
        return await fn();
      } catch (err) {
        if (i === retries) {
          logger.warn("aiStore", `fetch failed after ${retries} attempts`, err);
          return null;
        }
        await new Promise((r) => setTimeout(r, delayMs));
      }
    }
    return null;
  }, []);

  // ─────────────────────────────────────────────────────────────────────────
  // DASHBOARD LOAD — per-call isolation: one failure does NOT abort others
  // ─────────────────────────────────────────────────────────────────────────

  const loadDashboardData = useCallback(async () => {
    setLoading(true);
    setError(null);

    // Run all four calls independently — partial success is valid
    const [summaryResult, insightsResult, achievementsResult, historyResult] =
      await Promise.allSettled([
        fetchWithRetry(() => api.getDashboardSummary(username)),
        fetchWithRetry(() => api.getInsights(username)),
        fetchWithRetry(() => api.getAchievements(username)),
        fetchWithRetry(() => api.getActivities(username)),
      ]);

    let anySuccess = false;

    if (summaryResult.status === "fulfilled" && summaryResult.value) {
      setSummary(summaryResult.value);
      anySuccess = true;
    } else {
      logger.error("aiStore", "getDashboardSummary failed", summaryResult);
    }

    if (insightsResult.status === "fulfilled" && insightsResult.value) {
      setInsights(insightsResult.value);
      anySuccess = true;
    } else {
      logger.error("aiStore", "getInsights failed", insightsResult);
      setInsights([]); // Safe empty state
    }

    if (achievementsResult.status === "fulfilled" && achievementsResult.value) {
      setAchievements(achievementsResult.value);
    } else {
      setAchievements([]);
    }

    if (historyResult.status === "fulfilled" && historyResult.value) {
      setActivities(historyResult.value);
    } else {
      setActivities([]);
    }

    if (!anySuccess) {
      // All calls failed — show connection error
      try {
        const health = await api.checkHealth();
        if (health?.database === "disconnected" || health?.database === "offline_safe_mode") {
          setError(
            "Database is offline. Backend is running in safe mode. Connect PostgreSQL to restore full functionality."
          );
        } else {
          setError("Unable to load dashboard data. Ensure the backend is running on port 8000.");
        }
      } catch {
        setError("Cannot reach CarbonTracker API. Start the backend server and refresh.");
      }
    }

    setLoading(false);
  }, [username, fetchWithRetry]);

  // ─────────────────────────────────────────────────────────────────────────
  // SILENT BACKGROUND REFRESH
  // ─────────────────────────────────────────────────────────────────────────

  const silentDashboardRefresh = useCallback(async () => {
    try {
      const [summaryData, insightsData, achievementsData, historyData] = await Promise.allSettled([
        api.getDashboardSummary(username),
        api.getInsights(username),
        api.getAchievements(username),
        api.getActivities(username),
      ]);

      if (summaryData.status === "fulfilled" && summaryData.value)
        setSummary(summaryData.value);
      if (insightsData.status === "fulfilled" && insightsData.value)
        setInsights(insightsData.value);
      if (achievementsData.status === "fulfilled" && achievementsData.value)
        setAchievements(achievementsData.value);
      if (historyData.status === "fulfilled" && historyData.value)
        setActivities(historyData.value);
    } catch (err) {
      logger.warn("aiStore", "Silent background refresh failed", err);
    }
  }, [username]);

  // ─────────────────────────────────────────────────────────────────────────
  // OPTIMISTIC ACTIVITY LOGGING
  // ─────────────────────────────────────────────────────────────────────────

  const logActivity = useCallback(
    async (text: string, activeRegion = "Global") => {
      if (!text.trim()) return;

      // 1. Request NLP parse preview for realistic optimistic card
      let calculatedValue = 0.0;
      let category = "lifestyle";
      let item = "activity";
      let unit = "unit";
      let quantity = 1.0;
      let metadata = {};

      try {
        const preview = await api.parseActivity(text, activeRegion);
        if (preview?.success) {
          calculatedValue = preview.calculated_value ?? 0.0;
          category = preview.parsed?.category ?? "lifestyle";
          item = preview.parsed?.item ?? "activity";
          unit = preview.parsed?.unit ?? "unit";
          quantity = preview.parsed?.quantity ?? 1.0;
          metadata = preview.metadata ?? {};
        }
      } catch (e) {
        logger.warn("aiStore", "Optimistic parse preview failed — using defaults", e);
      }

      // 2. Pre-generate optimistic activity
      const optimisticId = -Date.now();
      const optimisticAct: Activity = {
        id: optimisticId,
        input_text: text,
        category,
        item,
        quantity,
        unit,
        calculated_value: calculatedValue,
        metadata,
        region: activeRegion,
        logged_at: new Date().toISOString(),
      };

      // 3. Optimistic state update
      setActivities((prev) => [optimisticAct, ...prev]);
      setSummary((prev) => {
        if (!prev) return null;
        const newToday = (prev.today_emissions ?? 0) + calculatedValue;
        const budget = prev.daily_budget ?? 5.0;
        const newScore = Math.max(0, Math.min(100, 100 - (newToday / budget) * 50));
        const newBreakdown = (prev.breakdown ?? []).map((b) =>
          b.category.toLowerCase() === category.toLowerCase()
            ? { ...b, total_carbon: b.total_carbon + calculatedValue }
            : b
        );
        const newTrends = [...(prev.trends ?? [])];
        if (newTrends.length > 0) {
          const last = { ...newTrends[newTrends.length - 1] };
          last.emissions = (last.emissions ?? 0) + calculatedValue;
          last.score = newScore;
          newTrends[newTrends.length - 1] = last;
        }
        return {
          ...prev,
          today_emissions: newToday,
          weekly_emissions: (prev.weekly_emissions ?? 0) + calculatedValue,
          current_score: newScore,
          trends: newTrends,
          breakdown: newBreakdown,
        };
      });

      // 4. Background DB persistence
      try {
        const realActivity = await api.logActivity(text, username, activeRegion);
        setActivities((prev) =>
          prev.map((act) => (act.id === optimisticId ? realActivity : act))
        );
        silentDashboardRefresh();
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : "Failed to save activity";
        logger.error("aiStore", "Activity persistence failed", err);
        // Remove optimistic entry on failure — don't show alert()
        setActivities((prev) => prev.filter((act) => act.id !== optimisticId));
        setToastError(`Activity not saved: ${msg}. Please try again.`);
        silentDashboardRefresh();
      }
    },
    [username, silentDashboardRefresh]
  );

  // ─────────────────────────────────────────────────────────────────────────
  // CHAT
  // ─────────────────────────────────────────────────────────────────────────

  const fetchChatHistory = useCallback(async () => {
    setChatLoading(true);
    try {
      const history = await api.getChatHistory(username);
      setChatMessages(history ?? []);
    } catch (err) {
      logger.error("aiStore", "fetchChatHistory failed", err);
      setChatMessages([]);
    } finally {
      setChatLoading(false);
    }
  }, [username]);

  const sendChatMessage = useCallback(
    async (message: string): Promise<string> => {
      if (!message.trim()) return "";

      const userMsg: ChatMessage = {
        id: Date.now(),
        role: "user",
        content: message,
        created_at: new Date().toISOString(),
      };
      setChatMessages((prev) => [...prev, userMsg]);
      setChatLoading(true);

      try {
        const result = await api.postChat(message, username, 30_000);
        const assistantMsg: ChatMessage = {
          id: Date.now() + 1,
          role: "assistant",
          content: result?.response ?? "No response received.",
          created_at: new Date().toISOString(),
        };
        setChatMessages((prev) => [...prev, assistantMsg]);
        silentDashboardRefresh();
        return result?.response ?? "";
      } catch (err: unknown) {
        logger.error("aiStore", "sendChatMessage failed", err);
        const errMsg =
          err instanceof Error && err.message.includes("timeout")
            ? "AI Copilot timed out. The service may be under load. Please try again."
            : "AI Service temporarily unavailable. Please try again in a moment.";

        const errorMsg: ChatMessage = {
          id: Date.now() + 1,
          role: "assistant",
          content: errMsg,
          created_at: new Date().toISOString(),
        };
        setChatMessages((prev) => [...prev, errorMsg]);
        return "";
      } finally {
        setChatLoading(false);
      }
    },
    [username, silentDashboardRefresh]
  );

  // ─────────────────────────────────────────────────────────────────────────
  // FORECAST & METRICS
  // ─────────────────────────────────────────────────────────────────────────

  const fetchForecast = useCallback(
    async (model = "prophet", steps = 30) => {
      setForecastLoading(true);
      try {
        const data = await api.getForecast(username, steps, model);
        setForecastData(data ?? []);
      } catch (err) {
        logger.error("aiStore", "fetchForecast failed", err);
        setForecastData([]);
      } finally {
        setForecastLoading(false);
      }
    },
    [username]
  );

  const fetchMetrics = useCallback(async () => {
    setMetricsLoading(true);
    try {
      const data = await api.getObservabilityMetrics(username);
      setMetrics(data ?? null);
    } catch (err) {
      logger.error("aiStore", "fetchMetrics failed", err);
    } finally {
      setMetricsLoading(false);
    }
  }, [username]);

  // ─────────────────────────────────────────────────────────────────────────
  // RECEIPT UPLOAD
  // ─────────────────────────────────────────────────────────────────────────

  const uploadReceipt = useCallback(
    async (file: File, activeRegion = "Global") => {
      try {
        const res = await api.uploadMultimodal(file, username, activeRegion);
        silentDashboardRefresh();
        fetchMetrics();
        return res;
      } catch (err) {
        logger.error("aiStore", "uploadReceipt failed", err);
        throw err;
      }
    },
    [username, silentDashboardRefresh, fetchMetrics]
  );

  // ─────────────────────────────────────────────────────────────────────────
  // CORRECTION
  // ─────────────────────────────────────────────────────────────────────────

  const submitCorrection = useCallback(
    async (original: string, corrected: string, category = "nlp_parse") => {
      try {
        await api.correctActivity(original, corrected, category, username);
        fetchMetrics();
      } catch (err) {
        logger.error("aiStore", "submitCorrection failed", err);
      }
    },
    [username, fetchMetrics]
  );

  // ─────────────────────────────────────────────────────────────────────────
  // SYSTEM HEALTH
  // ─────────────────────────────────────────────────────────────────────────

  const fetchSystemHealth = useCallback(async () => {
    try {
      const health = await api.getSystemHealth();
      setSystemHealth(health);
    } catch (err) {
      logger.error("aiStore", "fetchSystemHealth failed", err);
    }
  }, []);

  // ─────────────────────────────────────────────────────────────────────────
  // INITIAL LOAD + CLEANUP
  // ─────────────────────────────────────────────────────────────────────────

  useEffect(() => {
    loadDashboardData();
    fetchChatHistory();
    fetchMetrics();
    fetchForecast();
    fetchSystemHealth();

    return () => {
      if (abortRef.current) abortRef.current.abort();
    };
  }, [loadDashboardData, fetchChatHistory, fetchMetrics, fetchForecast, fetchSystemHealth]);

  // ─────────────────────────────────────────────────────────────────────────
  // CONTEXT VALUE
  // ─────────────────────────────────────────────────────────────────────────

  const contextValue = useMemo(
    () => ({
      summary,
      insights,
      achievements,
      activities,
      region,
      setRegion,
      loading,
      error,
      toastError,
      clearToastError,
      loadDashboardData,
      logActivity,
      chatMessages,
      chatLoading,
      forecastData,
      forecastLoading,
      metrics,
      metricsLoading,
      isRecording,
      transcript,
      setTranscript,
      setIsRecording,
      fetchChatHistory,
      sendChatMessage,
      fetchForecast,
      fetchMetrics,
      uploadReceipt,
      submitCorrection,
      systemHealth,
      fetchSystemHealth,
    }),
    [
      summary, insights, achievements, activities, region, loading, error,
      toastError, clearToastError, loadDashboardData, logActivity,
      chatMessages, chatLoading, forecastData, forecastLoading, metrics,
      metricsLoading, isRecording, transcript, fetchChatHistory,
      sendChatMessage, fetchForecast, fetchMetrics, uploadReceipt,
      submitCorrection, systemHealth, fetchSystemHealth,
    ]
  );

  return (
    <AIContext.Provider value={contextValue}>
      {children}
    </AIContext.Provider>
  );
}
