const HOST = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const BASE_URL = HOST.endsWith("/api/v1") ? HOST : `${HOST}/api/v1`;

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

class ApiService {
  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${BASE_URL}${endpoint}`;
    
    const headers = new Headers(options.headers || {});
    if (options.body && !headers.has("Content-Type")) {
      headers.set("Content-Type", "application/json");
    }
    
    const response = await fetch(url, { ...options, headers });
    
    if (!response.ok) {
      const errorText = await response.text();
      let errorDetail = "API Request failed";
      try {
        const errJson = JSON.parse(errorText);
        errorDetail = errJson.detail || errorDetail;
      } catch {
        errorDetail = errorText || errorDetail;
      }
      throw new Error(errorDetail);
    }
    
    const result = await response.json();
    if (result && typeof result === "object" && "success" in result && "data" in result) {
      if (!result.success) {
        throw new Error(result.error || "API Request failed");
      }
      return result.data as T;
    }
    return result as T;
  }

  async parseActivity(text: string, region = "Global"): Promise<ParseResult> {
    return this.request<ParseResult>(`/activities/parse?text=${encodeURIComponent(text)}&region=${encodeURIComponent(region)}`);
  }

  async logActivity(text: string, username = "demo_user", region = "Global"): Promise<Activity> {
    return this.request<Activity>("/activities", {
      method: "POST",
      body: JSON.stringify({ text, username, region }),
    });
  }

  async getActivities(username = "demo_user", limit = 20, offset = 0): Promise<Activity[]> {
    return this.request<Activity[]>(`/activities?username=${username}&limit=${limit}&offset=${offset}`);
  }

  async getDashboardSummary(username = "demo_user"): Promise<DashboardSummary> {
    return this.request<DashboardSummary>(`/dashboard/summary?username=${username}`);
  }

  async getInsights(username = "demo_user"): Promise<AIInsight[]> {
    return this.request<AIInsight[]>(`/insights?username=${username}`);
  }

  async getAchievements(username = "demo_user"): Promise<Achievement[]> {
    return this.request<Achievement[]>(`/achievements?username=${username}`);
  }

  async postChat(message: string, username = "demo_user"): Promise<{ response: string }> {
    return this.request<{ response: string }>("/chat", {
      method: "POST",
      body: JSON.stringify({ message, username }),
    });
  }

  async getChatHistory(username = "demo_user"): Promise<ChatMessage[]> {
    return this.request<ChatMessage[]>(`/chat/history?username=${username}`);
  }

  async getForecast(username = "demo_user", steps = 30, model = "prophet"): Promise<ForecastData[]> {
    return this.request<ForecastData[]>(`/analytics/forecast?username=${username}&steps=${steps}&model=${model}`);
  }

  async uploadMultimodal(file: File, username = "demo_user", region = "Global"): Promise<any> {
    const formData = new FormData();
    formData.append("file", file);
    
    const url = `${BASE_URL}/activities/upload-multimodal?username=${encodeURIComponent(username)}&region=${encodeURIComponent(region)}`;
    const response = await fetch(url, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(errorText || "File upload failed");
    }

    const result = await response.json();
    if (result && typeof result === "object" && "success" in result && "data" in result) {
      if (!result.success) {
        throw new Error(result.error || "File upload failed");
      }
      return result.data;
    }
    return result;
  }

  async getObservabilityMetrics(username = "demo_user"): Promise<ObservabilityMetrics> {
    return this.request<ObservabilityMetrics>(`/observability/metrics?username=${username}`);
  }

  async correctActivity(original_text: string, corrected_text: string, category = "nlp_parse", username = "demo_user"): Promise<any> {
    return this.request<any>("/activities/correct", {
      method: "POST",
      body: JSON.stringify({ original_text, corrected_text, category, username }),
    });
  }

  async seedDatabase(username = "demo_user"): Promise<{ status: string; message: string }> {
    return this.request<{ status: string; message: string }>(`/seed?username=${username}`, {
      method: "POST",
    });
  }

  async checkHealth(): Promise<{ backend: string; database: string; status: string }> {
    try {
      const response = await fetch(`${HOST}/health`);
      if (!response.ok) throw new Error("Health check returned bad response");
      const result = await response.json();
      if (result && typeof result === "object" && "success" in result && "data" in result) {
        return result.data;
      }
      return result;
    } catch (err) {
      throw new Error("Unable to contact backend server");
    }
  }
}

export const api = new ApiService();
