"use client";

import React, { useState, useEffect } from "react";
import { User, Mail, ShieldAlert, CheckCircle, Loader2, KeyRound, Server, Eye, Database } from "lucide-react";
import api from "../services/api";

interface ProfileData {
  username: string;
  email: string;
  xp: number;
  level: number;
  joined_date: string;
}

interface SecurityData {
  environment: string;
  ssl_active: boolean;
  auth_enabled: boolean;
  jwt_algorithm: string;
}

export default function Settings() {
  const [profile, setProfile] = useState<ProfileData | null>(null);
  const [security, setSecurity] = useState<SecurityData | null>(null);
  const [usernameInput, setUsernameInput] = useState("");
  const [emailInput, setEmailInput] = useState("");
  
  const [loadingProfile, setLoadingProfile] = useState(true);
  const [updatingProfile, setUpdatingProfile] = useState(false);
  const [resettingPassword, setResettingPassword] = useState(false);
  
  const [profileMsg, setProfileMsg] = useState<{ type: "success" | "error"; text: string } | null>(null);
  const [resetMsg, setResetMsg] = useState<{ type: "success" | "error"; text: string } | null>(null);

  useEffect(() => {
    async function loadData() {
      try {
        setLoadingProfile(true);
        const pData = await api.getProfile();
        if (pData) {
          setProfile(pData);
          setUsernameInput(pData.username);
          setEmailInput(pData.email || "");
        }
        
        const secRes = await api.getSecurityStatus();
        if (secRes && secRes.success && secRes.data) {
          setSecurity(secRes.data);
        } else if (secRes && secRes.environment) {
          setSecurity(secRes as any);
        }
      } catch (err) {
        console.error("Failed to load settings data:", err);
      } finally {
        setLoadingProfile(false);
      }
    }
    loadData();
  }, []);

  const handleUpdateProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!usernameInput.trim() || !emailInput.trim()) {
      setProfileMsg({ type: "error", text: "Username and email cannot be empty." });
      return;
    }
    setProfileMsg(null);
    setUpdatingProfile(true);
    try {
      await api.updateProfile(usernameInput.trim(), emailInput.trim());
      setProfileMsg({ type: "success", text: "Profile settings updated successfully!" });
      // Update local profile state
      if (profile) {
        setProfile({ ...profile, username: usernameInput.trim(), email: emailInput.trim() });
      }
    } catch (err: any) {
      setProfileMsg({ type: "error", text: err.message || "Failed to update profile details." });
    } finally {
      setUpdatingProfile(false);
    }
  };

  const handlePasswordReset = async () => {
    if (!emailInput.trim()) {
      setResetMsg({ type: "error", text: "Please provide an email to request a reset." });
      return;
    }
    setResetMsg(null);
    setResettingPassword(true);
    try {
      await api.requestReset(emailInput.trim());
      setResetMsg({ type: "success", text: "Password reset link sent to your registered email!" });
    } catch (err: any) {
      setResetMsg({ type: "error", text: err.message || "Failed to request password reset." });
    } finally {
      setResettingPassword(false);
    }
  };

  if (loadingProfile) {
    return (
      <div className="flex flex-col items-center justify-center p-12 space-y-4">
        <Loader2 className="w-8 h-8 text-emerald-500 animate-spin" />
        <span className="text-sm font-semibold text-stone-505 dark:text-stone-400">Loading profile configuration...</span>
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-2 duration-300">
      
      {/* Profile Settings Panel */}
      <div className="glass-card rounded-3xl p-6 sm:p-8 transition-all duration-300">
        <div className="flex items-center space-x-2.5 mb-6 border-b border-white/10 dark:border-white/5 pb-3">
          <User className="w-5 h-5 text-emerald-500" />
          <h3 className="font-bold text-lg text-earth-800 dark:text-forest-100">
            Account Preferences
          </h3>
        </div>

        <form onSubmit={handleUpdateProfile} className="space-y-6 max-w-xl">
          {profileMsg && (
            <div className={`p-4 rounded-xl border flex items-center space-x-2.5 text-xs font-semibold ${
              profileMsg.type === "success" 
                ? "bg-emerald-500/10 border-emerald-500/25 text-emerald-600 dark:text-emerald-400"
                : "bg-rose-500/10 border-rose-500/25 text-rose-600 dark:text-rose-400"
            }`}>
              {profileMsg.type === "success" ? <CheckCircle className="w-4 h-4 shrink-0" /> : <ShieldAlert className="w-4 h-4 shrink-0" />}
              <span>{profileMsg.text}</span>
            </div>
          )}

          <div className="space-y-2">
            <label className="text-xs font-bold uppercase tracking-wider text-earth-700 dark:text-stone-400">
              Username
            </label>
            <div className="relative">
              <input
                type="text"
                value={usernameInput}
                onChange={(e) => setUsernameInput(e.target.value)}
                className="w-full pl-10 pr-4 py-2.5 bg-stone-900/50 dark:bg-black/40 border border-white/10 rounded-xl text-sm outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500/25 transition-all text-earth-900 dark:text-white"
                placeholder="Username"
              />
              <User className="absolute left-3.5 top-3.5 w-4 h-4 text-stone-500" />
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-xs font-bold uppercase tracking-wider text-earth-700 dark:text-stone-400">
              Email Address
            </label>
            <div className="relative">
              <input
                type="email"
                value={emailInput}
                onChange={(e) => setEmailInput(e.target.value)}
                className="w-full pl-10 pr-4 py-2.5 bg-stone-900/50 dark:bg-black/40 border border-white/10 rounded-xl text-sm outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500/25 transition-all text-earth-900 dark:text-white"
                placeholder="Email Address"
              />
              <Mail className="absolute left-3.5 top-3.5 w-4 h-4 text-stone-500" />
            </div>
          </div>

          <div className="flex flex-col sm:flex-row gap-4 pt-2">
            <button
              type="submit"
              disabled={updatingProfile}
              className="px-6 py-2.5 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white rounded-xl text-xs font-bold transition-all flex items-center justify-center space-x-2 active:scale-95 cursor-pointer shadow-lg shadow-emerald-600/10"
            >
              {updatingProfile ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span>Updating...</span>
                </>
              ) : (
                <span>Save Changes</span>
              )}
            </button>

            <button
              type="button"
              onClick={handlePasswordReset}
              disabled={resettingPassword}
              className="px-6 py-2.5 bg-stone-800 hover:bg-stone-700 text-stone-200 border border-white/5 rounded-xl text-xs font-bold transition-all flex items-center justify-center space-x-2 active:scale-95 cursor-pointer"
            >
              {resettingPassword ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span>Requesting Reset...</span>
                </>
              ) : (
                <>
                  <KeyRound className="w-3.5 h-3.5" />
                  <span>Request Password Reset</span>
                </>
              )}
            </button>
          </div>

          {resetMsg && (
            <div className={`p-4 rounded-xl border flex items-center space-x-2.5 text-xs font-semibold ${
              resetMsg.type === "success" 
                ? "bg-emerald-500/10 border-emerald-500/25 text-emerald-600 dark:text-emerald-400"
                : "bg-rose-500/10 border-rose-500/25 text-rose-600 dark:text-rose-400"
            }`}>
              {resetMsg.type === "success" ? <CheckCircle className="w-4 h-4 shrink-0" /> : <ShieldAlert className="w-4 h-4 shrink-0" />}
              <span>{resetMsg.text}</span>
            </div>
          )}
        </form>
      </div>

      {/* Security Status Panel */}
      <div className="glass-card rounded-3xl p-6 sm:p-8 transition-all duration-300">
        <div className="flex items-center space-x-2.5 mb-6 border-b border-white/10 dark:border-white/5 pb-3">
          <KeyRound className="w-5 h-5 text-emerald-500" />
          <h3 className="font-bold text-lg text-earth-800 dark:text-forest-100">
            System Security & Infrastructure Audit
          </h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-4">
            <h4 className="text-xs font-extrabold uppercase tracking-wide text-stone-500 dark:text-stone-400 flex items-center space-x-1.5">
              <Server className="w-3.5 h-3.5" />
              <span>Environment Security</span>
            </h4>
            
            <div className="space-y-3 bg-stone-900/20 dark:bg-black/20 border border-white/5 rounded-2xl p-4 text-xs font-semibold">
              <div className="flex justify-between items-center">
                <span className="text-stone-500 dark:text-stone-400">Current Node Mode</span>
                <span className={`px-2 py-0.5 rounded text-[10px] uppercase font-extrabold ${
                  security?.environment === "production"
                    ? "bg-rose-500/15 text-rose-500 border border-rose-500/25"
                    : "bg-emerald-500/15 text-emerald-500 border border-emerald-500/25"
                }`}>
                  {security?.environment || "development"}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-stone-500 dark:text-stone-400">Database SSL Negotiation</span>
                <span className={`px-2 py-0.5 rounded text-[10px] uppercase font-extrabold ${
                  security?.ssl_active
                    ? "bg-emerald-500/15 text-emerald-500 border border-emerald-500/25"
                    : "bg-amber-500/15 text-amber-500 border border-amber-500/25"
                }`}>
                  {security?.ssl_active ? "Enforced (Required)" : "Inactive / Local Standard"}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-stone-500 dark:text-stone-400">JWT Token Security Standard</span>
                <span className="font-mono text-stone-300">{security?.jwt_algorithm || "HS256"}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-stone-500 dark:text-stone-400">Authentication System</span>
                <span className="text-emerald-500 font-extrabold">Active (OAuth2 Bearer Flow)</span>
              </div>
            </div>
          </div>

          <div className="space-y-4">
            <h4 className="text-xs font-extrabold uppercase tracking-wide text-stone-500 dark:text-stone-400 flex items-center space-x-1.5">
              <Database className="w-3.5 h-3.5" />
              <span>Hardening Protections</span>
            </h4>
            
            <div className="space-y-3 bg-stone-900/20 dark:bg-black/20 border border-white/5 rounded-2xl p-4 text-xs font-semibold">
              <div className="flex justify-between items-center">
                <span className="text-stone-500 dark:text-stone-400">Max Upload Body Size</span>
                <span className="text-emerald-500 font-extrabold">5MB Maximum (Enforced)</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-stone-500 dark:text-stone-400">JWT Key Rotation</span>
                <span className="text-emerald-500 font-extrabold">Rotates on Refresh (Rotation Flow)</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-stone-500 dark:text-stone-400">XSS Payload Scanning</span>
                <span className="text-emerald-500 font-extrabold">Active (Reject on Script/JS URI)</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-stone-500 dark:text-stone-400">Active SQL Injection Prevention</span>
                <span className="text-emerald-500 font-extrabold">Active (Parameterized Queries)</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
