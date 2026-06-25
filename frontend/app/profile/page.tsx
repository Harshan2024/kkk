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
    const activeToken = localStorage.getItem("carbontracker_token");
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
      // 1. Fetch Profile info
      const res = await api.getProfile();
      // Handle both wrapped and unwrapped response structure
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

      // 2. Fetch Gamification profile
      try {
        const gProfile = await api.getGamificationProfile();
        const summary = await api.getDashboardSummary();
        const analytics = await api.getAnalytics();
        const achievementsList = await api.getAchievements();

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
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isAuthenticated && token) {
      loadProfileData();
    }
  }, [isAuthenticated, token]);

  // Handle profile update submit
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
      // Handle both wrapped and unwrapped response structure
      const p = (res && (res as any).data) ? (res as any).data : res;
      if (p) {
        setSaveSuccess("Profile updated successfully!");
        setProfile(p);
        // Sync local storage user
        localStorage.setItem("carbontracker_user", JSON.stringify(p));
      } else {
        setError("Failed to save profile changes.");
      }
    } catch (err: any) {
      setError(err?.message || "An error occurred while saving profile.");
    } finally {
      setSaving(false);
    }
  };

  // Handle avatar image file select
  const handleAvatarChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0) return;
    const file = e.target.files[0];

    // File validation
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
        localStorage.setItem("carbontracker_user", JSON.stringify(p));
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

  // UI calculations
  const memberSince = profile?.created_at
    ? new Date(profile.created_at).toLocaleDateString("en-US", { year: "numeric", month: "long" })
    : "June 2026";

  const initials = profile?.full_name
    ? profile.full_name.split(" ").map((n: string) => n[0]).join("").toUpperCase().substring(0, 2)
    : profile?.username?.substring(0, 2).toUpperCase() || "CT";

  // XP Progress Calculation
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
    <div className="min-h-screen bg-[#080d0a] text-stone-100 font-sans relative overflow-x-hidden transition-colors duration-300">
      {/* Background Matrix/Glows */}
      <div className="absolute inset-0 dot-matrix pointer-events-none z-0" />
      <div className="absolute top-[-10%] left-[-5%] w-[45%] aspect-square rounded-full bg-emerald-600/5 blur-[120px] pointer-events-none z-0" />
      <div className="absolute bottom-[-10%] right-[-5%] w-[45%] aspect-square rounded-full bg-emerald-700/5 blur-[120px] pointer-events-none z-0" />

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
              <button 
                onClick={() => router.push("/")}
                className="p-2.5 rounded-xl bg-white/[0.02] hover:bg-white/[0.04] border border-white/5 text-stone-400 hover:text-white transition-all cursor-pointer"
              >
                <ArrowLeft className="w-4 h-4" />
              </button>
              <div>
                <h1 className="text-xl sm:text-2xl font-black tracking-tight text-white flex items-center gap-1.5 font-outfit">
                  User <span className="text-emerald-450">Console</span>
                </h1>
                <p className="text-[10px] font-bold text-stone-550 uppercase tracking-widest leading-none mt-1">
                  Manage credentials, profile tags, and stats
                </p>
              </div>
            </div>
          </div>

          {/* Error & Success Message banners */}
          {error && (
            <div className="p-4 rounded-2xl border border-rose-500/30 bg-rose-500/10 text-rose-400 text-xs font-bold animate-in fade-in select-none">
              {error}
            </div>
          )}
          {saveSuccess && (
            <div className="p-4 rounded-2xl border border-emerald-500/30 bg-emerald-500/10 text-emerald-450 text-xs font-bold animate-in fade-in select-none">
              {saveSuccess}
            </div>
          )}

          {loading ? (
            /* Skeleton Loading State */
            <div className="grid grid-cols-1 xl:grid-cols-3 gap-6 animate-pulse select-none">
              <div className="xl:col-span-1 space-y-6">
                <div className="glass-card rounded-3xl h-[360px] bg-white/5 border border-white/5" />
                <div className="glass-card rounded-3xl h-[280px] bg-white/5 border border-white/5" />
              </div>
              <div className="xl:col-span-2 space-y-6">
                <div className="glass-card rounded-3xl h-[660px] bg-white/5 border border-white/5" />
              </div>
            </div>
          ) : (
            <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
              {/* Left Column — Avatar Card + Carbon ID Card */}
              <div className="xl:col-span-1 space-y-6 flex flex-col">
                {/* 1. Avatar Dashboard Card */}
                <div className="glass-card rounded-3xl p-6 border border-white/5 bg-[#0a120f]/80 backdrop-blur-xl flex flex-col items-center justify-center text-center shadow-xl relative overflow-hidden select-none">
                  {/* Decorative glowing green blob */}
                  <div className="absolute top-0 right-0 w-24 h-24 bg-emerald-500/5 blur-[40px] pointer-events-none rounded-full" />
                  
                  {/* Avatar Upload Container */}
                  <div className="relative group mb-4">
                    <div className="w-24 h-24 rounded-full overflow-hidden border-2 border-emerald-500/35 bg-stone-900 shadow-lg flex items-center justify-center text-2xl font-black text-white relative">
                      {profile?.profile_picture ? (
                        /* Standard absolute URL server mapping fallback */
                        <img 
                          src={profile.profile_picture.startsWith("http") ? profile.profile_picture : `http://localhost:8001${profile.profile_picture}`} 
                          alt="Profile Avatar" 
                          className="w-full h-full object-cover" 
                        />
                      ) : (
                        <span>{initials}</span>
                      )}

                      {/* Upload Loading Overlay */}
                      {uploadingAvatar && (
                        <div className="absolute inset-0 bg-black/60 flex items-center justify-center">
                          <Loader2 className="w-6 h-6 text-emerald-450 animate-spin" />
                        </div>
                      )}
                    </div>
                    
                    {/* Camera Trigger */}
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

                  <h3 className="text-base font-black text-white">{profile?.full_name || profile?.username}</h3>
                  <p className="text-[10px] font-extrabold uppercase tracking-widest text-emerald-450 mt-1">
                    Level {profile?.level || 1} • {getRank(profile?.carbon_score || 96.0)}
                  </p>
                  <p className="text-[10px] text-stone-500 mt-2 font-bold leading-relaxed max-w-xs line-clamp-3">
                    {profile?.bio || "No biography provided yet. Write something about your sustainability journey!"}
                  </p>

                  {avatarError && (
                    <span className="text-[9px] font-bold text-rose-400 mt-3 block">{avatarError}</span>
                  )}
                </div>

                {/* 2. Premium Carbon Identity Card */}
                <div className="glass-card rounded-3xl p-6 border border-emerald-950/20 bg-gradient-to-br from-[#0c1a13] via-[#09100c] to-[#040805] shadow-2xl relative overflow-hidden flex flex-col justify-between aspect-[1.58/1] select-none text-stone-100 group hover:border-emerald-500/20 transition-all duration-300">
                  {/* Holographic Watermark Glows */}
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

                  {/* Body details */}
                  <div className="my-6">
                    <span className="text-[8px] text-stone-500 uppercase font-black tracking-wider block mb-1">
                      Identity Holder
                    </span>
                    <h2 className="text-sm sm:text-base font-black tracking-tight text-white truncate">
                      {profile?.full_name || profile?.username || "Guest Sustainability Agent"}
                    </h2>
                    
                    {/* XP Progress Bar */}
                    <div className="mt-3.5 space-y-1">
                      <div className="flex justify-between text-[8px] font-mono text-stone-400">
                        <span>XP PROGRESS</span>
                        <span>{profile?.xp || 0} / {nextLevelXp} XP ({xpPct}%)</span>
                      </div>
                      <div className="w-full h-1.5 rounded-full bg-white/5 overflow-hidden">
                        <div 
                          className="h-full rounded-full bg-gradient-to-r from-emerald-500 to-teal-400" 
                          style={{ width: `${xpPct}%` }}
                        ></div>
                      </div>
                    </div>
                  </div>

                  {/* Footer data row */}
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

                {/* 3. Statistics Panel */}
                <div className="glass-card rounded-3xl p-5 border border-white/5 bg-[#0a120f]/60 backdrop-blur-xl space-y-4 shadow-xl select-none flex-1">
                  <h3 className="text-xs font-black uppercase tracking-widest text-stone-400 flex items-center gap-1.5">
                    <Sparkles className="w-3.5 h-3.5 text-emerald-450" />
                    Telemetry Summary
                  </h3>

                  <div className="grid grid-cols-2 gap-3.5">
                    <div className="p-3 bg-white/[0.01] border border-white/5 rounded-2xl">
                      <span className="text-[7px] text-stone-500 uppercase font-black tracking-wider block mb-1">
                        Total Activities
                      </span>
                      <span className="text-base font-black text-white flex items-center gap-1">
                        <Leaf className="w-3.5 h-3.5 text-emerald-500" />
                        {stats.totalActivities}
                      </span>
                    </div>

                    <div className="p-3 bg-white/[0.01] border border-white/5 rounded-2xl">
                      <span className="text-[7px] text-stone-500 uppercase font-black tracking-wider block mb-1">
                        Current Streak
                      </span>
                      <span className="text-base font-black text-orange-450 flex items-center gap-1">
                        <Flame className="w-3.5 h-3.5 text-orange-500 fill-orange-500" />
                        {stats.currentStreak} Days
                      </span>
                    </div>

                    <div className="p-3 bg-white/[0.01] border border-white/5 rounded-2xl">
                      <span className="text-[7px] text-stone-500 uppercase font-black tracking-wider block mb-1">
                        Weekly Footprint
                      </span>
                      <span className="text-base font-black text-teal-400 flex items-center gap-1">
                        <Zap className="w-3.5 h-3.5 text-teal-400" />
                        {stats.totalCarbon.toFixed(1)} kg
                      </span>
                    </div>

                    <div className="p-3 bg-white/[0.01] border border-white/5 rounded-2xl">
                      <span className="text-[7px] text-stone-500 uppercase font-black tracking-wider block mb-1">
                        Achievements
                      </span>
                      <span className="text-base font-black text-yellow-450 flex items-center gap-1">
                        <Trophy className="w-3.5 h-3.5 text-amber-500" />
                        {stats.achievementsEarned}
                      </span>
                    </div>

                    <div className="p-3 bg-white/[0.01] border border-white/5 rounded-2xl">
                      <span className="text-[7px] text-stone-500 uppercase font-black tracking-wider block mb-1">
                        Redeemed Rewards
                      </span>
                      <span className="text-base font-black text-indigo-400 flex items-center gap-1">
                        <ShoppingBag className="w-3.5 h-3.5 text-indigo-400" />
                        {stats.rewardsRedeemed}
                      </span>
                    </div>

                    <div className="p-3 bg-white/[0.01] border border-white/5 rounded-2xl">
                      <span className="text-[7px] text-stone-500 uppercase font-black tracking-wider block mb-1">
                        Weekly Trend
                      </span>
                      <span className="text-xs font-black text-emerald-450 flex items-center mt-1 select-none">
                        📈 {stats.weeklyTrend}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Right Column — Editable Fields Form */}
              <div className="xl:col-span-2">
                <div className="glass-card rounded-3xl p-6 sm:p-8 border border-white/5 bg-[#0a120f]/80 backdrop-blur-xl shadow-2xl relative overflow-hidden">
                  <div className="absolute top-0 right-0 w-32 h-32 bg-emerald-500/5 blur-[50px] pointer-events-none rounded-full" />
                  
                  <h3 className="text-sm font-black uppercase tracking-wider text-white mb-6 flex items-center gap-2">
                    <User className="w-4 h-4 text-emerald-450" />
                    Profile Details & Configurations
                  </h3>

                  <form onSubmit={handleSaveProfile} className="space-y-6">
                    {/* General Bio field */}
                    <div className="space-y-2">
                      <label className="text-[10px] font-black uppercase text-stone-400 tracking-wider">
                        Bio / Description
                      </label>
                      <textarea
                        value={bio}
                        onChange={(e) => setBio(e.target.value)}
                        placeholder="Tell others about yourself..."
                        rows={3}
                        className="w-full px-4 py-3 bg-[#060a08] border border-white/5 focus:border-emerald-500/30 rounded-2xl text-xs text-white placeholder-stone-600 focus:outline-none transition-all resize-none"
                      />
                    </div>

                    {/* Personal Details Section */}
                    <div className="border-t border-white/5 pt-6">
                      <h4 className="text-[10px] font-black uppercase tracking-widest text-emerald-400 mb-4">
                        Personal Info
                      </h4>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                        <div className="space-y-2">
                          <label className="text-[10px] font-black uppercase text-stone-400 tracking-wider flex items-center gap-1.5">
                            <User className="w-3.5 h-3.5 text-stone-500" /> Full Name
                          </label>
                          <input
                            type="text"
                            value={fullName}
                            onChange={(e) => setFullName(e.target.value)}
                            placeholder="John Doe"
                            className="w-full px-4 py-3 bg-[#060a08] border border-white/5 focus:border-emerald-500/30 rounded-2xl text-xs text-white placeholder-stone-600 focus:outline-none"
                          />
                        </div>

                        <div className="space-y-2">
                          <label className="text-[10px] font-black uppercase text-stone-400 tracking-wider flex items-center gap-1.5">
                            <Phone className="w-3.5 h-3.5 text-stone-500" /> Phone Number
                          </label>
                          <input
                            type="tel"
                            value={phoneNumber}
                            onChange={(e) => setPhoneNumber(e.target.value)}
                            placeholder="+1 (555) 000-0000"
                            className="w-full px-4 py-3 bg-[#060a08] border border-white/5 focus:border-emerald-500/30 rounded-2xl text-xs text-white placeholder-stone-600 focus:outline-none"
                          />
                        </div>

                        <div className="space-y-2">
                          <label className="text-[10px] font-black uppercase text-stone-400 tracking-wider flex items-center gap-1.5">
                            <Calendar className="w-3.5 h-3.5 text-stone-500" /> Date of Birth
                          </label>
                          <input
                            type="date"
                            value={dob}
                            onChange={(e) => setDob(e.target.value)}
                            className="w-full px-4 py-3 bg-[#060a08] border border-white/5 focus:border-emerald-500/30 rounded-2xl text-xs text-white placeholder-stone-600 focus:outline-none focus:ring-0 appearance-none"
                          />
                        </div>

                        <div className="space-y-2">
                          <label className="text-[10px] font-black uppercase text-stone-400 tracking-wider flex items-center gap-1.5">
                            <User className="w-3.5 h-3.5 text-stone-500" /> Gender
                          </label>
                          <div className="relative">
                            <select
                              value={gender}
                              onChange={(e) => setGender(e.target.value)}
                              className="w-full px-4 py-3 bg-[#060a08] border border-white/5 focus:border-emerald-500/30 rounded-2xl text-xs text-white focus:outline-none appearance-none"
                            >
                              <option value="" className="bg-[#0b120f] text-stone-500">Select Gender</option>
                              <option value="Male" className="bg-[#0b120f] text-white">Male</option>
                              <option value="Female" className="bg-[#0b120f] text-white">Female</option>
                              <option value="Non-binary" className="bg-[#0b120f] text-white">Non-binary</option>
                              <option value="Prefer not to say" className="bg-[#0b120f] text-white">Prefer not to say</option>
                            </select>
                            <span className="absolute right-4 top-1/2 -translate-y-1/2 text-stone-500 pointer-events-none text-[8px]">▼</span>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Regional details section */}
                    <div className="border-t border-white/5 pt-6">
                      <h4 className="text-[10px] font-black uppercase tracking-widest text-emerald-400 mb-4">
                        Geography & Academic Details
                      </h4>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                        <div className="space-y-2">
                          <label className="text-[10px] font-black uppercase text-stone-400 tracking-wider flex items-center gap-1.5">
                            <MapPin className="w-3.5 h-3.5 text-stone-500" /> Location / City
                          </label>
                          <input
                            type="text"
                            value={location}
                            onChange={(e) => setLocation(e.target.value)}
                            placeholder="New York"
                            className="w-full px-4 py-3 bg-[#060a08] border border-white/5 focus:border-emerald-500/30 rounded-2xl text-xs text-white placeholder-stone-600 focus:outline-none"
                          />
                        </div>

                        <div className="space-y-2">
                          <label className="text-[10px] font-black uppercase text-stone-400 tracking-wider flex items-center gap-1.5">
                            <Globe className="w-3.5 h-3.5 text-stone-500" /> Country
                          </label>
                          <input
                            type="text"
                            value={country}
                            onChange={(e) => setCountry(e.target.value)}
                            placeholder="United States"
                            className="w-full px-4 py-3 bg-[#060a08] border border-white/5 focus:border-emerald-500/30 rounded-2xl text-xs text-white placeholder-stone-600 focus:outline-none"
                          />
                        </div>

                        <div className="space-y-2">
                          <label className="text-[10px] font-black uppercase text-stone-400 tracking-wider flex items-center gap-1.5">
                            <GraduationCap className="w-3.5 h-3.5 text-stone-500" /> University / College
                          </label>
                          <input
                            type="text"
                            value={college}
                            onChange={(e) => setCollege(e.target.value)}
                            placeholder="Harvard University"
                            className="w-full px-4 py-3 bg-[#060a08] border border-white/5 focus:border-emerald-500/30 rounded-2xl text-xs text-white placeholder-stone-600 focus:outline-none"
                          />
                        </div>

                        <div className="space-y-2">
                          <label className="text-[10px] font-black uppercase text-stone-400 tracking-wider flex items-center gap-1.5">
                            <GraduationCap className="w-3.5 h-3.5 text-stone-500" /> Department / Major
                          </label>
                          <input
                            type="text"
                            value={department}
                            onChange={(e) => setDepartment(e.target.value)}
                            placeholder="Environmental Engineering"
                            className="w-full px-4 py-3 bg-[#060a08] border border-white/5 focus:border-emerald-500/30 rounded-2xl text-xs text-white placeholder-stone-600 focus:outline-none"
                          />
                        </div>
                      </div>
                    </div>

                    {/* Metadata (Read Only) Section */}
                    <div className="border-t border-white/5 pt-6 select-none">
                      <h4 className="text-[10px] font-black uppercase tracking-widest text-stone-500 mb-4 flex items-center gap-1.5">
                        <Shield className="w-3.5 h-3.5" /> Read-Only Account Details
                      </h4>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-[11px] font-bold text-stone-400">
                        <div className="flex justify-between items-center bg-white/[0.01] border border-white/5 p-3 rounded-2xl">
                          <span className="text-stone-550 flex items-center gap-1"><Mail className="w-3.5 h-3.5" /> EMAIL</span>
                          <span className="text-stone-300 select-all">{profile?.email || "john.doe@example.com"}</span>
                        </div>

                        <div className="flex justify-between items-center bg-white/[0.01] border border-white/5 p-3 rounded-2xl">
                          <span className="text-stone-550 flex items-center gap-1"><Shield className="w-3.5 h-3.5" /> USER ID</span>
                          <span className="text-stone-300 font-mono select-all">USR-{profile?.user_id ? String(profile.user_id).padStart(4, "0") : "0001"}</span>
                        </div>

                        <div className="flex justify-between items-center bg-white/[0.01] border border-white/5 p-3 rounded-2xl">
                          <span className="text-stone-550 flex items-center gap-1"><Calendar className="w-3.5 h-3.5" /> JOINED</span>
                          <span className="text-stone-300">{memberSince}</span>
                        </div>

                        <div className="flex justify-between items-center bg-white/[0.01] border border-white/5 p-3 rounded-2xl">
                          <span className="text-stone-550 flex items-center gap-1"><Shield className="w-3.5 h-3.5" /> AUTH PROVIDER</span>
                          <span className="text-emerald-450 uppercase text-[9px] font-black bg-emerald-950/20 border border-emerald-500/15 px-2 py-0.5 rounded-full tracking-wider">
                            {profile?.auth_provider || "credentials"}
                          </span>
                        </div>
                      </div>
                    </div>

                    <button
                      type="submit"
                      disabled={saving}
                      className="mt-4 w-full py-3.5 bg-gradient-to-r from-emerald-600 to-emerald-500 hover:from-emerald-500 hover:to-emerald-450 text-white font-extrabold text-xs uppercase tracking-wider rounded-2xl transition-all shadow-lg shadow-emerald-500/10 active:scale-95 flex items-center justify-center gap-2 cursor-pointer"
                    >
                      {saving ? (
                        <Loader2 className="w-4 h-4 animate-spin text-white" />
                      ) : (
                        <>
                          <Save className="w-4 h-4" />
                          <span>Commit Profile Updates</span>
                        </>
                      )}
                    </button>
                  </form>
                </div>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
