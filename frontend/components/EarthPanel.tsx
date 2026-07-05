"use client";

import React from "react";
import { Globe, Leaf } from "lucide-react";
import { motion } from "framer-motion";
import { Card } from "./ui/Card";
import { Badge } from "./ui/Badge";
import Image from "next/image";

interface EarthPanelProps {
  score: number;
}

export default function EarthPanel({ score = 93 }: EarthPanelProps) {
  // Map score to user percentile
  const userPercentile = Math.min(99, Math.max(20, Math.round(score * 0.8 + 10)));

  return (
    <Card className="flex flex-col justify-between items-center relative overflow-hidden select-none min-h-[420px] h-full" hover={false}>
      {/* Background radial glows */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-72 h-72 rounded-full bg-emerald-500/10 blur-[80px] pointer-events-none z-0"></div>
      
      {/* Title Header */}
      <div className="w-full flex items-center space-x-2.5 pb-3 border-b border-white/5 relative z-10">
        <div className="w-6 h-6 rounded-lg bg-emerald-500/10 flex items-center justify-center border border-emerald-500/20">
          <Globe className="w-3.5 h-3.5 text-emerald-400" />
        </div>
        <h3 className="font-extrabold text-xs text-theme-secondary uppercase tracking-widest">
          Carbon Earth Status
        </h3>
      </div>

      {/* Centerpiece Earth Visualization */}
      <div className="relative flex-1 flex items-center justify-center my-6 relative z-10 w-full">
        {/* Animated outer aura rings */}
        <motion.div 
          animate={{ scale: [1, 1.05, 1], opacity: [0.3, 0.45, 0.3] }}
          transition={{ duration: 6, repeat: Infinity, ease: "easeInOut" }}
          className="absolute w-56 h-56 rounded-full border border-emerald-500/10 flex items-center justify-center"
        >
          <div className="w-48 h-48 rounded-full border border-emerald-500/5"></div>
        </motion.div>

        {/* Orbiting particle */}
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 12, repeat: Infinity, ease: "linear" }}
          className="absolute w-60 h-60 rounded-full pointer-events-none"
        >
          <div className="w-2.5 h-2.5 rounded-full bg-emerald-400/80 shadow-lg shadow-emerald-400 absolute top-0 left-1/2 -translate-x-1/2"></div>
        </motion.div>

        {/* The Earth Image */}
        <motion.div
          animate={{ 
            y: [-6, 6, -6],
            rotate: 360
          }}
          transition={{ 
            y: { duration: 4.5, repeat: Infinity, ease: "easeInOut" },
            rotate: { duration: 90, repeat: Infinity, ease: "linear" }
          }}
          className="w-44 h-44 drop-shadow-[0_0_35px_rgba(16,185,129,0.25)] relative"
        >
          <Image 
            src="/earth_glowing.png" 
            alt="Glowing Earth" 
            width={176}
            height={176}
            className="w-full h-full object-contain"
            priority
          />
        </motion.div>
      </div>

      {/* Bottom details & Badge */}
      <div className="w-full flex flex-col items-center text-center space-y-3.5 relative z-10">
        <Badge variant="success" size="md" dot>
          <span className="flex items-center gap-1.5">
            <Leaf className="w-3.5 h-3.5" />
            Eco-Champion
          </span>
        </Badge>

        <div>
          <p className="text-[11px] font-bold text-theme-secondary leading-normal max-w-[210px] font-sans">
            You are doing better than{" "}
            <span className="text-theme-brand font-extrabold text-xs">{userPercentile}%</span> of
            users today!
          </p>
          <span className="text-[9px] text-theme-muted font-bold block mt-1 uppercase tracking-wider font-sans">
            &ldquo;Small choices today, a better planet tomorrow.&rdquo;
          </span>
        </div>
      </div>
    </Card>
  );
}
