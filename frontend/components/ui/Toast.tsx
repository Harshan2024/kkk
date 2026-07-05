"use client";

import React, { useEffect, useState, useCallback } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { CheckCircle2, XCircle, AlertTriangle, Info, X, RotateCcw } from "lucide-react";
import { clsx } from "clsx";

// ─── Types ────────────────────────────────────────────────────────────────────

export type ToastType = "success" | "error" | "warning" | "info" | "undo";

export interface Toast {
  id: string;
  type: ToastType;
  title?: string;
  message: string;
  duration?: number;
  onUndo?: () => void;
}

// ─── Toast Store (singleton) ──────────────────────────────────────────────────

type ToastListener = (toasts: Toast[]) => void;
let _toasts: Toast[] = [];
const _listeners: Set<ToastListener> = new Set();

function notify() {
  _listeners.forEach(l => l([..._toasts]));
}

export const toast = {
  show(t: Omit<Toast, "id">) {
    const id = Math.random().toString(36).slice(2);
    _toasts = [{ ...t, id }, ..._toasts].slice(0, 5);
    notify();
    if (t.duration !== 0) {
      setTimeout(() => toast.remove(id), t.duration ?? 4000);
    }
    return id;
  },
  success(message: string, title?: string) {
    return toast.show({ type: "success", message, title });
  },
  error(message: string, title?: string) {
    return toast.show({ type: "error", message, title, duration: 6000 });
  },
  warning(message: string, title?: string) {
    return toast.show({ type: "warning", message, title, duration: 5000 });
  },
  info(message: string, title?: string) {
    return toast.show({ type: "info", message, title });
  },
  undo(message: string, onUndo: () => void) {
    return toast.show({ type: "undo", message, onUndo, duration: 5000 });
  },
  remove(id: string) {
    _toasts = _toasts.filter(t => t.id !== id);
    notify();
  },
  clear() {
    _toasts = [];
    notify();
  },
};

// ─── Icon map ─────────────────────────────────────────────────────────────────

const ICONS: Record<ToastType, React.ReactNode> = {
  success:  <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />,
  error:    <XCircle className="w-4 h-4 text-rose-400 flex-shrink-0" />,
  warning:  <AlertTriangle className="w-4 h-4 text-amber-400 flex-shrink-0" />,
  info:     <Info className="w-4 h-4 text-sky-400 flex-shrink-0" />,
  undo:     <RotateCcw className="w-4 h-4 text-indigo-400 flex-shrink-0" />,
};

const STYLES: Record<ToastType, string> = {
  success: "border-emerald-500/25 bg-emerald-500/8",
  error:   "border-rose-500/25 bg-rose-500/8",
  warning: "border-amber-500/25 bg-amber-500/8",
  info:    "border-sky-500/25 bg-sky-500/8",
  undo:    "border-indigo-500/25 bg-indigo-500/8",
};

const TITLE_COLORS: Record<ToastType, string> = {
  success: "text-emerald-450",
  error:   "text-rose-450",
  warning: "text-amber-450",
  info:    "text-sky-450",
  undo:    "text-indigo-450",
};

// ─── Toast Item ───────────────────────────────────────────────────────────────

function ToastItem({ t, onRemove }: { t: Toast; onRemove: (id: string) => void }) {
  return (
    <motion.div
      layout
      initial={{ opacity: 0, x: 80, scale: 0.95 }}
      animate={{ opacity: 1, x: 0, scale: 1 }}
      exit={{ opacity: 0, x: 80, scale: 0.9 }}
      transition={{ type: "spring", stiffness: 400, damping: 25 }}
      className={clsx(
        "glass-premium rounded-2xl px-4 py-3 max-w-sm w-full border shadow-xl",
        "flex items-start gap-3",
        STYLES[t.type]
      )}
    >
      {ICONS[t.type]}
      <div className="flex-1 min-w-0">
        {t.title && (
          <p className={clsx("text-[11px] font-extrabold leading-tight mb-0.5", TITLE_COLORS[t.type])}>
            {t.title}
          </p>
        )}
        <p className="text-[11px] font-bold text-theme-primary leading-relaxed">{t.message}</p>
        {t.type === "undo" && t.onUndo && (
          <button
            onClick={() => { t.onUndo?.(); onRemove(t.id); }}
            className="mt-1.5 text-[10px] font-extrabold text-indigo-400 hover:text-indigo-300 uppercase tracking-wider cursor-pointer underline"
          >
            Undo
          </button>
        )}
      </div>
      <button
        onClick={() => onRemove(t.id)}
        className="text-theme-muted hover:text-theme-primary transition-colors cursor-pointer flex-shrink-0 mt-0.5"
      >
        <X className="w-3.5 h-3.5" />
      </button>
    </motion.div>
  );
}

// ─── Toast Container ──────────────────────────────────────────────────────────

export function ToastContainer() {
  const [toasts, setToasts] = useState<Toast[]>([]);

  useEffect(() => {
    const listener: ToastListener = (t) => setToasts(t);
    _listeners.add(listener);
    return () => { _listeners.delete(listener); };
  }, []);

  const remove = useCallback((id: string) => toast.remove(id), []);

  return (
    <div className="fixed bottom-6 right-6 z-[9999] flex flex-col gap-2 items-end pointer-events-none">
      <AnimatePresence mode="popLayout">
        {toasts.map(t => (
          <div key={t.id} className="pointer-events-auto">
            <ToastItem t={t} onRemove={remove} />
          </div>
        ))}
      </AnimatePresence>
    </div>
  );
}

export default ToastContainer;
