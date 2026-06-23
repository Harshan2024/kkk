"use client";

import React, { useState, useEffect, useRef } from "react";
import { 
  Brain, Sparkles, Send, Award, Calendar, BarChart3, 
  TrendingDown, Shield, User, ChevronRight, Zap, Utensils, 
  Car, Trash2, CheckCircle2, MessageSquare, AlertCircle
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import api, { HabitAnalysis, CoachWeeklyReport, CoachMonthlyReport } from "../services/api";

function EmptyState({ message }: { message: string }) {
  return (
    <div className="glass-card rounded-3xl p-8 border border-white/5 bg-white/[0.01] text-center flex flex-col items-center justify-center">
      <AlertCircle className="w-10 h-10 text-stone-500 mb-3 animate-pulse" />
      <p className="text-xs font-bold text-stone-400">{message}</p>
    </div>
  );
}

export default function CoachDashboard() {
  const [activeTab, setActiveTab] = useState<"habits" | "reports" | "plan">("habits");
  
  // Data States
  const [analysis, setAnalysis] = useState<HabitAnalysis | null>(null);
  const [weeklyReport, setWeeklyReport] = useState<CoachWeeklyReport | null>(null);
  const [monthlyReport, setMonthlyReport] = useState<CoachMonthlyReport | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Chat States
  const [messages, setMessages] = useState<{ id: number; role: "user" | "assistant"; content: string }[]>([
    {
      id: 1,
      role: "assistant",
      content: "Hello! I am your AI Sustainability Coach. I analyze your logged activities and provide daily insights to help you reduce your carbon footprint. Ask me about your habits or get a report!"
    }
  ]);
  const [inputValue, setInputValue] = useState("");
  const [isChatLoading, setIsChatLoading] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

  const fetchCoachData = async () => {
    setIsLoading(true);
    try {
      const aData = await api.getCoachAnalysis();
      setAnalysis(aData);
      
      const wData = await api.getWeeklyCoachReport();
      setWeeklyReport(wData);
      
      const mData = await api.getMonthlyCoachReport();
      setMonthlyReport(mData);
    } catch (err) {
      console.error("Failed to load AI coach payload", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchCoachData();
  }, []);

  useEffect(() => {
    if (chatEndRef.current) {
      chatEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, isChatLoading]);

  const handleSendChat = async (text: string) => {
    if (!text.trim()) return;
    
    // Add user message
    const userMsg = { id: Date.now(), role: "user" as const, content: text };
    setMessages(prev => [...prev, userMsg]);
    setIsChatLoading(true);
    setInputValue("");

    try {
      const result = await api.postCoachChat(text);
      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        role: "assistant" as const,
        content: result.response
      }]);
    } catch (err) {
      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        role: "assistant" as const,
        content: "Sorry, I had trouble processing your query. Please make sure the backend is running and try again."
      }]);
    } finally {
      setIsChatLoading(false);
    }
  };

  const handleQuickQuery = (query: string) => {
    handleSendChat(query);
  };

  const getFoodIcon = (profile: string) => {
    return <Utensils className="w-5 h-5 text-emerald-400" />;
  };

  const getTransportIcon = (profile: string) => {
    return <Car className="w-5 h-5 text-sky-400" />;
  };

  const getEnergyIcon = (finding: string) => {
    return <Zap className="w-5 h-5 text-amber-400" />;
  };

  const getWasteIcon = (profile: string) => {
    return <Trash2 className="w-5 h-5 text-rose-400" />;
  };

  const formatHeader = (title: string) => {
    return title.replace(/_/g, " ").toUpperCase();
  };

  const safeAnalysis = {
    energy: analysis?.energy ?? {} as any,
    food: analysis?.food ?? {} as any,
    transport: analysis?.transport ?? {} as any,
    waste: analysis?.waste ?? {} as any
  };

  if (isLoading) {
    return (
      <div className="space-y-6 select-none">
        <div className="glass-card rounded-3xl p-6 border border-emerald-500/10 bg-gradient-to-br from-emerald-950/5 via-[#080d0a]/40 to-[#080d0a]/10 relative overflow-hidden flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div className="absolute top-0 right-0 w-32 h-32 bg-emerald-500/5 blur-[55px] pointer-events-none rounded-full" />
          <div className="flex items-center space-x-3.5">
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-emerald-500/20 to-teal-700/20 border border-emerald-500/30 flex items-center justify-center shadow-lg shadow-emerald-500/5">
              <Brain className="w-6 h-6 text-emerald-400" />
            </div>
            <div>
              <h1 className="text-lg font-black tracking-tight text-white flex items-center gap-1.5">
                AI Sustainability Coach <span className="text-[10px] font-black px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 uppercase tracking-widest">Expert System</span>
              </h1>
              <p className="text-[11px] font-bold text-stone-500 mt-0.5">
                Analyzes history, patterns, and categories to guide carbon-conscious habits.
              </p>
            </div>
          </div>
        </div>
        <div className="glass-card rounded-3xl p-6 h-[400px] animate-pulse bg-white/5 border border-white/5" />
      </div>
    );
  }

  if (!analysis) {
    return <EmptyState message="No sustainability data available yet." />;
  }

  return (
    <div className="space-y-6 select-none">
      {/* Header Panel */}
      <div className="glass-card rounded-3xl p-6 border border-emerald-500/10 bg-gradient-to-br from-emerald-950/5 via-[#080d0a]/40 to-[#080d0a]/10 relative overflow-hidden flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div className="absolute top-0 right-0 w-32 h-32 bg-emerald-500/5 blur-[55px] pointer-events-none rounded-full" />
        <div className="flex items-center space-x-3.5">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-emerald-500/20 to-teal-700/20 border border-emerald-500/30 flex items-center justify-center shadow-lg shadow-emerald-500/5">
            <Brain className="w-6 h-6 text-emerald-400" />
          </div>
          <div>
            <h1 className="text-lg font-black tracking-tight text-white flex items-center gap-1.5">
              AI Sustainability Coach <span className="text-[10px] font-black px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 uppercase tracking-widest">Expert System</span>
            </h1>
            <p className="text-[11px] font-bold text-stone-500 mt-0.5">
              Analyzes history, patterns, and categories to guide carbon-conscious habits.
            </p>
          </div>
        </div>
        
        {/* Navigation Tabs */}
        <div className="flex bg-stone-950 p-1 border border-white/5 rounded-2xl">
          {(["habits", "reports", "plan"] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-4 py-2 rounded-xl text-xs font-black uppercase tracking-wider transition-all cursor-pointer ${
                activeTab === tab 
                  ? "bg-emerald-950/40 text-emerald-400 border border-emerald-500/20" 
                  : "text-stone-400 hover:text-stone-200"
              }`}
            >
              {tab}
            </button>
          ))}
        </div>
      </div>

      {/* Main Grid Content */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        
        {/* Left Side Tab Views (8 Columns) */}
        <div className="lg:col-span-8 space-y-6">
          
          {isLoading ? (
            <div className="glass-card rounded-3xl p-6 h-[400px] animate-pulse bg-white/5 border border-white/5" />
          ) : (
            <AnimatePresence mode="wait">
              {activeTab === "habits" && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  className="space-y-6"
                >
                  {/* Habit Profiles (Energy, Food, Transport, Waste) */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    
                    {/* Energy card */}
                    <div className="glass-card rounded-2xl p-5 border border-white/5 bg-white/[0.01] flex flex-col justify-between">
                      <div>
                        <div className="flex items-center gap-2.5 mb-3">
                          {getEnergyIcon(analysis?.energy?.finding ?? "")}
                          <h3 className="text-xs font-black uppercase tracking-wider text-stone-300">Energy Habits</h3>
                        </div>
                        <p className="text-xs font-bold text-stone-400 leading-relaxed">
                          {analysis?.energy?.finding ?? "No energy data available"}
                        </p>
                      </div>
                      <div className="border-t border-white/5 pt-3.5 mt-4 text-[10px] font-black uppercase text-stone-500 tracking-wider">
                        AC Usage: <span className="text-amber-400 font-black">{(safeAnalysis.energy?.ac_hours ?? 0).toFixed(1)} hrs/day</span>
                      </div>
                    </div>

                    {/* Food card */}
                    <div className="glass-card rounded-2xl p-5 border border-white/5 bg-white/[0.01] flex flex-col justify-between">
                      <div>
                        <div className="flex items-center gap-2.5 mb-3">
                          {getFoodIcon(safeAnalysis.food?.food_profile ?? "")}
                          <h3 className="text-xs font-black uppercase tracking-wider text-stone-300">Food Habits</h3>
                        </div>
                        <p className="text-xs font-bold text-stone-400 leading-relaxed">
                          {analysis?.food?.finding ?? "No food data available"}
                        </p>
                      </div>
                      <div className="border-t border-white/5 pt-3.5 mt-4 grid grid-cols-2 text-[10px] font-black uppercase text-stone-500 tracking-wider gap-2">
                        <div>Veg Ratio: <span className="text-emerald-450">{Math.round((safeAnalysis.food?.veg_ratio ?? 0) * 100)}%</span></div>
                        <div>Animal Ratio: <span className="text-rose-450">{Math.round((safeAnalysis.food?.animal_ratio ?? 0) * 100)}%</span></div>
                      </div>
                    </div>

                    {/* Transport card */}
                    <div className="glass-card rounded-2xl p-5 border border-white/5 bg-white/[0.01] flex flex-col justify-between">
                      <div>
                        <div className="flex items-center gap-2.5 mb-3">
                          {getTransportIcon(safeAnalysis.transport?.transport_profile ?? "")}
                          <h3 className="text-xs font-black uppercase tracking-wider text-stone-300">Transport Habits</h3>
                        </div>
                        <p className="text-xs font-bold text-stone-400 leading-relaxed">
                          {analysis?.transport?.finding ?? "No transport data available"}
                        </p>
                      </div>
                      <div className="border-t border-white/5 pt-3.5 mt-4 text-[10px] font-black uppercase text-stone-500 tracking-wider">
                        Public Transport Ratio: <span className="text-sky-400 font-black">{Math.round((safeAnalysis.transport?.public_transport_ratio ?? 0) * 100)}%</span>
                      </div>
                    </div>

                    {/* Waste card */}
                    <div className="glass-card rounded-2xl p-5 border border-white/5 bg-white/[0.01] flex flex-col justify-between">
                      <div>
                        <div className="flex items-center gap-2.5 mb-3">
                          {getWasteIcon(safeAnalysis.waste?.waste_profile ?? "")}
                          <h3 className="text-xs font-black uppercase tracking-wider text-stone-300">Waste Habits</h3>
                        </div>
                        <p className="text-xs font-bold text-stone-400 leading-relaxed">
                          {analysis?.waste?.finding ?? "No waste data available"}
                        </p>
                      </div>
                      <div className="border-t border-white/5 pt-3.5 mt-4 text-[10px] font-black uppercase text-stone-500 tracking-wider">
                        Recycling events: <span className="text-rose-400 font-black">{safeAnalysis.waste?.recycling_frequency ?? 0} times</span>
                      </div>
                    </div>

                  </div>

                  {/* Detected Patterns */}
                  {Array.isArray(analysis?.patterns) && analysis.patterns.length > 0 && (
                    <div className="glass-card rounded-3xl p-5 border border-white/5 bg-white/[0.01]">
                      <h3 className="text-xs font-black uppercase tracking-widest text-stone-450 mb-3.5">
                        Detected Pattern Signals
                      </h3>
                      <div className="space-y-2">
                        {(analysis.patterns ?? []).map((pat, idx) => (
                          <div key={idx} className="flex items-center justify-between p-3 border border-white/5 bg-stone-900/40 rounded-xl">
                            <span className="text-xs font-bold text-white uppercase tracking-wider">{pat.pattern.replace(/_/g, " ")}</span>
                            <span className="text-[10px] font-black uppercase px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                              Confidence {Math.round(pat.confidence * 100)}%
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </motion.div>
              )}

              {activeTab === "reports" && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  className="space-y-6"
                >
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                    {/* Weekly Report Card */}
                    <div className="glass-card rounded-3xl p-5 border border-white/5 bg-white/[0.01] flex flex-col justify-between">
                      <div>
                        <span className="text-[9px] font-black uppercase tracking-widest text-stone-550 flex items-center gap-1.5 mb-3">
                          <Calendar className="w-3.5 h-3.5 text-stone-400" />
                          Weekly Coach Report
                        </span>
                        
                        <div className="space-y-4">
                          <div>
                            <div className="text-2xl font-black text-white">
                              {(weeklyReport?.weekly_carbon ?? 0.0).toFixed(1)} <span className="text-[11px] text-stone-450 font-bold uppercase">kg CO2e</span>
                            </div>
                            <span className="text-[9px] font-semibold text-stone-500">Emissions last 7 days</span>
                          </div>
                          
                          <div className="p-3 bg-stone-950 rounded-2xl space-y-2 border border-white/5">
                            <div className="text-xs font-bold text-stone-300">
                              Peak Carbon: <span className="text-rose-400 font-extrabold">{weeklyReport?.top_source ?? "N/A"}</span>
                            </div>
                            <div className="text-xs font-bold text-stone-300">
                              Potential Savings: <span className="text-emerald-450 font-extrabold">-{(weeklyReport?.potential_reduction ?? 0.0).toFixed(1)} kg</span>
                            </div>
                          </div>
                        </div>
                      </div>
                      
                      <p className="text-xs font-bold text-stone-450 mt-4 leading-relaxed italic border-t border-white/5 pt-3">
                        &ldquo;{weeklyReport?.summary ?? "No summary available."}&rdquo;
                      </p>
                    </div>

                    {/* Monthly Report Card */}
                    <div className="glass-card rounded-3xl p-5 border border-white/5 bg-white/[0.01] flex flex-col justify-between">
                      <div>
                        <span className="text-[9px] font-black uppercase tracking-widest text-stone-550 flex items-center gap-1.5 mb-3">
                          <BarChart3 className="w-3.5 h-3.5 text-stone-400" />
                          Monthly Coach Report
                        </span>
                        
                        <div className="space-y-3">
                          <div>
                            <div className="text-2xl font-black text-white">
                              {(monthlyReport?.monthly_carbon ?? 0.0).toFixed(1)} <span className="text-[11px] text-stone-450 font-bold uppercase">kg CO2e</span>
                            </div>
                            <span className="text-[9px] font-semibold text-stone-500">Emissions last 30 days</span>
                          </div>
                          
                          <div className="space-y-1.5">
                            <span className="text-[8px] font-black uppercase tracking-wider text-stone-500 block">Category Rankings</span>
                            {(monthlyReport?.category_ranking ?? []).map((item, idx) => (
                              <div key={idx} className="flex justify-between items-center text-[11px] font-bold text-stone-300">
                                <span className="capitalize">{item.category}</span>
                                <span>{(item.carbon ?? 0.0).toFixed(1)} kg</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      </div>

                      <div className="border-t border-white/5 pt-3 mt-4 space-y-1">
                        <span className="text-[8px] font-black uppercase tracking-wider text-stone-500 block">Behavior Insights</span>
                        {(monthlyReport?.behavior_changes ?? []).map((b, idx) => (
                          <p key={idx} className="text-[10px] font-bold text-stone-400 leading-tight flex items-start gap-1">
                            <span>•</span> <span>{b}</span>
                          </p>
                        ))}
                      </div>
                    </div>
                  </div>

                  {/* Achievements and Reduction Milestones */}
                  {Array.isArray(monthlyReport?.achievements) && monthlyReport.achievements.length > 0 && (
                    <div className="glass-card rounded-3xl p-5 border border-white/5 bg-white/[0.01]">
                      <h3 className="text-xs font-black uppercase tracking-widest text-stone-450 mb-3">
                        Carbon Achievements Unlocked
                      </h3>
                      <div className="flex flex-wrap gap-2.5">
                        {(monthlyReport.achievements ?? []).map((ach, idx) => (
                          <div key={idx} className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-emerald-500/20 bg-emerald-500/5 text-emerald-400 text-xs font-bold">
                            <Award className="w-4 h-4" />
                            <span className="capitalize">{(ach ?? "").replace(/_/g, " ")}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </motion.div>
              )}

              {activeTab === "plan" && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  className="space-y-6"
                >
                  {/* 7 Day action plan */}
                  <div className="glass-card rounded-3xl p-5 border border-white/5 bg-white/[0.01] space-y-4">
                    <h3 className="text-xs font-black uppercase tracking-widest text-stone-450 flex items-center gap-1.5">
                      <TrendingDown className="w-4 h-4 text-emerald-450 animate-pulse" />
                      7-Day Carbon Action Plan
                    </h3>
                    
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
                      {Array.isArray(monthlyReport?.recommendations) && monthlyReport.recommendations.length > 0 && (
                        <div className="sm:col-span-2 p-3 bg-stone-900/40 border border-white/5 rounded-2xl text-xs font-bold text-stone-300 flex items-start gap-2.5">
                          <CheckCircle2 className="w-4.5 h-4.5 text-emerald-400 mt-0.5 flex-shrink-0" />
                          <div>
                            <span className="text-[10px] font-black uppercase tracking-wider text-emerald-400 block mb-0.5">Primary Target Recommendation</span>
                            {monthlyReport.recommendations[0]}
                          </div>
                        </div>
                      )}
                      
                      {/* Day plans */}
                      {[
                        { day: 1, task: "Walk or cycle for trips under 2 km" },
                        { day: 2, task: "Reduce AC usage by 1 hour" },
                        { day: 3, task: "Choose a vegetarian meal" },
                        { day: 4, task: "Audit lightbulbs; ensure LED alternatives are in place" },
                        { day: 5, task: "Separate plastics and paper from trash bins" },
                        { day: 6, task: "Turn off appliances completely when leaving rooms" },
                        { day: 7, task: "Swap a private vehicle trip for public transit" }
                      ].map((item) => (
                        <div key={item.day} className="flex gap-3.5 p-3.5 border border-white/5 bg-stone-900/20 rounded-2xl items-center hover:border-emerald-500/10 transition-all duration-300">
                          <div className="w-8 h-8 rounded-full border border-emerald-500/20 bg-emerald-500/5 text-emerald-400 flex items-center justify-center font-black text-xs">
                            {item.day}
                          </div>
                          <span className="text-xs font-bold text-stone-300 leading-tight">{item.task}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          )}
          
        </div>

        {/* Right Side Coach Chat Panel (4 Columns) */}
        <div className="lg:col-span-4 space-y-6">
          <div className="glass-card rounded-3xl border border-white/5 bg-stone-900/50 flex flex-col h-[520px] overflow-hidden">
            {/* Header info */}
            <div className="p-4 border-b border-white/5 bg-gradient-to-r from-emerald-950/20 to-teal-950/20 flex items-center gap-2.5">
              <MessageSquare className="w-5 h-5 text-emerald-400" />
              <div>
                <h4 className="text-xs font-black text-white uppercase tracking-wider">Coach Chat Companion</h4>
                <span className="text-[9px] font-bold text-stone-500 block leading-none mt-0.5">Deterministic Real Data Engine</span>
              </div>
            </div>
            
            {/* Messages box */}
            <div className="flex-1 overflow-y-auto p-4 space-y-3.5">
              {messages.map((m) => (
                <div key={m.id} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
                  <div className={`max-w-[90%] rounded-xl px-3.5 py-2.5 text-xs leading-normal font-semibold ${
                    m.role === "user" 
                      ? "bg-emerald-600 text-white rounded-tr-sm border border-emerald-500/20 shadow-md"
                      : "bg-white/5 border border-white/5 text-stone-300 rounded-tl-sm"
                  }`}>
                    <p className="whitespace-pre-line leading-relaxed">{m.content}</p>
                  </div>
                </div>
              ))}
              {isChatLoading && (
                <div className="flex justify-start">
                  <div className="bg-white/5 border border-white/5 rounded-xl rounded-tl-sm px-3.5 py-2 flex items-center space-x-2">
                    <span className="w-1.5 h-1.5 bg-stone-500 rounded-full animate-ping" />
                    <span className="text-[10px] font-black text-stone-550 uppercase tracking-widest">Coach Typing...</span>
                  </div>
                </div>
              )}
              <div ref={chatEndRef} />
            </div>

            {/* Suggested prompts helper buttons */}
            <div className="px-4 pb-2 border-t border-white/5 pt-3 bg-stone-950/40">
              <span className="text-[8px] font-black uppercase tracking-wider text-stone-500 block mb-1.5">Coach Quick Queries</span>
              <div className="flex flex-wrap gap-1.5">
                {[
                  { text: "Analyze my habits", label: "Habits" },
                  { text: "What is my biggest source?", label: "Max Source" },
                  { text: "Give me a weekly report", label: "Weekly Report" },
                  { text: "Provide a 7-day sustainability plan", label: "7-Day Plan" }
                ].map((item, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleQuickQuery(item.text)}
                    disabled={isChatLoading}
                    className="text-[9px] font-black uppercase tracking-wider border border-white/5 hover:border-emerald-500/25 bg-white/5 hover:bg-emerald-500/5 text-stone-300 hover:text-emerald-400 px-2 py-1.5 rounded-lg transition-all cursor-pointer active:scale-95 disabled:opacity-40"
                  >
                    {item.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Input field */}
            <form 
              onSubmit={(e) => {
                e.preventDefault();
                handleSendChat(inputValue);
              }} 
              className="p-3 border-t border-white/5 bg-stone-950 flex items-center gap-2"
            >
              <input
                type="text"
                placeholder="Ask coach: 'how can I improve?'"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                disabled={isChatLoading}
                className="flex-1 bg-white/5 border border-white/10 rounded-xl px-3 py-2 text-xs text-stone-200 placeholder-stone-600 focus:outline-none focus:border-emerald-500 transition-all font-semibold"
              />
              <button
                type="submit"
                disabled={!inputValue.trim() || isChatLoading}
                className="p-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white disabled:opacity-40 transition-all cursor-pointer"
              >
                <Send className="w-4 h-4" />
              </button>
            </form>

          </div>
        </div>

      </div>
    </div>
  );
}
