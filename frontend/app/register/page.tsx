"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Sparkles, Mail, Lock, User, ArrowRight, Shield } from "lucide-react";
import Link from "next/link";
import api from "../../services/api";

export default function RegisterPage() {
  const router = useRouter();

  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    if (!username || !email || !password) {
      setError("Please fill in all fields");
      return;
    }
    if (password.length < 8) {
      setError("Password must be at least 8 characters");
      return;
    }
    setLoading(true);

    try {
      const res = await api.register(username, email, password);
      setLoading(false);
      if (res && res.success !== false) {
        router.push("/login?registered=true");
      } else {
        setError(res?.message || "Registration failed");
      }
    } catch (err: any) {
      setLoading(false);
      setError(err?.message || "Registration failed. Username or email might be taken.");
    }
  };

  // Redirect if already authenticated
  React.useEffect(() => {
    const token = localStorage.getItem("carbontracker_token");
    if (token) {
      router.push("/");
    }
  }, [router]);

  return (
    <div className="min-h-screen bg-[#080d0a] text-stone-100 font-sans relative overflow-hidden flex items-center justify-center p-4">
      {/* Background Matrix/Glows */}
      <div className="absolute inset-0 dot-matrix pointer-events-none z-0" />
      <div className="absolute top-[-10%] left-[-5%] w-[50%] aspect-square rounded-full bg-emerald-600/5 blur-[120px] pointer-events-none z-0" />
      <div className="absolute bottom-[-10%] right-[-5%] w-[50%] aspect-square rounded-full bg-emerald-700/5 blur-[120px] pointer-events-none z-0" />

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="w-full max-w-md glass-card rounded-3xl p-8 relative z-10 border border-white/5 bg-[#0a120f]/80 backdrop-blur-xl shadow-2xl shadow-black/60"
      >
        {/* Logo and Header */}
        <div className="flex flex-col items-center mb-8">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-emerald-50 to-teal-700 flex items-center justify-center shadow-xl shadow-emerald-500/25 mb-4">
            <span className="text-white font-black text-xl tracking-tighter">CT</span>
          </div>
          <h1 className="text-2xl font-black tracking-tight text-white flex items-center gap-1.5 font-outfit">
            Create an Account
          </h1>
          <p className="text-xs font-bold text-stone-500 mt-2 font-mono uppercase tracking-widest text-center">
            Join the sustainability operating system
          </p>
        </div>

        {error && (
          <div className="p-3 mb-6 rounded-2xl border border-red-500/25 bg-red-500/5 text-red-400 text-xs font-medium leading-relaxed">
            {error}
          </div>
        )}

        {/* Register Form */}
        <form onSubmit={handleRegister} className="space-y-5">
          <div className="space-y-2">
            <label className="text-[10px] font-black uppercase text-stone-400 tracking-wider block">
              Username
            </label>
            <div className="relative">
              <User className="w-4 h-4 text-stone-500 absolute left-4 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                required
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="e.g. greenwarrior"
                className="w-full pl-12 pr-4 py-3 bg-[#060a08] border border-white/5 focus:border-emerald-500/30 rounded-2xl text-xs text-white placeholder-stone-600 focus:outline-none transition-all"
              />
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-[10px] font-black uppercase text-stone-400 tracking-wider block">
              Email Address
            </label>
            <div className="relative">
              <Mail className="w-4 h-4 text-stone-500 absolute left-4 top-1/2 -translate-y-1/2" />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="name@example.com"
                className="w-full pl-12 pr-4 py-3 bg-[#060a08] border border-white/5 focus:border-emerald-500/30 rounded-2xl text-xs text-white placeholder-stone-600 focus:outline-none transition-all"
              />
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-[10px] font-black uppercase text-stone-400 tracking-wider block">
              Password
            </label>
            <div className="relative">
              <Lock className="w-4 h-4 text-stone-500 absolute left-4 top-1/2 -translate-y-1/2" />
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Minimum 8 characters"
                className="w-full pl-12 pr-4 py-3 bg-[#060a08] border border-white/5 focus:border-emerald-500/30 rounded-2xl text-xs text-white placeholder-stone-600 focus:outline-none transition-all"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3.5 bg-gradient-to-r from-emerald-600 to-emerald-500 hover:from-emerald-500 hover:to-emerald-450 text-white font-extrabold text-xs uppercase tracking-wider rounded-2xl transition-all shadow-lg shadow-emerald-500/10 active:scale-95 cursor-pointer flex items-center justify-center gap-2"
          >
            {loading ? (
              <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
            ) : (
              <>
                <span>Build Eco Profile</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>
        </form>

        {/* Footer info */}
        <div className="mt-8 text-center border-t border-white/5 pt-6">
          <p className="text-xs text-stone-500 font-bold">
            Already have an account?{" "}
            <Link href="/login" className="text-emerald-450 hover:underline cursor-pointer">
              Sign In
            </Link>
          </p>
        </div>
      </motion.div>
    </div>
  );
}
