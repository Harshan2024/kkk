"use client";

import React, { useState } from "react";
import { Leaf, RefreshCw, CheckCircle2, Globe, AlertTriangle } from "lucide-react";
import { useAIStore } from "../stores/aiStore";
import { api } from "../services/api";

interface NavbarProps {
  onRefresh: () => void;
  region: string;
  onRegionChange: (region: string) => void;
}

const REGIONS = [
  { value: "Global", label: "Global Grid" },
  { value: "India", label: "India Grid" },
  { value: "USA", label: "USA Grid" },
  { value: "California", label: "California Grid" },
  { value: "Germany", label: "Germany Grid" },
  { value: "France", label: "France Grid" }
];

export default function Navbar({ onRefresh, region, onRegionChange }: NavbarProps) {
  const [seeding, setSeeding] = useState(false);
  const [seeded, setSeeded] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const { setToastError } = useAIStore();

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
        console.error(err);
        setToastError(err.message || "Genuine system failure occurred during seeding.");
      } finally {
        setSeeding(false);
      }
    } else {
      setShowConfirm(false);
      setSeeding(true);
      try {
        const res = await api.seedDatabase("demo_user", true);
        if (!res.success) {
          setToastError(res.error || "Seeding failed.");
          return;
        }
        setSeeded(true);
        onRefresh();
        setTimeout(() => setSeeded(false), 3000);
      } catch (err: any) {
        console.error(err);
        setToastError(err.message || "Genuine system failure occurred during seeding.");
      } finally {
        setSeeding(false);
      }
    }
  };

  return (
    <header className="sticky top-0 z-50 w-full border-b border-white/10 dark:border-white/5 bg-background-light/75 dark:bg-background-dark/75 backdrop-blur-md transition-colors duration-300">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Branding Logo */}
        <div className="flex items-center space-x-2">
          <div className="w-10 h-10 rounded-xl bg-forest-600 flex items-center justify-center shadow-lg shadow-forest-500/20">
            <Leaf className="w-5.5 h-5.5 text-white" />
          </div>
          <div>
            <span className="text-xl font-bold tracking-tight text-forest-800 dark:text-forest-400">
              Carbon<span className="text-earth-600 dark:text-white">Tracker</span>
            </span>
            <div className="text-[10px] uppercase font-bold tracking-wider text-forest-600/80 dark:text-forest-500/80">
              Sustainability Startup
            </div>
          </div>
        </div>

        {/* Demo Controls & Region Selection */}
        <div className="flex items-center space-x-3">
          {/* Region Dropdown Selector */}
          <div className="relative flex items-center bg-white/5 border border-white/10 rounded-xl px-3 py-1.5 text-xs sm:text-sm font-semibold transition-all duration-300">
            <Globe className="w-4 h-4 text-forest-500 mr-2" />
            <select
              value={region}
              onChange={(e) => onRegionChange(e.target.value)}
              className="bg-transparent text-earth-800 dark:text-stone-100 focus:outline-none cursor-pointer pr-1"
            >
              {REGIONS.map((reg) => (
                <option key={reg.value} value={reg.value} className="bg-background-light dark:bg-background-dark text-earth-800 dark:text-stone-100">
                  {reg.label}
                </option>
              ))}
            </select>
          </div>

          <button
            onClick={handleSeed}
            disabled={seeding}
            className={`flex items-center space-x-2 px-4 py-2 rounded-xl text-xs sm:text-sm font-semibold border transition-all duration-300 ${
              seeded
                ? "bg-forest-600/10 text-forest-500 border-forest-500/30"
                : "bg-white/5 hover:bg-forest-600/15 text-earth-800 dark:text-forest-100 hover:text-forest-600 dark:hover:text-forest-400 border-white/10 hover:border-forest-500/25 active:scale-95"
            }`}
          >
            {seeding ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin text-forest-500" />
                <span className="hidden sm:inline">Seeding database...</span>
                <span className="sm:hidden">Seeding...</span>
              </>
            ) : seeded ? (
              <>
                <CheckCircle2 className="w-4 h-4 text-forest-500" />
                <span className="hidden sm:inline">Demo seeded!</span>
                <span className="sm:hidden">Seeded!</span>
              </>
            ) : (
              <>
                <RefreshCw className="w-4 h-4 text-forest-500" />
                <span>Reset & Seed</span>
              </>
            )}
          </button>
        </div>
      </div>

      {showConfirm && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
          <div className="glass-card max-w-sm w-full rounded-3xl p-6 border border-emerald-500/20 bg-background-light dark:bg-background-dark shadow-2xl flex flex-col space-y-4">
            <div className="flex items-center space-x-3 text-amber-500">
              <div className="p-2 bg-amber-500/10 border border-amber-500/20 rounded-xl">
                <AlertTriangle className="w-5 h-5" />
              </div>
              <h3 className="font-extrabold text-earth-800 dark:text-stone-200 text-xs uppercase tracking-wider">
                Reset Demo Data
              </h3>
            </div>
            
            <p className="text-xs text-stone-500 dark:text-stone-400 leading-relaxed">
              This action will reset demo data and may remove existing records. Continue?
            </p>
            
            <div className="flex items-center justify-end space-x-3 pt-2">
              <button
                onClick={() => setShowConfirm(false)}
                className="px-4 py-2 rounded-xl text-xs font-semibold text-stone-500 hover:text-earth-800 dark:text-stone-400 dark:hover:text-white bg-white/5 border border-white/10 dark:border-white/5 hover:bg-white/10 transition-all cursor-pointer"
              >
                Cancel
              </button>
              <button
                onClick={() => handleSeed(true)}
                className="px-4 py-2 rounded-xl text-xs font-semibold text-white bg-emerald-600 hover:bg-emerald-500 border border-emerald-500/20 transition-all cursor-pointer"
              >
                Confirm Reset
              </button>
            </div>
          </div>
        </div>
      )}
    </header>
  );
}
