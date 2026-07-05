/**
 * cache.ts — CarbonTracker Client-Side TTL Cache
 * ================================================
 * Simple Map-based cache with per-entry TTL expiry.
 * Prevents redundant API calls for stable data like profile,
 * dashboard summary, achievements, and insights.
 *
 * Usage:
 *   cache.set("profile", data, 5 * 60_000);  // 5 min TTL
 *   const data = cache.get<ProfileResponse>("profile");
 *   cache.invalidate("profile");
 *   cache.clear();  // called on logout
 */

interface CacheEntry<T> {
  data: T;
  expiry: number;
}

class TtlCache {
  private _store = new Map<string, CacheEntry<unknown>>();

  /** Retrieve cached data if still valid, or null if missing/expired. */
  get<T>(key: string): T | null {
    const entry = this._store.get(key);
    if (!entry) return null;
    if (Date.now() > entry.expiry) {
      this._store.delete(key);
      return null;
    }
    return entry.data as T;
  }

  /** Store data with a TTL in milliseconds. */
  set<T>(key: string, data: T, ttlMs: number): void {
    this._store.set(key, { data, expiry: Date.now() + ttlMs });
  }

  /** Remove a single entry (e.g. after mutation). */
  invalidate(key: string): void {
    this._store.delete(key);
  }

  /** Invalidate all entries whose keys start with prefix. */
  invalidatePrefix(prefix: string): void {
    for (const key of this._store.keys()) {
      if (key.startsWith(prefix)) this._store.delete(key);
    }
  }

  /** Clear the entire cache (called on logout). */
  clear(): void {
    this._store.clear();
  }

  /** Number of live (non-expired) entries. */
  get size(): number {
    let count = 0;
    const now = Date.now();
    for (const entry of this._store.values()) {
      if (now <= entry.expiry) count++;
    }
    return count;
  }
}

/** Singleton export — shared across the entire app. */
export const cache = new TtlCache();

// Cache key constants
export const CACHE_KEYS = {
  PROFILE:           "profile",
  DASHBOARD_SUMMARY: "dashboard:summary",
  ACHIEVEMENTS:      "achievements",
  INSIGHTS:          "insights",
  SYSTEM_HEALTH:     "system:health",
  ANALYTICS:         "analytics",
} as const;

// TTL constants
export const CACHE_TTL = {
  PROFILE:           5 * 60_000,   // 5 minutes
  DASHBOARD_SUMMARY: 2 * 60_000,   // 2 minutes
  ACHIEVEMENTS:      10 * 60_000,  // 10 minutes
  INSIGHTS:          3 * 60_000,   // 3 minutes
  SYSTEM_HEALTH:     30_000,       // 30 seconds
  ANALYTICS:         2 * 60_000,   // 2 minutes
} as const;
