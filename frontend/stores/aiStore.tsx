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
  ApiError,
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
import { createEmptySummary } from "../utils/validators";
import {
  saveToken,
  loadToken,
  removeToken,
  saveUser,
  loadUser,
  saveRefreshToken,
  saveLoginTimestamp,
  isAuthenticated as checkAuthLocal,
} from "../services/authService";
import { healthMonitor } from "../services/healthMonitor";
import { cache } from "../services/cache";

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
  smartDevicesEnabled: boolean;

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
  startupPhase: "init" | "validating" | "loading" | "ready";
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
  smartDevicesEnabled: false,
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
  startupPhase: "init",
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

  // Startup phase for phased skeleton loading
  // "init" → reading localStorage
  // "validating" → verifying JWT with backend
  // "loading" → loading dashboard data
  // "ready" → all done, show UI
  const [startupPhase, setStartupPhase] = useState<"init" | "validating" | "loading" | "ready">("init");
  const [systemHealth, setSystemHealth] = useState<SystemHealth | null>(null);
  const [featureFlags, setFeatureFlags] = useState<Record<string, boolean>>({});

  // Analytics State
  const [analyticsData, setAnalyticsData] = useState<AnalyticsPayload | null>(null);
  const [analyticsLoading, setAnalyticsLoading] = useState(false);
  const [retryCount, setRetryCount] = useState(0);

  const classifyError = useCallback((err: any): string => {
    // Prefer typed ApiError.status for accurate HTTP status detection
    const httpStatus = err instanceof ApiError ? err.status : null;
    const msg = err?.message || String(err);

    // 401 / 403: authentication / authorisation — NOT a connectivity failure
    if (httpStatus === 401 || httpStatus === 403 ||
        msg.includes("401") || msg.includes("403") ||
        msg.toLowerCase().includes("session expired") ||
        msg.toLowerCase().includes("credentials")) {
      return "Session expired. Please login again.";
    }
    // 404: endpoint missing
    if (httpStatus === 404 || msg.includes("404")) {
      return "Dashboard service unavailable.";
    }
    // 500: server-side error — backend is reachable but broken
    if (httpStatus === 500 || msg.includes("500") || msg.toLowerCase().includes("internal server error")) {
      return "Unexpected server error.";
    }
    // True network/connectivity failure: no HTTP status, and matches network error patterns
    const isNetworkFailure =
      !httpStatus &&
      (msg.toLowerCase().includes("failed to fetch") ||
        msg.toLowerCase().includes("network error") ||
        msg.toLowerCase().includes("backend unavailable") ||
        msg.toLowerCase().includes("connection timeout") ||
        msg.toLowerCase().includes("connection error"));
    if (isNetworkFailure) {
      return "Unable to connect to backend.";
    }
    // Timeout: no HTTP status, explicit timeout message
    if (!httpStatus && msg.toLowerCase().includes("timeout")) {
      return "Connection timed out. Please check the backend is running.";
    }
    return msg || "Unexpected server error.";
  }, []);


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
 
  const smartDevicesEnabled = useMemo(() => {
    if (featureFlags.enable_smart_devices !== undefined) {
      return featureFlags.enable_smart_devices;
    }
    return false;
  }, [featureFlags]);

  // Unmount abort controller
  const abortRef = useRef<AbortController | null>(null);
  const prevDbStatusRef = useRef<string | null>(null);
  // Stable ref to logout to avoid forward-reference in useCallback deps
  const logoutRef = useRef<() => void>(() => {});

  // Request deduplication refs
  const isDashboardLoadingRef = useRef(false);
  const isSystemHealthLoadingRef = useRef(false);
  const isDeferredLoadingRef = useRef(false);
  const isChatHistoryLoadingRef = useRef(false);
  const isAnalyticsLoadingRef = useRef(false);

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
    setRetryCount(0); // reset automatic retry counter on manual load trigger

    if (abortRef.current) {
      abortRef.current.abort();
    }
    const abortCtrl = new AbortController();
    abortRef.current = abortCtrl;
    const signal = abortCtrl.signal;

    const savedToken = loadToken();
    if (!savedToken) {
      logger.info("aiStore", "loadDashboardData: no token found, aborting");
      setLoading(false);
      isDashboardLoadingRef.current = false;
      return;
    }

    try {
      logger.info("aiStore", "[DEBUG] loadDashboardData → calling getDashboardSummary (JWT in header)");
      const summaryResult = await fetchWithRetry(() => api.getDashboardSummary(signal));
      if (summaryResult) {
        setSummary(summaryResult);
        setError(null);
        logger.info("aiStore", "[DEBUG] loadDashboardData → getDashboardSummary SUCCESS");
      } else {
        logger.warn("aiStore", "getDashboardSummary returned null, using safe empty defaults");
        setSummary(createEmptySummary());
        setError(null);
      }
    } catch (err: any) {
      logger.error("aiStore", "getDashboardSummary failed", err);
      const classified = classifyError(err);
      if (classified === "Session expired. Please login again.") {
        logoutRef.current();
      } else {
        logger.warn("aiStore", `Using fallback empty summary due to: ${classified}`);
        setSummary(createEmptySummary());
        setToastError(`Dashboard summary unavailable: ${classified}`);
        setError(null);
      }
    } finally {
      setLoading(false);
      isDashboardLoadingRef.current = false;
    }
  }, [fetchWithRetry, classifyError]);

  // ─────────────────────────────────────────────────────────────────────────
  // SILENT BACKGROUND REFRESH
  // ─────────────────────────────────────────────────────────────────────────

  const silentDashboardRefresh = useCallback(async () => {
    try {
      const summaryData = await api.getDashboardSummary();
      if (summaryData) {
        setSummary(summaryData);
      }
      // Silently refresh the other deferred endpoints in background
      api.getInsights().then((res) => setInsights(res ?? [])).catch(() => {});
      api.getAchievements().then((res) => setAchievements(res ?? [])).catch(() => {});
      api.getActivities().then((res) => setActivities(res ?? [])).catch(() => {});
    } catch (err) {
      logger.warn("aiStore", "Silent background refresh failed", err);
    }
  }, []);

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
        const realActivity = await api.logActivity(text, activeRegion);
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
      const history = await api.getChatHistory();
      setChatMessages(history ?? []);
    } catch (err) {
      logger.error("aiStore", "fetchChatHistory failed", err);
      setChatMessages([]);
    } finally {
      setChatLoading(false);
      isChatHistoryLoadingRef.current = false;
    }
  }, []);

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
        const result = await api.postChat(message, 30_000);
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
        const res = await api.getForecast(steps, model, generate);
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
    [forecastEnabled]
  );

  const fetchMetrics = useCallback(async () => {
    setMetricsLoading(true);
    try {
      const data = await api.getObservabilityMetrics();
      setMetrics(data ?? null);
    } catch (err) {
      logger.error("aiStore", "fetchMetrics failed", err);
    } finally {
      setMetricsLoading(false);
    }
  }, []);

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
        const res = await api.uploadMultimodal(file, activeRegion);
        silentDashboardRefresh();
        return res;
      } catch (err) {
        logger.error("aiStore", "uploadReceipt failed", err);
        throw err;
      }
    },
    [silentDashboardRefresh]
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
        await api.correctActivity(original, corrected, category);
      } catch (err) {
        logger.error("aiStore", "submitCorrection failed", err);
      }
    },
    []
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

    const insightsPromise = fetchWithRetry(() => api.getInsights())
      .then((res) => setInsights(res ?? []))
      .catch(() => setInsights([]))
      .finally(() => setInsightsLoading(false));

    const achievementsPromise = fetchWithRetry(() => api.getAchievements())
      .then((res) => setAchievements(res ?? []))
      .catch(() => setAchievements([]))
      .finally(() => setAchievementsLoading(false));

    const activitiesPromise = fetchWithRetry(() => api.getActivities())
      .then((res) => setActivities(res ?? []))
      .catch(() => setActivities([]))
      .finally(() => setActivitiesLoading(false));

    const chatPromise = fetchChatHistory();

    await Promise.allSettled([insightsPromise, achievementsPromise, activitiesPromise, chatPromise]);
    isDeferredLoadingRef.current = false;
  }, [fetchWithRetry, fetchChatHistory]);

  const checkServerRestart = useCallback(async (signal?: AbortSignal) => {
    try {
      const metricsData = await api.getObservabilityMetrics() as any;
      const uptime = metricsData?.system?.uptime_seconds;
      if (typeof uptime === "number") {
        const currentBootTime = Date.now() - uptime * 1000;
        if (typeof window !== "undefined" && typeof window.sessionStorage !== "undefined") {
          const savedBootTime = window.sessionStorage.getItem("carbontracker_boot_time");
          window.sessionStorage.setItem("carbontracker_boot_time", String(currentBootTime));
          if (savedBootTime) {
            const diff = Math.abs(parseFloat(savedBootTime) - currentBootTime);
            if (diff > 10000) { // 10 seconds difference tolerance
              logger.warn("aiStore", "[DEBUG] Server restart detected! Logging out.");
              logoutRef.current();
              return true;
            }
          }
        }
      }
    } catch (err) {
      logger.warn("aiStore", "Failed to verify server boot time", err);
    }
    return false;
  }, []);

  const fetchSystemHealth = useCallback(async () => {
    if (isSystemHealthLoadingRef.current) {
      logger.info("aiStore", "fetchSystemHealth already in progress, skipping duplicate call");
      return;
    }
    isSystemHealthLoadingRef.current = true;
    try {
      const health = await api.getSystemHealth();
      setSystemHealth(health);
      
      // Check for server restart during health poll
      await checkServerRestart();
      
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
  }, [loadDashboardData, checkServerRestart]);

  const fetchAnalytics = useCallback(async () => {
    if (isAnalyticsLoadingRef.current) {
      logger.info("aiStore", "fetchAnalytics already in progress, skipping duplicate call");
      return;
    }
    isAnalyticsLoadingRef.current = true;
    setAnalyticsLoading(true);
    try {
      const data = await api.getAnalytics();
      setAnalyticsData(data ?? DEFAULT_ANALYTICS);
    } catch (err) {
      logger.error("aiStore", "fetchAnalytics failed", err);
      setAnalyticsData(DEFAULT_ANALYTICS);
      setToastError("Unable to load analytics dashboard data.");
    } finally {
      setAnalyticsLoading(false);
      isAnalyticsLoadingRef.current = false;
    }
  }, []);

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
      logger.info("aiStore", `[DEBUG] login → POST /auth/login for email: ${email}`);
      const tokenData = await api.login(email, password);
      if (tokenData && tokenData.access_token) {
        logger.info("aiStore", "[DEBUG] login → access_token received, saving to storage");
        saveToken(tokenData.access_token);
        // Save refresh token if provided by backend
        if (tokenData.refresh_token) {
          saveRefreshToken(tokenData.refresh_token);
          logger.info("aiStore", "[DEBUG] login → refresh_token saved");
        }
        saveLoginTimestamp();
        setToken(tokenData.access_token);
        setIsAuthenticated(true);
        // Load profile immediately after token is saved
        logger.info("aiStore", "[DEBUG] login → calling getProfile to hydrate user state");
        const profile = await api.getProfile();
        saveUser(profile);
        setUser(profile);
        logger.info("aiStore", `[DEBUG] login → profile loaded for: ${profile.username}`);
        return true;
      }
      logger.warn("aiStore", "[DEBUG] login → no access_token in tokenData response");
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
    logger.info("aiStore", "[DEBUG] logout → clearing token and user from storage");
    api.logout().catch((err) => {
      logger.warn("aiStore", "api.logout failed", err);
    });
    removeToken();
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

  // Keep logoutRef in sync so loadDashboardData can call logout without circular deps
  useEffect(() => {
    logoutRef.current = logout;
  }, [logout]);

  // Listen for ct:force-logout event dispatched by api.ts when refresh token is expired
  useEffect(() => {
    const handleForceLogout = () => {
      logger.warn("aiStore", "[DEBUG] ct:force-logout event received — clearing session");
      logout();
    };
    window.addEventListener("ct:force-logout", handleForceLogout);
    return () => window.removeEventListener("ct:force-logout", handleForceLogout);
  }, [logout]);

  // Subscribe to background health monitor events
  useEffect(() => {
    const handleHealth = (e: Event) => {
      const health = (e as CustomEvent).detail;
      if (health) setSystemHealth(health);
    };
    window.addEventListener("carbontracker:health", handleHealth);
    // Start the health monitor singleton
    healthMonitor.start();
    return () => {
      window.removeEventListener("carbontracker:health", handleHealth);
    };
  }, []);

  const updateProfile = useCallback(async (username: string, email: string): Promise<boolean> => {
    try {
      logger.info("aiStore", `[DEBUG] updateProfile → PUT /profile for user: ${username}`);
      const res = await api.updateProfile({ username, email });
      if (res?.success !== false) {
        const profile = await api.getProfile();
        saveUser(profile);
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

  // Centralized deterministic startup sequence
  const startup = useCallback(async () => {
    setLoading(true);
    setError(null);
    setStartupPhase("init");
    logger.info("aiStore", "[DEBUG] Executing centralized startup sequence");

    if (abortRef.current) {
      abortRef.current.abort();
    }
    const abortCtrl = new AbortController();
    abortRef.current = abortCtrl;
    const signal = abortCtrl.signal;

    // Clear client-side TTL caches on startup
    cache.clear();

    // Check if localhost server restarted
    const restarted = await checkServerRestart(signal);
    if (restarted) {
      setLoading(false);
      setStartupPhase("ready");
      return;
    }

    // 1. Initialize Authentication & Local JWT validation
    const savedToken = loadToken();
    const savedUser = loadUser<ReturnType<typeof JSON.parse>>();

    if (!savedToken) {
      logger.info("aiStore", "[DEBUG] startup → No token in storage → unauthenticated");
      setToken(null);
      setUser(null);
      setIsAuthenticated(false);
      setLoading(false);
      setStartupPhase("ready");
      return;
    }

    // Decode JWT token locally to verify expiration and structure integrity
    let isInvalidOrExpired = false;
    try {
      const parts = savedToken.split(".");
      if (parts.length === 3) {
        const payload = JSON.parse(atob(parts[1]));
        if (payload.exp && payload.exp * 1000 < Date.now()) {
          isInvalidOrExpired = true;
          logger.warn("aiStore", "[DEBUG] startup → Saved JWT token has expired locally.");
        } else {
          logger.info("aiStore", `[DEBUG] startup → JWT local check OK. Expires: ${new Date(payload.exp * 1000).toISOString()}`);
        }
      } else {
        isInvalidOrExpired = true;
        logger.warn("aiStore", "[DEBUG] startup → Invalid JWT format in localStorage.");
      }
    } catch (e) {
      isInvalidOrExpired = true;
      logger.warn("aiStore", "[DEBUG] startup → Failed to decode JWT.", e);
    }

    if (isInvalidOrExpired) {
      logger.warn("aiStore", "[DEBUG] startup → Token expired/corrupt locally → trying refresh token");
      setStartupPhase("validating");
      try {
        const newAccessToken = await api.refreshToken();
        if (newAccessToken) {
          logger.info("aiStore", "[DEBUG] startup → Refresh token success, got new access token");
          setToken(newAccessToken);
          setIsAuthenticated(true);
        } else {
          throw new Error("No new access token returned");
        }
      } catch (err) {
        logger.warn("aiStore", "[DEBUG] startup → Refresh token failed/absent → clearing session", err);
        removeToken();
        setToken(null);
        setUser(null);
        setIsAuthenticated(false);
        setLoading(false);
        setStartupPhase("ready");
        return;
      }
    }

    // Assign token to state before making any API calls
    setToken(savedToken);
    setIsAuthenticated(true);
    if (savedUser) {
      try {
        setUser(savedUser as any);
      } catch {
        // ignore
      }
    }

    // 3. Backend JWT validation — verify token is still accepted by the server
    setStartupPhase("validating");
    let currentProfile: ProfileResponse | null = null;
    try {
      logger.info("aiStore", "[DEBUG] startup → Verifying token with backend via GET /profile");
      currentProfile = await api.getProfile(signal);
      saveUser(currentProfile);
      setUser(currentProfile);
      logger.info("aiStore", `[DEBUG] startup → Backend JWT validation OK for user: ${currentProfile.username}`);
    } catch (err: any) {
      logger.error("aiStore", "[DEBUG] startup → Backend JWT token validation failed", err);
      const httpStatus = err instanceof ApiError ? err.status : null;
      const msg = err?.message || String(err);

      // AbortError: request was cancelled intentionally (React StrictMode double-mount,
      // component unmount cleanup, or manual abort). This is NOT a connectivity failure.
      // Silently ignore — the second mount will retry successfully.
      if (err?.name === "AbortError" || signal.aborted) {
        logger.info("aiStore", "[DEBUG] startup → Profile fetch was aborted (StrictMode/unmount) — ignoring");
        return;
      }

      // 401/403 — token rejected by backend: clear it and redirect to login
      const isAuthError =
        httpStatus === 401 ||
        httpStatus === 403 ||
        msg.includes("401") ||
        msg.includes("403") ||
        msg.toLowerCase().includes("credentials") ||
        msg.toLowerCase().includes("signature");

      if (isAuthError) {
        logger.warn("aiStore", "[DEBUG] startup → Auth error from backend → clearing token");
        removeToken();
        setToken(null);
        setUser(null);
        setIsAuthenticated(false);
        setLoading(false);
        return;
      }

      // HTTP error with a status code: backend IS reachable but returned an error.
      // Do NOT show "Unable to connect" — show the real server error message.
      if (httpStatus) {
        logger.warn("aiStore", `[DEBUG] startup → Profile fetch returned HTTP ${httpStatus} — backend reachable`);
        setError(`Backend returned an error (HTTP ${httpStatus}). Please try again.`);
        setLoading(false);
        return;
      }

      // No HTTP status: genuine network/timeout failure.
      logger.warn("aiStore", "[DEBUG] startup → Network/timeout error reaching backend");
      setError("Unable to connect to backend.");
      setLoading(false);
      return;
    }

    // 4. Fetch System Health & status
    try {
      logger.info("aiStore", "Loading system health status");
      const health = await api.getSystemHealth(signal);
      setSystemHealth(health);
      
      const currentDbStatus = health?.database || "online";
      if (health && !health.failed && (currentDbStatus === "offline" || currentDbStatus === "degraded")) {
        setError("Reconnecting to database...");
      }

      // Feature flags
      try {
        const flags = await api.getFeatureFlags(signal);
        setFeatureFlags(flags);
      } catch (flagErr) {
        logger.warn("aiStore", "Failed to fetch feature flags during startup", flagErr);
      }
    } catch (err) {
      logger.warn("aiStore", "Failed to check system health during startup", err);
    }

    // 5. Load Dashboard Summary
    try {
      logger.info("aiStore", `[DEBUG] startup → Loading dashboard summary (JWT in Authorization header)`);
      const summaryResult = await api.getDashboardSummary(signal);
      if (summaryResult) {
        setSummary(summaryResult);
        logger.info("aiStore", "[DEBUG] startup → getDashboardSummary SUCCESS");
      } else {
        logger.warn("aiStore", "getDashboardSummary returned null during startup, using safe empty defaults");
        setSummary(createEmptySummary());
      }
    } catch (err: any) {
      logger.error("aiStore", "[DEBUG] startup → Failed to load dashboard summary", err);
      const classified = classifyError(err);
      if (classified === "Session expired. Please login again.") {
        logoutRef.current();
        return;
      }
      logger.warn("aiStore", `Using fallback empty summary on startup due to: ${classified}`);
      setSummary(createEmptySummary());
      setToastError(`Dashboard summary unavailable: ${classified}`);
    }

    // 6. Deferred/Background loader of list data
    setStartupPhase("loading");
    try {
      api.getInsights(signal).then((res) => setInsights(res ?? [])).catch(() => {});
      api.getAchievements(signal).then((res) => setAchievements(res ?? [])).catch(() => {});
      api.getActivities(20, 0, signal).then((res) => setActivities(res ?? [])).catch(() => {});
      fetchChatHistory();
    } catch (err) {
      logger.warn("aiStore", "Failed loading background data during startup", err);
    }

    setLoading(false);
    setStartupPhase("ready");
  }, [fetchChatHistory, classifyError]);

  // Critical startup load on mount
  useEffect(() => {
    startup();
    return () => {
      if (abortRef.current) abortRef.current.abort();
    };
  }, [startup]);

  // Automatic retry on retryable errors (network/summary failure)
  useEffect(() => {
    if (error && error !== "Reconnecting to database..." && retryCount < 3) {
      const timer = setTimeout(() => {
        logger.info("aiStore", `Auto-retrying dashboard load (attempt ${retryCount + 1}/3)`);
        setRetryCount((prev) => prev + 1);
        loadDashboardData();
      }, 5000 * Math.pow(2, retryCount)); // 5s, 10s, 20s
      return () => clearTimeout(timer);
    }
  }, [error, retryCount, loadDashboardData]);

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
      smartDevicesEnabled,
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
      startupPhase,
    }),
    [
      summary, insights, insightsLoading, achievements, achievementsLoading,
      activities, activitiesLoading, region, loading, error,
      toastError, clearToastError, setToastError, loadDashboardData, logActivity,
      chatMessages, chatLoading, forecastData, forecastLoading, forecastStatus, metrics,
      metricsLoading, isRecording, transcript, fetchChatHistory,
      sendChatMessage, fetchForecast, fetchMetrics, uploadReceipt,
      submitCorrection, systemHealth, fetchSystemHealth, forecastEnabled, smartDevicesEnabled,
      analyticsData, analyticsLoading, fetchAnalytics,
      user, isAuthenticated, token, login, register, logout, updateProfile, activeUsername,
      startupPhase,
    ]
  );

  return (
    <AIContext.Provider value={contextValue}>
      {children}
    </AIContext.Provider>
  );
}
