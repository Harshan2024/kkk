"use client";

import React from "react";
import { motion } from "framer-motion";
import { clsx } from "clsx";

// ─── Types ────────────────────────────────────────────────────────────────────

interface CardProps {
  children: React.ReactNode;
  className?: string;
  hover?: boolean;
  glow?: boolean;
  gradientBorder?: boolean;
  noPadding?: boolean;
  onClick?: () => void;
  animate?: boolean;
}

// ─── Card Component ───────────────────────────────────────────────────────────

export const Card = React.memo(function Card({
  children,
  className,
  hover = true,
  glow = false,
  gradientBorder = false,
  noPadding = false,
  onClick,
  animate = false,
}: CardProps) {
  const base = (
    <div
      onClick={onClick}
      className={clsx(
        "glass-premium rounded-3xl",
        !noPadding && "p-5",
        hover && "card-hover-lift",
        glow && "card-glow-brand",
        gradientBorder && "gradient-border",
        onClick && "cursor-pointer",
        className
      )}
    >
      {children}
    </div>
  );

  if (animate) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        whileHover={hover ? { y: -3, scale: 1.01 } : {}}
        transition={{ type: "spring", stiffness: 400, damping: 25 }}
        onClick={onClick}
        className={clsx(
          "glass-premium rounded-3xl",
          !noPadding && "p-5",
          hover && "card-hover-lift",
          glow && "card-glow-brand",
          gradientBorder && "gradient-border",
          onClick && "cursor-pointer",
          className
        )}
      >
        {children}
      </motion.div>
    );
  }

  return base;
});

// ─── KPI Card ─────────────────────────────────────────────────────────────────

interface KpiCardProps {
  label: string;
  value: string | number;
  unit?: string;
  icon?: React.ReactNode;
  iconBg?: string;
  trend?: { value: number; improved: boolean };
  sparkline?: React.ReactNode;
  footer?: React.ReactNode;
  className?: string;
}

export const KpiCard = React.memo(function KpiCard({
  label,
  value,
  unit,
  icon,
  iconBg = "bg-emerald-500/10",
  trend,
  sparkline,
  footer,
  className,
}: KpiCardProps) {
  return (
    <motion.div
      whileHover={{ y: -3, scale: 1.01 }}
      transition={{ type: "spring", stiffness: 400, damping: 25 }}
      className={clsx("glass-premium rounded-2xl p-4.5 flex flex-col justify-between card-hover-lift", className)}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0 space-y-1.5">
          <div className="flex items-center gap-1.5">
            {icon && (
              <span className={clsx("w-6 h-6 rounded-lg flex items-center justify-center flex-shrink-0", iconBg)}>
                {icon}
              </span>
            )}
            <span className="text-[10px] font-black uppercase tracking-wider text-theme-muted truncate">
              {label}
            </span>
          </div>
          <div className="flex items-baseline gap-1.5">
            <span className="text-2xl font-black text-theme-primary leading-none font-display">
              {value}
            </span>
            {unit && (
              <span className="text-[10px] font-semibold text-theme-muted uppercase">{unit}</span>
            )}
          </div>
        </div>
        {sparkline && <div className="opacity-80 flex-shrink-0">{sparkline}</div>}
      </div>

      {(trend || footer) && (
        <div className="mt-2 flex items-center gap-1.5">
          {trend && (
            <span
              className={clsx(
                "text-[10px] font-bold flex items-center gap-0.5",
                trend.improved ? "text-emerald-400" : "text-rose-400"
              )}
            >
              {trend.improved ? "↓" : "↑"} {Math.abs(trend.value).toFixed(1)}%
              <span className="text-theme-muted font-normal ml-0.5">vs yesterday</span>
            </span>
          )}
          {footer && !trend && <div className="text-[10px] font-bold text-theme-muted">{footer}</div>}
        </div>
      )}
    </motion.div>
  );
});

export default Card;
