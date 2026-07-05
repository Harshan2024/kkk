"use client";

import React from "react";
import Link from "next/link";
import { ArrowLeft, Leaf } from "lucide-react";
import { Card } from "../components/ui/Card";
import { Button } from "../components/ui/Button";

export default function NotFound() {
  return (
    <div className="min-h-screen bg-theme-base text-theme-primary flex flex-col items-center justify-center p-4 relative overflow-hidden">
      {/* Background decoration */}
      <div className="absolute inset-0 dot-matrix pointer-events-none z-0"></div>
      <div className="absolute top-[25%] left-[25%] w-[50%] aspect-square rounded-full bg-theme-brand-muted opacity-20 blur-[120px] pointer-events-none z-0"></div>

      <div className="max-w-md w-full relative z-10">
        <Card className="p-8 sm:p-10 text-center space-y-6" hover={false}>
          <div className="w-12 h-12 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center mx-auto mb-2">
            <Leaf className="w-6 h-6 text-theme-brand animate-pulse" />
          </div>
          
          <div>
            <h1 className="text-6xl font-black tracking-tight text-theme-brand font-display">404</h1>
            <h2 className="text-lg font-extrabold text-theme-secondary mt-2 font-display">Page Not Found</h2>
            <p className="text-theme-muted text-xs mt-3 leading-relaxed font-sans">
              The sustainability console segment you requested cannot be located. It might have been migrated or updated.
            </p>
          </div>

          <Link href="/" className="inline-block">
            <Button size="sm" icon={<ArrowLeft className="w-4 h-4" />}>
              Back to Dashboard
            </Button>
          </Link>
        </Card>
      </div>
    </div>
  );
}
