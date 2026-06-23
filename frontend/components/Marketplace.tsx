"use client";

import React, { useState, useEffect } from "react";
import { ShoppingBag, Zap, Shield, Palette, Award, FileText, CheckCircle2, AlertCircle } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import api, { VirtualReward, GamificationProfile } from "../services/api";
import { getSafeRewards } from "../utils/rewardsHelper";

const ICON_MAP: Record<string, any> = {
  shield: Shield,
  palette: Palette,
  award: Award,
  file: FileText,
};

export default function Marketplace() {
  const [profile, setProfile] = useState<GamificationProfile | null>(null);
  const [rewards, setRewards] = useState<VirtualReward[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [toast, setToast] = useState<{ type: "success" | "error"; message: string } | null>(null);

  const loadData = async () => {
    setIsLoading(true);
    try {
      const pData = await api.getGamificationProfile();
      setProfile(pData);

      const rResponse = await api.getGamificationRewards();
      const validatedRewards = getSafeRewards(rResponse?.rewards ?? []);
      setRewards(validatedRewards);
    } catch (err) {
      console.error("Failed to load marketplace data", err);
      setRewards([]);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const safeRewards = Array.isArray(rewards) ? rewards : [];

  const handleRedeem = async (rewardId: string) => {
    try {
      const res = await api.redeemVirtualReward(rewardId);
      if (res.status === "success") {
        setToast({ type: "success", message: res.message });
        loadData();
      }
    } catch (err: any) {
      const msg = err?.message || "Failed to redeem reward";
      setToast({ type: "error", message: msg });
    }
  };

  useEffect(() => {
    if (toast) {
      const timer = setTimeout(() => setToast(null), 4000);
      return () => clearTimeout(timer);
    }
  }, [toast]);

  return (
    <div className="space-y-6 select-none relative">
      {/* Toast Notification */}
      <AnimatePresence>
        {toast && (
          <motion.div
            initial={{ opacity: 0, y: -20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -20, scale: 0.95 }}
            className="fixed top-6 right-6 z-[100] max-w-sm"
          >
            <div className={`glass-card rounded-2xl p-4 border flex items-start gap-3 shadow-xl ${
              toast.type === "success" 
                ? "border-emerald-500/30 bg-emerald-500/10 shadow-emerald-500/5 text-emerald-400" 
                : "border-rose-500/30 bg-rose-500/10 shadow-rose-500/5 text-rose-450"
            }`}>
              {toast.type === "success" ? <CheckCircle2 className="w-5 h-5 flex-shrink-0" /> : <AlertCircle className="w-5 h-5 flex-shrink-0" />}
              <div>
                <p className="text-xs font-bold leading-relaxed">{toast.message}</p>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Header card with current XP */}
      <div className="glass-card rounded-3xl p-6 border border-emerald-500/10 bg-gradient-to-br from-emerald-950/5 via-[#080d0a]/40 to-[#080d0a]/10 relative overflow-hidden flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div className="absolute top-0 right-0 w-32 h-32 bg-emerald-500/5 blur-[55px] pointer-events-none rounded-full" />
        <div className="flex items-center space-x-3.5">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-emerald-500/20 to-teal-700/20 border border-emerald-500/30 flex items-center justify-center shadow-lg shadow-emerald-500/5">
            <ShoppingBag className="w-6 h-6 text-emerald-400" />
          </div>
          <div>
            <h1 className="text-lg font-black tracking-tight text-white flex items-center gap-1.5">
              Virtual Rewards Shop <span className="text-[10px] font-black px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 uppercase tracking-widest">XP Redemption</span>
            </h1>
            <p className="text-[11px] font-bold text-stone-500 mt-0.5">
              Accrue XP from green choices and trade them in for virtual badges and profile titles.
            </p>
          </div>
        </div>

        {profile && (
          <div className="flex items-center gap-3 bg-stone-950 border border-white/5 px-4 py-2.5 rounded-2xl">
            <Zap className="w-5 h-5 text-amber-400 fill-amber-400 animate-pulse" />
            <div>
              <span className="text-[8px] font-black text-stone-500 uppercase tracking-wider block">Available Balance</span>
              <span className="text-sm font-black text-white">{profile.available_xp} <span className="text-[10px] text-stone-400 font-bold">XP</span></span>
            </div>
          </div>
        )}
      </div>

      {isLoading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {[1, 2, 3, 4].map(idx => (
            <div key={idx} className="glass-card rounded-2xl p-5 h-[160px] animate-pulse bg-white/5 border border-white/5" />
          ))}
        </div>
      ) : safeRewards.length === 0 ? (
        <div className="w-full py-12 text-center border border-dashed border-white/5 rounded-3xl bg-white/[0.01]">
          <span className="text-xs text-stone-500 font-extrabold uppercase tracking-widest animate-pulse">
            No rewards available yet.
          </span>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {(Array.isArray(rewards) ? rewards : []).map(item => {
            const Icon = ICON_MAP[item.icon] || Shield;
            const canAfford = profile ? profile.available_xp >= item.cost : false;

            return (
              <div 
                key={item.id}
                className={`glass-card rounded-2xl p-5 border transition-all duration-300 flex flex-col justify-between h-[160px] ${
                  item.redeemed 
                    ? "bg-emerald-950/[0.03] border-emerald-500/15" 
                    : "bg-white/[0.01] border-white/5 hover:border-emerald-500/10"
                }`}
              >
                <div className="flex items-start gap-4">
                  <div className={`w-10 h-10 rounded-xl border flex items-center justify-center flex-shrink-0 ${
                    item.redeemed 
                      ? "text-emerald-400 bg-emerald-500/10 border-emerald-500/20"
                      : "text-stone-400 bg-white/5 border-white/5"
                  }`}>
                    <Icon className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="text-xs font-black text-white uppercase tracking-wider">{item.name}</h3>
                    <p className="text-[10px] text-stone-500 font-bold leading-relaxed mt-1">{item.description}</p>
                  </div>
                </div>

                <div className="flex items-center justify-between border-t border-white/5 pt-3 mt-3">
                  <div className="flex items-center gap-1">
                    <span className="text-[9px] font-black text-amber-400 bg-amber-500/10 px-1.5 py-0.5 rounded border border-amber-500/20">
                      {item.cost} XP
                    </span>
                  </div>

                  {item.redeemed ? (
                    <span className="text-[9px] font-black uppercase text-emerald-450 bg-emerald-500/15 border border-emerald-500/20 px-3 py-1.5 rounded-xl">
                      Redeemed ✓
                    </span>
                  ) : (
                    <button
                      onClick={() => handleRedeem(item.id)}
                      disabled={!canAfford}
                      className={`px-3 py-1.5 rounded-xl font-extrabold text-[10px] uppercase transition-all tracking-wider cursor-pointer active:scale-95 ${
                        canAfford 
                          ? "bg-emerald-600 hover:bg-emerald-500 text-white shadow shadow-emerald-600/20" 
                          : "bg-white/5 text-stone-600 border border-white/5 cursor-not-allowed"
                      }`}
                    >
                      Redeem Reward
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
