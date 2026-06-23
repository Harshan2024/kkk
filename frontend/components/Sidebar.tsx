"use client";

import React from "react";
import { 
  LayoutDashboard, ClipboardList, BarChart3, Trophy, 
  ShoppingBag, Users, History, Settings, Flame, Gift, X, Cpu, Brain
} from "lucide-react";
import { motion } from "framer-motion";

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

export default function Sidebar({ 
  currentTab, 
  onTabChange, 
  username = "Harshan R", 
  xp = 150, 
  level = 1,
  streak = 1,
  isOpen = false,
  onClose
}: SidebarProps) {
  const menuItems = [
    { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
    { id: "logger", label: "Activity Logger", icon: ClipboardList },
    { id: "analytics", label: "Analytics", icon: BarChart3 },
    { id: "coach", label: "AI Coach", icon: Brain },
    { id: "devices", label: "Smart Devices", icon: Cpu },
    { id: "quests", label: "Quests", icon: Trophy },
    { id: "marketplace", label: "Marketplace", icon: ShoppingBag },
    { id: "community", label: "Community", icon: Users },
    { id: "history", label: "History", icon: History },
    { id: "settings", label: "Settings", icon: Settings },
  ];

  return (
    <>
      {/* Mobile drawer backdrop */}
      {isOpen && (
        <div 
          onClick={onClose} 
          className="fixed inset-0 bg-black/60 backdrop-blur-xs z-25 lg:hidden"
        />
      )}
      
      <aside className={`w-64 h-screen fixed left-0 top-0 bg-[#040805] border-r border-emerald-950/30 flex flex-col justify-between p-4 z-30 select-none transition-transform duration-300 lg:translate-x-0 ${
        isOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
      }`}>
        <div>
          {/* App Logo */}
          <div className="flex items-center justify-between px-2 py-3 mb-5">
            <div className="flex items-center space-x-2.5">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-emerald-500 to-teal-700 flex items-center justify-center shadow-lg shadow-emerald-500/20">
                <span className="text-white font-black text-sm tracking-tighter">CT</span>
              </div>
              <div>
                <h1 className="text-sm font-black tracking-tight text-white flex items-center gap-1">
                  CarbonTracker <span className="text-emerald-400 text-xs">AI</span>
                </h1>
                <span className="text-[9px] font-bold text-stone-500 uppercase tracking-widest block leading-none">
                  Sustainability OS
                </span>
              </div>
            </div>
            {onClose && (
              <button 
                onClick={onClose} 
                className="lg:hidden p-1.5 rounded-lg text-stone-500 hover:text-white transition-all cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            )}
          </div>

          {/* Navigation Rail */}
          <nav className="space-y-1">
            {menuItems.map((item) => {
              const Icon = item.icon;
              const isActive = currentTab === item.id;
              
              return (
                <button
                  key={item.id}
                  onClick={() => {
                    onTabChange(item.id);
                    if (onClose) onClose();
                  }}
                  className={`w-full flex items-center space-x-3 px-3 py-2.5 rounded-xl text-xs font-bold tracking-wide transition-all group relative cursor-pointer ${
                    isActive 
                      ? "bg-emerald-950/20 text-emerald-400 border border-emerald-500/10 shadow-sm" 
                      : "text-stone-400 hover:text-stone-200 hover:bg-white/[0.02]"
                  }`}
                >
                  {isActive && (
                    <motion.div 
                      layoutId="activeIndicator"
                      className="absolute left-0 w-1 h-5 rounded-r bg-emerald-400"
                      transition={{ type: "spring", stiffness: 380, damping: 30 }}
                    />
                  )}
                  <Icon className={`w-4 h-4 transition-transform group-hover:scale-105 ${isActive ? "text-emerald-400" : "text-stone-400"}`} />
                  <span>{item.label}</span>
                </button>
              );
            })}
          </nav>
        </div>

        {/* Footer widgets */}
        <div className="space-y-4 pt-4 border-t border-white/5">
          {/* User Card */}
          <div className="flex items-center space-x-3 bg-white/[0.02] border border-white/5 rounded-2xl p-3">
            <div className="w-10 h-10 rounded-full overflow-hidden border border-emerald-500/20 bg-stone-900 flex-shrink-0 flex items-center justify-center text-xs font-bold text-white">
              HR
            </div>
            <div className="min-w-0">
              <h4 className="text-xs font-black text-white truncate">{username}</h4>
              <p className="text-[10px] text-stone-500 font-bold mt-0.5">
                Level {level} • {xp} XP
              </p>
            </div>
          </div>

          {/* Streak Block */}
          <div className="bg-[#08120a] border border-emerald-950/44 rounded-2xl p-3.5 space-y-2">
            <div className="flex items-center justify-between text-[11px] font-bold text-stone-400">
              <span className="flex items-center gap-1.5 text-orange-450">
                <Flame className="w-3.5 h-3.5 text-orange-500 fill-orange-500 animate-pulse" />
                {streak} Day Streak
              </span>
              <span className="text-[9px] text-stone-550 uppercase">Keep it going!</span>
            </div>
            <div className="w-full h-1.5 rounded-full bg-white/5 overflow-hidden">
              <div 
                className="h-full rounded-full bg-gradient-to-r from-orange-500 to-amber-400" 
                style={{ width: `${Math.min(100, (streak / 7) * 100)}%` }}
              ></div>
            </div>
          </div>

          {/* Invite Friends card */}
          <div className="relative bg-gradient-to-br from-indigo-950/40 to-purple-950/20 border border-indigo-500/10 rounded-2xl p-4 overflow-hidden shadow-lg shadow-black/30">
            <h5 className="text-[11px] font-black text-white uppercase tracking-wider">Invite Friends</h5>
            <p className="text-[10px] text-stone-400 leading-tight mt-1">
              Earn <span className="text-indigo-400 font-extrabold">100 XP</span> for each friend you invite!
            </p>
            
            <button className="mt-3 w-full py-1.5 rounded-xl bg-gradient-to-r from-indigo-650 to-indigo-600 hover:from-indigo-600 hover:to-indigo-550 text-white font-extrabold text-[10px] uppercase transition-all tracking-wider cursor-pointer shadow shadow-indigo-650/20 active:scale-95">
              Invite Now
            </button>
          </div>
        </div>
      </aside>
    </>
  );
}
