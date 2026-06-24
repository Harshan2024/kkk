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
  AnalyticsPayload,
  DEFAULT_ANALYTICS,
  ProfileResponse,
} from "../services/api";
import logger from "../utils/logger";

// ─────────────────────────────────────────────────────────────────────────────
// CONTEXT SHAPE
// ─────────────────────────────────────────────────────────────────────────────

interface AIContextProps {
  // Dashboard state
  summary: DashboardSummary | null;
  insights: AIInsight[];
  insightsLoading: boolean;
  achievements: Achievement[];
  achievementsLoading: boolean;
  activities: Activity[];
  activitiesLoading: boolean;
  region: string;
  loading: boolean;
  error: string | null;
  toastError: string | null;       // Non-blocking error notification
  clearToastError: () => void;
  setToastError: (msg: string | null) => void;

  setRegion: (r: string) => void;
  loadDashboardData: () => Promise<void>;
  logActivity: (text: string, region?: string) => Promise<void>;

  // Chat & AI
  chatMessages: ChatMessage[];
  chatLoading: boolean;
  forecastData: ForecastData[];
  forecastLoading: boolean;
  forecastStatus: string | null;
  metrics: ObservabilityMetrics | null;
  metricsLoading: boolean;
  isRecording: boolean;
  transcript: string;
  setTranscript: (text: string) => void;
  setIsRecording: (recording: boolean) => void;
  fetchChatHistory: () => Promise<void>;
  sendChatMessage: (message: string) => Promise<string>;
  fetchForecast: (model?: string, steps?: number, generate?: boolean) => Promise<void>;
  fetchMetrics: () => Promise<void>;
  uploadReceipt: (file: File, region?: string) => Promise<unknown>;
  submitCorrection: (original: string, corrected: string, category?: string) => Promise<void>;

  // System health
  systemHealth: SystemHealth | null;
  fetchSystemHealth: () => Promise<void>;
  forecastEnabled: boolean;

  // Analytics
  analyticsData: AnalyticsPayload | null;
  analyticsLoading: boolean;
  fetchAnalytics: () => Promise<void>;

  // Authentication State & Actions
  user: ProfileResponse | null;
  isAuthenticated: boolean;
  token: string | null;
  login: (email: string, password: string) => Promise<boolean>;
  register: (username: string, email: string, password: string) => Promise<boolean>;
  logout: () => void;
  updateProfile: (username: string, email: string) => Promise<boolean>;
  username: string;
}

export const AIContext = createContext<AIContextProps | undefined>(undefined);

export const DEFAULT_AI_CONTEXT_VALUE: AIContextProps = {
  summary: null,
  insights: [],
  insightsLoading: false,
  achievements: [],
  achievementsLoading: false,
  activities: [],
  activitiesLoading: false,
  region: "Global",
  loading: false,
  error: null,
  toastError: null,
  clearToastError: () => {},
  setToastError: () => {},
  setRegion: () => {},
  loadDashboardData: async () => {},
  logActivity: async () => {},
  chatMessages: [],
  chatLoading: false,
  forecastData: [],
  forecastLoading: false,
  forecastStatus: null,
  metrics: null,
  metricsLoading: false,
  isRecording: false,
  transcript: "",
  setTranscript: () => {},
  setIsRecording: () => {},
  fetchChatHistory: async () => {},
  sendChatMessage: async () => "",
  fetchForecast: async () => {},
  fetchMetrics: async () => {},
  uploadReceipt: async () => ({}),
  submitCorrection: async () => {},
  systemHealth: null,
  fetchSystemHealth: async () => {},
  forecastEnabled: false,
  analyticsData: null,
  analyticsLoading: false,
  fetchAnalytics: async () => {},
  user: null,
  isAuthenticated: false,
  token: null,
  login: async () => false,
  register: async () => false,
  logout: () => {},
  updateProfile: async () => false,
  username: "demo_user",
};

export function useAIStore() {
  const context = useContext(AIContext);
  if (!context) {
    logger.warn("useAIStore", "useAIStore called outside AIStoreProvider, returning default fallback state.");
    return DEFAULT_AI_CONTEXT_VALUE;
  }
  return context;
}

// ─────────────────────────────────────────────────────────────────────────────
// PROVIDER
// ─────────────────────────────────────────────────────────────────────────────

export function AIStoreProvider({
  children,
  username: initialUsername = "demo_user",
}: {
  children: React.ReactNode;
  username?: string;
}) {
  // Authentication State
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<ProfileResponse | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  const activeUsername = useMemo(() => {
    return user?.username || initialUsername || "demo_user";
  }, [user, initialUsername]);

  // Core dashboard state
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [insights, setInsights] = useState<AIInsight[]>([]);
  const [insightsLoading, setInsightsLoading] = useState(false);
  const [achievements, setAchievements] = useState<Achievement[]>([]);
  const [achievementsLoading, setAchievementsLoading] = useState(false);
  const [activities, setActivities] = useState<Activity[]>([]);
  const [activitiesLoading, setActivitiesLoading] = useState(false);
  const [region, setRegion] = useState("Global");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [toastError, setToastError] = useState<string | null>(null);

  // Chat / voice / forecast
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [chatLoading, setChatLoading] = useState(false);
  const [forecastData, setForecastData] = useState<ForecastData[]>([]);
  const [forecastLoading, setForecastLoading] = useState(false);
  const [forecastStatus, setForecastStatus] = useState<string | null>(null);
  const [metrics, setMetrics] = useState<ObservabilityMetrics | null>(null);
  const [metricsLoading, setMetricsLoading] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [systemHealth, setSystemHealth] = useState<SystemHealth | null>(null);
  const [featureFlags, setFeatureFlags] = useState<Record<string, boolean>>({});

  // Analytics State
  const [analyticsData, setAnalyticsData] = useState<AnalyticsPayload | null>(null);
  const [analyticsLoading, setAnalyticsLoading] = useState(false);

  const forecastEnabled = useMemo(() => {
    const envVal = process.env.NEXT_PUBLIC_FORECAST_ENABLED;
    if (envVal !== undefined) {
      return envVal === "true" || envVal === "1";
    }
    if (featureFlags.FORECAST_ENABLED !== undefined) {
      return featureFlags.FORECAST_ENABLED;
    }
    if (featureFlags.enable_forecasting !== undefined) {
      return featureFlags.enable_forecasting;
    }
    return false;
  }, [featureFlags]);

  // Unmount abort controller
  const abortRef = useRef<AbortController | null>(null);
  const prevDbStatusRef = useRef<string | null>(null);

  // Request deduplication refs
  const isDashboardLoadingRef = useRef(false);
  const isSystemHealthLoadingRef = useRef(false);
  const isDeferredLoadingRef = useRef(false);
  const isChatHistoryLoadingRef = useRef(false);

  // Status syncing refs for polling loop
  const systemHealthRef = useRef<SystemHealth | null>(null);
  const errorRef = useRef<string | null>(null);

  const clearToastError = useCallback(() => setToastError(null), []);

  // ─────────────────────────────────────────────────────────────────────────
  // RETRY HELPER
  // ─────────────────────────────────────────────────────────────────────────

  const fetchWithRetry = useCallback(async <T,>(
    fn: () => Promise<T>,
    retries = 1,
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
    if (isDashboardLoadingRef.current) {
      logger.info("aiStore", "loadDashboardData already in progress, skipping duplicate call");
      return;
    }
    isDashboardLoadingRef.current = true;
    setLoading(true);
    setError(null);

    try {
      const summaryResult = await fetchWithRetry(() => api.getDashboardSummary(activeUsername));
      if (summaryResult) {
        setSummary(summaryResult);
      } else {
        logger.error("aiStore", "getDashboardSummary failed");
        setError("Unable to load dashboard summary.");
      }
    } catch (err) {
      logger.error("aiStore", "getDashboardSummary failed", err);
      setError("Cannot reach CarbonTracker API. Start the backend server and refresh.");
    } finally {
      setLoading(false);
      isDashboardLoadingRef.current = false;
    }
  }, [activeUsername, fetchWithRetry]);

  // ─────────────────────────────────────────────────────────────────────────
  // SILENT BACKGROUND REFRESH
  // ─────────────────────────────────────────────────────────────────────────

  const silentDashboardRefresh = useCallback(async () => {
    try {
      const summaryData = await api.getDashboardSummary(activeUsername);
      if (summaryData) {
        setSummary(summaryData);
      }
      // Silently refresh the other deferred endpoints in background
      api.getInsights(activeUsername).then((res) => setInsights(res ?? [])).catch(() => {});
      api.getAchievements(activeUsername).then((res) => setAchievements(res ?? [])).catch(() => {});
      api.getActivities(activeUsername).then((res) => setActivities(res ?? [])).catch(() => {});
    } catch (err) {
      logger.warn("aiStore", "Silent background refresh failed", err);
    }
  }, [activeUsername]);

  // ─────────────────────────────────────────────────────────────────────────
  // OPTIMISTIC ACTIVITY LOGGING
  // ─────────────────────────────────────────────────────────────────────────

  const logActivity = useCallback(
    async (text: string, activeRegion = "Global") => {
      if (!text.trim()) return;

      if (
        error === "Reconnecting to database..." ||
        error?.includes("Database temporarily unavailable") ||
        (systemHealth && (systemHealth.database === "offline" || systemHealth.database === "degraded"))
      ) {
        setToastError("Database temporarily unavailable. Running in read-only mode.");
        return;
      }

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
        const realActivity = await api.logActivity(text, activeUsername, activeRegion);
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
    [activeUsername, silentDashboardRefresh]
  );

  // ─────────────────────────────────────────────────────────────────────────
  // CHAT
  // ─────────────────────────────────────────────────────────────────────────

  const fetchChatHistory = useCallback(async () => {
    if (isChatHistoryLoadingRef.current) {
      logger.info("aiStore", "fetchChatHistory already in progress, skipping duplicate call");
      return;
    }
    isChatHistoryLoadingRef.current = true;
    setChatLoading(true);
    try {
      const history = await api.getChatHistory(activeUsername);
      setChatMessages(history ?? []);
    } catch (err) {
      logger.error("aiStore", "fetchChatHistory failed", err);
      setChatMessages([]);
    } finally {
      setChatLoading(false);
      isChatHistoryLoadingRef.current = false;
    }
  }, [activeUsername]);

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
        const result = await api.postChat(message, activeUsername, 30_000);
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
    [activeUsername, silentDashboardRefresh]
  );

  // ─────────────────────────────────────────────────────────────────────────
  // FORECAST & METRICS
  // ─────────────────────────────────────────────────────────────────────────

  const fetchForecast = useCallback(
    async (model = "prophet", steps = 30, generate = false) => {
      if (!forecastEnabled) {
        logger.info("aiStore", "Forecast is disabled via feature flag, skipping request");
        setForecastData([]);
        setForecastStatus("disabled");
        return;
      }
      setForecastLoading(true);
      try {
        const res = await api.getForecast(activeUsername, steps, model, generate);
        setForecastData(res.data ?? []);
        setForecastStatus(res.status ?? null);
      } catch (err: any) {
        const isIntentionalDisable = 
          err?.message?.includes("temporarily disabled") || 
          err?.message?.includes("503");
          
        if (isIntentionalDisable) {
          setForecastData([]);
          setForecastStatus("disabled_intentionally");
        } else {
          logger.error("aiStore", "fetchForecast failed", err);
          setForecastData([]);
          setForecastStatus("error");
        }
      } finally {
        setForecastLoading(false);
      }
    },
    [activeUsername, forecastEnabled]
  );

  const fetchMetrics = useCallback(async () => {
    setMetricsLoading(true);
    try {
      const data = await api.getObservabilityMetrics(activeUsername);
      setMetrics(data ?? null);
    } catch (err) {
      logger.error("aiStore", "fetchMetrics failed", err);
    } finally {
      setMetricsLoading(false);
    }
  }, [activeUsername]);

  // ─────────────────────────────────────────────────────────────────────────
  // RECEIPT UPLOAD
  // ─────────────────────────────────────────────────────────────────────────

  const uploadReceipt = useCallback(
    async (file: File, activeRegion = "Global") => {
      if (
        error === "Reconnecting to database..." ||
        error?.includes("Database temporarily unavailable") ||
        (systemHealth && (systemHealth.database === "offline" || systemHealth.database === "degraded"))
      ) {
        setToastError("Database temporarily unavailable. Running in read-only mode.");
        throw new Error("Database temporarily unavailable. Running in read-only mode.");
      }
      try {
        const res = await api.uploadMultimodal(file, activeUsername, activeRegion);
        silentDashboardRefresh();
        return res;
      } catch (err) {
        logger.error("aiStore", "uploadReceipt failed", err);
        throw err;
      }
    },
    [activeUsername, silentDashboardRefresh]
  );

  // ─────────────────────────────────────────────────────────────────────────
  // CORRECTION
  // ─────────────────────────────────────────────────────────────────────────

  const submitCorrection = useCallback(
    async (original: string, corrected: string, category = "nlp_parse") => {
      if (
        error === "Reconnecting to database..." ||
        error?.includes("Database temporarily unavailable") ||
        (systemHealth && (systemHealth.database === "offline" || systemHealth.database === "degraded"))
      ) {
        setToastError("Database temporarily unavailable. Running in read-only mode.");
        return;
      }
      try {
        await api.correctActivity(original, corrected, category, activeUsername);
      } catch (err) {
        logger.error("aiStore", "submitCorrection failed", err);
      }
    },
    [activeUsername]
  );

  // ─────────────────────────────────────────────────────────────────────────
  // SYSTEM HEALTH
  // ─────────────────────────────────────────────────────────────────────────

  const loadDeferredData = useCallback(async () => {
    if (isDeferredLoadingRef.current) {
      logger.info("aiStore", "loadDeferredData already in progress, skipping duplicate call");
      return;
    }
    isDeferredLoadingRef.current = true;
    setInsightsLoading(true);
    setAchievementsLoading(true);
    setActivitiesLoading(true);
    setMetricsLoading(false);
    setForecastLoading(false);
    setChatLoading(true);

    const insightsPromise = fetchWithRetry(() => api.getInsights(activeUsername))
      .then((res) => setInsights(res ?? []))
      .catch(() => setInsights([]))
      .finally(() => setInsightsLoading(false));

    const achievementsPromise = fetchWithRetry(() => api.getAchievements(activeUsername))
      .then((res) => setAchievements(res ?? []))
      .catch(() => setAchievements([]))
      .finally(() => setAchievementsLoading(false));

    const activitiesPromise = fetchWithRetry(() => api.getActivities(activeUsername))
      .then((res) => setActivities(res ?? []))
      .catch(() => setActivities([]))
      .finally(() => setActivitiesLoading(false));

    const chatPromise = fetchChatHistory();

    await Promise.allSettled([insightsPromise, achievementsPromise, activitiesPromise, chatPromise]);
    isDeferredLoadingRef.current = false;
  }, [activeUsername, fetchWithRetry, fetchChatHistory]);

  const fetchSystemHealth = useCallback(async () => {
    if (isSystemHealthLoadingRef.current) {
      logger.info("aiStore", "fetchSystemHealth already in progress, skipping duplicate call");
      return;
    }
    isSystemHealthLoadingRef.current = true;
    try {
      const health = await api.getSystemHealth();
      setSystemHealth(health);
      
      try {
        const flags = await api.getFeatureFlags();
        setFeatureFlags(flags);
      } catch (flagErr) {
        logger.warn("aiStore", "fetchFeatureFlags failed", flagErr);
      }
      
      const currentDbStatus = health?.database || "online";
      const prevDbStatus = prevDbStatusRef.current;
      prevDbStatusRef.current = currentDbStatus;

      if (health && !health.failed && (currentDbStatus === "offline" || currentDbStatus === "degraded")) {
        setError("Reconnecting to database...");
      } else {
        setError((prev) => prev === "Reconnecting to database..." || prev?.includes("Database temporarily unavailable") ? null : prev);
        
        // Auto-refresh: transition from offline/degraded back to online
        if (
          prevDbStatus &&
          (prevDbStatus === "offline" || prevDbStatus === "degraded") &&
          currentDbStatus === "online"
        ) {
          logger.info("aiStore", "Database recovered! Triggering automatic dashboard refresh.");
          loadDashboardData();
        }
      }
    } catch (err) {
      logger.warn("aiStore", "fetchSystemHealth failed", err);
    } finally {
      isSystemHealthLoadingRef.current = false;
    }
  }, [loadDashboardData]);

  const fetchAnalytics = useCallback(async () => {
    setAnalyticsLoading(true);
    try {
      const data = await api.getAnalytics(activeUsername);
      setAnalyticsData(data ?? DEFAULT_ANALYTICS);
    } catch (err) {
      logger.error("aiStore", "fetchAnalytics failed", err);
      setAnalyticsData(DEFAULT_ANALYTICS);
      setToastError("Unable to load analytics dashboard data.");
    } finally {
      setAnalyticsLoading(false);
    }
  }, [activeUsername]);

  // ─────────────────────────────────────────────────────────────────────────
  // INITIAL LOAD + DEFERRED LOADING
  // ─────────────────────────────────────────────────────────────────────────

  // Sync state values to refs to avoid polling loop recreation
  useEffect(() => {
    systemHealthRef.current = systemHealth;
  }, [systemHealth]);

  useEffect(() => {
    errorRef.current = error;
  }, [error]);

  // Authentication Actions
  const login = useCallback(async (email: string, password: string): Promise<boolean> => {
    try {
      const tokenData = await api.login(email, password);
      if (tokenData && tokenData.access_token) {
        localStorage.setItem("carbontracker_token", tokenData.access_token);
        setToken(tokenData.access_token);
        setIsAuthenticated(true);
        // Load profile immediately
        const profile = await api.getProfile();
        localStorage.setItem("carbontracker_user", JSON.stringify(profile));
        setUser(profile);
        return true;
      }
      return false;
    } catch (err: any) {
      logger.error("aiStore", "Login failed", err);
      setToastError(err?.message || "Login failed");
      return false;
    }
  }, []);

  const register = useCallback(async (username: string, email: string, password: string): Promise<boolean> => {
    try {
      const res = await api.register(username, email, password);
      return res?.success !== false;
    } catch (err: any) {
      logger.error("aiStore", "Registration failed", err);
      setToastError(err?.message || "Registration failed");
      return false;
    }
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem("carbontracker_token");
    localStorage.removeItem("carbontracker_user");
    setToken(null);
    setUser(null);
    setIsAuthenticated(false);
    setSummary(null);
    setInsights([]);
    setAchievements([]);
    setActivities([]);
    setChatMessages([]);
    setAnalyticsData(null);
  }, []);

  const updateProfile = useCallback(async (username: string, email: string): Promise<boolean> => {
    try {
      const res = await api.updateProfile(username, email);
      if (res?.success !== false) {
        const profile = await api.getProfile();
        localStorage.setItem("carbontracker_user", JSON.stringify(profile));
        setUser(profile);
        return true;
      }
      return false;
    } catch (err: any) {
      logger.error("aiStore", "Profile update failed", err);
      setToastError(err?.message || "Profile update failed");
      return false;
    }
  }, []);

  // Critical startup load and auto-login
  useEffect(() => {
    const savedToken = localStorage.getItem("carbontracker_token");
    const savedUser = localStorage.getItem("carbontracker_user");
    if (savedToken) {
      setToken(savedToken);
      setIsAuthenticated(true);
      if (savedUser) {
        try {
          setUser(JSON.parse(savedUser));
        } catch {
          // ignore
        }
      }
      // Validate saved token & fetch latest profile
      api.getProfile()
        .then((profile) => {
          localStorage.setItem("carbontracker_user", JSON.stringify(profile));
          setUser(profile);
        })
        .catch((err) => {
          logger.warn("aiStore", "Failed to validate saved token, logging out", err);
          logout();
        });
    }
    
    loadDashboardData();
    fetchSystemHealth();

    return () => {
      if (abortRef.current) abortRef.current.abort();
    };
  }, [loadDashboardData, fetchSystemHealth, logout]);

  // Controlled polling loop — runs once and schedules dynamically based on synced refs
  useEffect(() => {
    let timeoutId: NodeJS.Timeout | null = null;
    const poll = () => {
      const isReconnecting =
        errorRef.current === "Reconnecting to database..." ||
        (systemHealthRef.current &&
          (systemHealthRef.current.database === "offline" ||
            systemHealthRef.current.database === "degraded"));
      const delay = isReconnecting ? 5000 : 30000;

      timeoutId = setTimeout(async () => {
        await fetchSystemHealth();
        poll();
      }, delay);
    };

    poll();

    return () => {
      if (timeoutId) clearTimeout(timeoutId);
    };
  }, [fetchSystemHealth]);

  // Deferred loader triggers 50ms after summary is loaded
  useEffect(() => {
    if (!loading && summary) {
      const timer = setTimeout(() => {
        loadDeferredData();
      }, 50);
      return () => clearTimeout(timer);
    }
  }, [loading, summary, loadDeferredData]);

  // ─────────────────────────────────────────────────────────────────────────
  // CONTEXT VALUE
  // ─────────────────────────────────────────────────────────────────────────

  const contextValue = useMemo(
    () => ({
      summary,
      insights,
      insightsLoading,
      achievements,
      achievementsLoading,
      activities,
      activitiesLoading,
      region,
      setRegion,
      loading,
      error,
      toastError,
      clearToastError,
      setToastError,
      loadDashboardData,
      logActivity,
      chatMessages,
      chatLoading,
      forecastData,
      forecastLoading,
      forecastStatus,
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
      forecastEnabled,
      analyticsData,
      analyticsLoading,
      fetchAnalytics,
      user,
      isAuthenticated,
      token,
      login,
      register,
      logout,
      updateProfile,
      username: activeUsername,
    }),
    [
      summary, insights, insightsLoading, achievements, achievementsLoading,
      activities, activitiesLoading, region, loading, error,
      toastError, clearToastError, setToastError, loadDashboardData, logActivity,
      chatMessages, chatLoading, forecastData, forecastLoading, forecastStatus, metrics,
      metricsLoading, isRecording, transcript, fetchChatHistory,
      sendChatMessage, fetchForecast, fetchMetrics, uploadReceipt,
      submitCorrection, systemHealth, fetchSystemHealth, forecastEnabled,
      analyticsData, analyticsLoading, fetchAnalytics,
      user, isAuthenticated, token, login, register, logout, updateProfile, activeUsername,
    ]
  );

  return (
    <AIContext.Provider value={contextValue}>
      {children}
    </AIContext.Provider>
  );
}
