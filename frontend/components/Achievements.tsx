"use client";

import React from "react";
import { Trophy, Lock, Award, ShieldCheck, Flame } from "lucide-react";
import { Achievement } from "../services/api";
import { motion } from "framer-motion";
import { Card } from "./ui/Card";
import { Badge } from "./ui/Badge";

interface AchievementsProps {
  unlockedList: Achievement[];
  loading: boolean;
}

const SYSTEM_ACHIEVEMENTS = [
  {
    name: "Eco Pioneer",
    description: "Logged your first carbon activity!",
    badge_type: "bronze",
    icon: Flame,
    color: "from-orange-500/25 to-amber-600/10 border-orange-500/30 text-orange-400"
  },
  {
    name: "Green Commuter",
    description: "Opted for low-emission transport (walk, cycle, metro or train).",
    badge_type: "silver",
    icon: Award,
    color: "from-sky-500/25 to-indigo-600/10 border-sky-500/30 text-sky-400"
  },
  {
    name: "Plant-based Champion",
    description: "Ate a carbon-conscious vegetarian or vegan meal.",
    badge_type: "silver",
    icon: ShieldCheck,
    color: "from-emerald-500/25 to-teal-600/10 border-emerald-500/30 text-emerald-400"
  },
  {
    name: "Power Saver",
    description: "Used energy-demanding appliances for 1 hour or less.",
    badge_type: "bronze",
    icon: Award,
    color: "from-amber-500/25 to-yellow-600/10 border-amber-500/30 text-amber-400"
  },
  {
    name: "Consistent Climateer",
    description: "Logged 5 or more activities in CarbonTracker.",
    badge_type: "gold",
    icon: Trophy,
    color: "from-yellow-400/30 to-amber-500/20 border-yellow-500/50 text-yellow-400 shadow-yellow-500/10"
  }
];

export default function Achievements({ unlockedList, loading }: AchievementsProps) {
  const isUnlocked = (name: string) => {
    return unlockedList.some((ach) => ach.name.toLowerCase() === name.toLowerCase());
  };

  const getUnlockDate = (name: string) => {
    const found = unlockedList.find((ach) => ach.name.toLowerCase() === name.toLowerCase());
    if (!found) return null;
    return new Date(found.unlocked_at).toLocaleDateString(undefined, {
      month: "short",
      day: "numeric",
    });
  };

  return (
    <Card className="p-6 sm:p-8" hover={false}>
      <div className="flex items-center space-x-2.5 mb-6 border-b border-white/5 pb-3">
        <Trophy className="w-5 h-5 text-yellow-500 animate-bounce" />
        <h3 className="font-bold text-lg text-theme-primary">
          Climate Achievements
        </h3>
      </div>

      {loading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4 animate-pulse">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="h-28 rounded-2xl bg-white/5 border-white/5"></div>
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
          {SYSTEM_ACHIEVEMENTS.map((sys) => {
            const unlocked = isUnlocked(sys.name);
            const date = getUnlockDate(sys.name);
            const Icon = sys.icon;
            
            return (
              <motion.div
                whileHover={unlocked ? { y: -4, scale: 1.02 } : {}}
                transition={{ type: "spring", stiffness: 350, damping: 22 }}
                key={sys.name}
                className={`relative flex flex-col justify-between p-4 rounded-2xl border transition-all duration-300 ${
                  unlocked
                    ? `bg-gradient-to-br ${sys.color} shadow-lg shadow-black/10`
                    : "bg-stone-950/20 border-white/5 text-theme-muted opacity-40 grayscale"
                }`}
              >
                {!unlocked && (
                  <div className="absolute top-2.5 right-2.5">
                    <Lock className="w-3.5 h-3.5 text-theme-muted" />
                  </div>
                )}

                <div>
                  <div className={`w-9 h-9 rounded-xl flex items-center justify-center mb-3 transition-colors duration-300 ${
                    unlocked ? "bg-white/10" : "bg-white/5"
                  }`}>
                    <Icon className="w-5 h-5" />
                  </div>
                  <h4 className={`text-xs font-extrabold uppercase tracking-wide ${
                    unlocked ? "text-theme-primary" : "text-theme-muted"
                  }`}>
                    {sys.name}
                  </h4>
                  <p className="text-[10px] leading-tight text-theme-secondary mt-1">
                    {sys.description}
                  </p>
                </div>

                <div className="mt-3 border-t border-white/5 pt-2 flex items-center justify-between text-[9px] font-bold tracking-wider text-theme-muted">
                  <span className="uppercase">{sys.badge_type}</span>
                  {unlocked && date ? (
                    <span className="text-theme-brand">UNLOCKED {date}</span>
                  ) : (
                    <span>LOCKED</span>
                  )}
                </div>
              </motion.div>
            );
          })}
        </div>
      )}
    </Card>
  );
}
