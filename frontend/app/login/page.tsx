"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { X, Sparkles, Mail, Lock, User, ArrowRight, Shield } from "lucide-react";
import Link from "next/link";
import api from "../../services/api";

export default function LoginPage() {
  const router = useRouter();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Password reset state
  const [resetEmail, setResetEmail] = useState("");
  const [resetModalOpen, setResetModalOpen] = useState(false);
  const [resetToken, setResetToken] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [resetStep, setResetStep] = useState(1); // 1: request, 2: confirm
  const [resetMessage, setResetMessage] = useState("");
  const [modalError, setModalError] = useState<string | null>(null);

  React.useEffect(() => {
    if (typeof window !== "undefined") {
      const params = new URLSearchParams(window.location.search);
      if (params.get("registered") === "true") {
        setSuccess("Registration successful. Please sign in with your credentials.");
      }
    }
  }, []);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    if (!email || !password) {
      setError("Please fill in all fields");
      return;
    }
    setLoading(true);

    try {
      const tokenData = await api.login(email, password);
      if (tokenData && tokenData.access_token) {
        localStorage.setItem("carbontracker_token", tokenData.access_token);
        
        try {
          const profile = await api.getProfile();
          localStorage.setItem("carbontracker_user", JSON.stringify(profile));
        } catch (profileErr) {
          console.error("Failed to load profile details", profileErr);
        }
        
        setLoading(false);
        router.push("/");
      } else {
        setLoading(false);
        setError("Invalid email or password");
      }
    } catch (err: any) {
      setLoading(false);
      setError(err?.message || "Failed to sign in. Please verify your credentials.");
    }
  };

  const handleRequestReset = async (e: React.FormEvent) => {
    e.preventDefault();
    setModalError(null);
    setResetMessage("");
    if (!resetEmail) {
      setModalError("Please enter your email");
      return;
    }
    setLoading(true);
    try {
      const res = await api.requestReset(resetEmail);
      if (res && res.token) {
        setResetStep(2);
        setResetToken(res.token);
        setResetMessage(`Reset token generated (mock delivery): ${res.token}`);
      } else {
        setModalError("Could not request reset");
      }
    } catch (err: any) {
      setModalError(err.message || "Failed to request password reset");
    } finally {
      setLoading(false);
    }
  };

  const handleConfirmReset = async (e: React.FormEvent) => {
    e.preventDefault();
    setModalError(null);
    if (!newPassword) {
      setModalError("Please enter a new password");
      return;
    }
    setLoading(true);
    try {
      const res = await api.confirmReset(resetToken, newPassword);
      if (res && res.success) {
        setResetModalOpen(false);
        setResetStep(1);
        setResetEmail("");
        setNewPassword("");
        setResetMessage("");
        setSuccess("Password has been reset successfully. Please login.");
      }
    } catch (err: any) {
      setModalError(err.message || "Failed to reset password");
    } finally {
      setLoading(false);
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
            Welcome back to <span className="text-emerald-450">CarbonTracker</span>
          </h1>
          <p className="text-xs font-bold text-stone-500 mt-2 font-mono uppercase tracking-widest text-center">
            Enter credentials to access your console
          </p>
        </div>

        {error && (
          <div className="p-3 mb-6 rounded-2xl border border-red-500/25 bg-red-500/5 text-red-400 text-xs font-medium leading-relaxed">
            {error}
          </div>
        )}

        {success && (
          <div className="p-3 mb-6 rounded-2xl border border-emerald-500/25 bg-emerald-500/5 text-emerald-450 text-xs font-medium leading-relaxed">
            {success}
          </div>
        )}

        {/* Login Form */}
        <form onSubmit={handleLogin} className="space-y-6">
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
            <div className="flex justify-between items-center">
              <label className="text-[10px] font-black uppercase text-stone-400 tracking-wider block">
                Password
              </label>
              <button
                type="button"
                onClick={() => setResetModalOpen(true)}
                className="text-[10px] font-bold text-emerald-450 hover:underline cursor-pointer"
              >
                Forgot Password?
              </button>
            </div>
            <div className="relative">
              <Lock className="w-4 h-4 text-stone-500 absolute left-4 top-1/2 -translate-y-1/2" />
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••••••"
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
                <span>Sign In to System</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>
        </form>

        {/* Footer info */}
        <div className="mt-8 text-center border-t border-white/5 pt-6">
          <p className="text-xs text-stone-500 font-bold">
            New to CarbonTracker?{" "}
            <Link href="/register" className="text-emerald-450 hover:underline cursor-pointer">
              Create an Account
            </Link>
          </p>
        </div>
      </motion.div>

      {/* Password Reset Modal */}
      <AnimatePresence>
        {resetModalOpen && (
          <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="w-full max-w-md glass-card rounded-3xl p-8 border border-white/10 bg-[#0c1411]"
            >
              <div className="flex justify-between items-center mb-6">
                <h3 className="text-sm font-black uppercase tracking-wider text-white">
                  Reset System Password
                </h3>
                <button
                  onClick={() => {
                    setResetModalOpen(false);
                    setResetStep(1);
                    setResetMessage("");
                  }}
                  className="text-stone-500 hover:text-white cursor-pointer transition-colors"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              {resetMessage && (
                <div className="p-3 mb-4 rounded-xl border border-amber-500/25 bg-amber-500/5 text-amber-300 text-[10px] font-mono leading-relaxed break-all">
                  {resetMessage}
                </div>
              )}

              {modalError && (
                <div className="p-3 mb-4 rounded-xl border border-red-500/25 bg-red-500/5 text-red-450 text-[10px] font-mono leading-relaxed">
                  {modalError}
                </div>
              )}

              {resetStep === 1 ? (
                <form onSubmit={handleRequestReset} className="space-y-4">
                  <p className="text-xs text-stone-400 leading-relaxed font-bold">
                    Enter your email address and we'll generate a verification token to update your credentials.
                  </p>
                  <div className="space-y-2">
                    <label className="text-[10px] font-black uppercase text-stone-400 tracking-wider">
                      Email Address
                    </label>
                    <input
                      type="email"
                      required
                      value={resetEmail}
                      onChange={(e) => setResetEmail(e.target.value)}
                      placeholder="name@example.com"
                      className="w-full px-4 py-3 bg-[#060a08] border border-white/5 focus:border-emerald-500/30 rounded-2xl text-xs text-white placeholder-stone-600 focus:outline-none transition-all"
                    />
                  </div>
                  <button
                    type="submit"
                    disabled={loading}
                    className="w-full py-3 bg-emerald-600 hover:bg-emerald-500 text-white font-extrabold text-xs uppercase tracking-wider rounded-2xl transition-all cursor-pointer"
                  >
                    Request Reset Token
                  </button>
                </form>
              ) : (
                <form onSubmit={handleConfirmReset} className="space-y-4">
                  <div className="space-y-2">
                    <label className="text-[10px] font-black uppercase text-stone-400 tracking-wider">
                      Reset Token
                    </label>
                    <input
                      type="text"
                      required
                      value={resetToken}
                      onChange={(e) => setResetToken(e.target.value)}
                      className="w-full px-4 py-3 bg-[#060a08] border border-white/5 rounded-2xl text-xs text-white focus:outline-none"
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="text-[10px] font-black uppercase text-stone-400 tracking-wider">
                      New Password
                    </label>
                    <input
                      type="password"
                      required
                      value={newPassword}
                      onChange={(e) => setNewPassword(e.target.value)}
                      placeholder="••••••••"
                      className="w-full px-4 py-3 bg-[#060a08] border border-white/5 focus:border-emerald-500/30 rounded-2xl text-xs text-white focus:outline-none transition-all"
                    />
                  </div>
                  <button
                    type="submit"
                    disabled={loading}
                    className="w-full py-3 bg-emerald-600 hover:bg-emerald-500 text-white font-extrabold text-xs uppercase tracking-wider rounded-2xl transition-all cursor-pointer"
                  >
                    Confirm New Password
                  </button>
                </form>
              )}
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}
