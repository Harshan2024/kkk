"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { X, Sparkles, Mail, Lock, ArrowRight, Shield } from "lucide-react";
import Link from "next/link";
import api from "../../services/api";
import { isAuthenticated } from "../../services/authService";
import { Card } from "../../components/ui/Card";
import { Badge } from "../../components/ui/Badge";
import { Button } from "../../components/ui/Button";
import { Input } from "../../components/ui/Input";
import { useAIStore } from "../../stores/aiStore";

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAIStore();

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
      const success = await login(email, password);
      setLoading(false);
      if (success) {
        router.push("/");
      } else {
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

  React.useEffect(() => {
    if (isAuthenticated()) {
      router.push("/");
    }
  }, [router]);

  return (
    <div className="min-h-screen bg-theme-base text-theme-primary font-sans relative overflow-hidden flex items-center justify-center p-4">
      {/* Background Matrix/Glows */}
      <div className="absolute inset-0 dot-matrix pointer-events-none z-0" />
      <div className="absolute top-[-10%] left-[-5%] w-[50%] aspect-square rounded-full bg-theme-brand-muted opacity-20 blur-[120px] pointer-events-none z-0" />
      <div className="absolute bottom-[-10%] right-[-5%] w-[50%] aspect-square rounded-full bg-theme-brand-muted opacity-25 blur-[120px] pointer-events-none z-0" />

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="w-full max-w-md relative z-10"
      >
        <Card className="p-8 shadow-2xl" hover={false}>
          {/* Logo and Header */}
          <div className="flex flex-col items-center mb-8">
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-emerald-400 to-emerald-700 flex items-center justify-center shadow-xl shadow-emerald-500/25 mb-4">
              <span className="text-white font-black text-xl tracking-tighter">CT</span>
            </div>
            <h1 className="text-2xl font-black tracking-tight text-theme-heading flex items-center gap-1.5 font-display">
              Welcome to <span className="text-theme-brand">CarbonTracker</span>
            </h1>
            <p className="text-xs font-bold text-theme-muted mt-2 font-mono uppercase tracking-widest text-center">
              Sustainability Operating System
            </p>
          </div>

          {error && (
            <div className="p-3 mb-6 rounded-2xl border border-red-500/25 bg-red-500/5 text-rose-450 text-xs font-medium leading-relaxed">
              {error}
            </div>
          )}

          {success && (
            <div className="p-3 mb-6 rounded-2xl border border-emerald-500/25 bg-emerald-500/5 text-theme-brand text-xs font-medium leading-relaxed">
              {success}
            </div>
          )}

          {/* Login Form */}
          <form onSubmit={handleLogin} className="space-y-6">
            <Input 
              label="Email Address"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="name@example.com"
              leftIcon={<Mail className="w-4 h-4" />}
            />

            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <label className="text-[10px] font-black uppercase text-theme-muted tracking-wider block">
                  Password
                </label>
                <button
                  type="button"
                  onClick={() => setResetModalOpen(true)}
                  className="text-[10px] font-bold text-theme-brand hover:underline cursor-pointer"
                >
                  Forgot Password?
                </button>
              </div>
              <Input 
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••••••"
                leftIcon={<Lock className="w-4 h-4" />}
              />
            </div>

            <Button
              type="submit"
              disabled={loading}
              className="w-full mt-4"
              size="lg"
              glow
            >
              {loading ? (
                <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              ) : (
                <>
                  <span>Sign In to System</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </Button>
          </form>

          {/* Footer info */}
          <div className="mt-8 text-center border-t border-theme-subtle pt-6">
            <p className="text-xs text-theme-muted font-bold">
              New to CarbonTracker?{" "}
              <Link href="/register" className="text-theme-brand hover:underline cursor-pointer">
                Create an Account
              </Link>
            </p>
          </div>
        </Card>
      </motion.div>

      {/* Password Reset Modal */}
      <AnimatePresence>
        {resetModalOpen && (
          <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="w-full max-w-md relative z-10"
            >
              <Card className="p-8" hover={false}>
                <div className="flex justify-between items-center mb-6">
                  <h3 className="text-sm font-black uppercase tracking-wider text-theme-primary font-display">
                    Reset Credentials
                  </h3>
                  <button
                    onClick={() => {
                      setResetModalOpen(false);
                      setResetStep(1);
                      setResetMessage("");
                    }}
                    className="text-theme-muted hover:text-theme-primary cursor-pointer transition-colors"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>

                {resetMessage && (
                  <div className="p-3 mb-4 rounded-xl border border-amber-500/25 bg-amber-500/5 text-amber-305 text-[10px] font-mono leading-relaxed break-all">
                    {resetMessage}
                  </div>
                )}

                {modalError && (
                  <div className="p-3 mb-4 rounded-xl border border-red-500/25 bg-red-500/5 text-rose-450 text-[10px] font-mono leading-relaxed">
                    {modalError}
                  </div>
                )}

                {resetStep === 1 ? (
                  <form onSubmit={handleRequestReset} className="space-y-4">
                    <p className="text-xs text-theme-secondary leading-relaxed font-bold font-sans">
                      Enter email and we'll generate a verification token to update credentials.
                    </p>
                    <Input 
                      label="Email Address"
                      type="email"
                      required
                      value={resetEmail}
                      onChange={(e) => setResetEmail(e.target.value)}
                      placeholder="name@example.com"
                    />
                    <Button
                      type="submit"
                      disabled={loading}
                      className="w-full mt-4"
                    >
                      Request Reset Token
                    </Button>
                  </form>
                ) : (
                  <form onSubmit={handleConfirmReset} className="space-y-4">
                    <Input 
                      label="Reset Token"
                      type="text"
                      required
                      value={resetToken}
                      onChange={(e) => setResetToken(e.target.value)}
                    />
                    <Input 
                      label="New Password"
                      type="password"
                      required
                      value={newPassword}
                      onChange={(e) => setNewPassword(e.target.value)}
                      placeholder="••••••••"
                    />
                    <Button
                      type="submit"
                      disabled={loading}
                      className="w-full mt-4"
                    >
                      Confirm New Password
                    </Button>
                  </form>
                )}
              </Card>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}
