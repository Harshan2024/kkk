"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { 
  User, Mail, Phone, MapPin, Globe, GraduationCap, Calendar, 
  Award, Flame, Leaf, Zap, Shield, Camera, Save, ArrowLeft, Loader2, Sparkles, Trophy, ShoppingBag
} from "lucide-react";

import Sidebar from "../../components/Sidebar";
import Topbar from "../../components/Topbar";
import ErrorBoundary from "../../components/ErrorBoundary";
import api from "../../services/api";
import { loadToken, removeToken, saveUser } from "../../services/authService";
import { Card } from "../../components/ui/Card";
import { Badge } from "../../components/ui/Badge";
import { Button } from "../../components/ui/Button";
import { Input, Textarea, Select } from "../../components/ui/Input";
import { ProfileSkeleton } from "../../components/ui/Skeleton";
import PremiumCursor from "../../components/PremiumCursor";

export default function ProfilePage() {
  const router = useRouter();

  // Authentication state
  const [isAuthenticated, setIsAuthenticated] = useState(true);
  const [token, setToken] = useState<string | null>(null);

  // Profile data state
  const [profile, setProfile] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saveSuccess, setSaveSuccess] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  // Statistics state
  const [stats, setStats] = useState({
    totalActivities: 0,
    currentStreak: 1,
    longestStreak: 1,
    totalCarbon: 0.0,
    achievementsEarned: 0,
    rewardsRedeemed: 0,
    weeklyTrend: "Stable"
  });

  // Sidebar/Topbar state
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [region, setRegion] = useState("Global");

  // Form states
  const [fullName, setFullName] = useState("");
  const [phoneNumber, setPhoneNumber] = useState("");
  const [dob, setDob] = useState("");
  const [gender, setGender] = useState("");
  const [location, setLocation] = useState("");
  const [country, setCountry] = useState("");
  const [college, setCollege] = useState("");
  const [department, setDepartment] = useState("");
  const [bio, setBio] = useState("");

  // Avatar upload state
  const [uploadingAvatar, setUploadingAvatar] = useState(false);
  const [avatarError, setAvatarError] = useState<string | null>(null);

  // Verify authentication on mount
  useEffect(() => {
    const activeToken = loadToken();
    if (!activeToken) {
      setIsAuthenticated(false);
      router.push("/login");
    } else {
      setToken(activeToken);
    }
  }, [router]);

  // Load profile and statistics data
  const loadProfileData = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getProfile();
      const p = (res && (res as any).data) ? (res as any).data : res;
      if (p) {
        setProfile(p);
        setFullName(p.full_name || "");
        setPhoneNumber(p.phone_number || "");
        setDob(p.date_of_birth || "");
        setGender(p.gender || "");
        setLocation(p.location || "");
        setCountry(p.country || "");
        setCollege(p.college || "");
        setDepartment(p.department || "");
        setBio(p.bio || "");
      } else {
        setProfile(res);
      }

      try {
        const [gProfile, summary, achievementsList] = await Promise.all([
          api.getGamificationProfile().catch(err => { console.warn("Failed to fetch gamification profile:", err); return null; }),
          api.getDashboardSummary().catch(err => { console.warn("Failed to fetch summary:", err); return null; }),
          api.getAchievements().catch(err => { console.warn("Failed to fetch achievements:", err); return [] })
        ]);

        setStats({
          totalActivities: summary?.trends?.length || 0,
          currentStreak: gProfile?.streak || summary?.streaks?.current_streak || 1,
          longestStreak: summary?.streaks?.longest_streak || gProfile?.streak || 1,
          totalCarbon: summary?.weekly_emissions || 0.0,
          achievementsEarned: achievementsList?.length || gProfile?.level || 0,
          rewardsRedeemed: gProfile?.redeemed_rewards?.length || 0,
          weeklyTrend: summary?.ai_dashboard?.weekly_trend || "Stable"
        });
      } catch (statsErr) {
        console.error("Failed to load full stats, using default computed fallbacks", statsErr);
      }

    } catch (err: any) {
      console.error(err);
      setError(err?.message || "Failed to load profile data.");
      const msg = err?.message || String(err);
      const isAuthError = msg.includes("401") || msg.includes("403") || msg.toLowerCase().includes("session expired") || msg.toLowerCase().includes("token") || msg.toLowerCase().includes("credentials") || msg.toLowerCase().includes("signature");
      if (isAuthError) {
        removeToken();
        router.push("/login");
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isAuthenticated && token) {
      loadProfileData();
    }
  }, [isAuthenticated, token]);

  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setSaveSuccess(null);
    setError(null);

    const payload = {
      full_name: fullName,
      phone_number: phoneNumber,
      date_of_birth: dob,
      gender: gender,
      location: location,
      country: country,
      college: college,
      department: department,
      bio: bio
    };

    try {
      const res = await api.updateProfile(payload);
      const p = (res && (res as any).data) ? (res as any).data : res;
      if (p) {
        setSaveSuccess("Profile updated successfully!");
        setProfile(p);
        saveUser(p);
      } else {
        setError("Failed to save profile changes.");
      }
    } catch (err: any) {
      setError(err?.message || "An error occurred while saving profile.");
    } finally {
      setSaving(false);
    }
  };

  const handleAvatarChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0) return;
    const file = e.target.files[0];

    const validExtensions = ["png", "jpg", "jpeg", "webp", "gif"];
    const ext = file.name.split(".").pop()?.toLowerCase();
    if (!ext || !validExtensions.includes(ext)) {
      setAvatarError("Supported formats: PNG, JPG, JPEG, WEBP, GIF");
      return;
    }
    if (file.size > 5 * 1024 * 1024) {
      setAvatarError("File size exceeds 5MB limit");
      return;
    }

    setUploadingAvatar(true);
    setAvatarError(null);
    setSaveSuccess(null);

    try {
      const res = await api.uploadAvatar(file);
      const p = (res && res.data) ? res.data : res;
      const success = res && (res.success !== undefined ? res.success : !!p);
      if (success && p) {
        setProfile(p);
        saveUser(p);
        setSaveSuccess("Profile picture updated!");
      } else {
        setAvatarError("Failed to upload avatar");
      }
    } catch (err: any) {
      setAvatarError(err?.message || "Failed to upload avatar");
    } finally {
      setUploadingAvatar(false);
    }
  };

  const memberSince = profile?.created_at
    ? new Date(profile.created_at).toLocaleDateString("en-US", { year: "numeric", month: "long" })
    : "June 2026";

  const initials = profile?.full_name
    ? profile.full_name.split(" ").map((n: string) => n[0]).join("").toUpperCase().substring(0, 2)
    : profile?.username?.substring(0, 2).toUpperCase() || "CT";

  const nextLevelXp = (profile?.level || 1) * 200;
  const currentXp = profile?.xp || 0;
  const xpPct = Math.min(100, Math.round((currentXp / nextLevelXp) * 100));

  const getRank = (score: number) => {
    if (score >= 95) return "Elite Eco Citizen";
    if (score >= 90) return "Sustainer Champion";
    if (score >= 80) return "Green Guardian";
    return "Eco Apprentice";
  };

  if (!isAuthenticated) return null;

  return (
    <div className="min-h-screen bg-theme-base text-theme-primary font-sans relative overflow-x-hidden transition-colors duration-300">
      {/* Background Matrix/Glows */}
      <div className="absolute inset-0 dot-matrix pointer-events-none z-0" />
      <div className="absolute top-[-10%] left-[-5%] w-[45%] aspect-square rounded-full bg-theme-brand-muted opacity-25 blur-[120px] pointer-events-none z-0" />
      <div className="absolute bottom-[-10%] right-[-5%] w-[45%] aspect-square rounded-full bg-theme-brand-muted opacity-20 blur-[120px] pointer-events-none z-0" />

      <PremiumCursor />

      {/* Sidebar */}
      <ErrorBoundary>
        <Sidebar
          currentTab="profile"
          onTabChange={(tab) => router.push(`/?tab=${tab}`)}
          username={profile?.username || "Guest"}
          xp={profile?.xp || 0}
          level={profile?.level || 1}
          streak={stats.currentStreak}
          isOpen={sidebarOpen}
          onClose={() => setSidebarOpen(false)}
        />
      </ErrorBoundary>

      {/* Main Viewport */}
      <div className="lg:pl-64 flex flex-col min-h-screen relative z-10">
        <ErrorBoundary>
          <Topbar onRefresh={loadProfileData} region={region} onRegionChange={setRegion} />
        </ErrorBoundary>

        <main className="flex-1 px-4 sm:px-6 lg:px-8 py-6 space-y-6">
          {/* Header Row */}
          <div className="flex items-center justify-between select-none">
            <div className="flex items-center space-x-3">
              <Button 
                variant="secondary"
                size="sm"
                onClick={() => router.push("/")}
              >
                <ArrowLeft className="w-4 h-4" />
              </Button>
              <div>
                <h1 className="text-xl sm:text-2xl font-black tracking-tight text-white flex items-center gap-1.5 font-display">
                  User <span className="text-theme-brand">Console</span>
                </h1>
                <p className="text-[10px] font-bold text-theme-muted uppercase tracking-widest leading-none mt-1 font-sans">
                  Manage credentials, profile tags, and stats
                </p>
              </div>
            </div>
          </div>

          {/* Success/Error Banners */}
          {error && (
            <div className="p-4 rounded-2xl border border-rose-500/30 bg-rose-500/10 text-rose-450 text-xs font-bold animate-in fade-in select-none">
              {error}
            </div>
          )}
          {saveSuccess && (
            <div className="p-4 rounded-2xl border border-emerald-500/30 bg-emerald-500/10 text-theme-brand text-xs font-bold animate-in fade-in select-none">
              {saveSuccess}
            </div>
          )}

          {loading ? (
            <ProfileSkeleton />
          ) : (
            <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
              {/* Left Column */}
              <div className="xl:col-span-1 space-y-6 flex flex-col">
                {/* 1. Avatar Card */}
                <Card className="flex flex-col items-center justify-center text-center shadow-xl relative overflow-hidden select-none" hover={false}>
                  <div className="absolute top-0 right-0 w-24 h-24 bg-emerald-500/5 blur-[40px] pointer-events-none rounded-full" />
                  
                  <div className="relative group mb-4">
                    <div className="w-24 h-24 rounded-full overflow-hidden border-2 border-emerald-500/35 bg-stone-900 shadow-lg flex items-center justify-center text-2xl font-black text-white relative">
                      {profile?.profile_picture ? (
                        <img 
                          src={profile.profile_picture.startsWith("http") ? profile.profile_picture : `${process.env.NEXT_PUBLIC_API_URL || "https://kkk-harshan-sona.onrender.com"}${profile.profile_picture}`} 
                          alt="Profile Avatar" 
                          className="w-full h-full object-cover" 
                        />
                      ) : (
                        <span>{initials}</span>
                      )}

                      {uploadingAvatar && (
                        <div className="absolute inset-0 bg-black/60 flex items-center justify-center">
                          <Loader2 className="w-6 h-6 text-theme-brand animate-spin" />
                        </div>
                      )}
                    </div>
                    
                    <label className="absolute bottom-0 right-0 p-2 bg-emerald-600 hover:bg-emerald-500 rounded-full border border-emerald-500/40 text-white cursor-pointer transition-all shadow-md active:scale-95 group-hover:scale-105">
                      <Camera className="w-3.5 h-3.5" />
                      <input 
                        type="file" 
                        accept="image/*" 
                        onChange={handleAvatarChange} 
                        className="hidden" 
                        disabled={uploadingAvatar}
                      />
                    </label>
                  </div>

                  <h3 className="text-base font-black text-theme-primary">{profile?.full_name || profile?.username}</h3>
                  <p className="text-[10px] font-extrabold uppercase tracking-widest text-theme-brand mt-1">
                    Level {profile?.level || 1} • {getRank(profile?.carbon_score || 96.0)}
                  </p>
                  <p className="text-[10px] text-theme-muted mt-2 font-bold leading-relaxed max-w-xs line-clamp-3 font-sans">
                    {profile?.bio || "No biography provided yet. Write something about your sustainability journey!"}
                  </p>

                  {avatarError && (
                    <span className="text-[9px] font-bold text-rose-450 mt-3 block">{avatarError}</span>
                  )}
                </Card>

                {/* 2. Carbon Identity Card */}
                <div className="glass-premium rounded-3xl p-6 border border-emerald-950/20 bg-gradient-to-br from-[#0c1a13] via-[#09100c] to-[#040805] shadow-2xl relative overflow-hidden flex flex-col justify-between aspect-[1.58/1] select-none text-stone-100 group hover:border-emerald-500/20 transition-all duration-300">
                  <div className="absolute top-0 right-0 w-36 h-36 bg-emerald-500/10 blur-[60px] pointer-events-none rounded-full" />
                  <div className="absolute bottom-0 left-0 w-24 h-24 bg-teal-500/5 blur-[40px] pointer-events-none rounded-full" />

                  {/* Header Row */}
                  <div className="flex justify-between items-start">
                    <div className="flex items-center space-x-2">
                      <div className="w-7 h-7 rounded-lg bg-emerald-500/10 flex items-center justify-center border border-emerald-500/20">
                        <Leaf className="w-4 h-4 text-emerald-400" />
                      </div>
                      <div>
                        <h4 className="text-[10px] font-black uppercase tracking-widest text-stone-300">
                          CarbonIdentity
                        </h4>
                        <span className="text-[7px] text-stone-500 uppercase tracking-widest font-extrabold leading-none block">
                          Sustainability OS
                        </span>
                      </div>
                    </div>
                    <span className="text-[9px] font-mono px-2 py-0.5 rounded bg-emerald-950/40 border border-emerald-500/15 text-emerald-400 font-bold uppercase tracking-wider">
                      RANK #{profile?.level ? Math.max(1, 100 - profile.level * 2) : 98}
                    </span>
                  </div>

                  {/* Body Details */}
                  <div className="my-6">
                    <span className="text-[8px] text-stone-550 uppercase font-black tracking-wider block mb-1">
                      Identity Holder
                    </span>
                    <h2 className="text-sm sm:text-base font-black tracking-tight text-white truncate font-display">
                      {profile?.full_name || profile?.username || "Guest Sustainability Agent"}
                    </h2>
                    
                    <div className="mt-3.5 space-y-1">
                      <div className="flex justify-between text-[8px] font-mono text-stone-400">
                        <span>XP PROGRESS</span>
                        <span>{profile?.xp || 0} / {nextLevelXp} XP ({xpPct}%)</span>
                      </div>
                      <div className="w-full h-1.5 rounded-full bg-white/5 overflow-hidden">
                        <div 
                          className="h-full rounded-full bg-gradient-to-r from-emerald-500 to-teal-400" 
                          style={{ width: `${xpPct}%` }}
                        />
                      </div>
                    </div>
                  </div>

                  {/* Footer Row */}
                  <div className="grid grid-cols-3 gap-2 border-t border-white/5 pt-3 text-[9px] font-mono text-stone-400">
                    <div>
                      <span className="text-[7px] text-stone-550 block leading-none font-bold uppercase">Score</span>
                      <span className="text-white font-bold block mt-0.5">{(profile?.carbon_score || 96.0).toFixed(1)}</span>
                    </div>
                    <div>
                      <span className="text-[7px] text-stone-550 block leading-none font-bold uppercase">Level</span>
                      <span className="text-white font-bold block mt-0.5">Lvl {profile?.level || 1}</span>
                    </div>
                    <div>
                      <span className="text-[7px] text-stone-550 block leading-none font-bold uppercase">Member Since</span>
                      <span className="text-white font-bold block mt-0.5">{memberSince}</span>
                    </div>
                  </div>
                </div>

                {/* 3. Telemetry Panel */}
                <Card hover={false} className="space-y-4 flex-1">
                  <h3 className="text-xs font-black uppercase tracking-widest text-theme-muted flex items-center gap-1.5">
                    <Sparkles className="w-3.5 h-3.5 text-theme-brand" />
                    Telemetry Summary
                  </h3>

                  <div className="grid grid-cols-2 gap-3.5">
                    <div className="p-3 bg-white/[0.01] border border-theme-subtle rounded-2xl">
                      <span className="text-[7px] text-theme-muted uppercase font-black tracking-wider block mb-1">
                        Total Activities
                      </span>
                      <span className="text-base font-black text-theme-primary flex items-center gap-1">
                        <Leaf className="w-3.5 h-3.5 text-emerald-555" />
                        {stats.totalActivities}
                      </span>
                    </div>

                    <div className="p-3 bg-white/[0.01] border border-theme-subtle rounded-2xl">
                      <span className="text-[7px] text-theme-muted uppercase font-black tracking-wider block mb-1">
                        Current Streak
                      </span>
                      <span className="text-base font-black text-orange-450 flex items-center gap-1">
                        <Flame className="w-3.5 h-3.5 text-orange-500 fill-orange-500" />
                        {stats.currentStreak} Days
                      </span>
                    </div>

                    <div className="p-3 bg-white/[0.01] border border-theme-subtle rounded-2xl">
                      <span className="text-[7px] text-theme-muted uppercase font-black tracking-wider block mb-1">
                        Weekly Footprint
                      </span>
                      <span className="text-base font-black text-teal-400 flex items-center gap-1">
                        <Zap className="w-3.5 h-3.5 text-teal-400" />
                        {stats.totalCarbon.toFixed(1)} kg
                      </span>
                    </div>

                    <div className="p-3 bg-white/[0.01] border border-theme-subtle rounded-2xl">
                      <span className="text-[7px] text-theme-muted uppercase font-black tracking-wider block mb-1">
                        Achievements
                      </span>
                      <span className="text-base font-black text-yellow-455 flex items-center gap-1">
                        <Trophy className="w-3.5 h-3.5 text-amber-500" />
                        {stats.achievementsEarned}
                      </span>
                    </div>

                    <div className="p-3 bg-white/[0.01] border border-theme-subtle rounded-2xl">
                      <span className="text-[7px] text-theme-muted uppercase font-black tracking-wider block mb-1">
                        Redeemed Rewards
                      </span>
                      <span className="text-base font-black text-indigo-400 flex items-center gap-1">
                        <ShoppingBag className="w-3.5 h-3.5 text-indigo-450" />
                        {stats.rewardsRedeemed}
                      </span>
                    </div>

                    <div className="p-3 bg-white/[0.01] border border-theme-subtle rounded-2xl">
                      <span className="text-[7px] text-theme-muted uppercase font-black tracking-wider block mb-1">
                        Weekly Trend
                      </span>
                      <span className="text-xs font-black text-theme-brand flex items-center mt-1 select-none">
                        📈 {stats.weeklyTrend}
                      </span>
                    </div>
                  </div>
                </Card>
              </div>

              {/* Right Column Form */}
              <div className="xl:col-span-2">
                <Card hover={false} className="p-6 sm:p-8 relative overflow-hidden">
                  <div className="absolute top-0 right-0 w-32 h-32 bg-emerald-500/5 blur-[50px] pointer-events-none rounded-full" />
                  
                  <h3 className="text-sm font-black uppercase tracking-wider text-theme-primary mb-6 flex items-center gap-2 font-display">
                    <User className="w-4 h-4 text-theme-brand" />
                    Profile Configurations
                  </h3>

                  <form onSubmit={handleSaveProfile} className="space-y-6">
                    <Textarea 
                      label="Bio / Description"
                      value={bio}
                      onChange={(e) => setBio(e.target.value)}
                      placeholder="Tell others about your sustainability journey..."
                      rows={3}
                    />

                    {/* Personal Details */}
                    <div className="border-t border-white/5 pt-6">
                      <h4 className="text-[10px] font-black uppercase tracking-widest text-theme-brand mb-4">
                        Personal Info
                      </h4>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                        <Input 
                          label="Full Name"
                          value={fullName}
                          onChange={(e) => setFullName(e.target.value)}
                          placeholder="John Doe"
                          leftIcon={<User className="w-4 h-4" />}
                        />
                        <Input 
                          label="Phone Number"
                          value={phoneNumber}
                          onChange={(e) => setPhoneNumber(e.target.value)}
                          placeholder="+1 (555) 000-0000"
                          leftIcon={<Phone className="w-4 h-4" />}
                        />
                        <Input 
                          label="Date of Birth"
                          type="date"
                          value={dob}
                          onChange={(e) => setDob(e.target.value)}
                          leftIcon={<Calendar className="w-4 h-4" />}
                        />
                        <Select 
                          label="Gender"
                          value={gender}
                          onChange={(e) => setGender(e.target.value)}
                          options={[
                            { value: "", label: "Select Gender" },
                            { value: "Male", label: "Male" },
                            { value: "Female", label: "Female" },
                            { value: "Non-binary", label: "Non-binary" },
                            { value: "Prefer not to say", label: "Prefer not to say" }
                          ]}
                        />
                      </div>
                    </div>

                    {/* Geography & Academic Details */}
                    <div className="border-t border-white/5 pt-6">
                      <h4 className="text-[10px] font-black uppercase tracking-widest text-theme-brand mb-4">
                        Geography & Academic Details
                      </h4>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                        <Input 
                          label="Location / City"
                          value={location}
                          onChange={(e) => setLocation(e.target.value)}
                          placeholder="New York"
                          leftIcon={<MapPin className="w-4 h-4" />}
                        />
                        <Input 
                          label="Country"
                          value={country}
                          onChange={(e) => setCountry(e.target.value)}
                          placeholder="United States"
                          leftIcon={<Globe className="w-4 h-4" />}
                        />
                        <Input 
                          label="University / College"
                          value={college}
                          onChange={(e) => setCollege(e.target.value)}
                          placeholder="Harvard University"
                          leftIcon={<GraduationCap className="w-4 h-4" />}
                        />
                        <Input 
                          label="Department / Major"
                          value={department}
                          onChange={(e) => setDepartment(e.target.value)}
                          placeholder="Environmental Sciences"
                          leftIcon={<GraduationCap className="w-4 h-4" />}
                        />
                      </div>
                    </div>

                    {/* Read-Only Account Details */}
                    <div className="border-t border-white/5 pt-6 select-none">
                      <h4 className="text-[10px] font-black uppercase tracking-widest text-theme-muted mb-4 flex items-center gap-1.5">
                        <Shield className="w-3.5 h-3.5" /> Read-Only Details
                      </h4>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-[11px] font-bold text-theme-muted">
                        <div className="flex justify-between items-center bg-white/[0.01] border border-theme-subtle p-3 rounded-2xl">
                          <span className="flex items-center gap-1"><Mail className="w-3.5 h-3.5" /> EMAIL</span>
                          <span className="text-theme-secondary select-all">{profile?.email || "john.doe@example.com"}</span>
                        </div>

                        <div className="flex justify-between items-center bg-white/[0.01] border border-theme-subtle p-3 rounded-2xl">
                          <span className="flex items-center gap-1"><Shield className="w-3.5 h-3.5" /> USER ID</span>
                          <span className="text-theme-secondary font-mono select-all">USR-{profile?.user_id ? String(profile.user_id).padStart(4, "0") : "0001"}</span>
                        </div>

                        <div className="flex justify-between items-center bg-white/[0.01] border border-theme-subtle p-3 rounded-2xl">
                          <span className="flex items-center gap-1"><Calendar className="w-3.5 h-3.5" /> JOINED</span>
                          <span className="text-theme-secondary">{memberSince}</span>
                        </div>

                        <div className="flex justify-between items-center bg-white/[0.01] border border-theme-subtle p-3 rounded-2xl">
                          <span className="flex items-center gap-1"><Shield className="w-3.5 h-3.5" /> AUTH PROVIDER</span>
                          <Badge variant="brand" size="xs">
                            {profile?.auth_provider || "credentials"}
                          </Badge>
                        </div>
                      </div>
                    </div>

                    <Button
                      type="submit"
                      disabled={saving}
                      size="lg"
                      className="w-full"
                      glow
                    >
                      {saving ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        <>
                          <Save className="w-4 h-4" />
                          <span>Commit Profile Updates</span>
                        </>
                      )}
                    </Button>
                  </form>
                </Card>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
