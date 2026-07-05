"use client";

import React, { useState, useRef, useEffect } from "react";
import {
  Bell, RefreshCw, CheckCircle2, AlertTriangle, X,
  Search, Sun, Moon, Palette, ChevronDown, User, LogOut, Settings
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { useAIStore } from "../stores/aiStore";
import { useTheme, THEMES, THEME_GROUPS } from "../stores/themeStore";
import { api } from "../services/api";
import Link from "next/link";

// ─── Props ────────────────────────────────────────────────────────────────────

interface TopbarProps {
  onRefresh: () => void;
  region: string;
  onRegionChange: (region: string) => void;
}

// ─── Notifications (demo) ────────────────────────────────────────────────────

const DEMO_NOTIFICATIONS = [
  { id: 1, icon: "🌿", title: "Streak maintained!", body: "You're on a 12-day green streak.", time: "2m ago", read: false },
  { id: 2, icon: "⚡", title: "New AI tip ready", body: "Switch to LED bulbs to save 0.4 kg/week.", time: "1h ago", read: false },
  { id: 3, icon: "🏆", title: "Achievement unlocked", body: "Carbon Warrior — 100 activities logged.", time: "3h ago", read: true },
];

export const Topbar = React.memo(function Topbar({ onRefresh, region, onRegionChange }: TopbarProps) {
  const [seeding, setSeeding] = useState(false);
  const [seeded, setSeeded] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [showNotifs, setShowNotifs] = useState(false);
  const [showTheme, setShowTheme] = useState(false);
  const [showProfile, setShowProfile] = useState(false);
  const [searchFocused, setSearchFocused] = useState(false);
  const [notifications, setNotifications] = useState(DEMO_NOTIFICATIONS);
  const { setToastError, user, logout } = useAIStore();
  const { theme, setTheme, isDark, toggleDark } = useTheme();

  const notifRef = useRef<HTMLDivElement>(null);
  const themeRef = useRef<HTMLDivElement>(null);
  const profileRef = useRef<HTMLDivElement>(null);

  const unreadCount = notifications.filter(n => !n.read).length;

  // Close panels on outside click
  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      if (notifRef.current && !notifRef.current.contains(e.target as Node)) setShowNotifs(false);
      if (themeRef.current && !themeRef.current.contains(e.target as Node)) setShowTheme(false);
      if (profileRef.current && !profileRef.current.contains(e.target as Node)) setShowProfile(false);
    };
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  const markAllRead = () => setNotifications(prev => prev.map(n => ({ ...n, read: true })));

  const handleSeed = async (forceConfirm = false) => {
    if (!forceConfirm) {
      setSeeding(true);
      try {
        const res = await api.seedDatabase("demo_user", false);
        if (!res.success) {
          if (res.error && res.error.includes("Safety lock active")) {
            setShowConfirm(true);
          } else {
            setToastError(res.error || "Seed endpoint disabled outside development environment");
          }
          return;
        }
        setSeeded(true);
        onRefresh();
        setTimeout(() => setSeeded(false), 3000);
      } catch (err: any) {
        setToastError(err.message || "Seeding failed.");
      } finally {
        setSeeding(false);
      }
    } else {
      setShowConfirm(false);
      setSeeding(true);
      try {
        const res = await api.seedDatabase("demo_user", true);
        if (!res.success) { setToastError(res.error || "Seeding failed."); return; }
        setSeeded(true);
        onRefresh();
        setTimeout(() => setSeeded(false), 3000);
      } catch (err: any) {
        setToastError(err.message || "Seeding failed.");
      } finally {
        setSeeding(false);
      }
    }
  };

  const currentTheme = THEMES.find(t => t.id === theme);

  return (
    <header
      className="sticky top-0 z-20 w-full px-4 sm:px-6 py-3 flex items-center justify-between gap-4 select-none"
      style={{
        background: "var(--topbar-bg)",
        backdropFilter: "blur(20px)",
        WebkitBackdropFilter: "blur(20px)",
        borderBottom: "1px solid var(--border-subtle)",
      }}
    >
      {/* ─── Left: Status + Search ────────────────────────────────────── */}
      <div className="flex items-center gap-3 flex-1">
        {/* AI Sync badge */}
        <span className="hidden sm:flex text-[9px] font-black uppercase tracking-widest items-center gap-1.5 px-2.5 py-1 rounded-full"
          style={{ color: "var(--text-brand)", background: "var(--brand-muted)", border: "1px solid var(--brand-glow)" }}>
          <span className="w-1.5 h-1.5 rounded-full animate-pulse"
            style={{ background: "var(--brand-primary)" }} />
          AI Sync Enabled
        </span>

        {/* Global search */}
        <div className={`relative hidden md:flex items-center transition-all duration-300 ${searchFocused ? "flex-1 max-w-sm" : "w-48"}`}>
          <Search className="absolute left-3 w-3.5 h-3.5 text-theme-muted pointer-events-none" />
          <input
            type="text"
            placeholder="Search anything..."
            onFocus={() => setSearchFocused(true)}
            onBlur={() => setSearchFocused(false)}
            className="w-full pl-9 pr-10 py-1.5 text-xs rounded-xl transition-all duration-200 focus:outline-none"
            style={{
              background: "var(--bg-elevated)",
              border: searchFocused ? "1px solid var(--border-strong)" : "1px solid var(--border-subtle)",
              color: "var(--text-primary)",
            }}
          />
          <kbd className="absolute right-2.5 text-[9px] px-1.5 py-0.5 rounded font-mono text-theme-muted"
            style={{ background: "var(--bg-overlay)", border: "1px solid var(--border-subtle)" }}>
            ⌘K
          </kbd>
        </div>
      </div>

      {/* ─── Right: Controls ──────────────────────────────────────────── */}
      <div className="flex items-center gap-1.5">

        {/* Seed button */}
        <button
          onClick={() => handleSeed(false)}
          disabled={seeding}
          className={`hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-[9px] font-extrabold uppercase tracking-wider border transition-all ${
            seeded
              ? "text-emerald-400 border-emerald-500/20"
              : "text-theme-muted border-theme-subtle hover:text-theme-primary hover:border-theme"
          } cursor-pointer active:scale-95`}
          style={{ background: seeded ? "var(--brand-muted)" : "var(--bg-elevated)" }}
        >
          {seeding ? <RefreshCw className="w-3 h-3 animate-spin" /> : seeded ? <CheckCircle2 className="w-3 h-3" /> : <RefreshCw className="w-3 h-3" />}
          {seeded ? "Seeded!" : "Seed DB"}
        </button>

        {/* Theme switcher */}
        <div ref={themeRef} className="relative">
          <button
            onClick={() => { setShowTheme(v => !v); setShowNotifs(false); setShowProfile(false); }}
            className="w-8 h-8 rounded-xl flex items-center justify-center text-theme-muted hover:text-theme-primary cursor-pointer transition-all"
            style={{ background: "var(--bg-elevated)", border: "1px solid var(--border-subtle)" }}
            title="Theme"
          >
            <Palette className="w-3.5 h-3.5" />
          </button>

          <AnimatePresence>
            {showTheme && (
              <motion.div
                initial={{ opacity: 0, y: 8, scale: 0.96 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: 8, scale: 0.96 }}
                transition={{ type: "spring", stiffness: 400, damping: 25 }}
                className="absolute right-0 top-11 z-50 w-64 rounded-2xl overflow-hidden shadow-2xl"
                style={{
                  background: "var(--bg-surface)",
                  border: "1px solid var(--border-default)",
                  boxShadow: "0 20px 60px rgba(0,0,0,0.6)",
                }}
              >
                <div className="p-3">
                  <p className="text-[9px] font-black uppercase tracking-widest text-theme-muted mb-2 px-1">Dark Themes</p>
                  <div className="grid grid-cols-5 gap-1.5 mb-3">
                    {THEME_GROUPS.dark.map(t => (
                      <button
                        key={t.id}
                        onClick={() => { setTheme(t.id); setShowTheme(false); }}
                        title={t.label}
                        className={`h-8 rounded-lg flex items-center justify-center text-sm transition-all cursor-pointer ${theme === t.id ? "ring-2 scale-110" : "hover:scale-105"}`}
                        style={{
                          background: "var(--bg-elevated)",
                          border: theme === t.id ? "1px solid var(--brand-primary)" : "1px solid var(--border-subtle)",
                        }}
                      >
                        {t.emoji}
                      </button>
                    ))}
                  </div>
                  <p className="text-[9px] font-black uppercase tracking-widest text-theme-muted mb-2 px-1">Light Themes</p>
                  <div className="grid grid-cols-5 gap-1.5 mb-3">
                    {THEME_GROUPS.light.map(t => (
                      <button
                        key={t.id}
                        onClick={() => { setTheme(t.id); setShowTheme(false); }}
                        title={t.label}
                        className={`h-8 rounded-lg flex items-center justify-center text-sm transition-all cursor-pointer ${theme === t.id ? "ring-2 scale-110" : "hover:scale-105"}`}
                        style={{
                          background: "var(--bg-elevated)",
                          border: theme === t.id ? "1px solid var(--brand-primary)" : "1px solid var(--border-subtle)",
                        }}
                      >
                        {t.emoji}
                      </button>
                    ))}
                  </div>
                  <p className="text-[9px] font-black uppercase tracking-widest text-theme-muted mb-2 px-1">Accessibility</p>
                  <div className="grid grid-cols-3 gap-1.5">
                    {THEME_GROUPS.accessibility.map(t => (
                      <button
                        key={t.id}
                        onClick={() => { setTheme(t.id); setShowTheme(false); }}
                        title={t.label}
                        className="h-8 rounded-lg flex items-center justify-center gap-1.5 text-[9px] font-bold cursor-pointer transition-all hover:scale-105"
                        style={{
                          background: "var(--bg-elevated)",
                          border: theme === t.id ? "1px solid var(--brand-primary)" : "1px solid var(--border-subtle)",
                          color: "var(--text-secondary)",
                        }}
                      >
                        {t.emoji} <span className="hidden sm:inline truncate">{t.label.split(" ")[0]}</span>
                      </button>
                    ))}
                  </div>
                  {/* Current theme label */}
                  <div className="mt-3 pt-2 flex items-center gap-1.5" style={{ borderTop: "1px solid var(--border-subtle)" }}>
                    <span className="text-sm">{currentTheme?.emoji}</span>
                    <span className="text-[10px] font-bold text-theme-muted">{currentTheme?.label}</span>
                    <button onClick={toggleDark} className="ml-auto p-1 rounded-lg cursor-pointer transition-all hover:opacity-80"
                      style={{ background: "var(--bg-elevated)", border: "1px solid var(--border-subtle)" }}>
                      {isDark ? <Sun className="w-3 h-3 text-amber-400" /> : <Moon className="w-3 h-3 text-indigo-400" />}
                    </button>
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Notifications */}
        <div ref={notifRef} className="relative">
          <button
            onClick={() => { setShowNotifs(v => !v); setShowTheme(false); setShowProfile(false); }}
            className="relative w-8 h-8 rounded-xl flex items-center justify-center text-theme-muted hover:text-theme-primary cursor-pointer transition-all"
            style={{ background: "var(--bg-elevated)", border: "1px solid var(--border-subtle)" }}
          >
            <Bell className="w-3.5 h-3.5" />
            {unreadCount > 0 && (
              <span className="absolute -top-0.5 -right-0.5 w-3.5 h-3.5 rounded-full text-[8px] font-black text-white flex items-center justify-center"
                style={{ background: "var(--brand-primary)" }}>
                {unreadCount}
              </span>
            )}
          </button>

          <AnimatePresence>
            {showNotifs && (
              <motion.div
                initial={{ opacity: 0, y: 8, scale: 0.96 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: 8, scale: 0.96 }}
                transition={{ type: "spring", stiffness: 400, damping: 25 }}
                className="absolute right-0 top-11 z-50 w-72 rounded-2xl overflow-hidden shadow-2xl"
                style={{
                  background: "var(--bg-surface)",
                  border: "1px solid var(--border-default)",
                  boxShadow: "0 20px 60px rgba(0,0,0,0.6)",
                }}
              >
                <div className="flex items-center justify-between p-3 pb-0">
                  <span className="text-[10px] font-black uppercase tracking-widest text-theme-muted">Notifications</span>
                  <button onClick={markAllRead} className="text-[9px] font-bold cursor-pointer hover:underline"
                    style={{ color: "var(--text-brand)" }}>Mark all read</button>
                </div>
                <div className="p-2 space-y-1 max-h-72 overflow-y-auto">
                  {notifications.map(n => (
                    <div key={n.id}
                      className={`flex items-start gap-2.5 p-2.5 rounded-xl transition-all ${!n.read ? "opacity-100" : "opacity-60"}`}
                      style={{ background: n.read ? "transparent" : "var(--brand-muted)", border: "1px solid var(--border-subtle)" }}>
                      <span className="text-base flex-shrink-0 mt-0.5">{n.icon}</span>
                      <div className="flex-1 min-w-0">
                        <p className="text-[11px] font-bold text-theme-primary leading-tight">{n.title}</p>
                        <p className="text-[10px] text-theme-muted leading-tight mt-0.5">{n.body}</p>
                      </div>
                      <span className="text-[9px] text-theme-muted flex-shrink-0">{n.time}</span>
                    </div>
                  ))}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Profile menu */}
        <div ref={profileRef} className="relative">
          <button
            onClick={() => { setShowProfile(v => !v); setShowTheme(false); setShowNotifs(false); }}
            className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-black text-white cursor-pointer transition-all"
            style={{
              background: "linear-gradient(135deg, var(--brand-secondary), var(--brand-primary))",
              boxShadow: "0 2px 8px var(--brand-glow)",
            }}
          >
            {user?.username ? user.username.substring(0, 2).toUpperCase() : "HA"}
          </button>

          <AnimatePresence>
            {showProfile && (
              <motion.div
                initial={{ opacity: 0, y: 8, scale: 0.96 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: 8, scale: 0.96 }}
                transition={{ type: "spring", stiffness: 400, damping: 25 }}
                className="absolute right-0 top-11 z-50 w-48 rounded-2xl overflow-hidden shadow-2xl"
                style={{
                  background: "var(--bg-surface)",
                  border: "1px solid var(--border-default)",
                  boxShadow: "0 20px 60px rgba(0,0,0,0.6)",
                }}
              >
                <div className="p-3 border-b" style={{ borderColor: "var(--border-subtle)" }}>
                  <p className="text-xs font-black text-theme-primary">{user?.username || "Guest"}</p>
                  <p className="text-[10px] text-theme-muted">Sustainability OS</p>
                </div>
                <div className="p-1.5 space-y-0.5">
                  <Link href="/profile" onClick={() => setShowProfile(false)}
                    className="flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs font-bold text-theme-secondary hover:text-theme-primary cursor-pointer transition-all hover:bg-theme-elevated">
                    <User className="w-3.5 h-3.5" /> Profile
                  </Link>
                  <Link href="/?tab=settings" onClick={() => setShowProfile(false)}
                    className="flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs font-bold text-theme-secondary hover:text-theme-primary cursor-pointer transition-all">
                    <Settings className="w-3.5 h-3.5" /> Settings
                  </Link>
                  <button
                    onClick={() => { logout(); window.location.reload(); }}
                    className="w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs font-bold text-rose-400 hover:text-rose-300 cursor-pointer transition-all">
                    <LogOut className="w-3.5 h-3.5" /> Sign Out
                  </button>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>

      {/* ─── Seed Confirm Modal ───────────────────────────────────────────── */}
      <AnimatePresence>
        {showConfirm && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="glass-premium max-w-sm w-full rounded-3xl p-6 shadow-2xl flex flex-col space-y-4"
              style={{ border: "1px solid var(--border-default)" }}
            >
              <div className="flex items-center gap-3 text-amber-400">
                <div className="p-2 rounded-xl" style={{ background: "rgba(245,158,11,0.1)", border: "1px solid rgba(245,158,11,0.2)" }}>
                  <AlertTriangle className="w-5 h-5" />
                </div>
                <h3 className="font-extrabold text-theme-primary text-xs uppercase tracking-wider">Reset Demo Data</h3>
              </div>
              <p className="text-xs text-theme-secondary leading-relaxed">
                This will reset demo data and may remove existing records. Continue?
              </p>
              <div className="flex items-center justify-end gap-3 pt-1">
                <button
                  onClick={() => setShowConfirm(false)}
                  className="px-4 py-2 rounded-xl text-[10px] font-bold uppercase cursor-pointer transition-all"
                  style={{ background: "var(--bg-elevated)", border: "1px solid var(--border-subtle)", color: "var(--text-secondary)" }}
                >Cancel</button>
                <button
                  onClick={() => handleSeed(true)}
                  className="px-4 py-2 rounded-xl text-[10px] font-bold uppercase cursor-pointer text-white transition-all"
                  style={{ background: "var(--brand-primary)" }}
                >Confirm Reset</button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </header>
  );
});

export default Topbar;
