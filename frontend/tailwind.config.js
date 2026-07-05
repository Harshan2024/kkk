/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./stores/**/*.{js,ts,jsx,tsx}",
    "./services/**/*.{js,ts,jsx,tsx}"
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        // ─── Brand / Semantic ───────────────────────────────────────────────
        background: {
          light: "#f4f6f3",
          dark: "#0b120f",
        },
        card: {
          light: "rgba(255, 255, 255, 0.7)",
          dark: "rgba(18, 30, 25, 0.6)",
        },
        // ─── Forest Green (Default Theme) ───────────────────────────────────
        forest: {
          50: "#f0fdf4",
          100: "#dcfce7",
          200: "#bbf7d0",
          300: "#86efac",
          400: "#4ade80",
          450: "#22d160",
          500: "#22c55e",
          600: "#16a34a",
          650: "#148a40",
          700: "#15803d",
          800: "#166534",
          900: "#14532d",
          950: "#052e16",
        },
        // ─── Earth / Stone ──────────────────────────────────────────────────
        earth: {
          50: "#fafaf9",
          100: "#f5f5f4",
          200: "#e7e5e4",
          300: "#d6d3d1",
          400: "#a8a29e",
          500: "#78716c",
          600: "#57534e",
          700: "#44403c",
          800: "#292524",
          900: "#1c1917",
          950: "#0c0a09",
        },
        // ─── Carbon / Slate ─────────────────────────────────────────────────
        carbon: {
          50: "#f8fafc",
          100: "#f1f5f9",
          200: "#e2e8f0",
          300: "#cbd5e1",
          400: "#94a3b8",
          500: "#64748b",
          600: "#475569",
          700: "#334155",
          800: "#1e293b",
          900: "#0f172a",
          950: "#020617",
        },
        // ─── Ocean Blue Theme ────────────────────────────────────────────────
        ocean: {
          400: "#38bdf8",
          500: "#0ea5e9",
          600: "#0284c7",
          700: "#0369a1",
          900: "#0c1a2e",
          950: "#060d18",
        },
        // ─── Aurora Purple Theme ─────────────────────────────────────────────
        aurora: {
          400: "#c084fc",
          500: "#a855f7",
          600: "#9333ea",
          700: "#7e22ce",
          900: "#1a0a2e",
          950: "#0d0518",
        },
        // ─── Crimson Red Theme ───────────────────────────────────────────────
        crimson: {
          400: "#f87171",
          500: "#ef4444",
          600: "#dc2626",
          700: "#b91c1c",
          900: "#2d0a0a",
          950: "#180505",
        },
        // ─── Sunset Orange Theme ─────────────────────────────────────────────
        sunset: {
          400: "#fb923c",
          500: "#f97316",
          600: "#ea580c",
          700: "#c2410c",
          900: "#2d1008",
          950: "#180804",
        },
        // ─── Golden Sand Theme ───────────────────────────────────────────────
        golden: {
          400: "#facc15",
          500: "#eab308",
          600: "#ca8a04",
          700: "#a16207",
          900: "#1c1204",
          950: "#0d0902",
        },
        // ─── Arctic Blue Theme ───────────────────────────────────────────────
        arctic: {
          400: "#67e8f9",
          500: "#22d3ee",
          600: "#06b6d4",
          700: "#0891b2",
          900: "#0a1e26",
          950: "#040d12",
        },
        // ─── Emerald Green Theme ─────────────────────────────────────────────
        emerald: {
          50: "#ecfdf5",
          100: "#d1fae5",
          200: "#a7f3d0",
          300: "#6ee7b7",
          400: "#34d399",
          450: "#10d888",
          500: "#10b981",
          600: "#059669",
          700: "#047857",
          800: "#065f46",
          900: "#064e3b",
          950: "#022c22",
        },
        // ─── Mint (Light Theme) ──────────────────────────────────────────────
        mint: {
          400: "#4ade80",
          500: "#22c55e",
          50: "#f0fdf4",
          100: "#dcfce7",
        },
        // ─── Extended Orange ─────────────────────────────────────────────────
        orange: {
          450: "#ff7a35",
          500: "#f97316",
          600: "#ea580c",
        },
        // ─── Extended Rose ───────────────────────────────────────────────────
        rose: {
          450: "#fb6b7a",
          500: "#f43f5e",
        },
        // ─── Extended Amber ──────────────────────────────────────────────────
        amber: {
          450: "#fbbf24",
          500: "#f59e0b",
        },
        // ─── Extended Stone ──────────────────────────────────────────────────
        stone: {
          450: "#9ca3a0",
          550: "#6b7572",
        },
        // ─── Extended Indigo ─────────────────────────────────────────────────
        indigo: {
          550: "#4f46e5",
          650: "#3730a3",
        },
      },

      // ─── Typography ─────────────────────────────────────────────────────────
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "-apple-system", "sans-serif"],
        heading: ["Poppins", "Inter", "ui-sans-serif", "sans-serif"],
        display: ["Space Grotesk", "Poppins", "Inter", "sans-serif"],
        mono: ["JetBrains Mono", "Fira Code", "ui-monospace", "monospace"],
      },
      fontSize: {
        "2xs": ["0.625rem", { lineHeight: "0.875rem" }],
        "3xs": ["0.5rem", { lineHeight: "0.75rem" }],
      },

      // ─── Spacing ─────────────────────────────────────────────────────────────
      spacing: {
        "4.5": "1.125rem",
        "13": "3.25rem",
        "15": "3.75rem",
        "18": "4.5rem",
        "22": "5.5rem",
        "26": "6.5rem",
        "72": "18rem",
        "76": "19rem",
        "80": "20rem",
        "88": "22rem",
        "96": "24rem",
      },

      // ─── Border Radius ───────────────────────────────────────────────────────
      borderRadius: {
        "4xl": "2rem",
        "5xl": "2.5rem",
      },

      // ─── Backdrop Blur ───────────────────────────────────────────────────────
      backdropBlur: {
        xs: "2px",
        "4xl": "64px",
      },

      // ─── Box Shadows ─────────────────────────────────────────────────────────
      boxShadow: {
        "glow-green": "0 0 20px -4px rgba(34, 197, 94, 0.4), 0 0 40px -8px rgba(34, 197, 94, 0.2)",
        "glow-green-sm": "0 0 10px -2px rgba(34, 197, 94, 0.3)",
        "glow-blue": "0 0 20px -4px rgba(14, 165, 233, 0.4)",
        "glow-purple": "0 0 20px -4px rgba(168, 85, 247, 0.4)",
        "card": "0 12px 40px -4px rgba(0,0,0,0.5), inset 0 1px 0 0 rgba(255,255,255,0.03)",
        "card-hover": "0 20px 60px -8px rgba(0,0,0,0.6), inset 0 1px 0 0 rgba(255,255,255,0.05)",
        "premium": "0 25px 50px -12px rgba(0,0,0,0.8), 0 0 0 1px rgba(255,255,255,0.05)",
      },

      // ─── Animations & Keyframes ──────────────────────────────────────────────
      animation: {
        "fade-in": "fade-in 0.3s ease forwards",
        "fade-out": "fade-out 0.2s ease forwards",
        "slide-up": "slide-up 0.4s cubic-bezier(0.16, 1, 0.3, 1) forwards",
        "slide-down": "slide-down 0.3s cubic-bezier(0.16, 1, 0.3, 1) forwards",
        "slide-in-right": "slide-in-right 0.4s cubic-bezier(0.16, 1, 0.3, 1) forwards",
        "scale-in": "scale-in 0.3s cubic-bezier(0.16, 1, 0.3, 1) forwards",
        "bounce-in": "bounce-in 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275) forwards",
        "shimmer": "shimmer 2s linear infinite",
        "count-up": "count-up 0.6s ease-out forwards",
        "ripple": "ripple 0.6s linear",
        "glow-pulse": "glow-pulse 3s ease-in-out infinite",
        "float": "float 6s ease-in-out infinite",
        "spin-slow": "spin 4s linear infinite",
        "ping-slow": "ping 2s cubic-bezier(0, 0, 0.2, 1) infinite",
        "progress": "progress 1s ease-out forwards",
        "stagger-in": "fade-in 0.4s ease forwards",
        "cursor-grow": "cursor-grow 0.15s ease",
        "soft-glow": "soft-glow 4.5s cubic-bezier(0.4, 0, 0.2, 1) infinite",
      },
      keyframes: {
        "fade-in": {
          "0%": { opacity: "0", transform: "translateY(4px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "fade-out": {
          "0%": { opacity: "1" },
          "100%": { opacity: "0" },
        },
        "slide-up": {
          "0%": { opacity: "0", transform: "translateY(16px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "slide-down": {
          "0%": { opacity: "0", transform: "translateY(-8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "slide-in-right": {
          "0%": { opacity: "0", transform: "translateX(24px)" },
          "100%": { opacity: "1", transform: "translateX(0)" },
        },
        "scale-in": {
          "0%": { opacity: "0", transform: "scale(0.95)" },
          "100%": { opacity: "1", transform: "scale(1)" },
        },
        "bounce-in": {
          "0%": { opacity: "0", transform: "scale(0.8)" },
          "60%": { transform: "scale(1.05)" },
          "100%": { opacity: "1", transform: "scale(1)" },
        },
        "shimmer": {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
        "ripple": {
          "0%": { transform: "scale(0)", opacity: "0.6" },
          "100%": { transform: "scale(4)", opacity: "0" },
        },
        "glow-pulse": {
          "0%, 100%": { boxShadow: "0 0 10px -2px rgba(34,197,94,0.2)" },
          "50%": { boxShadow: "0 0 25px -4px rgba(34,197,94,0.45)" },
        },
        "float": {
          "0%, 100%": { transform: "translateY(0px)" },
          "50%": { transform: "translateY(-10px)" },
        },
        "progress": {
          "0%": { width: "0%" },
          "100%": { width: "var(--progress-width, 100%)" },
        },
        "cursor-grow": {
          "0%": { transform: "scale(1)" },
          "100%": { transform: "scale(1.5)" },
        },
        "soft-glow": {
          "0%, 100%": {
            boxShadow: "0 0 15px 1px rgba(34, 197, 94, 0.12)",
            filter: "drop-shadow(0 0 4px rgba(34, 197, 94, 0.05))",
          },
          "50%": {
            boxShadow: "0 0 22px 3px rgba(34, 197, 94, 0.22)",
            filter: "drop-shadow(0 0 8px rgba(34, 197, 94, 0.12))",
          },
        },
      },

      // ─── Transition Timing ───────────────────────────────────────────────────
      transitionTimingFunction: {
        DEFAULT: "cubic-bezier(0.16, 1, 0.3, 1)",
        "spring": "cubic-bezier(0.16, 1, 0.3, 1)",
        "bounce-out": "cubic-bezier(0.175, 0.885, 0.32, 1.275)",
      },
      transitionDuration: {
        DEFAULT: "200ms",
        "150": "150ms",
        "180": "180ms",
        "200": "200ms",
        "220": "220ms",
        "250": "250ms",
      },
    },
  },
  plugins: [],
};
