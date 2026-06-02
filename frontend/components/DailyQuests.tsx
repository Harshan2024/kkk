"use client";

import React from "react";
import { Trophy, Bike, Plug, Leaf, Recycle, ChevronRight, Check } from "lucide-react";
import { motion } from "framer-motion";
import { useAIStore } from "../stores/aiStore";

interface Quest {
  id: string;
  name: string;
  description: string;
  progress: number;
  max: number;
  xp: number;
  icon: any;
  color: string;
}

const ICON_MAP: Record<string, any> = {
  Bike: Bike,
  Plug: Plug,
  Leaf: Leaf,
  Recycle: Recycle,
};

export default function DailyQuests() {
  const { summary } = useAIStore();

  const quests: Quest[] = summary?.quests?.map((q) => ({
    ...q,
    icon: ICON_MAP[q.icon] || Leaf
  })) || [
    {
      id: "q1",
      name: "The Velocity Shift",
      description: "Swap 5 km of driving for cycling or walking.",
      progress: 3,
      max: 5,
      xp: 150,
      icon: Bike,
      color: "text-emerald-450 bg-emerald-500/10 border-emerald-500/20"
    },
    {
      id: "q2",
      name: "Phantom Load Hunt",
      description: "Unplug 3 idle appliances for 2 hours.",
      progress: 1,
      max: 3,
      xp: 120,
      icon: Plug,
      color: "text-indigo-400 bg-indigo-500/10 border-indigo-500/20"
    },
    {
      id: "q3",
      name: "The Green Feast",
      description: "Eat a vegetarian or vegan meal.",
      progress: 1,
      max: 1,
      xp: 100,
      icon: Leaf,
      color: "text-emerald-400 bg-emerald-500/15 border-emerald-500/30"
    },
    {
      id: "q4",
      name: "Zero Plastic Hero",
      description: "Avoid single-use plastics today.",
      progress: 0,
      max: 1,
      xp: 80,
      icon: Recycle,
      color: "text-emerald-550 bg-emerald-600/10 border-emerald-500/10"
    }
  ];

  const overallProgress = quests.length > 0 
    ? quests.reduce((acc, curr) => acc + (curr.progress / curr.max), 0) / quests.length
    : 0;

  return (
    <div className="glass-card rounded-3xl p-5 sm:p-6 transition-all duration-300 flex flex-col justify-between h-[360px] select-none">
      <div>
        {/* Header */}
        <div className="flex items-center justify-between pb-3 border-b border-white/5 mb-3">
          <div className="flex items-center space-x-2.5">
            <div className="w-6 h-6 rounded-lg bg-emerald-500/10 flex items-center justify-center border border-emerald-500/20">
              <Trophy className="w-3.5 h-3.5 text-amber-500" />
            </div>
            <h3 className="font-extrabold text-xs text-stone-300 uppercase tracking-widest">
              Daily Eco-Quests
            </h3>
          </div>
          <button className="text-[10px] text-emerald-400 hover:text-emerald-350 font-extrabold uppercase transition-colors">
            View All
          </button>
        </div>

        {/* Quests List */}
        <div className="space-y-2 max-h-[220px] overflow-y-auto pr-1">
          {quests.map((quest) => {
            const Icon = quest.icon;
            const isCompleted = quest.progress === quest.max;
            
            return (
              <motion.div
                key={quest.id}
                whileHover={{ x: 3 }}
                className={`flex items-center justify-between p-2 rounded-2xl border transition-all duration-300 ${
                  isCompleted 
                    ? "bg-emerald-950/10 border-emerald-500/20 text-stone-400 opacity-75"
                    : "bg-white/[0.01] border-white/5 text-stone-300 hover:bg-white/[0.02]"
                }`}
              >
                {/* Left Side: Icon & Details */}
                <div className="flex items-center space-x-3 min-w-0 flex-1">
                  {/* Icon */}
                  <div className={`w-8 h-8 rounded-xl flex items-center justify-center border flex-shrink-0 ${quest.color}`}>
                    <Icon className="w-4 h-4" />
                  </div>
                  
                  {/* Text Details */}
                  <div className="min-w-0 pr-1.5">
                    <h4 className="text-[11px] font-black text-white truncate">{quest.name}</h4>
                    <p className="text-[9px] text-stone-500 font-bold truncate mt-0.5 leading-tight">{quest.description}</p>
                    
                    {/* Linear Progress bar */}
                    {!isCompleted && (
                      <div className="flex items-center gap-1.5 mt-1.5">
                        <div className="w-16 h-1 rounded-full bg-white/5 overflow-hidden">
                          <div 
                            className="h-full rounded-full bg-emerald-500"
                            style={{ width: `${(quest.progress / quest.max) * 100}%` }}
                          ></div>
                        </div>
                        <span className="text-[8px] text-stone-500 font-extrabold">{quest.progress}/{quest.max}</span>
                      </div>
                    )}
                  </div>
                </div>

                {/* Right Side: Reward / Completion Badge */}
                <div className="flex-shrink-0 flex items-center pl-2">
                  {isCompleted ? (
                    <div className="w-5 h-5 rounded-full bg-emerald-500/20 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
                      <Check className="w-3.5 h-3.5 stroke-[3px]" />
                    </div>
                  ) : (
                    <div className="flex items-center gap-1">
                      <span className="text-[9px] font-black text-emerald-400 bg-emerald-500/10 px-1.5 py-0.5 rounded border border-emerald-500/20">
                        +{quest.xp} XP
                      </span>
                      <ChevronRight className="w-3.5 h-3.5 text-stone-605" />
                    </div>
                  )}
                </div>
              </motion.div>
            );
          })}
        </div>
      </div>

      {/* Complete bonus notifier button */}
      <button className="w-full py-2 bg-gradient-to-r from-emerald-950/40 to-emerald-900/20 border border-emerald-500/10 rounded-xl text-[10px] font-extrabold uppercase text-emerald-400 hover:text-emerald-350 transition-all flex items-center justify-center gap-1.5 cursor-pointer">
        <span>Complete all quests to earn bonus 200 XP!</span>
        <span>🎁</span>
      </button>
    </div>
  );
}
