"use client";

import React from "react";
import { Trophy, Lock, Award, ShieldCheck, Flame } from "lucide-react";
import { Achievement } from "../services/api";
import { motion } from "framer-motion";

interface AchievementsProps {
  unlockedList: Achievement[];
  loading: boolean;
}

// Master list of all possible achievements to render locked/unlocked states
const SYSTEM_ACHIEVEMENTS = [
  {
    name: "Eco Pioneer",
    description: "Logged your first carbon activity!",
    badge_type: "bronze",
    icon: Flame,
    color: "from-orange-500/25 to-amber-600/10 border-orange-500/30 text-orange-500"
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
    color: "from-yellow-400/30 to-amber-500/20 border-yellow-500/50 text-yellow-500 shadow-yellow-500/10"
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
    <div className="glass-card rounded-3xl p-6 sm:p-8 transition-all duration-300">
      <div className="flex items-center space-x-2.5 mb-6 border-b border-white/10 dark:border-white/5 pb-3">
        <Trophy className="w-5 h-5 text-yellow-500 animate-bounce" />
        <h3 className="font-bold text-lg text-earth-800 dark:text-forest-100">
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
                    : "bg-stone-950/20 dark:bg-black/20 border-white/5 text-stone-600 dark:text-stone-750 opacity-40 grayscale"
                }`}
              >
                {/* Lock icon for locked achievements */}
                {!unlocked && (
                  <div className="absolute top-2.5 right-2.5">
                    <Lock className="w-3.5 h-3.5 text-stone-500 dark:text-stone-700" />
                  </div>
                )}

                <div>
                  <div className={`w-9 h-9 rounded-xl flex items-center justify-center mb-3 transition-colors duration-300 ${
                    unlocked ? "bg-white/10" : "bg-white/5"
                  }`}>
                    <Icon className="w-5 h-5" />
                  </div>
                  <h4 className={`text-xs font-extrabold uppercase tracking-wide ${
                    unlocked ? "text-earth-900 dark:text-white" : "text-stone-500 dark:text-stone-600"
                  }`}>
                    {sys.name}
                  </h4>
                  <p className="text-[10px] leading-tight text-earth-700 dark:text-stone-400 mt-1">
                    {sys.description}
                  </p>
                </div>

                <div className="mt-3 border-t border-white/10 dark:border-white/5 pt-2 flex items-center justify-between text-[9px] font-bold tracking-wider">
                  <span className="uppercase">{sys.badge_type}</span>
                  {unlocked && date ? (
                    <span className="text-stone-500 dark:text-stone-400">UNLOCKED {date}</span>
                  ) : (
                    <span className="text-stone-605 dark:text-stone-705">LOCKED</span>
                  )}
                </div>
              </motion.div>
            );
          })}
        </div>
      )}
    </div>
  );
}
