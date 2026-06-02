/**
 * logger.ts — CarbonTracker Frontend Logger
 * ==========================================
 * LOCKED: Core infrastructure. Do not modify without team review.
 *
 * Centralized structured logging for all frontend errors and events.
 * Stores recent errors in sessionStorage for diagnostics.
 * Replace all bare console.error() calls with logger.error().
 */

export type LogLevel = "debug" | "info" | "warn" | "error" | "critical";

export interface LogEntry {
  timestamp: string;
  level: LogLevel;
  context: string;
  message: string;
  details?: unknown;
}

const MAX_STORED_ENTRIES = 50;
const STORAGE_KEY = "ct_error_log";

function getStoredEntries(): LogEntry[] {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

function storeEntry(entry: LogEntry): void {
  try {
    const entries = getStoredEntries();
    entries.unshift(entry); // newest first
    const trimmed = entries.slice(0, MAX_STORED_ENTRIES);
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(trimmed));
  } catch {
    // sessionStorage unavailable — silent fail
  }
}

function createEntry(
  level: LogLevel,
  context: string,
  message: string,
  details?: unknown
): LogEntry {
  return {
    timestamp: new Date().toISOString(),
    level,
    context,
    message,
    details,
  };
}

class Logger {
  private isDev = process.env.NODE_ENV !== "production";

  private emit(entry: LogEntry): void {
    const prefix = `[CarbonTracker] [${entry.level.toUpperCase()}] [${entry.context}]`;
    const msg = `${prefix} ${entry.message}`;

    switch (entry.level) {
      case "debug":
        if (this.isDev) console.debug(msg, entry.details ?? "");
        break;
      case "info":
        if (this.isDev) console.info(msg, entry.details ?? "");
        break;
      case "warn":
        console.warn(msg, entry.details ?? "");
        storeEntry(entry);
        break;
      case "error":
      case "critical":
        console.error(msg, entry.details ?? "");
        storeEntry(entry);
        break;
    }
  }

  debug(context: string, message: string, details?: unknown): void {
    this.emit(createEntry("debug", context, message, details));
  }

  info(context: string, message: string, details?: unknown): void {
    this.emit(createEntry("info", context, message, details));
  }

  warn(context: string, message: string, details?: unknown): void {
    this.emit(createEntry("warn", context, message, details));
  }

  error(context: string, message: string, details?: unknown): void {
    this.emit(createEntry("error", context, message, details));
  }

  critical(context: string, message: string, details?: unknown): void {
    this.emit(createEntry("critical", context, message, details));
  }

  /** Returns stored error log for diagnostics panel */
  getLog(): LogEntry[] {
    return getStoredEntries();
  }

  /** Clears stored log */
  clearLog(): void {
    try {
      sessionStorage.removeItem(STORAGE_KEY);
    } catch {
      // silent
    }
  }
}

export const logger = new Logger();
export default logger;
