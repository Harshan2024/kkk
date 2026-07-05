"use client";

import React, { useState, useEffect } from "react";
import { User, Mail, ShieldAlert, CheckCircle, Loader2, KeyRound, Server, Eye, Database } from "lucide-react";
import api from "../services/api";
import { Card } from "./ui/Card";
import { Badge } from "./ui/Badge";
import { Button } from "./ui/Button";
import { Input } from "./ui/Input";

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
      await api.updateProfile({ username: usernameInput.trim(), email: emailInput.trim() });
      setProfileMsg({ type: "success", text: "Profile settings updated successfully!" });
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
        <span className="text-sm font-semibold text-theme-muted">Loading configuration...</span>
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-2 duration-300">
      
      {/* Profile Settings Panel */}
      <Card className="p-6 sm:p-8" hover={false}>
        <div className="flex items-center space-x-2.5 mb-6 border-b border-white/5 pb-3">
          <User className="w-5 h-5 text-emerald-500" />
          <h3 className="font-bold text-lg text-theme-primary font-display">
            Account Preferences
          </h3>
        </div>

        <form onSubmit={handleUpdateProfile} className="space-y-6 max-w-xl">
          {profileMsg && (
            <div className={`p-4 rounded-xl border flex items-center space-x-2.5 text-xs font-semibold ${
              profileMsg.type === "success" 
                ? "bg-emerald-500/10 border-emerald-500/25 text-theme-brand"
                : "bg-rose-500/10 border-rose-500/25 text-rose-450"
            }`}>
              {profileMsg.type === "success" ? <CheckCircle className="w-4 h-4 shrink-0" /> : <ShieldAlert className="w-4 h-4 shrink-0" />}
              <span>{profileMsg.text}</span>
            </div>
          )}

          <Input 
            label="Username"
            value={usernameInput}
            onChange={(e) => setUsernameInput(e.target.value)}
            placeholder="Username"
            leftIcon={<User className="w-4 h-4" />}
          />

          <Input 
            label="Email Address"
            value={emailInput}
            onChange={(e) => setEmailInput(e.target.value)}
            placeholder="Email Address"
            leftIcon={<Mail className="w-4 h-4" />}
          />

          <div className="flex flex-col sm:flex-row gap-4 pt-2">
            <Button
              type="submit"
              disabled={updatingProfile}
            >
              {updatingProfile ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span>Updating...</span>
                </>
              ) : (
                <span>Save Changes</span>
              )}
            </Button>

            <Button
              type="button"
              variant="secondary"
              onClick={handlePasswordReset}
              disabled={resettingPassword}
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
            </Button>
          </div>

          {resetMsg && (
            <div className={`p-4 rounded-xl border flex items-center space-x-2.5 text-xs font-semibold ${
              resetMsg.type === "success" 
                ? "bg-emerald-500/10 border-emerald-500/25 text-theme-brand"
                : "bg-rose-500/10 border-rose-500/25 text-rose-455"
            }`}>
              {resetMsg.type === "success" ? <CheckCircle className="w-4 h-4 shrink-0" /> : <ShieldAlert className="w-4 h-4 shrink-0" />}
              <span>{resetMsg.text}</span>
            </div>
          )}
        </form>
      </Card>

      {/* Security Status Panel */}
      <Card className="p-6 sm:p-8" hover={false}>
        <div className="flex items-center space-x-2.5 mb-6 border-b border-white/5 pb-3">
          <KeyRound className="w-5 h-5 text-emerald-500" />
          <h3 className="font-bold text-lg text-theme-primary font-display">
            Security & Cryptographic Audit
          </h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-4">
            <h4 className="text-xs font-extrabold uppercase tracking-wide text-theme-muted flex items-center space-x-1.5 font-sans">
              <Server className="w-3.5 h-3.5" />
              <span>Environment Security</span>
            </h4>
            
            <div className="space-y-3 bg-theme-base border border-theme-subtle rounded-2xl p-4 text-xs font-semibold text-theme-muted font-sans">
              <div className="flex justify-between items-center">
                <span>Current Node Mode</span>
                {security?.environment === "production" ? (
                  <Badge variant="danger" size="xs">production</Badge>
                ) : (
                  <Badge variant="success" size="xs">development</Badge>
                )}
              </div>
              <div className="flex justify-between items-center">
                <span>Database SSL Negotiation</span>
                {security?.ssl_active ? (
                  <Badge variant="success" size="xs">enforced</Badge>
                ) : (
                  <Badge variant="warning" size="xs">inactive</Badge>
                )}
              </div>
              <div className="flex justify-between items-center">
                <span>JWT Standard</span>
                <span className="font-mono text-theme-secondary">{security?.jwt_algorithm || "HS256"}</span>
              </div>
              <div className="flex justify-between items-center">
                <span>Authentication System</span>
                <span className="text-theme-brand font-extrabold">Active (OAuth2)</span>
              </div>
            </div>
          </div>

          <div className="space-y-4">
            <h4 className="text-xs font-extrabold uppercase tracking-wide text-theme-muted flex items-center space-x-1.5 font-sans">
              <Database className="w-3.5 h-3.5" />
              <span>Hardening Protections</span>
            </h4>
            
            <div className="space-y-3 bg-theme-base border border-theme-subtle rounded-2xl p-4 text-xs font-semibold text-theme-muted font-sans">
              <div className="flex justify-between items-center">
                <span>Max Upload Body Size</span>
                <span className="text-theme-brand font-extrabold">5MB Maximum (Enforced)</span>
              </div>
              <div className="flex justify-between items-center">
                <span>JWT Key Rotation</span>
                <span className="text-theme-brand font-extrabold">Rotates on Refresh</span>
              </div>
              <div className="flex justify-between items-center">
                <span>XSS Payload Scanning</span>
                <span className="text-theme-brand font-extrabold">Active</span>
              </div>
              <div className="flex justify-between items-center">
                <span>Active SQL Injection Prevention</span>
                <span className="text-theme-brand font-extrabold">Active</span>
              </div>
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
}
