"use client";

import React, { useState } from "react";
import { Clock, Utensils, Car, Tv, ShoppingBag, Trash2, Droplet, Activity as ActivityIcon, Leaf, ChevronDown } from "lucide-react";
import { Activity } from "../services/api";
import { getSafeCategory } from "../utils/safeCategory";
import { motion } from "framer-motion";

interface ActivityHistoryProps {
  activities: Activity[];
  loading: boolean;
}

const CATEGORY_ICONS: Record<string, any> = {
  food: Utensils,
  transport: Car,
  appliances: Tv,
  electricity: Tv,
  shopping: ShoppingBag,
  waste: Trash2,
  water: Droplet,
  lifestyle: ActivityIcon,
};

const CATEGORY_COLORS: Record<string, string> = {
  food: "text-emerald-500 bg-emerald-500/10 border-emerald-500/20",
  transport: "text-sky-500 bg-sky-500/10 border-sky-500/20",
  electricity: "text-amber-500 bg-amber-500/10 border-amber-500/20",
  appliances: "text-indigo-500 bg-indigo-500/10 border-indigo-500/20",
  shopping: "text-purple-500 bg-purple-500/10 border-purple-500/20",
  waste: "text-rose-500 bg-rose-500/10 border-rose-500/20",
  water: "text-cyan-500 bg-cyan-500/10 border-cyan-500/20",
  lifestyle: "text-slate-500 bg-slate-500/10 border-slate-500/20",
};

const containerVariants = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: {
      staggerChildren: 0.04,
    },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 12 },
  show: { 
    opacity: 1, 
    y: 0, 
    transition: { type: "spring", stiffness: 350, damping: 26 } 
  },
};

export default function ActivityHistory({ activities, loading }: ActivityHistoryProps) {
  const [visibleCount, setVisibleCount] = useState(5);

  const getIcon = (category?: string | null) => {
    const safeCategory = getSafeCategory(category);
    const IconComponent = CATEGORY_ICONS[safeCategory] || Leaf;
    const colorClass = CATEGORY_COLORS[safeCategory] || "text-emerald-500 bg-emerald-500/10 border-emerald-500/20";
    
    return (
      <div className={`w-10 h-10 rounded-xl border flex items-center justify-center ${colorClass}`}>
        <IconComponent className="w-5 h-5" />
      </div>
    );
  };

  const formatTime = (isoString: string) => {
    try {
      const d = new Date(isoString);
      return d.toLocaleTimeString(undefined, {
        hour: "numeric",
        minute: "2-digit",
        hour12: true,
      });
    } catch {
      return "Just now";
    }
  };

  const formatDate = (isoString: string) => {
    try {
      const d = new Date(isoString);
      return d.toLocaleDateString(undefined, {
        month: "short",
        day: "numeric",
      });
    } catch {
      return "Today";
    }
  };

  const handleLoadMore = () => {
    setVisibleCount((prev) => prev + 5);
  };

  const visibleActivities = activities.slice(0, visibleCount);

  return (
    <div className="glass-card rounded-3xl p-6 sm:p-8 flex flex-col justify-between h-full transition-all duration-300">
      <div>
        <div className="flex items-center space-x-2.5 mb-6 border-b border-white/10 dark:border-white/5 pb-3">
          <Clock className="w-5 h-5 text-forest-500" />
          <h3 className="font-bold text-lg text-earth-800 dark:text-forest-100">
            Carbon Logs History
          </h3>
        </div>

        {loading ? (
          <div className="space-y-4 animate-pulse">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-16 rounded-xl bg-white/5 border-white/5"></div>
            ))}
          </div>
        ) : activities.length > 0 ? (
          <motion.div 
            variants={containerVariants}
            initial="hidden"
            animate="show"
            className="space-y-3.5 max-h-[460px] overflow-y-auto pr-1"
          >
            {visibleActivities.map((a) => (
              <motion.div
                variants={itemVariants}
                key={a.id}
                className="flex items-center justify-between p-3.5 rounded-2xl border border-white/10 dark:border-white/5 bg-white/5 dark:bg-black/10 hover:bg-white/10 dark:hover:bg-black/20 transition-all duration-300"
              >
                {/* Category Icon and Info */}
                <div className="flex items-center space-x-3.5 min-w-0">
                  {getIcon(a.category)}
                  <div className="min-w-0">
                    <p className="text-sm font-semibold text-earth-800 dark:text-white truncate">
                      "{a.input_text}"
                    </p>
                    <div className="flex items-center space-x-2 mt-0.5 text-xs text-stone-400 font-medium">
                      <span className="capitalize text-forest-700 dark:text-forest-400">
                        {a.item}
                      </span>
                      <span>•</span>
                      <span>
                        {a.quantity} {a.unit}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Emissions output & logged date */}
                <div className="text-right flex-shrink-0 pl-3">
                  <div className="text-sm font-extrabold text-earth-900 dark:text-white">
                    {a.calculated_value.toFixed(2)}{" "}
                    <span className="text-[10px] font-normal text-stone-400">kg</span>
                  </div>
                  {a.id < 0 ? (
                    <motion.div 
                      animate={{ opacity: [0.5, 1, 0.5] }}
                      transition={{ duration: 1.5, repeat: Infinity, ease: "easeInOut" }}
                      className="text-[8px] bg-amber-500/10 text-amber-500 border border-amber-500/20 px-1.5 py-0.5 rounded font-black uppercase tracking-widest mt-1 inline-flex items-center gap-1.5"
                    >
                      <span className="w-1.5 h-1.5 rounded-full bg-amber-550 animate-pulse"></span>
                      Syncing
                    </motion.div>
                  ) : (
                    <div className="text-[10px] text-stone-400 font-bold uppercase mt-0.5">
                      {formatDate(a.logged_at)} {formatTime(a.logged_at)}
                    </div>
                  )}
                </div>
              </motion.div>
            ))}
          </motion.div>
        ) : (
          <div className="text-center py-12 text-xs text-stone-500">
            No logs loaded. Reset database using the button above or type to add your first activity!
          </div>
        )}
      </div>

      {activities.length > visibleCount && !loading && (
        <button
          onClick={handleLoadMore}
          className="mt-4 w-full py-2 bg-white/5 hover:bg-forest-600/10 hover:text-forest-500 border border-white/10 hover:border-forest-500/30 rounded-xl text-xs font-bold flex items-center justify-center space-x-1.5 transition-all duration-300 active:scale-95 cursor-pointer"
        >
          <span>Load More</span>
          <ChevronDown className="w-3.5 h-3.5" />
        </button>
      )}
    </div>
  );
}
