"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Sparkles, Mail, Lock, User, ArrowRight, Shield } from "lucide-react";
import Link from "next/link";
import api from "../../services/api";
import { isAuthenticated } from "../../services/authService";
import { Card } from "../../components/ui/Card";
import { Badge } from "../../components/ui/Badge";
import { Button } from "../../components/ui/Button";
import { Input } from "../../components/ui/Input";

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
              Create Profile
            </h1>
            <p className="text-xs font-bold text-theme-muted mt-2 font-mono uppercase tracking-widest text-center">
              Join the sustainability operating system
            </p>
          </div>

          {error && (
            <div className="p-3 mb-6 rounded-2xl border border-red-500/25 bg-red-500/5 text-rose-450 text-xs font-medium leading-relaxed">
              {error}
            </div>
          )}

          {/* Register Form */}
          <form onSubmit={handleRegister} className="space-y-5">
            <Input 
              label="Username"
              type="text"
              required
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="e.g. greenwarrior"
              leftIcon={<User className="w-4 h-4" />}
            />

            <Input 
              label="Email Address"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="name@example.com"
              leftIcon={<Mail className="w-4 h-4" />}
            />

            <Input 
              label="Password"
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Minimum 8 characters"
              leftIcon={<Lock className="w-4 h-4" />}
            />

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
                  <span>Build Eco Profile</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </Button>
          </form>

          {/* Footer info */}
          <div className="mt-8 text-center border-t border-theme-subtle pt-6">
            <p className="text-xs text-theme-muted font-bold">
              Already have an account?{" "}
              <Link href="/login" className="text-theme-brand hover:underline cursor-pointer">
                Sign In
              </Link>
            </p>
          </div>
        </Card>
      </motion.div>
    </div>
  );
}
