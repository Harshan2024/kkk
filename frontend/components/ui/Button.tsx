"use client";

import React, { useRef, useCallback } from "react";
import { motion } from "framer-motion";
import { Loader2 } from "lucide-react";
import { clsx } from "clsx";

// ─── Types ────────────────────────────────────────────────────────────────────

import { HTMLMotionProps } from "framer-motion";

type ButtonVariant = "primary" | "secondary" | "ghost" | "outline" | "danger" | "success" | "warning";
type ButtonSize = "xs" | "sm" | "md" | "lg" | "xl";

interface ButtonProps extends Omit<HTMLMotionProps<"button">, "onDrag" | "onDragStart" | "onDragEnd" | "onDragOver" | "onDragEnter" | "onDragExit" | "onDragLeave" | "onDrop" | "onTransitionEnd" | "onAnimationStart" | "onAnimationEnd" | "onAnimationIteration"> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
  icon?: React.ReactNode;
  iconRight?: React.ReactNode;
  glow?: boolean;
  pill?: boolean;
  children?: React.ReactNode;
}

// ─── Variant Styles ───────────────────────────────────────────────────────────

const variantStyles: Record<ButtonVariant, string> = {
  primary:
    "bg-gradient-to-r from-emerald-600 to-emerald-500 hover:from-emerald-500 hover:to-emerald-400 text-white border border-emerald-500/30 shadow-glow-green-sm hover:shadow-glow-green",
  secondary:
    "bg-white/[0.04] hover:bg-white/[0.07] text-stone-200 border border-white/8 hover:border-white/12",
  ghost:
    "bg-transparent hover:bg-white/[0.04] text-stone-300 hover:text-white border border-transparent",
  outline:
    "bg-transparent border border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/10 hover:border-emerald-500/50",
  danger:
    "bg-gradient-to-r from-rose-700 to-rose-600 hover:from-rose-600 hover:to-rose-500 text-white border border-rose-500/30",
  success:
    "bg-gradient-to-r from-emerald-700 to-emerald-600 hover:from-emerald-600 hover:to-emerald-500 text-white border border-emerald-500/30",
  warning:
    "bg-gradient-to-r from-amber-700 to-amber-600 hover:from-amber-600 hover:to-amber-500 text-white border border-amber-500/30",
};

const sizeStyles: Record<ButtonSize, string> = {
  xs: "px-2.5 py-1 text-[10px] font-extrabold uppercase tracking-wider rounded-xl gap-1 max-sm:min-h-[44px]",
  sm: "px-3.5 py-1.5 text-xs font-bold rounded-xl gap-1.5 max-sm:min-h-[44px]",
  md: "px-4.5 py-2.5 text-sm font-semibold rounded-2xl gap-2 max-sm:min-h-[44px]",
  lg: "px-6 py-3 text-sm font-semibold rounded-2xl gap-2 min-h-[48px]",
  xl: "px-8 py-4 text-base font-semibold rounded-2xl gap-2.5 min-h-[56px]",
};

// ─── Component ────────────────────────────────────────────────────────────────

export const Button = React.memo(function Button({
  variant = "primary",
  size = "md",
  loading = false,
  icon,
  iconRight,
  glow = false,
  pill = false,
  children,
  disabled,
  className,
  onClick,
  ...props
}: ButtonProps) {
  const btnRef = useRef<HTMLButtonElement>(null);

  // Ripple effect handler
  const handleClick = useCallback(
    (e: React.MouseEvent<HTMLButtonElement>) => {
      if (disabled || loading) return;

      const btn = btnRef.current;
      if (btn) {
        const rect = btn.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        const ripple = document.createElement("span");
        ripple.style.cssText = `
          position: absolute;
          border-radius: 50%;
          width: 6px; height: 6px;
          left: ${x - 3}px; top: ${y - 3}px;
          background: rgba(255,255,255,0.35);
          transform: scale(0);
          animation: ripple-effect 0.5s linear forwards;
          pointer-events: none;
        `;
        btn.appendChild(ripple);
        setTimeout(() => ripple.remove(), 600);
      }

      onClick?.(e);
    },
    [disabled, loading, onClick]
  );

  const isDisabled = disabled || loading;

  return (
    <motion.button
      ref={btnRef as any}
      whileHover={isDisabled ? {} : { scale: 1.02, y: -1 }}
      whileTap={isDisabled ? {} : { scale: 0.95 }}
      transition={{ type: "spring", stiffness: 450, damping: 20 }}
      onClick={handleClick}
      disabled={isDisabled}
      className={clsx(
        // Base
        "relative inline-flex items-center justify-center font-semibold",
        "transition-all duration-200 ease-out",
        "select-none overflow-hidden",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-emerald-500/50",
        // Variant
        variantStyles[variant],
        // Size
        sizeStyles[size],
        // Pill
        pill ? "rounded-full" : "",
        // Glow
        glow ? "glow-btn" : "",
        // Disabled
        isDisabled ? "opacity-50 cursor-not-allowed pointer-events-none" : "cursor-pointer",
        className
      )}
      {...props}
    >
      {/* Loading spinner */}
      {loading && (
        <Loader2 className="w-4 h-4 animate-spin flex-shrink-0" />
      )}

      {/* Left icon */}
      {!loading && icon && (
        <span className="flex-shrink-0">{icon}</span>
      )}

      {/* Label */}
      {children && <span>{children}</span>}

      {/* Right icon */}
      {!loading && iconRight && (
        <span className="flex-shrink-0">{iconRight}</span>
      )}
    </motion.button>
  );
});

export default Button;
