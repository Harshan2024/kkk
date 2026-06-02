/**
 * validators.ts — CarbonTracker API Response Validator & Sanitizer
 * ================================================================
 * Ensures all API responses conform to expected shapes before
 * they reach components. Prevents null/undefined crashes by
 * replacing missing fields with safe defaults.
 *
 * Usage:
 *   const safe = sanitizeSummary(rawSummary);
 *   // safe.breakdown is always CategoryBreakdown[]
 *   // safe.trends is always TrendData[]
 *   // safe.today_emissions is always a number
 */

import {
  DashboardSummary,
  TrendData,
  CategoryBreakdown,
  AIInsight,
  Activity,
  Achievement,
  ForecastData,
  ChatMessage,
} from "../services/api";
import logger from "./logger";

// ─────────────────────────────────────────────────────────────────────────────
// PRIMITIVE HELPERS
// ─────────────────────────────────────────────────────────────────────────────

function safeNumber(val: unknown, fallback = 0): number {
  if (typeof val === "number" && isFinite(val)) return val;
  const parsed = parseFloat(String(val));
  return isFinite(parsed) ? parsed : fallback;
}

function safeString(val: unknown, fallback = ""): string {
  if (typeof val === "string") return val;
  if (val === null || val === undefined) return fallback;
  return String(val);
}

function safeArray<T>(val: unknown, fallback: T[] = []): T[] {
  if (Array.isArray(val)) return val;
  return fallback;
}

// ─────────────────────────────────────────────────────────────────────────────
// DASHBOARD SUMMARY SANITIZER
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Sanitizes a raw API DashboardSummary into a guaranteed-safe shape.
 * All numeric fields default to 0, all arrays default to [].
 * Always returns a valid DashboardSummary object — never null.
 */
export function sanitizeSummary(raw: unknown): DashboardSummary {
  if (!raw || typeof raw !== "object") {
    logger.warn("validators", "sanitizeSummary received non-object", raw);
    return createEmptySummary();
  }

  const r = raw as Record<string, unknown>;

  const trends = safeArray<TrendData>(r.trends).map(sanitizeTrend);
  const breakdown = safeArray<CategoryBreakdown>(r.breakdown).map(sanitizeBreakdown);

  // Validate strengths structure safely
  let streaks = undefined;
  if (r.streaks && typeof r.streaks === "object") {
    const s = r.streaks as Record<string, unknown>;
    streaks = {
      current_streak: safeNumber(s.current_streak, 1),
      longest_streak: safeNumber(s.longest_streak, 1),
      carbon_streak: safeNumber(s.carbon_streak, 0),
      score_streak: safeNumber(s.score_streak, 0),
      monthly_performance: safeArray<number>(s.monthly_performance)
    };
  }

  // Validate quests structure safely
  const quests = safeArray<unknown>(r.quests).map((q) => {
    if (!q || typeof q !== "object") return null;
    const qRec = q as Record<string, unknown>;
    return {
      id: safeString(qRec.id, "q_empty"),
      name: safeString(qRec.name, "Quest"),
      description: safeString(qRec.description, ""),
      progress: safeNumber(qRec.progress, 0),
      max: safeNumber(qRec.max, 1),
      xp: safeNumber(qRec.xp, 50),
      icon: safeString(qRec.icon, "Leaf"),
      color: safeString(qRec.color, "text-emerald-400 bg-emerald-500/10 border-emerald-500/20")
    };
  }).filter(Boolean) as any[];

  // Validate AI dashboard structure safely
  let ai_dashboard = undefined;
  if (r.ai_dashboard && typeof r.ai_dashboard === "object") {
    const aid = r.ai_dashboard as Record<string, unknown>;
    ai_dashboard = {
      top_emission_source: safeString(aid.top_emission_source, "lifestyle"),
      weekly_trend: safeString(aid.weekly_trend, "stable"),
      behavior_change: safeString(aid.behavior_change, ""),
      predicted_monthly_emissions: safeNumber(aid.predicted_monthly_emissions, 0),
      biggest_improvement_area: safeString(aid.biggest_improvement_area, ""),
      personalized_sustainability_summary: safeString(aid.personalized_sustainability_summary, "")
    };
  }

  // Validate insight feed structure safely
  const insight_feed = safeArray<unknown>(r.insight_feed).map((inf) => {
    if (!inf || typeof inf !== "object") return null;
    const infRec = inf as Record<string, unknown>;
    return {
      text: safeString(infRec.text, ""),
      timestamp: safeString(infRec.timestamp, new Date().toISOString()),
      type: safeString(infRec.type, "info")
    };
  }).filter(Boolean) as any[];

  return {
    today_emissions: safeNumber(r.today_emissions),
    yesterday_emissions: safeNumber(r.yesterday_emissions),
    weekly_emissions: safeNumber(r.weekly_emissions),
    current_score: safeNumber(r.current_score, 100),
    avg_weekly_score: safeNumber(r.avg_weekly_score, 100),
    daily_budget: safeNumber(r.daily_budget, 5.0),
    breakdown,
    trends,
    achievements_count: safeNumber(r.achievements_count),
    habit_cards: safeArray(r.habit_cards),
    xp: safeNumber(r.xp, 150),
    level: safeNumber(r.level, 1),
    level_name: safeString(r.level_name, "Eco Beginner"),
    progress_pct: safeNumber(r.progress_pct, 0.0),
    streaks,
    quests,
    ai_dashboard,
    insight_feed
  };
}

function sanitizeTrend(raw: unknown): TrendData {
  if (!raw || typeof raw !== "object") return { date: "?", date_full: "Unknown", emissions: 0, score: 100 };
  const r = raw as Record<string, unknown>;
  return {
    date: safeString(r.date, "?"),
    date_full: safeString(r.date_full, safeString(r.date, "Unknown")),
    emissions: safeNumber(r.emissions),
    score: safeNumber(r.score, 100),
  };
}

function sanitizeBreakdown(raw: unknown): CategoryBreakdown {
  if (!raw || typeof raw !== "object") return { category: "unknown", total_carbon: 0, count: 0, percentage: 0 };
  const r = raw as Record<string, unknown>;
  return {
    category: safeString(r.category, "unknown"),
    total_carbon: safeNumber(r.total_carbon),
    count: safeNumber(r.count),
    percentage: safeNumber(r.percentage),
  };
}

export function createEmptySummary(): DashboardSummary {
  return {
    today_emissions: 0,
    yesterday_emissions: 0,
    weekly_emissions: 0,
    current_score: 100,
    avg_weekly_score: 100,
    daily_budget: 5.0,
    breakdown: [],
    trends: [],
    achievements_count: 0,
    habit_cards: [],
  };
}

// ─────────────────────────────────────────────────────────────────────────────
// INSIGHTS SANITIZER
// ─────────────────────────────────────────────────────────────────────────────

export function sanitizeInsights(raw: unknown): AIInsight[] {
  const arr = safeArray<unknown>(raw);
  return arr.filter(Boolean).map((item) => {
    if (!item || typeof item !== "object") return null;
    const r = item as Record<string, unknown>;
    return {
      id: safeNumber(r.id, Math.random()),
      content: safeString(r.content, "No insight available"),
      category: r.category ? safeString(r.category) : null,
      impact_estimate: safeString(r.impact_estimate, "Unknown"),
      impact_level: safeString(r.impact_level, "low"),
      impact_value: safeNumber(r.impact_value),
      feasibility: r.feasibility ? safeString(r.feasibility) : undefined,
      difficulty: r.difficulty ? safeString(r.difficulty) : undefined,
      confidence_score: r.confidence_score ? safeNumber(r.confidence_score) : undefined,
      sustainability_gain: r.sustainability_gain ? safeNumber(r.sustainability_gain) : undefined,
      why_explanation: r.why_explanation ? safeString(r.why_explanation) : null,
      how_calculation: r.how_calculation ? safeString(r.how_calculation) : null,
      weighted_priority_score: r.weighted_priority_score ? safeNumber(r.weighted_priority_score) : undefined,
      created_at: safeString(r.created_at, new Date().toISOString()),
    } as AIInsight;
  }).filter(Boolean) as AIInsight[];
}

// ─────────────────────────────────────────────────────────────────────────────
// ACTIVITIES SANITIZER
// ─────────────────────────────────────────────────────────────────────────────

export function sanitizeActivities(raw: unknown): Activity[] {
  const arr = safeArray<unknown>(raw);
  return arr.filter(Boolean).map((item) => {
    if (!item || typeof item !== "object") return null;
    const r = item as Record<string, unknown>;
    return {
      id: safeNumber(r.id, Date.now()),
      input_text: safeString(r.input_text, ""),
      category: r.category ? safeString(r.category) : null,
      item: safeString(r.item, "unknown"),
      quantity: safeNumber(r.quantity, 1),
      unit: safeString(r.unit, "unit"),
      calculated_value: safeNumber(r.calculated_value),
      metadata: (r.metadata as Record<string, unknown>) ?? {},
      region: safeString(r.region, "Global"),
      logged_at: safeString(r.logged_at, new Date().toISOString()),
    } as Activity;
  }).filter(Boolean) as Activity[];
}

// ─────────────────────────────────────────────────────────────────────────────
// ACHIEVEMENTS SANITIZER
// ─────────────────────────────────────────────────────────────────────────────

export function sanitizeAchievements(raw: unknown): Achievement[] {
  const arr = safeArray<unknown>(raw);
  return arr.filter(Boolean).map((item) => {
    if (!item || typeof item !== "object") return null;
    const r = item as Record<string, unknown>;
    return {
      id: safeNumber(r.id, Date.now()),
      name: safeString(r.name, "Achievement"),
      description: safeString(r.description, ""),
      badge_type: safeString(r.badge_type, "bronze"),
      unlocked_at: safeString(r.unlocked_at, new Date().toISOString()),
    } as Achievement;
  }).filter(Boolean) as Achievement[];
}

// ─────────────────────────────────────────────────────────────────────────────
// FORECAST SANITIZER
// ─────────────────────────────────────────────────────────────────────────────

export function sanitizeForecast(raw: unknown): ForecastData[] {
  const arr = safeArray<unknown>(raw);
  return arr.filter(Boolean).map((item) => {
    if (!item || typeof item !== "object") return null;
    const r = item as Record<string, unknown>;
    return {
      date: safeString(r.date, "?"),
      label: safeString(r.label, safeString(r.date, "?")),
      expected: safeNumber(r.expected),
      optimistic: safeNumber(r.optimistic),
      pessimistic: safeNumber(r.pessimistic),
    } as ForecastData;
  }).filter(Boolean) as ForecastData[];
}

// ─────────────────────────────────────────────────────────────────────────────
// CHAT MESSAGES SANITIZER
// ─────────────────────────────────────────────────────────────────────────────

export function sanitizeChatMessages(raw: unknown): ChatMessage[] {
  const arr = safeArray<unknown>(raw);
  return arr.filter(Boolean).map((item) => {
    if (!item || typeof item !== "object") return null;
    const r = item as Record<string, unknown>;
    return {
      id: safeNumber(r.id, Date.now()),
      role: safeString(r.role, "assistant"),
      content: safeString(r.content, ""),
      created_at: safeString(r.created_at, new Date().toISOString()),
      context_tags: Array.isArray(r.context_tags) ? r.context_tags as string[] : undefined,
    } as ChatMessage;
  }).filter(Boolean) as ChatMessage[];
}
