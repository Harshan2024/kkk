import React, { createContext, useContext, useState, useEffect, useCallback } from "react";
import { api, ChatMessage, ForecastData, ObservabilityMetrics, Activity, DashboardSummary, AIInsight, Achievement } from "../services/api";

interface AIContextProps {
  // Centralized dashboard states
  summary: DashboardSummary | null;
  insights: AIInsight[];
  achievements: Achievement[];
  activities: Activity[];
  region: string;
  loading: boolean;
  error: string | null;
  setRegion: (r: string) => void;
  loadDashboardData: () => Promise<void>;
  logActivity: (text: string, region?: string) => Promise<void>;

  // Chat & AI states
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
  uploadReceipt: (file: File, region?: string) => Promise<any>;
  submitCorrection: (original: string, corrected: string, category?: string) => Promise<void>;
}

export const AIContext = createContext<AIContextProps | undefined>(undefined);

export function useAIStore() {
  const context = useContext(AIContext);
  if (!context) {
    throw new Error("useAIStore must be used within an AIStoreProvider");
  }
  return context;
}

export function AIStoreProvider({ children, username = "demo_user" }: { children: React.ReactNode; username?: string }) {
  // Dashboard hook states
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [insights, setInsights] = useState<AIInsight[]>([]);
  const [achievements, setAchievements] = useState<Achievement[]>([]);
  const [activities, setActivities] = useState<Activity[]>([]);
  const [region, setRegion] = useState("Global");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Chat/Voice/Forecast states
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [chatLoading, setChatLoading] = useState(false);
  const [forecastData, setForecastData] = useState<ForecastData[]>([]);
  const [forecastLoading, setForecastLoading] = useState(false);
  const [metrics, setMetrics] = useState<ObservabilityMetrics | null>(null);
  const [metricsLoading, setMetricsLoading] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [transcript, setTranscript] = useState("");

  const fetchWithRetry = async <T,>(fn: () => Promise<T>, retries = 3, delayMs = 600): Promise<T> => {
    for (let i = 1; i <= retries; i++) {
      try {
        return await fn();
      } catch (err) {
        if (i === retries) throw err;
        await new Promise((resolve) => setTimeout(resolve, delayMs));
      }
    }
    throw new Error("Failed after retries");
  };

  // Main loader for Dashboard layout
  const loadDashboardData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [summaryData, insightsData, achievementsData, historyData] = await Promise.all([
        fetchWithRetry(() => api.getDashboardSummary(username)),
        fetchWithRetry(() => api.getInsights(username)),
        fetchWithRetry(() => api.getAchievements(username)),
        fetchWithRetry(() => api.getActivities(username))
      ]);
      
      setSummary(summaryData);
      setInsights(insightsData);
      setAchievements(achievementsData);
      setActivities(historyData);
    } catch (err: any) {
      console.error("Dashboard data fetching failed:", err);
      try {
        const health = await api.checkHealth();
        if (health && health.database === "disconnected") {
          setError("FastAPI server is running, but database connection failed. Please check PostgreSQL status.");
        } else {
          setError("An error occurred while loading dashboard statistics. Please reset database.");
        }
      } catch {
        setError("Failed to connect to the CarbonTracker API server. Ensure backend is running on http://127.0.0.1:8000.");
      }
    } finally {
      setLoading(false);
    }
  }, [username]);

  // Silent Background Refresher to coordinate incremental state updates
  const silentDashboardRefresh = useCallback(async () => {
    try {
      const [summaryData, insightsData, achievementsData, historyData] = await Promise.all([
        api.getDashboardSummary(username),
        api.getInsights(username),
        api.getAchievements(username),
        api.getActivities(username)
      ]);
      setSummary(summaryData);
      setInsights(insightsData);
      setAchievements(achievementsData);
      setActivities(historyData);
    } catch (err) {
      console.error("Silent background refresh failed:", err);
    }
  }, [username]);

  // OPTIMISTIC LOGGING IMPLEMENTATION
  const logActivity = useCallback(async (text: string, activeRegion = "Global") => {
    if (!text.trim()) return;

    // 1. Immediately request the NLP parse preview (takes ~15ms) to build a realistic optimistic activity card
    let calculatedValue = 1.0;
    let category = "lifestyle";
    let item = "activity";
    let unit = "unit";
    let quantity = 1.0;
    let metadata = {};

    try {
      const preview = await api.parseActivity(text, activeRegion);
      if (preview && preview.success) {
        calculatedValue = preview.calculated_value;
        category = preview.parsed.category;
        item = preview.parsed.item;
        unit = preview.parsed.unit;
        quantity = preview.parsed.quantity;
        metadata = preview.metadata;
      }
    } catch (e) {
      console.warn("Optimistic preview parse failed, falling back to guess-based mapping", e);
    }

    // 2. Pre-generate optimistic activity log
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
      logged_at: new Date().toISOString()
    };

    // 3. Prepend optimistic activity locally
    setActivities((prev) => [optimisticAct, ...prev]);

    // 4. Update stats state instantly
    setSummary((prev) => {
      if (!prev) return null;
      
      const newTodayEmissions = prev.today_emissions + calculatedValue;
      const daily_budget = prev.daily_budget || 5.0;
      const newScore = Math.max(0, Math.min(100, 100 - (newTodayEmissions / daily_budget) * 50));
      
      // Update category breakdown totals
      const newBreakdown = prev.breakdown.map((b) => {
        if (b.category.toLowerCase() === category.toLowerCase()) {
          const total_carbon = b.total_carbon + calculatedValue;
          return { ...b, total_carbon };
        }
        return b;
      });

      // Update final trend array element
      const newTrends = [...prev.trends];
      if (newTrends.length > 0) {
        const lastTrend = { ...newTrends[newTrends.length - 1] };
        lastTrend.emissions = lastTrend.emissions + calculatedValue;
        lastTrend.score = newScore;
        newTrends[newTrends.length - 1] = lastTrend;
      }

      return {
        ...prev,
        today_emissions: newTodayEmissions,
        weekly_emissions: prev.weekly_emissions + calculatedValue,
        current_score: newScore,
        trends: newTrends,
        breakdown: newBreakdown
      };
    });

    // 5. Process the DB write asynchronously on backend
    try {
      const realActivity = await api.logActivity(text, username, activeRegion);
      
      // Swap optimistic card with real db record (contains correct database ID)
      setActivities((prev) =>
        prev.map((act) => (act.id === optimisticId ? realActivity : act))
      );
      
      // 6. Refresh summary and insights in background without page reload blocks
      silentDashboardRefresh();
    } catch (err: any) {
      console.error("Background persistence logging failed:", err);
      // Remove optimistic log if backend write error
      setActivities((prev) => prev.filter((act) => act.id !== optimisticId));
      silentDashboardRefresh();
      alert(err.message || "Failed to save activity to database!");
    }
  }, [username, silentDashboardRefresh]);

  const fetchChatHistory = useCallback(async () => {
    setChatLoading(true);
    try {
      const history = await api.getChatHistory(username);
      setChatMessages(history);
    } catch (err) {
      console.error("Failed to fetch chat history:", err);
    } finally {
      setChatLoading(false);
    }
  }, [username]);

  const sendChatMessage = useCallback(async (message: string): Promise<string> => {
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
      const result = await api.postChat(message, username);
      const assistantMsg: ChatMessage = {
        id: Date.now() + 1,
        role: "assistant",
        content: result.response,
        created_at: new Date().toISOString(),
      };
      setChatMessages((prev) => [...prev, assistantMsg]);
      
      fetchMetrics();
      // Silently refresh dashboard stats as conversation might have logged things/identified habits
      silentDashboardRefresh();
      
      return result.response;
    } catch (err) {
      console.error("Failed to send chat message:", err);
      const errorMsg: ChatMessage = {
        id: Date.now() + 1,
        role: "assistant",
        content: "Sorry, I encountered an issue parsing your query. Please try again.",
        created_at: new Date().toISOString(),
      };
      setChatMessages((prev) => [...prev, errorMsg]);
      return "";
    } finally {
      setChatLoading(false);
    }
  }, [username, silentDashboardRefresh]);

  const fetchForecast = useCallback(async (model = "prophet", steps = 30) => {
    setForecastLoading(true);
    try {
      const data = await api.getForecast(username, steps, model);
      setForecastData(data);
    } catch (err) {
      console.error("Failed to fetch forecast:", err);
    } finally {
      setForecastLoading(false);
    }
  }, [username]);

  const fetchMetrics = useCallback(async () => {
    setMetricsLoading(true);
    try {
      const data = await api.getObservabilityMetrics(username);
      setMetrics(data);
    } catch (err) {
      console.error("Failed to fetch observability metrics:", err);
    } finally {
      setMetricsLoading(false);
    }
  }, [username]);

  const uploadReceipt = useCallback(async (file: File, activeRegion = "Global") => {
    try {
      const res = await api.uploadMultimodal(file, username, activeRegion);
      // Silently sync dashboard activities and insights scanned from receipt
      silentDashboardRefresh();
      fetchMetrics();
      return res;
    } catch (err) {
      console.error("Failed to upload receipt:", err);
      throw err;
    }
  }, [username, silentDashboardRefresh]);

  const submitCorrection = useCallback(async (original: string, corrected: string, category = "nlp_parse") => {
    try {
      await api.correctActivity(original, corrected, category, username);
      fetchMetrics();
    } catch (err) {
      console.error("Failed to submit correction:", err);
    }
  }, [username]);

  // Initial load
  useEffect(() => {
    loadDashboardData();
    fetchChatHistory();
    fetchMetrics();
    fetchForecast();
  }, [loadDashboardData, fetchChatHistory, fetchMetrics, fetchForecast]);

  return (
    <AIContext.Provider
      value={{
        summary,
        insights,
        achievements,
        activities,
        region,
        setRegion,
        loading,
        error,
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
      }}
    >
      {children}
    </AIContext.Provider>
  );
}
