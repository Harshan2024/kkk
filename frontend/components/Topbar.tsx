"use client";

import React, { useState } from "react";
import { Bell, HelpCircle, RefreshCw, CheckCircle2, Globe } from "lucide-react";
import { useAIStore } from "../stores/aiStore";
import { api } from "../services/api";

interface TopbarProps {
  onRefresh: () => void;
  region: string;
  onRegionChange: (region: string) => void;
}

const REGIONS = [
  { value: "Global", label: "Forest Green" },
  { value: "India", label: "Neon Emerald" },
  { value: "USA", label: "Slate Blue" },
  { value: "California", label: "Solar Amber" },
  { value: "Germany", label: "Wind Teal" },
  { value: "France", label: "Hydric Indigo" }
];

export default function Topbar({ onRefresh, region, onRegionChange }: TopbarProps) {
  const [seeding, setSeeding] = useState(false);
  const [seeded, setSeeded] = useState(false);

  const handleSeed = async () => {
    setSeeding(true);
    try {
      await api.seedDatabase();
      setSeeded(true);
      onRefresh();
      setTimeout(() => setSeeded(false), 3000);
    } catch (err) {
      console.error(err);
    } finally {
      setSeeding(false);
    }
  };

  const getActiveLabel = () => {
    const found = REGIONS.find((r) => r.value === region);
    return found ? found.label : "Forest Green";
  };

  return (
    <header className="sticky top-0 z-20 w-full bg-[#080d0a]/65 backdrop-blur-md border-b border-emerald-950/20 px-8 py-3.5 flex items-center justify-between select-none">
      <div className="flex items-center space-x-3">
        {/* Dynamic status display */}
        <span className="text-[10px] text-emerald-500 bg-emerald-500/10 border border-emerald-500/20 px-2.5 py-1 rounded-full uppercase tracking-widest font-black flex items-center gap-1.5 animate-pulse">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
          AI Sync Enabled
        </span>
      </div>

      <div className="flex items-center space-x-5">
        {/* Seeding Button for developer demo */}
        <button
          onClick={handleSeed}
          disabled={seeding}
          className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-xl text-[10px] font-extrabold uppercase tracking-wider border transition-all duration-300 ${
            seeded
              ? "bg-emerald-950/20 text-emerald-400 border-emerald-500/20"
              : "bg-white/[0.02] border-white/5 text-stone-400 hover:text-stone-200 hover:bg-white/[0.04] active:scale-95 cursor-pointer"
          }`}
        >
          {seeding ? (
            <>
              <RefreshCw className="w-3 h-3 animate-spin text-emerald-400" />
              <span>Seeding...</span>
            </>
          ) : seeded ? (
            <>
              <CheckCircle2 className="w-3 h-3 text-emerald-400" />
              <span>Seeded!</span>
            </>
          ) : (
            <>
              <RefreshCw className="w-3 h-3 text-emerald-500" />
              <span>Reset & Seed</span>
            </>
          )}
        </button>

        {/* Custom Theme (Region) Dropdown Selector */}
        <div className="relative flex items-center bg-white/[0.02] hover:bg-white/[0.04] border border-white/5 rounded-xl px-3 py-1.5 text-xs font-bold transition-all select-none">
          <span className="text-stone-400 mr-1">Theme: </span>
          <span className="text-emerald-400 flex items-center gap-1 cursor-pointer font-bold">
            🌲 {getActiveLabel()}
          </span>
          <select
            value={region}
            onChange={(e) => onRegionChange(e.target.value)}
            className="absolute inset-0 opacity-0 cursor-pointer w-full font-bold"
          >
            {REGIONS.map((reg) => (
              <option key={reg.value} value={reg.value} className="bg-[#0b120f] text-white">
                🌲 {reg.label} ({reg.value} Grid)
              </option>
            ))}
          </select>
        </div>

        {/* Notifications Icon */}
        <button className="relative w-8 h-8 rounded-xl bg-white/[0.02] hover:bg-white/[0.04] border border-white/5 flex items-center justify-center text-stone-400 hover:text-white transition-all cursor-pointer">
          <Bell className="w-4 h-4" />
          <span className="absolute top-1 right-1 w-2 h-2 rounded-full bg-emerald-400 border-2 border-[#080d0a]"></span>
        </button>

        {/* Help Icon */}
        <button className="w-8 h-8 rounded-xl bg-white/[0.02] hover:bg-white/[0.04] border border-white/5 flex items-center justify-center text-stone-400 hover:text-white transition-all cursor-pointer font-bold">
          <HelpCircle className="w-4 h-4" />
        </button>

        {/* User profile avatar */}
        <div className="w-8 h-8 rounded-full overflow-hidden border border-emerald-500/20 bg-stone-900 flex-shrink-0 flex items-center justify-center text-xs font-bold text-white shadow shadow-emerald-500/10 cursor-pointer hover:border-emerald-400 transition-colors">
          HR
        </div>
      </div>
    </header>
  );
}
