"use client";

import React from "react";
import { clsx } from "clsx";

// ─── Skeleton Line ────────────────────────────────────────────────────────────

interface SkeletonProps {
  className?: string;
  width?: string;
  height?: string;
  rounded?: string;
}

export function Skeleton({ className, width, height, rounded = "rounded-lg" }: SkeletonProps) {
  return (
    <div
      className={clsx("skeleton", rounded, className)}
      style={{ width, height }}
    />
  );
}

// ─── Card Skeleton ────────────────────────────────────────────────────────────

export function CardSkeleton({ className, lines = 3 }: { className?: string; lines?: number }) {
  return (
    <div className={clsx("glass-premium rounded-3xl p-5 space-y-3", className)}>
      <Skeleton className="h-3 w-1/3" />
      <Skeleton className="h-8 w-2/3" />
      {Array.from({ length: lines - 2 }).map((_, i) => (
        <Skeleton key={i} className={clsx("h-2.5", i === lines - 3 ? "w-1/2" : "w-full")} />
      ))}
    </div>
  );
}

// ─── KPI Skeleton ─────────────────────────────────────────────────────────────

export function KpiSkeleton({ count = 4 }: { count?: number }) {
  return (
    <div className={`grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-${count} gap-5 w-full`}>
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="glass-premium rounded-2xl p-4.5 h-[115px] flex flex-col justify-between">
          <div className="space-y-2">
            <Skeleton className="h-2.5 w-1/2" />
            <Skeleton className="h-7 w-2/3" rounded="rounded-xl" />
          </div>
          <Skeleton className="h-2 w-1/3" />
        </div>
      ))}
    </div>
  );
}

// ─── List Skeleton ────────────────────────────────────────────────────────────

export function ListSkeleton({ rows = 5, className }: { rows?: number; className?: string }) {
  return (
    <div className={clsx("space-y-3", className)}>
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="flex items-center gap-3 p-3 glass-premium rounded-2xl">
          <Skeleton className="w-9 h-9 flex-shrink-0" rounded="rounded-xl" />
          <div className="flex-1 space-y-1.5">
            <Skeleton className="h-2.5 w-3/4" />
            <Skeleton className="h-2 w-1/2" />
          </div>
          <Skeleton className="h-2.5 w-16 flex-shrink-0" />
        </div>
      ))}
    </div>
  );
}

// ─── Profile Skeleton ─────────────────────────────────────────────────────────

export function ProfileSkeleton() {
  return (
    <div className="grid grid-cols-1 xl:grid-cols-3 gap-6 animate-pulse">
      <div className="xl:col-span-1 space-y-6">
        <div className="glass-premium rounded-3xl h-[360px]" />
        <div className="glass-premium rounded-3xl h-[280px]" />
      </div>
      <div className="xl:col-span-2">
        <div className="glass-premium rounded-3xl h-[660px]" />
      </div>
    </div>
  );
}

export default Skeleton;
