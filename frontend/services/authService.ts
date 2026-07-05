/**
 * authService.ts — CarbonTracker Centralized Authentication Service
 * =================================================================
 * Single source of truth for all token storage, retrieval, validation
 * and Authorization header generation.
 *
 * Rules:
 *  - All token reads/writes go through this service — NEVER access
 *    localStorage("carbontracker_token") directly outside this file.
 *  - getAuthorizationHeader() is the ONLY way to obtain the Bearer header.
 *  - isAuthenticated() performs a lightweight local JWT expiry check.
 *
 * Phase P1: Added refresh_token, login timestamp, session age helpers.
 */

const TOKEN_KEY         = "carbontracker_token";
const REFRESH_TOKEN_KEY = "carbontracker_refresh_token";
const USER_KEY          = "carbontracker_user";
const LOGIN_TS_KEY      = "carbontracker_login_ts";

// ─────────────────────────────────────────────────────────────────────────────
// ACCESS TOKEN
// ─────────────────────────────────────────────────────────────────────────────

/** Save the JWT access token to localStorage (single call-site). */
export function saveToken(token: string): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(TOKEN_KEY, token);
}

/** Load the raw JWT string, or null if missing. */
export function loadToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

/** Remove ALL auth data from localStorage (access, refresh, user, timestamp). */
export function removeToken(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
  localStorage.removeItem(LOGIN_TS_KEY);
}

/**
 * Returns true iff a non-expired JWT access token exists in storage.
 * Performs a local decode — does NOT make a network call.
 */
export function isAuthenticated(): boolean {
  const token = loadToken();
  if (!token) return false;
  try {
    const parts = token.split(".");
    if (parts.length !== 3) return false;
    const payload = JSON.parse(atob(parts[1]));
    if (payload.exp && payload.exp * 1000 < Date.now()) return false;
    return true;
  } catch {
    return false;
  }
}

/**
 * Returns the Authorization header value for authenticated requests,
 * or null if no valid token exists.
 *
 * Usage:
 *   const authHeader = getAuthorizationHeader();
 *   if (authHeader) headers.set("Authorization", authHeader);
 */
export function getAuthorizationHeader(): string | null {
  const token = loadToken();
  if (!token) return null;
  return `Bearer ${token}`;
}

// ─────────────────────────────────────────────────────────────────────────────
// REFRESH TOKEN
// ─────────────────────────────────────────────────────────────────────────────

/** Save the JWT refresh token to localStorage. */
export function saveRefreshToken(token: string): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(REFRESH_TOKEN_KEY, token);
}

/** Load the refresh token, or null if missing. */
export function loadRefreshToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(REFRESH_TOKEN_KEY);
}

/** Remove only the refresh token (access token preserved). */
export function removeRefreshToken(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(REFRESH_TOKEN_KEY);
}

/**
 * Returns true iff a non-expired refresh token exists in storage.
 * Backend refresh tokens are long-lived (typically 7–30 days).
 */
export function hasValidRefreshToken(): boolean {
  const token = loadRefreshToken();
  if (!token) return false;
  try {
    const parts = token.split(".");
    if (parts.length !== 3) return false;
    const payload = JSON.parse(atob(parts[1]));
    if (payload.exp && payload.exp * 1000 < Date.now()) return false;
    return true;
  } catch {
    return false;
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// USER PROFILE CACHE
// ─────────────────────────────────────────────────────────────────────────────

/** Save the user profile object to localStorage. */
export function saveUser(user: object): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

/** Load the cached user profile, or null. */
export function loadUser<T = unknown>(): T | null {
  if (typeof window === "undefined") return null;
  const raw = localStorage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as T;
  } catch {
    return null;
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// LOGIN TIMESTAMP
// ─────────────────────────────────────────────────────────────────────────────

/** Record the unix-ms timestamp when the user logged in. */
export function saveLoginTimestamp(): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(LOGIN_TS_KEY, String(Date.now()));
}

/** Load the login timestamp, or null if not stored. */
export function loadLoginTimestamp(): number | null {
  if (typeof window === "undefined") return null;
  const raw = localStorage.getItem(LOGIN_TS_KEY);
  if (!raw) return null;
  const parsed = parseInt(raw, 10);
  return isNaN(parsed) ? null : parsed;
}

/**
 * Returns session age in minutes since login, or null if no session.
 * Useful for "Logged in 3 hours ago" style status display.
 */
export function getSessionAgeMinutes(): number | null {
  const ts = loadLoginTimestamp();
  if (ts === null) return null;
  return Math.floor((Date.now() - ts) / 60_000);
}

