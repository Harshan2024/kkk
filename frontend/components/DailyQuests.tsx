"use client";

import React, { useState, useEffect } from "react";
import { Trophy, Bike, Plug, Leaf, Recycle, Check } from "lucide-react";
import { motion } from "framer-motion";
import api, { ChallengeProgress } from "../services/api";
import { Card } from "./ui/Card";
import { Badge } from "./ui/Badge";

const ICON_MAP: Record<string, any> = {
  Bike: Bike,
  Plug: Plug,
  Leaf: Leaf,
  Recycle: Recycle,
  Trophy: Trophy,
};

const DEFAULT_COLORS = "text-emerald-400 bg-emerald-500/10 border-emerald-500/20";

export default function DailyQuests() {
  const [challenges, setChallenges] = useState<{ daily: ChallengeProgress[]; weekly: ChallengeProgress[] }>({ daily: [], weekly: [] });
  const [isLoading, setIsLoading] = useState(true);

  const fetchChallenges = async () => {
    try {
      const data = await api.getGamificationChallenges();
      if (data) {
        setChallenges(data);
      }
    } catch (err) {
      console.error("Failed to load live quests", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchChallenges();
  }, []);

  const quests = [
    ...(challenges.daily || []).map(q => ({ ...q, type: "Daily", icon: ICON_MAP[q.icon] || Leaf })),
    ...(challenges.weekly || []).map(q => ({ ...q, type: "Weekly", icon: ICON_MAP[q.icon] || Trophy }))
  ];

  const displayQuests = quests.length > 0 ? quests : [
    {
      id: "q1",
      name: "The Velocity Shift",
      description: "Swap 5 km of driving for cycling or walking.",
      progress: 3,
      max: 5,
      xp: 150,
      icon: Bike,
      color: "text-emerald-450 bg-emerald-500/10 border-emerald-500/20",
      completed: false,
      type: "Daily"
    },
    {
      id: "q2",
      name: "Phantom Load Hunt",
      description: "Unplug 3 idle appliances for 2 hours.",
      progress: 1,
      max: 3,
      xp: 120,
      icon: Plug,
      color: "text-indigo-400 bg-indigo-500/10 border-indigo-500/20",
      completed: false,
      type: "Daily"
    },
    {
      id: "q3",
      name: "The Green Feast",
      description: "Eat a vegetarian or vegan meal.",
      progress: 1,
      max: 1,
      xp: 100,
      icon: Leaf,
      color: "text-emerald-400 bg-emerald-500/15 border-emerald-500/30",
      completed: true,
      type: "Daily"
    }
  ];

  return (
    <Card className="flex flex-col justify-between h-[360px] select-none" hover={false}>
      <div>
        {/* Header */}
        <div className="flex items-center justify-between pb-3 border-b border-white/5 mb-3">
          <div className="flex items-center space-x-2.5">
            <div className="w-6 h-6 rounded-lg bg-emerald-500/10 flex items-center justify-center border border-emerald-500/20">
              <Trophy className="w-3.5 h-3.5 text-amber-500" />
            </div>
            <h3 className="font-extrabold text-xs text-theme-secondary uppercase tracking-widest">
              Live Challenges
            </h3>
          </div>
          <span className="text-[9px] font-black uppercase text-theme-muted tracking-wider">
            Active
          </span>
        </div>

        {/* Quests List */}
        <div className="space-y-2 max-h-[220px] overflow-y-auto pr-1">
          {displayQuests.map((quest) => {
            const Icon = quest.icon;
            const isCompleted = quest.completed || quest.progress >= quest.max;
            
            return (
              <motion.div
                key={quest.id}
                whileHover={{ x: 2 }}
                className={`flex items-center justify-between p-2 rounded-2xl border transition-all duration-300 ${
                  isCompleted 
                    ? "bg-emerald-950/10 border-emerald-500/20 text-theme-muted opacity-75"
                    : "bg-white/[0.01] border-white/5 text-theme-secondary hover:bg-white/[0.02]"
                }`}
              >
                <div className="flex items-center space-x-3 min-w-0 flex-1">
                  <div className={`w-8 h-8 rounded-xl flex items-center justify-center border flex-shrink-0 ${
                    isCompleted ? "text-emerald-400 bg-emerald-500/10 border-emerald-500/20" : (quest.color || DEFAULT_COLORS)
                  }`}>
                    <Icon className="w-4 h-4" />
                  </div>
                  
                  <div className="min-w-0 pr-1.5 flex-1">
                    <div className="flex items-center gap-1.5">
                      <h4 className="text-[11px] font-black text-theme-primary truncate">{quest.name}</h4>
                      <span className="text-[7px] font-extrabold px-1.5 py-0.5 rounded bg-white/5 text-theme-muted uppercase tracking-wider">
                        {quest.type}
                      </span>
                    </div>
                    <p className="text-[9px] text-theme-muted font-bold truncate mt-0.5 leading-tight">{quest.description}</p>
                    
                    {!isCompleted && (
                      <div className="flex items-center gap-1.5 mt-1.5">
                        <div className="w-16 h-1 rounded-full bg-white/5 overflow-hidden">
                          <div 
                            className="h-full rounded-full"
                            style={{ width: `${(quest.progress / quest.max) * 100}%`, backgroundColor: "var(--brand-primary)" }}
                          />
                        </div>
                        <span className="text-[8px] text-theme-muted font-extrabold">{quest.progress}/{quest.max}</span>
                      </div>
                    )}
                  </div>
                </div>

                <div className="flex-shrink-0 flex items-center pl-2">
                  {isCompleted ? (
                    <div className="w-5 h-5 rounded-full bg-emerald-500/20 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
                      <Check className="w-3.5 h-3.5 stroke-[3px]" />
                    </div>
                  ) : (
                    <div className="flex items-center gap-1">
                      <span className="text-[9px] font-black text-theme-brand bg-emerald-500/10 px-1.5 py-0.5 rounded border border-emerald-500/20">
                        +{quest.xp} XP
                      </span>
                    </div>
                  )}
                </div>
              </motion.div>
            );
          })}
        </div>
      </div>

      <div className="w-full py-2 bg-gradient-to-r from-emerald-950/40 to-emerald-900/20 border border-emerald-500/10 rounded-xl text-[10px] font-extrabold uppercase text-theme-brand flex items-center justify-center gap-1.5">
        <span>Challenges sync automatically from logs!</span>
        <span>⚡</span>
      </div>
    </Card>
  );
}
