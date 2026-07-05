"use client";

import React from "react";
import { clsx } from "clsx";

// ─── Types ────────────────────────────────────────────────────────────────────

type BadgeVariant =
  | "default" | "success" | "warning" | "danger" | "info"
  | "brand" | "muted" | "purple" | "orange" | "sky";

type BadgeSize = "xs" | "sm" | "md";

interface BadgeProps {
  variant?: BadgeVariant;
  size?: BadgeSize;
  dot?: boolean;
  pulse?: boolean;
  children: React.ReactNode;
  className?: string;
}

// ─── Style maps ───────────────────────────────────────────────────────────────

const variantStyles: Record<BadgeVariant, string> = {
  default:  "bg-white/[0.06] text-stone-300 border-white/8",
  success:  "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
  warning:  "bg-amber-500/10 text-amber-400 border-amber-500/20",
  danger:   "bg-rose-500/10 text-rose-400 border-rose-500/20",
  info:     "bg-sky-500/10 text-sky-400 border-sky-500/20",
  brand:    "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
  muted:    "bg-white/[0.03] text-stone-500 border-white/5",
  purple:   "bg-purple-500/10 text-purple-400 border-purple-500/20",
  orange:   "bg-orange-500/10 text-orange-400 border-orange-500/20",
  sky:      "bg-sky-500/10 text-sky-400 border-sky-500/20",
};

const dotColors: Record<BadgeVariant, string> = {
  default:  "bg-stone-400",
  success:  "bg-emerald-400",
  warning:  "bg-amber-400",
  danger:   "bg-rose-400",
  info:     "bg-sky-400",
  brand:    "bg-emerald-400",
  muted:    "bg-stone-500",
  purple:   "bg-purple-400",
  orange:   "bg-orange-400",
  sky:      "bg-sky-400",
};

const sizeStyles: Record<BadgeSize, string> = {
  xs: "text-[9px] px-1.5 py-0.5 gap-1",
  sm: "text-[10px] px-2 py-0.5 gap-1.5",
  md: "text-xs px-2.5 py-1 gap-1.5",
};

// ─── Component ────────────────────────────────────────────────────────────────

export function Badge({
  variant = "default",
  size = "sm",
  dot = false,
  pulse = false,
  children,
  className,
}: BadgeProps) {
  return (
    <span
      className={clsx(
        "inline-flex items-center font-extrabold uppercase tracking-wider rounded-full border",
        variantStyles[variant],
        sizeStyles[size],
        className
      )}
    >
      {dot && (
        <span className="relative flex-shrink-0">
          <span className={clsx("w-1.5 h-1.5 rounded-full block", dotColors[variant])} />
          {pulse && (
            <span className={clsx("absolute inset-0 rounded-full animate-ping opacity-60", dotColors[variant])} />
          )}
        </span>
      )}
      {children}
    </span>
  );
}

export default Badge;
