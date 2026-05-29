"use client";

import React from "react";
import { Rocket, Lock, Shield, Check } from "lucide-react";
import { motion } from "framer-motion";

interface StreakFooterProps {
  streak: number;
}

export default function StreakFooter({ streak = 1 }: StreakFooterProps) {
  const days = [1, 2, 3, 4, 5, 6, 7];

  return (
    <div className="glass-card rounded-2xl p-4 flex flex-col md:flex-row items-center justify-between gap-4 select-none relative overflow-hidden">
      {/* Background horizontal accent glow */}
      <div className="absolute left-0 bottom-0 w-full h-[2px] bg-gradient-to-r from-emerald-500/0 via-emerald-500/30 to-emerald-500/0 pointer-events-none"></div>

      {/* Left side info */}
      <div className="flex items-center space-x-3.5">
        <div className="w-9 h-9 rounded-xl bg-emerald-500/10 flex items-center justify-center border border-emerald-500/25 shadow shadow-emerald-500/10">
          <Rocket className="w-4.5 h-4.5 text-emerald-400 rotate-45" />
        </div>
        <div>
          <h4 className="text-xs font-black text-white uppercase tracking-wider flex items-center gap-1.5">
            Keep going! You're on a {streak} day streak.
          </h4>
          <p className="text-[10px] text-stone-500 font-bold mt-0.5">
            Build a 7 day streak to unlock the <span className="text-emerald-450 font-extrabold">"Green Warrior"</span> badge!
          </p>
        </div>
      </div>

      {/* Right side Day Timeline */}
      <div className="flex items-center space-x-2">
        {days.map((day) => {
          const isActive = day === streak;
          const isCompleted = day < streak;
          const isLast = day === 7;
          
          return (
            <div key={day} className="flex items-center">
              {/* Day bubble */}
              <motion.div
                whileHover={{ scale: 1.05 }}
                className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-black border transition-all duration-300 relative cursor-pointer ${
                  isActive 
                    ? "bg-emerald-500 border-emerald-400 text-[#080d0a] shadow-lg shadow-emerald-500/30"
                    : isCompleted
                    ? "bg-emerald-950/20 border-emerald-500/20 text-emerald-450"
                    : "bg-white/[0.01] border-white/5 text-stone-500"
                }`}
              >
                {isCompleted ? (
                  <Check className="w-3.5 h-3.5 stroke-[2.5px]" />
                ) : isLast ? (
                  <Shield className={`w-3.5 h-3.5 ${isActive ? "text-[#080d0a]" : "text-stone-500"}`} />
                ) : !isActive ? (
                  <div className="relative">
                    <span className="opacity-0">{day}</span>
                    <Lock className="w-2.5 h-2.5 text-stone-605 absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2" />
                  </div>
                ) : (
                  day
                )}
              </motion.div>

              {/* Connecting line */}
              {!isLast && (
                <div 
                  className={`w-3 sm:w-5 h-[1.5px] ${
                    isCompleted 
                      ? "bg-emerald-500/40" 
                      : "bg-white/5"
                  }`}
                />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
