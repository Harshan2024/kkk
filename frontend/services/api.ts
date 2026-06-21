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
  sanitizeSummary,
  sanitizeInsights,
  sanitizeActivities,
  sanitizeAchievements,
  sanitizeForecast,
  sanitizeChatMessages,
} from "../utils/validators";

const HOST = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";
const BASE_URL = HOST.endsWith("/api/v1") ? HOST : `${HOST}/api/v1`;

const DEFAULT_TIMEOUT_MS = 15_000;

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
      console.error(`[CarbonTracker API] TIMEOUT: ${url} after ${duration}ms`);
      throw new Error(`Connection timeout after ${timeoutMs / 1000}s. Please check the backend is running on port 8000.`);
    }
    logger.error("API", `[FAIL] ${endpoint} — network error after ${duration}ms`, err);
    console.error(`[CarbonTracker API] NETWORK ERROR: ${url}`, err);
    // Provide a clear actionable message instead of raw "Failed to fetch"
    const isDev = process.env.NODE_ENV !== "production";
    throw new Error(
      isDev
        ? `Backend unavailable at ${url}. Ensure the backend is running: cd backend && .venv\\Scripts\\python -m uvicorn app.main:app --port 8000`
        : "Backend server unavailable. Please try again in a moment."
    );
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

    const doFetch = async (): Promise<T> => {
      let response: Response;
      try {
        response = await fetchWithTimeout(url, { ...options, headers }, timeoutMs);
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : "Network error";
        throw new Error(msg);
      }

      if (!response.ok) {
        const errorText = await response.text().catch(() => "");
        let errorDetail = `HTTP ${response.status}`;
        try {
          const errJson = JSON.parse(errorText);
          errorDetail = errJson.detail || errJson.error || errorDetail;
        } catch {
          errorDetail = errorText || errorDetail;
        }
        throw new Error(errorDetail);
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

  async logActivity(text: string, username = "demo_user", region = "Global"): Promise<Activity> {
    return this.request<Activity>("/activities", {
      method: "POST",
      body: JSON.stringify({ text, username, region }),
    });
  }

  async getActivities(username = "demo_user", limit = 20, offset = 0): Promise<Activity[]> {
    const raw = await this.request<unknown>(
      `/activities?username=${username}&limit=${limit}&offset=${offset}`
    );
    return sanitizeActivities(raw);
  }

  // ─────────────────────────────────────────────────────────────────────────
  // DASHBOARD ENDPOINTS
  // ─────────────────────────────────────────────────────────────────────────

  async getDashboardSummary(username = "demo_user"): Promise<DashboardSummary> {
    const raw = await this.request<unknown>(`/dashboard/summary?username=${username}`);
    return sanitizeSummary(raw);
  }

  async getInsights(username = "demo_user"): Promise<AIInsight[]> {
    const raw = await this.request<unknown>(`/insights?username=${username}`);
    return sanitizeInsights(raw);
  }

  async getAchievements(username = "demo_user"): Promise<Achievement[]> {
    const raw = await this.request<unknown>(`/achievements?username=${username}`);
    return sanitizeAchievements(raw);
  }

  // ─────────────────────────────────────────────────────────────────────────
  // CHAT ENDPOINTS
  // ─────────────────────────────────────────────────────────────────────────

  async postChat(
    message: string,
    username = "demo_user",
    timeoutMs = 30_000
  ): Promise<{ response: string }> {
    return this.request<{ response: string }>(
      "/chat",
      { method: "POST", body: JSON.stringify({ message, username }) },
      timeoutMs
    );
  }

  async getChatHistory(username = "demo_user"): Promise<ChatMessage[]> {
    const raw = await this.request<unknown>(`/chat/history?username=${username}`);
    return sanitizeChatMessages(raw);
  }

  // ─────────────────────────────────────────────────────────────────────────
  // ANALYTICS & OBSERVABILITY
  // ─────────────────────────────────────────────────────────────────────────

  async getForecast(
    username = "demo_user",
    steps = 30,
    model = "prophet",
    generate = false
  ): Promise<{ status?: string; message?: string; data: ForecastData[] }> {
    const raw = await this.request<any>(
      `/analytics/forecast?username=${username}&steps=${steps}&model=${model}&generate=${generate}`
    );
    if (raw && typeof raw === "object" && raw.status === "pending") {
      return { status: "pending", message: raw.message, data: [] };
    }
    return { data: sanitizeForecast(raw) };
  }

  async getObservabilityMetrics(username = "demo_user"): Promise<ObservabilityMetrics> {
    return this.request<ObservabilityMetrics>(`/observability/metrics?username=${username}`);
  }

  async getHabitAnalysis(username = "demo_user"): Promise<any> {
    return this.request<any>(`/habit-analysis?username=${username}`);
  }

  async correctActivity(
    original_text: string,
    corrected_text: string,
    category = "nlp_parse",
    username = "demo_user"
  ): Promise<unknown> {
    return this.request<unknown>("/activities/correct", {
      method: "POST",
      body: JSON.stringify({ original_text, corrected_text, category, username }),
    });
  }

  // ─────────────────────────────────────────────────────────────────────────
  // MULTIMODAL UPLOAD
  // ─────────────────────────────────────────────────────────────────────────

  async uploadMultimodal(
    file: File,
    username = "demo_user",
    region = "Global"
  ): Promise<unknown> {
    const formData = new FormData();
    formData.append("file", file);

    const url = `${BASE_URL}/activities/upload-multimodal?username=${encodeURIComponent(username)}&region=${encodeURIComponent(region)}`;

    let response: Response;
    try {
      response = await fetchWithTimeout(url, { method: "POST", body: formData }, 60_000);
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

  async checkHealth(): Promise<HealthStatus> {
    try {
      const response = await fetchWithTimeout(`${HOST}/health`, {}, 15_000);
      if (!response.ok) throw new Error(`Health check ${response.status}`);
      const result = await response.json();
      if (result && typeof result === "object" && "data" in result) return result.data as HealthStatus;
      return result as HealthStatus;
    } catch (err) {
      logger.warn("ApiService", "Health check failed", { error: err });
      throw new Error("Unable to contact backend server");
    }
  }

  async getSystemHealth(): Promise<SystemHealth> {
    try {
      const response = await fetchWithTimeout(`${HOST}/api/system/status`, {}, 15_000);

      if (!response.ok) {
        if (response.status === 404) {
          logger.warn("ApiService", "System status check returned 404 - treating as degraded");
          return {
            backend: "degraded",
            database: "degraded",
            ai: "degraded",
            ocr: "degraded",
            cache: "degraded",
            iot: "degraded",
          };
        }

        if (response.status === 500) {
          logger.error("ApiService", "System status check returned 500");
        } else {
          logger.warn("ApiService", `System status check returned ${response.status}`);
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

      const result = await response.json();
      return result as SystemHealth;
    } catch (err: any) {
      // Only use Logger.error() for 500 server errors, database failures, and unexpected exceptions
      const is500 = err?.message?.includes("500") || err?.status === 500;
      const isDbFailure = err?.message?.includes("database") || err?.message?.toLowerCase().includes("db");

      if (is500 || isDbFailure) {
        logger.error("ApiService", "System status fetch failed (critical/db)", { error: err });
      } else {
        logger.warn("ApiService", "System status fetch failed (expected polling failure)", { error: err });
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
}

export const api = new ApiService();
export default api;
