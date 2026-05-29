"use client";

import React from "react";
import Link from "next/link";
import { ArrowLeft, Leaf } from "lucide-react";

export default function NotFound() {
  return (
    <div className="min-h-screen bg-[#080d0a] text-stone-100 flex flex-col items-center justify-center p-4 relative overflow-hidden">
      {/* Background decoration */}
      <div className="absolute inset-0 dot-matrix pointer-events-none z-0"></div>
      <div className="absolute top-[25%] left-[25%] w-[50%] aspect-square rounded-full bg-forest-500/5 blur-[120px] pointer-events-none z-0"></div>

      <div className="glass-card rounded-3xl p-8 sm:p-10 max-w-md w-full text-center space-y-6 relative z-10">
        <div className="w-12 h-12 rounded-2xl bg-forest-600/10 border border-forest-500/20 flex items-center justify-center mx-auto mb-2">
          <Leaf className="w-6 h-6 text-forest-400 animate-pulse" />
        </div>
        
        <div>
          <h1 className="text-6xl font-black tracking-tight text-forest-500">404</h1>
          <h2 className="text-lg font-extrabold text-stone-200 mt-2">Page Not Found</h2>
          <p className="text-stone-400 text-xs mt-3 leading-relaxed">
            The sustainability console segment you requested cannot be located. It might have been migrated or updated.
          </p>
        </div>

        <Link
          href="/"
          className="inline-flex items-center space-x-2 px-5 py-2.5 bg-forest-600 hover:bg-forest-500 text-white rounded-xl text-xs font-bold transition-all shadow-md shadow-forest-650/20 hover:scale-[1.02] active:scale-95 mx-auto"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Dashboard</span>
        </Link>
      </div>
    </div>
  );
}
