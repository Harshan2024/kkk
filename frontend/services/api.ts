/**
 * api.ts — CarbonTracker Frontend API Service
 * =============================================
 * LOCKED: Core API client. Do not modify without team review.
 *
 * All requests include:
 * - 15-second AbortController timeout
 * - Structured ApiResponse<T> envelope
 * - Per-endpoint typed return values
 * - Graceful degradation on failure (never throws unless caller opts in)
 */

import logger from "../utils/logger";
import {
  getAuthorizationHeader,
  saveToken,
  saveRefreshToken,
  loadRefreshToken,
} from "./authService";
import { cache, CACHE_KEYS, CACHE_TTL } from "./cache";
import {
  sanitizeSummary,
  sanitizeInsights,
  sanitizeActivities,
  sanitizeAchievements,
  sanitizeForecast,
  sanitizeChatMessages,
} from "../utils/validators";

const HOST = process.env.NEXT_PUBLIC_API_URL || "https://kkk-harshan-sona.onrender.com";
const BASE_URL = HOST.endsWith("/api/v1") ? HOST : `${HOST}/api/v1`;

const DEFAULT_TIMEOUT_MS = 15_000;

// ─────────────────────────────────────────────────────────────────────────────
// TOKEN REFRESH — queue-guarded, singleton in-flight
// ─────────────────────────────────────────────────────────────────────────────

/** True while a refresh call is in-flight. Prevents storm of concurrent refreshes. */
let _isRefreshing = false;
/** Callbacks waiting on the in-flight refresh to resolve. */
let _refreshQueue: Array<(token: string | null) => void> = [];

/**
 * refreshAccessToken — exchanges the stored refresh token for a new access+refresh pair.
 *
 * Queue pattern:
 *  - First caller fires the real POST /auth/refresh request.
 *  - All subsequent 401s that arrive while refresh is in-flight queue up.
 *  - When refresh resolves, ALL queued callers get the new token simultaneously.
 *  - If refresh fails (expired / revoked), all queued callers receive null →
 *    the global "ct:force-logout" event is dispatched so aiStore can clear state.
 *
 * Returns the new access token on success, null on failure.
 */
async function refreshAccessToken(): Promise<string | null> {
  if (_isRefreshing) {
    // Another refresh is already running — queue this caller
    return new Promise((resolve) => {
      _refreshQueue.push(resolve);
    });
  }

  const refreshToken = loadRefreshToken();
  if (!refreshToken) {
    logger.warn("ApiService", "refreshAccessToken: no refresh token in storage → force logout");
    window.dispatchEvent(new CustomEvent("ct:force-logout"));
    return null;
  }

  _isRefreshing = true;
  try {
    const response = await fetch(`${HOST}/api/v1/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken }),
      signal: AbortSignal.timeout(15_000),
    });

    if (!response.ok) {
      logger.warn("ApiService", `refreshAccessToken: backend returned ${response.status} → force logout`);
      _refreshQueue.forEach((cb) => cb(null));
      _refreshQueue = [];
      window.dispatchEvent(new CustomEvent("ct:force-logout"));
      return null;
    }

    const data = await response.json();
    const newAccessToken: string = data.access_token;
    const newRefreshToken: string | undefined = data.refresh_token;

    saveToken(newAccessToken);
    if (newRefreshToken) saveRefreshToken(newRefreshToken);

    logger.info("ApiService", "refreshAccessToken: token pair rotated successfully");
    _refreshQueue.forEach((cb) => cb(newAccessToken));
    _refreshQueue = [];
    return newAccessToken;
  } catch (err) {
    logger.error("ApiService", "refreshAccessToken: network error during refresh", { error: err });
    _refreshQueue.forEach((cb) => cb(null));
    _refreshQueue = [];
    window.dispatchEvent(new CustomEvent("ct:force-logout"));
    return null;
  } finally {
    _isRefreshing = false;
  }
}


// ─────────────────────────────────────────────────────────────────────────────
// TYPE DEFINITIONS
// ─────────────────────────────────────────────────────────────────────────────

export interface ActivityMetadata {
  calculation_type?: string;
  recipe_name?: string;
  ingredients?: Record<string, { weight_kg: number; factor: number; emissions_kg: number }>;
  estimated_weight_kg?: number;
  distance_km?: number;
  vehicle_mapped?: string;
  appliance_mapped?: string;
  appliance_watts?: number;
  duration_hours?: number;
  total_kwh?: number;
  grid_emission_factor?: number;
  item_mapped?: string;
  quantity_input?: number;
  unit_input?: string;
  quantity_calculated?: number;
  unit_calculated?: string;
  emission_factor?: number;
  source?: string;
  region_applied?: string;
  error?: string;
  fallback?: boolean;
}

export interface Activity {
  id: number;
  input_text: string;
  category?: string | null;
  item: string;
  quantity: number;
  unit: string;
  calculated_value: number;
  metadata: ActivityMetadata;
  region: string;
  logged_at: string;
}

export interface CategoryBreakdown {
  category: string;
  total_carbon: number;
  count: number;
  percentage: number;
}

export interface TrendData {
  date: string;
  date_full: string;
  emissions: number;
  score: number;
}

export interface DashboardSummary {
  today_emissions: number;
  yesterday_emissions: number;
  weekly_emissions: number;
  current_score: number;
  avg_weekly_score: number;
  daily_budget: number;
  breakdown: CategoryBreakdown[];
  trends: TrendData[];
  achievements_count: number;
  habit_cards?: unknown[];
  xp?: number;
  level?: number;
  level_name?: string;
  progress_pct?: number;
  streaks?: {
    current_streak: number;
    longest_streak: number;
    carbon_streak: number;
    score_streak: number;
    monthly_performance: number[];
  };
  quests?: {
    id: string;
    name: string;
    description: string;
    progress: number;
    max: number;
    xp: number;
    icon: string;
    color: string;
  }[];
  ai_dashboard?: {
    top_emission_source: string;
    weekly_trend: string;
    behavior_change: string;
    predicted_monthly_emissions: number;
    biggest_improvement_area: string;
    personalized_sustainability_summary: string;
  };
  insight_feed?: {
    text: string;
    timestamp: string;
    type: string;
  }[];
}

export interface AIInsight {
  id: number;
  content: string;
  category?: string | null;
  impact_estimate: string;
  impact_level: string;
  impact_value: number;
  feasibility?: string;
  difficulty?: string;
  confidence_score?: number;
  sustainability_gain?: number;
  why_explanation?: string | null;
  how_calculation?: string | null;
  weighted_priority_score?: number;
  created_at: string;
}

export interface Achievement {
  id: number;
  name: string;
  description: string;
  badge_type: string;
  unlocked_at: string;
}

export interface ParseResult {
  success: boolean;
  parsed: {
    category: string;
    item: string;
    quantity: number;
    unit: string;
    confidence: number;
    suggestions: string[];
    original_text: string;
  };
  calculated_value: number;
  metadata: ActivityMetadata;
  parts?: {
    parsed: {
      category: string;
      item: string;
      quantity: number;
      unit: string;
      confidence: number;
      suggestions: string[];
      original_text: string;
    };
    calculated_value: number;
    metadata: ActivityMetadata;
  }[];
}

export interface ChatMessage {
  id: number;
  role: string;
  content: string;
  created_at: string;
  context_tags?: string[];
}

export interface ForecastData {
  date: string;
  label: string;
  expected: number;
  optimistic: number;
  pessimistic: number;
}

export interface ObservabilityMetrics {
  total_user_corrections: number;
  avg_latencies?: Record<string, number>;
  avg_nlp_confidence?: number;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface ProfileResponse {
  username: string;
  email: string;
  xp: number;
  level: number;
  achievements: string[];
  sustainability_score: number;
  joined_date: string;
}

export interface HealthStatus {
  backend: string;
  mode?: string;
  database: string;
  statistics_api?: string;
  status?: string;
}

export interface SystemHealth {
  backend: string;
  database: string;
  ai: string;
  ocr: string;
  cache: string;
  iot: string;
  failed?: boolean;
}

/**
 * ApiError — typed HTTP error that carries the numeric HTTP status.
 * Use this instead of parsing error message strings to detect 401/403/404/500.
 */
export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

export interface HistoryItem {
  name: string;
  category: string;
  quantity: number;
  unit: string;
  factor: number;
  carbon: number;
  formula?: string;
  subtotal?: number;
}

export interface HistoryRecord {
  id: string;
  timestamp: string;
  activities: HistoryItem[];
  categories: string[];
  total_carbon: number;
  source: string;
}

export interface HistoryStats {
  total_activities: number;
  total_carbon: number;
  average_carbon: number;
  most_frequent_activity: string;
  highest_carbon_activity: string;
  lowest_carbon_activity: string;
}

export interface DayPlan {
  day: number;
  task: string;
}

export interface ActionPlan {
  plan: DayPlan[];
}

export interface HabitPattern {
  pattern: string;
  confidence: number;
  category: string;
}

export interface EnergyHabit {
  finding: string;
  ac_hours: number;
  ac_percentage: number;
}

export interface FoodHabit {
  finding: string;
  food_profile: string;
  veg_ratio: number;
  animal_ratio: number;
}

export interface TransportHabit {
  finding: string;
  transport_profile: string;
  public_transport_ratio: number;
}

export interface WasteHabit {
  finding: string;
  waste_profile: string;
  recycling_frequency: number;
}

export interface HabitAnalysis {
  patterns: HabitPattern[];
  energy: EnergyHabit;
  food: FoodHabit;
  transport: TransportHabit;
  waste: WasteHabit;
}

export interface CoachWeeklyReport {
  weekly_carbon: number;
  top_source: string;
  potential_reduction: number;
  summary: string;
}

export interface CoachMonthlyReport {
  monthly_carbon: number;
  category_ranking: { category: string; carbon: number }[];
  behavior_changes: string[];
  achievements: string[];
  recommendations: string[];
}

export interface ChallengeProgress {
  id: string;
  name: string;
  description: string;
  xp: number;
  progress: number;
  max: number;
  completed: boolean;
  icon: string;
  color: string;
}

export interface AchievementStatus {
  id: string;
  name: string;
  description: string;
  badge_type: string;
  unlocked: boolean;
  unlocked_at?: string;
  progress: number;
}

export interface VirtualReward {
  id: string;
  name: string;
  description: string;
  cost: number;
  redeemed: boolean;
  icon: string;
}

export interface GamificationProfile {
  username: string;
  xp: number;
  level: number;
  streak: number;
  sustainability_score: number;
  available_xp: number;
  total_xp: number;
  xp_needed_for_next_level: number;
  xp_in_current_level: number;
  level_progress_pct: number;
  redeemed_rewards: string[];
}


export interface DailySummary {
  date: string;
  activities: number;
  total_carbon: number;
  average: number;
  highest_activity: string;
  highest_carbon: number;
  trend_value: number;
  trend_status: string;
}

export interface WeeklySummary {
  weekly_total: number;
  daily_average: number;
  highest_day: string;
  highest_emission: number;
  trend_value: number;
  trend_status: string;
}

export interface MonthlySummary {
  monthly_total: number;
  daily_average: number;
  trend_value: number;
  trend_status: string;
}

export interface AnalyticsPayload {
  daily: DailySummary;
  weekly: WeeklySummary;
  monthly: MonthlySummary;
  category_breakdown: Record<string, number>;
  rankings: {
    top_sources: { activity: string; carbon: number }[];
    bottom_sources: { activity: string; carbon: number }[];
    most_frequent: { activity: string; count: number }[];
  };
  sustainability: {
    score: number;
    grade: string;
  };
  recommendations: string[];

  // Extensions to support alternative structures and hotfix keys
  daily_summary: {
    total_carbon: number;
    activities: number;
    average: number;
  };
  weekly_summary: {
    weekly_total: number;
  };
  monthly_summary: {
    monthly_total: number;
  };
  sustainability_score: {
    score: number;
    grade: string;
  };
  trend: {
    status: string;
  };
  total_carbon: number;
}

// ─────────────────────────────────────────────────────────────────────────────
// INTERNAL FETCH HELPER
// ─────────────────────────────────────────────────────────────────────────────

/** Internal — makes a fetch with AbortController timeout + duration logging. */
async function fetchWithTimeout(
  url: string,
  options: RequestInit = {},
  timeoutMs = DEFAULT_TIMEOUT_MS
): Promise<Response> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  if (options.signal) {
    if (options.signal.aborted) {
      controller.abort();
    } else {
      options.signal.addEventListener("abort", () => controller.abort());
    }
  }
  const startTime = performance.now();

  const isHealthCheck = url.endsWith("/health") || url.endsWith("/api/system/status");
  const endpoint = url.replace(/^https?:\/\/[^/]+/, "");

  // Debug: log every outgoing request (visible in browser DevTools console)
  if (process.env.NODE_ENV !== "production" && !isHealthCheck) {
    console.log(`[CarbonTracker API] Calling: ${options.method || "GET"} ${url}`);
  }

  try {
    const response = await fetch(url, { ...options, signal: controller.signal });
    clearTimeout(timer);
    const duration = Math.round(performance.now() - startTime);
    if (!isHealthCheck) {
      logger.info(
        "API",
        `[${options.method || "GET"}] ${endpoint} — ${response.status} — ${duration}ms`
      );
      if (process.env.NODE_ENV !== "production") {
        console.log(`[CarbonTracker API] Response: ${response.status} ${url} (${duration}ms)`);
      }
    }
    return response;
  } catch (err: unknown) {
    clearTimeout(timer);
    const duration = Math.round(performance.now() - startTime);
    if (err instanceof Error && err.name === "AbortError") {
      logger.warn("API", `[TIMEOUT] ${endpoint} — aborted after ${duration}ms (limit: ${timeoutMs}ms)`);
      // Production-safe timeout message — no localhost or port references
      throw new Error(`Connection timed out after ${timeoutMs / 1000}s. The backend may be starting up — please try again in a moment.`);
    }
    logger.error("API", `[FAIL] ${endpoint} — network error after ${duration}ms`, err);
    // Production-safe network error — never expose internal URLs or dev commands
    throw new Error("Backend server unavailable. Please check your connection and try again.");
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// RETRY HELPER — exponential backoff, network errors only
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Retries a fetch fn with exponential backoff.
 * Only retries on network/timeout errors, NOT on 4xx HTTP errors.
 * max retries = 2, delays: 1s → 2s
 */
async function withRetry<T>(
  fn: () => Promise<T>,
  endpoint: string,
  url: string,
  method: string,
  maxRetries = 2
): Promise<T> {
  let lastErr: unknown;
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    const attemptStart = performance.now();
    try {
      return await fn();
    } catch (err: unknown) {
      lastErr = err;
      const duration = Math.round(performance.now() - attemptStart);
      const msg = err instanceof Error ? err.message : "Unknown error";
      // Don't retry: validation/auth/bad-request errors
      const isHttp4xx = /HTTP 4\d\d/.test(msg);
      if (isHttp4xx || attempt === maxRetries) break;
      const delayMs = 1000 * Math.pow(2, attempt); // 1s, then 2s

      console.warn(
        `[RETRY WARNING] Attempt ${attempt + 1}/${maxRetries} failed.\n` +
        `- URL: ${url}\n` +
        `- Method: ${method}\n` +
        `- Duration: ${duration}ms\n` +
        `- Failure Reason: ${msg}\n` +
        `Retrying in ${delayMs}ms...`
      );

      logger.warn(
        "API",
        `[RETRY ${attempt + 1}/${maxRetries}] ${endpoint} failed after ${duration}ms (Reason: ${msg}) — retrying in ${delayMs}ms`
      );
      await new Promise((r) => setTimeout(r, delayMs));
    }
  }
  throw lastErr;
}

// ─────────────────────────────────────────────────────────────────────────────
// DEFAULT ANALYTICS FALLBACKS & NORMALIZERS
// ─────────────────────────────────────────────────────────────────────────────

export const DEFAULT_ANALYTICS: AnalyticsPayload = {
  daily: {
    date: "today",
    activities: 0,
    total_carbon: 0,
    average: 0,
    highest_activity: "",
    highest_carbon: 0,
    trend_value: 0,
    trend_status: "stable"
  },
  weekly: {
    weekly_total: 0,
    daily_average: 0,
    highest_day: "N/A",
    highest_emission: 0,
    trend_value: 0,
    trend_status: "stable"
  },
  monthly: {
    monthly_total: 0,
    daily_average: 0,
    trend_value: 0,
    trend_status: "stable"
  },
  category_breakdown: {
    transport: 0,
    food: 0,
    energy: 0,
    waste: 0
  },
  rankings: {
    top_sources: [],
    bottom_sources: [],
    most_frequent: []
  },
  sustainability: {
    score: 0,
    grade: "N/A"
  },

  // Requested format
  daily_summary: {
    total_carbon: 0,
    activities: 0,
    average: 0
  },
  weekly_summary: {
    weekly_total: 0
  },
  monthly_summary: {
    monthly_total: 0
  },
  sustainability_score: {
    score: 0,
    grade: "N/A"
  },
  recommendations: [],
  trend: {
    status: "stable"
  },
  total_carbon: 0
};

export function normalizeAnalytics(data: any): AnalyticsPayload {
  if (!data || typeof data !== "object") {
    return DEFAULT_ANALYTICS;
  }
  
  const daily = data.daily || {};
  const weekly = data.weekly || {};
  const monthly = data.monthly || {};
  const category_breakdown = data.category_breakdown || {};
  const rankings = data.rankings || {};
  const sustainability = data.sustainability || {};
  const recommendations = data.recommendations || [];

  return {
    ...DEFAULT_ANALYTICS,
    ...data,
    daily: {
      ...DEFAULT_ANALYTICS.daily,
      ...daily
    },
    weekly: {
      ...DEFAULT_ANALYTICS.weekly,
      ...weekly
    },
    monthly: {
      ...DEFAULT_ANALYTICS.monthly,
      ...monthly
    },
    category_breakdown: {
      ...DEFAULT_ANALYTICS.category_breakdown,
      ...category_breakdown
    },
    rankings: {
      ...DEFAULT_ANALYTICS.rankings,
      ...rankings
    },
    sustainability: {
      ...DEFAULT_ANALYTICS.sustainability,
      ...sustainability
    },
    recommendations: Array.isArray(recommendations) ? recommendations : [],
    
    // Map to requested keys for double safety
    daily_summary: {
      total_carbon: typeof daily.total_carbon === "number" ? daily.total_carbon : 0,
      activities: typeof daily.activities === "number" ? daily.activities : 0,
      average: typeof daily.average === "number" ? daily.average : 0
    },
    weekly_summary: {
      weekly_total: typeof weekly.weekly_total === "number" ? weekly.weekly_total : 0
    },
    monthly_summary: {
      monthly_total: typeof monthly.monthly_total === "number" ? monthly.monthly_total : 0
    },
    sustainability_score: {
      score: typeof sustainability.score === "number" ? sustainability.score : 0,
      grade: sustainability.grade || "N/A"
    },
    trend: {
      status: daily.trend_status || weekly.trend_status || monthly.trend_status || "stable"
    },
    total_carbon: typeof daily.total_carbon === "number" ? daily.total_carbon : 0
  };
}

// ─────────────────────────────────────────────────────────────────────────────
// API SERVICE CLASS
// ─────────────────────────────────────────────────────────────────────────────

class ApiService {
  /**
   * Core request method — includes:
   * - AbortController timeout (default 15s, configurable per endpoint)
   * - Exponential backoff retry for GET requests (max 2 retries: 1s → 2s)
   * - Duration logging via fetchWithTimeout
   * - Envelope unwrapping for { success, data, error }
   * - No retry on 4xx (bad request, auth, validation errors)
   */
  private async request<T>(
    endpoint: string,
    options: RequestInit = {},
    timeoutMs = DEFAULT_TIMEOUT_MS,
    retries = 2
  ): Promise<T> {
    const url = `${BASE_URL}${endpoint}`;

    const headers = new Headers(options.headers || {});
    if (options.body && !headers.has("Content-Type") && !(options.body instanceof FormData)) {
      headers.set("Content-Type", "application/json");
    }
    const authHeader = getAuthorizationHeader();
    if (authHeader) {
      headers.set("Authorization", authHeader);
    }

    const doFetch = async (isRetryAfterRefresh = false): Promise<T> => {
      let response: Response;
      try {
        // Always read the current token so post-refresh retries use the new one
        const currentAuthHeader = getAuthorizationHeader();
        if (currentAuthHeader) {
          headers.set("Authorization", currentAuthHeader);
        }
        response = await fetchWithTimeout(url, { ...options, headers }, timeoutMs);
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : "Network error";
        throw new Error(msg);
      }

      if (!response.ok) {
        // ── Auto token refresh on 401 ────────────────────────────────────────
        // Only attempt refresh once (isRetryAfterRefresh guard prevents loops)
        if (response.status === 401 && !isRetryAfterRefresh) {
          const newToken = await refreshAccessToken();
          if (newToken) {
            logger.info("ApiService", `Auto-refreshed token, retrying: ${endpoint}`);
            return doFetch(true); // retry with new token, no further refresh
          }
          // Refresh failed → force logout was already dispatched
          throw new ApiError(401, "Session expired. Please log in again.");
        }
        // ── Other HTTP errors ────────────────────────────────────────────────
        const errorText = await response.text().catch(() => "");
        let errorDetail = "";
        try {
          const errJson = JSON.parse(errorText);
          errorDetail = errJson.detail || errJson.error || "";
        } catch {
          errorDetail = errorText || "";
        }
        const finalMsg = errorDetail ? `HTTP ${response.status}: ${errorDetail}` : `HTTP ${response.status}`;
        throw new ApiError(response.status, finalMsg);
      }

      let result: unknown;
      try {
        result = await response.json();
      } catch {
        throw new Error("Invalid JSON response from server");
      }

      // Unwrap the { success, data, error } envelope
      if (result && typeof result === "object" && "success" in result && "data" in result) {
        const envelope = result as { success: boolean; data: unknown; error?: string };
        if (!envelope.success) {
          const errMsg = envelope.error || "API returned success=false";
          logger.warn("ApiService", `API success=false at ${endpoint}`, { error: errMsg });
          throw new Error(errMsg);
        }
        return envelope.data as T;
      }

      return result as T;
    };


    // Only retry safe idempotent GET requests
    const method = (options.method || "GET").toUpperCase();
    const shouldRetry = method === "GET" && retries > 0;
    return shouldRetry ? withRetry(doFetch, endpoint, url, method, retries) : doFetch();
  }

  // ─────────────────────────────────────────────────────────────────────────
  // ACTIVITY ENDPOINTS
  // ─────────────────────────────────────────────────────────────────────────

  async parseActivity(text: string, region = "Global"): Promise<ParseResult> {
    return this.request<ParseResult>(
      `/activities/parse?text=${encodeURIComponent(text)}&region=${encodeURIComponent(region)}`
    );
  }

  async logActivity(text: string, region = "Global"): Promise<Activity> {
    const res = await this.request<Activity>("/activities", {
      method: "POST",
      body: JSON.stringify({ text, region }),
    });
    // Invalidate dashboard summary and analytics cache on activity change
    cache.invalidate(CACHE_KEYS.DASHBOARD_SUMMARY);
    cache.invalidate(CACHE_KEYS.ANALYTICS);
    return res;
  }

  async getActivities(limit = 20, offset = 0, signal?: AbortSignal): Promise<Activity[]> {
    const raw = await this.request<unknown>(
      `/activities?limit=${limit}&offset=${offset}`,
      { signal }
    );
    return sanitizeActivities(raw);
  }

  // ─────────────────────────────────────────────────────────────────────────
  // DASHBOARD ENDPOINTS
  // ─────────────────────────────────────────────────────────────────────────

  async getDashboardSummary(signal?: AbortSignal): Promise<DashboardSummary> {
    const cached = cache.get<DashboardSummary>(CACHE_KEYS.DASHBOARD_SUMMARY);
    if (cached) return cached;

    const raw = await this.request<any>(`/dashboard/summary`, { signal });
    let summaryData: DashboardSummary;
    if (raw && typeof raw === "object") {
      if (raw.success === false) {
        throw new Error(raw.error || "Failed to retrieve dashboard summary");
      }
      if ("summary" in raw) {
        summaryData = sanitizeSummary(raw.summary);
      } else {
        summaryData = sanitizeSummary(raw);
      }
    } else {
      summaryData = sanitizeSummary(raw);
    }

    cache.set(CACHE_KEYS.DASHBOARD_SUMMARY, summaryData, CACHE_TTL.DASHBOARD_SUMMARY);
    return summaryData;
  }

  async getInsights(signal?: AbortSignal): Promise<AIInsight[]> {
    const cached = cache.get<AIInsight[]>(CACHE_KEYS.INSIGHTS);
    if (cached) return cached;

    const raw = await this.request<unknown>(`/insights`, { signal });
    const data = sanitizeInsights(raw);
    cache.set(CACHE_KEYS.INSIGHTS, data, CACHE_TTL.INSIGHTS);
    return data;
  }

  async getAchievements(signal?: AbortSignal): Promise<Achievement[]> {
    const cached = cache.get<Achievement[]>(CACHE_KEYS.ACHIEVEMENTS);
    if (cached) return cached;

    const raw = await this.request<unknown>(`/achievements`, { signal });
    const data = sanitizeAchievements(raw);
    cache.set(CACHE_KEYS.ACHIEVEMENTS, data, CACHE_TTL.ACHIEVEMENTS);
    return data;
  }

  // ─────────────────────────────────────────────────────────────────────────
  // CHAT ENDPOINTS
  // ─────────────────────────────────────────────────────────────────────────

  async postChat(
    message: string,
    timeoutMs = 30_000
  ): Promise<{ response: string }> {
    return this.request<{ response: string }>(
      "/chat",
      { method: "POST", body: JSON.stringify({ message }) },
      timeoutMs
    );
  }

  async getChatHistory(): Promise<ChatMessage[]> {
    const raw = await this.request<unknown>(`/chat/history`);
    return sanitizeChatMessages(raw);
  }

  // ─────────────────────────────────────────────────────────────────────────
  // ANALYTICS & OBSERVABILITY
  // ─────────────────────────────────────────────────────────────────────────

  async getForecast(
    steps = 30,
    model = "prophet",
    generate = false
  ): Promise<{ status?: string; message?: string; data: ForecastData[] }> {
    const raw = await this.request<any>(
      `/analytics/forecast?steps=${steps}&model=${model}&generate=${generate}`
    );
    if (raw && typeof raw === "object" && raw.status === "pending") {
      return { status: "pending", message: raw.message, data: [] };
    }
    return { data: sanitizeForecast(raw) };
  }

  async getObservabilityMetrics(): Promise<ObservabilityMetrics> {
    return this.request<ObservabilityMetrics>(`/observability/metrics`);
  }

  async getHabitAnalysis(): Promise<any> {
    return this.request<any>(`/habit-analysis`);
  }

  async getAnalytics(): Promise<AnalyticsPayload> {
    const cached = cache.get<AnalyticsPayload>(CACHE_KEYS.ANALYTICS);
    if (cached) return cached;

    try {
      const data = await this.request<any>(`/analytics`);
      const normalized = normalizeAnalytics(data);
      cache.set(CACHE_KEYS.ANALYTICS, normalized, CACHE_TTL.ANALYTICS);
      return normalized;
    } catch (err) {
      logger.warn("ApiService", "getAnalytics failed, returning DEFAULT_ANALYTICS", err);
      return DEFAULT_ANALYTICS;
    }
  }

  async correctActivity(
    original_text: string,
    corrected_text: string,
    category = "nlp_parse"
  ): Promise<unknown> {
    return this.request<unknown>("/activities/correct", {
      method: "POST",
      body: JSON.stringify({ original_text, corrected_text, category }),
    });
  }

  // ─────────────────────────────────────────────────────────────────────────
  // MULTIMODAL UPLOAD
  // ─────────────────────────────────────────────────────────────────────────

  async uploadMultimodal(
    file: File,
    region = "Global"
  ): Promise<unknown> {
    const formData = new FormData();
    formData.append("file", file);

    const headers = new Headers();
    const authHeader = getAuthorizationHeader();
    if (authHeader) {
      headers.set("Authorization", authHeader);
    }

    const url = `${BASE_URL}/activities/upload-multimodal?region=${encodeURIComponent(region)}`;

    let response: Response;
    try {
      response = await fetchWithTimeout(url, { method: "POST", body: formData, headers }, 60_000);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Upload failed";
      logger.error("ApiService", "Multimodal upload network error", { error: msg });
      throw new Error(msg);
    }

    if (!response.ok) {
      const errorText = await response.text().catch(() => "");
      throw new Error(errorText || "File upload failed");
    }

    const result = await response.json().catch(() => ({}));
    if (result && typeof result === "object" && "success" in result) {
      const env = result as { success: boolean; data: unknown; error?: string };
      if (!env.success) throw new Error(env.error || "Upload failed");
      return env.data;
    }
    return result;
  }

  // ─────────────────────────────────────────────────────────────────────────
  // DATABASE SEED
  // ─────────────────────────────────────────────────────────────────────────

  async seedDatabase(
    username = "demo_user",
    confirm = false
  ): Promise<{ success: boolean; data?: { status: string; message: string }; error?: string }> {
    const url = `${BASE_URL}/seed?username=${username}${confirm ? "&confirm=true" : ""}`;
    let response: Response;
    try {
      response = await fetchWithTimeout(url, { method: "POST" }, 60_000);
    } catch (err: unknown) {
      // Genuine network timeout/failure -> throw exception
      throw err;
    }

    if (response.status === 500) {
      // Genuine 500 system failure -> throw exception
      throw new Error("Internal server error during database seed.");
    }

    let result: any;
    try {
      result = await response.json();
    } catch {
      // Invalid response -> throw exception
      throw new Error("Invalid response format from server");
    }

    // Handle 403 Forbidden or expected safety warnings without throwing exceptions
    if (!response.ok) {
      const errorMsg = result.detail || result.error || `HTTP error ${response.status}`;
      return { success: false, error: errorMsg };
    }

    if (result && typeof result === "object" && "success" in result) {
      return {
        success: result.success,
        data: result.data,
        error: result.error,
      };
    }

    return { success: true, data: result };
  }

  // ─────────────────────────────────────────────────────────────────────────
  // HEALTH CHECKS
  // ─────────────────────────────────────────────────────────────────────────

  // ─────────────────────────────────────────────────────────────────────────
  // HISTORY DATA LAYER ENDPOINTS (Phase E.5)
  // ─────────────────────────────────────────────────────────────────────────

  async getHistoryList(params: {
    query?: string;
    category?: string;
    start_date?: string;
    end_date?: string;
    carbon_level?: string;
    sort_by?: string;
  } = {}, signal?: AbortSignal): Promise<HistoryRecord[]> {
    const queryParams = new URLSearchParams();
    if (params.query) queryParams.append("query", params.query);
    if (params.category) queryParams.append("category", params.category);
    if (params.start_date) queryParams.append("start_date", params.start_date);
    if (params.end_date) queryParams.append("end_date", params.end_date);
    if (params.carbon_level) queryParams.append("carbon_level", params.carbon_level);
    if (params.sort_by) queryParams.append("sort_by", params.sort_by);

    const raw = await this.request<unknown>(`/history?${queryParams.toString()}`, { signal });

    // Normalize: handle array, envelope objects, and unexpected shapes
    if (Array.isArray(raw)) return raw as HistoryRecord[];

    // If envelope wasn't fully unwrapped (e.g. {success, data, records})
    if (raw && typeof raw === "object") {
      const obj = raw as Record<string, unknown>;
      if (Array.isArray(obj["data"])) return obj["data"] as HistoryRecord[];
      if (Array.isArray(obj["records"])) return obj["records"] as HistoryRecord[];
    }

    // Fallback: return empty array to prevent slice crash
    console.warn("[CarbonTracker] getHistoryList: unexpected response shape", raw);
    return [];
  }

  async getHistoryStats(signal?: AbortSignal): Promise<HistoryStats> {
    return this.request<HistoryStats>("/history/stats", { signal });
  }

  async deleteHistoryRecord(id: string): Promise<void> {
    return this.request<void>(`/history/${id}`, { method: "DELETE" });
  }

  async createHistoryRecord(record: Partial<HistoryRecord>): Promise<HistoryRecord> {
    return this.request<HistoryRecord>("/history", {
      method: "POST",
      body: JSON.stringify(record),
    });
  }

  async updateHistoryRecord(id: string, record: Partial<HistoryRecord>): Promise<HistoryRecord> {
    return this.request<HistoryRecord>(`/history/${id}`, {
      method: "PUT",
      body: JSON.stringify(record),
    });
  }

  // ─────────────────────────────────────────────────────────────────────────
  // AI COACH DATA ENDPOINTS (Phase G)
  // ─────────────────────────────────────────────────────────────────────────

  async getCoachAnalysis(): Promise<HabitAnalysis> {
    return this.request<HabitAnalysis>("/coach/analysis");
  }

  async getWeeklyCoachReport(): Promise<CoachWeeklyReport> {
    return this.request<CoachWeeklyReport>("/coach/report/weekly");
  }

  async getMonthlyCoachReport(): Promise<CoachMonthlyReport> {
    return this.request<CoachMonthlyReport>("/coach/report/monthly");
  }

  async postCoachChat(message: string): Promise<{ response: string }> {
    return this.request<{ response: string }>("/coach/chat", {
      method: "POST",
      body: JSON.stringify({ message }),
    });
  }

  // ─────────────────────────────────────────────────────────────────────────
  // GAMIFICATION ENDPOINTS (Phase H)
  // ─────────────────────────────────────────────────────────────────────────

  async getGamificationProfile(): Promise<GamificationProfile> {
    return this.request<GamificationProfile>(`/gamification/profile`);
  }

  async getGamificationAchievements(): Promise<AchievementStatus[]> {
    return this.request<AchievementStatus[]>(`/gamification/achievements`);
  }

  async getGamificationChallenges(): Promise<{ daily: ChallengeProgress[]; weekly: ChallengeProgress[] }> {
    return this.request<{ daily: ChallengeProgress[]; weekly: ChallengeProgress[] }>(`/gamification/challenges`);
  }

  async getGamificationRewards(): Promise<{ success: boolean; rewards: VirtualReward[] }> {
    return this.request<{ success: boolean; rewards: VirtualReward[] }>(`/gamification/rewards`);
  }

  async redeemVirtualReward(rewardId: string): Promise<{ status: string; message: string; redeemed_rewards: string[] }> {
    return this.request<{ status: string; message: string; redeemed_rewards: string[] }>("/gamification/rewards/redeem", {
      method: "POST",
      body: JSON.stringify({ reward_id: rewardId }),
    });
  }

  // ─────────────────────────────────────────────────────────────────────────
  // AUTHENTICATION & PROFILE ENDPOINTS
  // ─────────────────────────────────────────────────────────────────────────

  async register(username: string, email: string, password: string): Promise<any> {
    return this.request<any>("/auth/register", {
      method: "POST",
      body: JSON.stringify({ username, email, password }),
    });
  }

  async login(email: string, password: string): Promise<TokenResponse> {
    return this.request<TokenResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
  }

  async refreshToken(): Promise<string | null> {
    return refreshAccessToken();
  }

  async logout(): Promise<void> {
    const refreshToken = loadRefreshToken();
    try {
      if (refreshToken) {
        await this.request<any>("/auth/logout", {
          method: "POST",
          body: JSON.stringify({ refresh_token: refreshToken }),
        });
      }
    } catch (err) {
      logger.warn("ApiService", "Failed to blacklist token during logout", err);
    } finally {
      cache.clear();
    }
  }

  async requestReset(email: string): Promise<any> {
    return this.request<any>("/auth/request-reset", {
      method: "POST",
      body: JSON.stringify({ email }),
    });
  }

  async confirmReset(token: string, newPassword: string): Promise<any> {
    return this.request<any>("/auth/confirm-reset", {
      method: "POST",
      body: JSON.stringify({ token, new_password: newPassword }),
    });
  }

  async getProfile(signal?: AbortSignal): Promise<ProfileResponse> {
    const cached = cache.get<ProfileResponse>(CACHE_KEYS.PROFILE);
    if (cached) return cached;

    const profile = await this.request<ProfileResponse>("/profile", { signal });
    cache.set(CACHE_KEYS.PROFILE, profile, CACHE_TTL.PROFILE);
    return profile;
  }

  async updateProfile(data: any): Promise<any> {
    const res = await this.request<any>("/profile", {
      method: "PUT",
      body: JSON.stringify(data),
    });
    cache.invalidate(CACHE_KEYS.PROFILE);
    return res;
  }

  async uploadAvatar(file: File): Promise<any> {
    const formData = new FormData();
    formData.append("file", file);

    const headers = new Headers();
    const authHeader = getAuthorizationHeader();
    if (authHeader) {
      headers.set("Authorization", authHeader);
    }

    const url = `${BASE_URL}/profile/avatar`;

    const response = await fetch(url, {
      method: "POST",
      body: formData,
      headers
    });

    if (!response.ok) {
      const errorText = await response.text();
      let errorDetail = "Avatar upload failed";
      try {
        const errJson = JSON.parse(errorText);
        errorDetail = errJson.detail || errJson.error || errorDetail;
      } catch {
        errorDetail = errorText || errorDetail;
      }
      throw new Error(errorDetail);
    }

    return response.json();
  }

  async getSecurityStatus(): Promise<any> {
    return this.request<any>("/security/status");
  }


  /**
   * checkHealth — lightweight public connectivity probe.
   * Uses GET /api/system/status (no auth required).
   * Returns HealthStatus on success, throws on network/server failure.
   */
  async checkHealth(): Promise<HealthStatus> {
    try {
      const response = await fetchWithTimeout(`${HOST}/api/system/status`, {}, 10_000);
      if (!response.ok) {
        // 4xx/5xx: backend is reachable but returned an HTTP error
        throw new ApiError(response.status, `Health probe returned HTTP ${response.status}`);
      }
      const result = await response.json();
      if (result && typeof result === "object" && "data" in result) return result.data as HealthStatus;
      return result as HealthStatus;
    } catch (err) {
      if (err instanceof ApiError) throw err; // re-throw HTTP errors as-is
      logger.warn("ApiService", "Health probe network failure", { error: err });
      throw new Error("Unable to contact backend server");
    }
  }

  /**
   * getSystemHealth — polls the public GET /api/system/status endpoint.
   *
   * Error mapping:
   *   200 OK          → parse and return SystemHealth
   *   401 / 403       → backend is online but auth/config issue; return backend:"online" with sub-services "unknown"
   *   404             → endpoint missing; return all "degraded"
   *   500             → server error; return backend:"error", failed:true
   *   Network/timeout → server unreachable; return backend:"offline", failed:true
   */
  async getSystemHealth(signal?: AbortSignal): Promise<SystemHealth> {
    try {
      const response = await fetchWithTimeout(`${HOST}/api/system/status`, { signal }, 15_000);

      if (!response.ok) {
        const status = response.status;

        // 401/403 — backend is reachable, auth/config issue on this endpoint (should not normally happen
        // since /api/system/status is public, but be defensive)
        if (status === 401 || status === 403) {
          logger.warn("ApiService", `System status returned ${status} — backend is reachable, treating as online`);
          return {
            backend: "online",
            database: "unknown",
            ai: "unknown",
            ocr: "unknown",
            cache: "unknown",
            iot: "unknown",
            failed: false,
          };
        }

        // 404 — endpoint missing; degraded but reachable
        if (status === 404) {
          logger.warn("ApiService", "System status check returned 404 — treating as degraded");
          return {
            backend: "degraded",
            database: "degraded",
            ai: "degraded",
            ocr: "degraded",
            cache: "degraded",
            iot: "degraded",
            failed: false,
          };
        }

        // 500 — server error
        if (status === 500) {
          logger.error("ApiService", "System status check returned 500 — backend error");
          return {
            backend: "error",
            database: "unknown",
            ai: "unknown",
            ocr: "unknown",
            cache: "unknown",
            iot: "unknown",
            failed: true,
          };
        }

        // Other non-2xx (e.g. 503 Service Unavailable)
        logger.warn("ApiService", `System status check returned unexpected ${status}`);
        return {
          backend: "degraded",
          database: "unknown",
          ai: "unknown",
          ocr: "unknown",
          cache: "unknown",
          iot: "unknown",
          failed: false,
        };
      }

      // 200 OK — parse the body
      const result = await response.json();

      // The public endpoint returns { status: "success", data: { backend, database, version } }
      // NOTE: The lightweight public endpoint only probes backend + database.
      // Sub-services (ai, ocr, cache, iot) are NOT included in the response — default them to "online".
      if (result && typeof result === "object") {
        // Envelope format: { status: "success", data: { backend, database, version } }
        if ("data" in result) {
          const d = (result as any).data as Partial<SystemHealth>;
          return {
            backend:  d.backend  || "online",
            database: d.database || "online",
            ai:       d.ai       || "online",
            ocr:      d.ocr      || "online",
            cache:    d.cache    || "online",
            iot:      d.iot      || "online",
            failed:   false,
          };
        }
        // Flat format: { backend: "online", database: "online" }
        const r = result as any;
        return {
          backend:  r.backend  || "online",
          database: r.database || "online",
          ai:       r.ai       || "online",
          ocr:      r.ocr      || "online",
          cache:    r.cache    || "online",
          iot:      r.iot      || "online",
          failed:   false,
        };
      }


      return result as SystemHealth;
    } catch (err: any) {
      // Network/timeout: true connectivity failure — server unreachable
      const isNetworkError =
        !err?.status && // no HTTP status → not an HTTP error
        (err?.name === "AbortError" ||
          err?.message?.toLowerCase().includes("failed to fetch") ||
          err?.message?.toLowerCase().includes("network error") ||
          err?.message?.toLowerCase().includes("timeout") ||
          err?.message?.toLowerCase().includes("backend unavailable"));

      if (isNetworkError) {
        logger.warn("ApiService", "System status: network unreachable", { error: err?.message });
      } else {
        logger.error("ApiService", "System status: unexpected exception", { error: err });
      }

      return {
        backend: "offline",
        database: "offline",
        ai: "offline",
        ocr: "offline",
        cache: "offline",
        iot: "offline",
        failed: true,
      };
    }
  }

  async getFeatureFlags(signal?: AbortSignal): Promise<Record<string, boolean>> {
    try {
      return await this.request<Record<string, boolean>>("/feature-flags", { signal });
    } catch (err) {
      logger.warn("ApiService", "Failed to fetch feature flags", { error: err });
      return {};
    }
  }
}

export const api = new ApiService();
export default api;
