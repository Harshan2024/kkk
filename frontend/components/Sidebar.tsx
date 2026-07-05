"use client";

import React, { useState } from "react";
import {
  LayoutDashboard, ClipboardList, BarChart3, Trophy,
  ShoppingBag, Users, History, Settings, Flame, X, Cpu, Brain, User,
  ChevronLeft, ChevronRight, Sparkles
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { useAIStore } from "../stores/aiStore";

// ─── Types ────────────────────────────────────────────────────────────────────

interface SidebarProps {
  currentTab: string;
  onTabChange: (tab: string) => void;
  username: string;
  xp: number;
  level: number;
  streak: number;
  isOpen?: boolean;
  onClose?: () => void;
}

// ─── Nav Items ────────────────────────────────────────────────────────────────

const menuItems = [
  { id: "dashboard",   label: "Dashboard",       icon: LayoutDashboard, color: "emerald" },
  { id: "logger",      label: "Activity Logger", icon: ClipboardList,   color: "sky"     },
  { id: "analytics",  label: "Analytics",        icon: BarChart3,       color: "indigo"  },
  { id: "coach",       label: "AI Coach",         icon: Brain,           color: "purple"  },
  { id: "devices",     label: "Smart Devices",    icon: Cpu,             color: "cyan"    },
  { id: "quests",      label: "Quests",           icon: Trophy,          color: "amber"   },
  { id: "marketplace", label: "Marketplace",      icon: ShoppingBag,     color: "pink"    },
  { id: "community",   label: "Community",        icon: Users,           color: "teal"    },
  { id: "history",     label: "History",          icon: History,         color: "orange"  },
  { id: "profile",     label: "Profile",          icon: User,            color: "violet"  },
  { id: "settings",    label: "Settings",         icon: Settings,        color: "stone"   },
];

const ICON_COLOR: Record<string, string> = {
  emerald: "text-emerald-400",
  sky:     "text-sky-400",
  indigo:  "text-indigo-400",
  purple:  "text-purple-400",
  cyan:    "text-cyan-400",
  amber:   "text-amber-400",
  pink:    "text-pink-400",
  teal:    "text-teal-400",
  orange:  "text-orange-400",
  violet:  "text-violet-400",
  stone:   "text-stone-400",
};

const ICON_BG: Record<string, string> = {
  emerald: "bg-emerald-500/10 border-emerald-500/20",
  sky:     "bg-sky-500/10 border-sky-500/20",
  indigo:  "bg-indigo-500/10 border-indigo-500/20",
  purple:  "bg-purple-500/10 border-purple-500/20",
  cyan:    "bg-cyan-500/10 border-cyan-500/20",
  amber:   "bg-amber-500/10 border-amber-500/20",
  pink:    "bg-pink-500/10 border-pink-500/20",
  teal:    "bg-teal-500/10 border-teal-500/20",
  orange:  "bg-orange-500/10 border-orange-500/20",
  violet:  "bg-violet-500/10 border-violet-500/20",
  stone:   "bg-stone-500/10 border-stone-500/20",
};

// ─── Component ────────────────────────────────────────────────────────────────

export const Sidebar = React.memo(function Sidebar({
  currentTab,
  onTabChange,
  username = "Harshan R",
  xp = 150,
  level = 1,
  streak = 1,
  isOpen = false,
  onClose
}: SidebarProps) {
  const { logout, smartDevicesEnabled } = useAIStore();
  const [collapsed, setCollapsed] = useState(false);

  const initials = username ? username.substring(0, 2).toUpperCase() : "CT";
  const nextLevelXp = level * 200;
  const xpPct = Math.min(100, Math.round((xp / nextLevelXp) * 100));

  const handleTabChange = (id: string) => {
    onTabChange(id);
    if (onClose) onClose();
  };

  const sidebarWidth = collapsed ? "w-16" : "w-64";

  return (
    <>
      {/* Mobile drawer backdrop */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-25 lg:hidden"
          />
        )}
      </AnimatePresence>

      <motion.aside
        animate={{ width: collapsed ? 64 : 256 }}
        transition={{ type: "spring", stiffness: 350, damping: 25 }}
        className={`h-screen fixed left-0 top-0 flex flex-col justify-between z-30 select-none
          transition-transform duration-300 lg:translate-x-0 overflow-hidden
          ${isOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"}
        `}
        style={{ background: "var(--sidebar-bg)", borderRight: "1px solid var(--border-subtle)" }}
      >
        {/* Inner gradient overlay */}
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute top-0 right-0 w-24 h-48 opacity-30"
            style={{ background: "radial-gradient(ellipse at top right, var(--brand-muted), transparent)" }} />
        </div>

        <div className="flex flex-col h-full overflow-hidden relative z-10">
          {/* ─── Header / Logo ───────────────────────────────────────────── */}
          <div className="flex items-center justify-between px-3 py-4 flex-shrink-0">
            <motion.div
              animate={{ opacity: collapsed ? 0 : 1, width: collapsed ? 0 : "auto" }}
              transition={{ duration: 0.2 }}
              className="flex items-center gap-2.5 overflow-hidden"
            >
              {/* Logo icon */}
              <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-emerald-400 to-emerald-700 flex items-center justify-center shadow-lg flex-shrink-0"
                style={{ boxShadow: "0 4px 12px var(--brand-glow)" }}>
                <span className="text-white font-black text-xs tracking-tighter">CT</span>
              </div>
              <div className="whitespace-nowrap">
                <h1 className="text-sm font-black tracking-tight text-theme-primary flex items-center gap-1">
                  CarbonTracker <span style={{ color: "var(--text-brand)" }} className="text-xs">AI</span>
                </h1>
                <span className="text-[9px] font-bold text-theme-muted uppercase tracking-widest block leading-none">
                  Sustainability OS
                </span>
              </div>
            </motion.div>

            {/* Collapsed logo */}
            {collapsed && (
              <motion.div
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                className="w-8 h-8 rounded-xl bg-gradient-to-br from-emerald-400 to-emerald-700 flex items-center justify-center shadow-lg mx-auto"
                style={{ boxShadow: "0 4px 12px var(--brand-glow)" }}
              >
                <span className="text-white font-black text-xs">CT</span>
              </motion.div>
            )}

            {/* Mobile close */}
            {onClose && !collapsed && (
              <button
                onClick={onClose}
                className="lg:hidden p-1.5 rounded-lg text-theme-muted hover:text-theme-primary transition-all cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            )}
          </div>

          {/* ─── Navigation ──────────────────────────────────────────────── */}
          <nav className="flex-1 overflow-y-auto overflow-x-hidden px-2 space-y-0.5 pb-2">
            {menuItems.filter((item) => item.id !== "devices" || smartDevicesEnabled).map((item) => {
              const Icon = item.icon;
              const isActive = currentTab === item.id;
              const color = item.color;

              return (
                <button
                  key={item.id}
                  onClick={() => handleTabChange(item.id)}
                  title={collapsed ? item.label : undefined}
                  className={`w-full flex items-center gap-3 px-2.5 py-2.5 rounded-xl text-xs font-bold
                    tracking-wide transition-all duration-200 group relative cursor-pointer
                    ${isActive
                      ? "text-theme-primary"
                      : "text-theme-muted hover:text-theme-primary"
                    }`}
                  style={isActive ? {
                    background: "var(--sidebar-active)",
                    border: `1px solid var(--border-default)`,
                  } : {
                    background: "transparent",
                    border: "1px solid transparent",
                  }}
                >
                  {/* Animated active indicator */}
                  {isActive && (
                    <motion.div
                      layoutId="activeIndicator"
                      className="absolute left-0 w-0.5 h-5 rounded-r-full"
                      style={{ background: "var(--brand-primary)" }}
                      transition={{ type: "spring", stiffness: 380, damping: 30 }}
                    />
                  )}

                  {/* Icon */}
                  <div className={`w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0 border transition-all duration-200
                    ${isActive
                      ? `${ICON_BG[color]}`
                      : "border-transparent group-hover:border-white/5 group-hover:bg-white/[0.03]"
                    }`}
                  >
                    <Icon className={`w-3.5 h-3.5 transition-all duration-200
                      ${isActive ? ICON_COLOR[color] : "text-theme-muted group-hover:text-theme-secondary"}`}
                    />
                  </div>

                  {/* Label */}
                  <motion.span
                    animate={{ opacity: collapsed ? 0 : 1, width: collapsed ? 0 : "auto" }}
                    transition={{ duration: 0.15 }}
                    className="whitespace-nowrap overflow-hidden"
                  >
                    {item.label}
                  </motion.span>
                </button>
              );
            })}
          </nav>

          {/* ─── Footer ──────────────────────────────────────────────────── */}
          <div className="flex-shrink-0 p-2 space-y-2 border-t"
            style={{ borderColor: "var(--border-subtle)" }}>

            {/* Streak Block */}
            {!collapsed && (
              <motion.div
                animate={{ opacity: collapsed ? 0 : 1 }}
                className="rounded-2xl p-3 space-y-2"
                style={{ background: "var(--bg-elevated)", border: "1px solid var(--border-subtle)" }}
              >
                <div className="flex items-center justify-between text-[11px] font-bold">
                  <span className="flex items-center gap-1.5 text-orange-400">
                    <Flame className="w-3.5 h-3.5 text-orange-500 fill-orange-500 animate-pulse" />
                    {streak} Day Streak
                  </span>
                  <span className="text-[9px] text-theme-muted uppercase tracking-wide">Keep it up!</span>
                </div>
                <div className="w-full h-1.5 rounded-full overflow-hidden"
                  style={{ background: "var(--bg-overlay)" }}>
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${Math.min(100, (streak / 7) * 100)}%` }}
                    transition={{ duration: 0.8, ease: "easeOut" }}
                    className="h-full rounded-full bg-gradient-to-r from-orange-500 to-amber-400"
                  />
                </div>
              </motion.div>
            )}

            {/* Invite Friends */}
            {!collapsed && (
              <motion.div
                animate={{ opacity: collapsed ? 0 : 1 }}
                className="relative rounded-2xl p-3.5 overflow-hidden"
                style={{
                  background: "linear-gradient(135deg, rgba(99,102,241,0.15) 0%, rgba(139,92,246,0.08) 100%)",
                  border: "1px solid rgba(99,102,241,0.15)"
                }}
              >
                <div className="absolute top-0 right-0 w-16 h-16 bg-indigo-500/10 blur-xl rounded-full pointer-events-none" />
                <div className="flex items-center gap-1.5 mb-1">
                  <Sparkles className="w-3 h-3 text-indigo-400" />
                  <h5 className="text-[11px] font-black text-white uppercase tracking-wider">Invite Friends</h5>
                </div>
                <p className="text-[10px] text-stone-400 leading-tight mb-2.5">
                  Earn <span className="text-indigo-400 font-extrabold">100 XP</span> for each friend!
                </p>
                <button className="w-full py-1.5 rounded-xl text-white font-extrabold text-[10px] uppercase tracking-wider cursor-pointer transition-all active:scale-95"
                  style={{ background: "linear-gradient(135deg, #6366f1, #7c3aed)" }}>
                  Invite Now
                </button>
              </motion.div>
            )}

            {/* User Card */}
            <div className={`flex items-center rounded-2xl p-2.5 transition-all
              ${collapsed ? "justify-center" : "justify-between gap-2"}`}
              style={{ background: "var(--bg-elevated)", border: "1px solid var(--border-subtle)" }}
            >
              {/* Avatar */}
              <div className="relative flex-shrink-0">
                <div className="w-8 h-8 rounded-full overflow-hidden flex items-center justify-center text-xs font-black text-white"
                  style={{
                    background: "linear-gradient(135deg, var(--brand-secondary), var(--brand-primary))",
                    boxShadow: "0 2px 8px var(--brand-glow)"
                  }}>
                  {initials}
                </div>
                {/* XP ring progress */}
                <svg className="absolute -inset-0.5 w-9 h-9 -rotate-90" viewBox="0 0 36 36">
                  <circle cx="18" cy="18" r="16" fill="none" strokeWidth="1.5"
                    stroke="rgba(255,255,255,0.05)" />
                  <circle cx="18" cy="18" r="16" fill="none" strokeWidth="1.5"
                    stroke="var(--brand-primary)" strokeLinecap="round"
                    strokeDasharray={`${xpPct} 100`}
                    style={{ opacity: 0.6 }} />
                </svg>
              </div>

              {!collapsed && (
                <>
                  <div className="flex-1 min-w-0">
                    <p className="text-[11px] font-black text-theme-primary truncate">{username}</p>
                    <p className="text-[9px] text-theme-muted font-bold">Lvl {level} · {xp} XP</p>
                  </div>
                  <button
                    onClick={() => { logout(); window.location.reload(); }}
                    className="text-[9px] font-extrabold uppercase text-rose-400 hover:text-rose-300 cursor-pointer transition-colors flex-shrink-0"
                  >
                    Exit
                  </button>
                </>
              )}
            </div>
          </div>
        </div>

        {/* ─── Collapse Toggle (desktop only) ──────────────────────────── */}
        <button
          onClick={() => setCollapsed(v => !v)}
          className="absolute -right-3 top-20 hidden lg:flex w-6 h-6 rounded-full items-center justify-center text-theme-muted hover:text-theme-primary cursor-pointer transition-all z-10 shadow-lg"
          style={{ background: "var(--bg-elevated)", border: "1px solid var(--border-default)" }}
        >
          {collapsed
            ? <ChevronRight className="w-3.5 h-3.5" />
            : <ChevronLeft className="w-3.5 h-3.5" />
          }
        </button>
      </motion.aside>
    </>
  );
});

export default Sidebar;
