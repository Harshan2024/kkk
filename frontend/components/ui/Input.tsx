"use client";

import React, { useState, useCallback } from "react";
import { clsx } from "clsx";
import { Eye, EyeOff } from "lucide-react";

// ─── Text Input ───────────────────────────────────────────────────────────────

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  leftIcon?: React.ReactNode;
  rightElement?: React.ReactNode;
  error?: string;
  hint?: string;
  showPasswordToggle?: boolean;
}

export const Input = React.memo(function Input({
  label,
  leftIcon,
  rightElement,
  error,
  hint,
  showPasswordToggle = false,
  type = "text",
  className,
  id,
  ...props
}: InputProps) {
  const [showPw, setShowPw] = useState(false);
  const inputId = id ?? label?.toLowerCase().replace(/\s+/g, "-");
  const inputType = showPasswordToggle ? (showPw ? "text" : "password") : type;

  return (
    <div className="space-y-1.5">
      {label && (
        <label
          htmlFor={inputId}
          className="text-[10px] font-black uppercase tracking-wider text-theme-muted block"
        >
          {label}
        </label>
      )}
      <div className="relative group">
        {leftIcon && (
          <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-theme-muted transition-colors group-focus-within:text-theme-brand pointer-events-none">
            {leftIcon}
          </span>
        )}
        <input
          id={inputId}
          type={inputType}
          aria-invalid={!!error}
          aria-describedby={error ? `${inputId}-error` : undefined}
          className={clsx(
            "w-full py-3 text-sm text-theme-primary placeholder-theme-muted",
            "bg-white/[0.02] rounded-2xl border transition-all duration-200",
            "focus:outline-none focus:ring-0",
            leftIcon ? "pl-11" : "pl-4",
            (rightElement || showPasswordToggle) ? "pr-11" : "pr-4",
            error
              ? "border-rose-550 focus:border-rose-500 focus:shadow-[0_0_0_3px_rgba(244,63,94,0.15)] bg-rose-500/[0.03]"
              : "border-theme-subtle focus:border-[var(--brand-primary)] focus:shadow-[0_0_0_3px_var(--brand-glow)] focus:bg-white/[0.03]",
            className
          )}
          {...props}
        />
        {showPasswordToggle && (
          <button
            type="button"
            onClick={() => setShowPw(v => !v)}
            className="absolute right-3.5 top-1/2 -translate-y-1/2 text-theme-muted hover:text-theme-secondary cursor-pointer transition-colors"
          >
            {showPw ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
          </button>
        )}
        {rightElement && !showPasswordToggle && (
          <span className="absolute right-3.5 top-1/2 -translate-y-1/2">
            {rightElement}
          </span>
        )}
      </div>
      {error && (
        <p id={`${inputId}-error`} className="text-[10px] font-bold text-rose-400 flex items-center gap-1">
          <span>⚠</span> {error}
        </p>
      )}
      {hint && !error && (
        <p className="text-[10px] text-theme-muted">{hint}</p>
      )}
    </div>
  );
});

// ─── Textarea ─────────────────────────────────────────────────────────────────

interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  error?: string;
  hint?: string;
  maxLength?: number;
}

export const Textarea = React.memo(function Textarea({
  label,
  error,
  hint,
  maxLength,
  className,
  id,
  value,
  ...props
}: TextareaProps) {
  const textareaId = id ?? label?.toLowerCase().replace(/\s+/g, "-");
  const charCount = typeof value === "string" ? value.length : 0;

  return (
    <div className="space-y-1.5">
      {label && (
        <div className="flex justify-between items-center">
          <label
            htmlFor={textareaId}
            className="text-[10px] font-black uppercase tracking-wider text-theme-muted"
          >
            {label}
          </label>
          {maxLength && (
            <span className="text-[9px] text-theme-muted">
              {charCount}/{maxLength}
            </span>
          )}
        </div>
      )}
      <textarea
        id={textareaId}
        value={value}
        maxLength={maxLength}
        aria-invalid={!!error}
        aria-describedby={error ? `${textareaId}-error` : undefined}
        className={clsx(
          "w-full px-4 py-3 text-sm text-theme-primary placeholder-theme-muted",
          "bg-white/[0.02] rounded-2xl border transition-all duration-200 resize-none",
          "focus:outline-none focus:ring-0",
          error
            ? "border-rose-550 focus:border-rose-500 focus:shadow-[0_0_0_3px_rgba(244,63,94,0.15)] bg-rose-500/[0.03]"
            : "border-theme-subtle focus:border-[var(--brand-primary)] focus:shadow-[0_0_0_3px_var(--brand-glow)] focus:bg-white/[0.03]",
          className
        )}
        {...props}
      />
      {error && (
        <p id={`${textareaId}-error`} className="text-[10px] font-bold text-rose-400">⚠ {error}</p>
      )}
      {hint && !error && (
        <p className="text-[10px] text-theme-muted">{hint}</p>
      )}
    </div>
  );
});

// ─── Select ───────────────────────────────────────────────────────────────────

interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  error?: string;
  options: { value: string; label: string }[];
}

export const Select = React.memo(function Select({ label, error, options, className, id, ...props }: SelectProps) {
  const selectId = id ?? label?.toLowerCase().replace(/\s+/g, "-");
  return (
    <div className="space-y-1.5">
      {label && (
        <label
          htmlFor={selectId}
          className="text-[10px] font-black uppercase tracking-wider text-theme-muted block"
        >
          {label}
        </label>
      )}
      <div className="relative">
        <select
          id={selectId}
          aria-invalid={!!error}
          aria-describedby={error ? `${selectId}-error` : undefined}
          className={clsx(
            "w-full px-4 py-3 text-sm text-theme-primary appearance-none cursor-pointer",
            "bg-white/[0.02] rounded-2xl border transition-all duration-200",
            "focus:outline-none focus:ring-0",
            error
              ? "border-rose-550 focus:border-rose-500 focus:shadow-[0_0_0_3px_rgba(244,63,94,0.15)]"
              : "border-theme-subtle focus:border-[var(--brand-primary)] focus:shadow-[0_0_0_3px_var(--brand-glow)] focus:bg-white/[0.03]",
            className
          )}
          {...props}
        >
          {options.map(opt => (
            <option key={opt.value} value={opt.value} className="bg-theme-surface text-theme-primary">
              {opt.label}
            </option>
          ))}
        </select>
        <span className="absolute right-4 top-1/2 -translate-y-1/2 text-theme-muted pointer-events-none text-[10px]">
          ▼
        </span>
      </div>
      {error && (
        <p id={`${selectId}-error`} className="text-[10px] font-bold text-rose-400">⚠ {error}</p>
      )}
    </div>
  );
});

export default Input;
