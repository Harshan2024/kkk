"use client";

import React, { useState, useEffect, useRef } from "react";
import { 
  Brain, Sparkles, Send, Award, Calendar, BarChart3, 
  TrendingDown, Shield, User, ChevronRight, Zap, Utensils, 
  Car, Trash2, CheckCircle2, MessageSquare, AlertCircle
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import api, { HabitAnalysis, CoachWeeklyReport, CoachMonthlyReport } from "../services/api";
import { Card } from "./ui/Card";
import { Badge } from "./ui/Badge";
import { Button } from "./ui/Button";

function EmptyState({ message }: { message: string }) {
  return (
    <Card className="p-8 text-center flex flex-col items-center justify-center" hover={false}>
      <AlertCircle className="w-10 h-10 text-theme-muted mb-3 animate-pulse" />
      <p className="text-xs font-bold text-theme-secondary">{message}</p>
    </Card>
  );
}

export default function CoachDashboard() {
  const [activeTab, setActiveTab] = useState<"habits" | "reports" | "plan" | "copilot">("habits");
  
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

  const safeAnalysis = {
    energy: analysis?.energy ?? {} as any,
    food: analysis?.food ?? {} as any,
    transport: analysis?.transport ?? {} as any,
    waste: analysis?.waste ?? {} as any
  };

  if (isLoading) {
    return (
      <div className="space-y-6 select-none">
        <div className="glass-premium rounded-3xl p-6 border border-emerald-500/10 bg-gradient-to-br from-emerald-950/5 via-theme-surface to-theme-base relative overflow-hidden flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div className="absolute top-0 right-0 w-32 h-32 bg-emerald-500/5 blur-[55px] pointer-events-none rounded-full" />
          <div className="flex items-center space-x-3.5">
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-emerald-500/20 to-teal-700/20 border border-emerald-500/30 flex items-center justify-center shadow-lg shadow-emerald-500/5 animate-pulse">
              <Brain className="w-6 h-6 text-emerald-400" />
            </div>
            <div>
              <h1 className="text-lg font-black tracking-tight text-theme-heading flex items-center gap-1.5 font-display">
                AI Sustainability Coach <Badge variant="success" size="xs">Expert Mode</Badge>
              </h1>
              <p className="text-[11px] font-bold text-theme-muted mt-0.5 font-sans">
                Real-time behavior analysis and carbon footprint mitigation engine.
              </p>
            </div>
          </div>
        </div>
        <div className="glass-premium rounded-3xl p-6 h-[400px] animate-pulse" />
      </div>
    );
  }

  if (!analysis) {
    return <EmptyState message="No sustainability data available yet." />;
  }

  return (
    <div className="space-y-6 select-none">
      {/* Header Panel */}
      <div className="glass-premium rounded-3xl p-6 border border-emerald-500/10 bg-gradient-to-br from-emerald-950/5 via-theme-surface to-theme-base relative overflow-hidden flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div className="absolute top-0 right-0 w-32 h-32 bg-emerald-500/5 blur-[55px] pointer-events-none rounded-full" />
        <div className="flex items-center space-x-3.5">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-emerald-500/20 to-teal-700/20 border border-emerald-500/30 flex items-center justify-center shadow-lg shadow-emerald-500/5">
            <Brain className="w-6 h-6 text-emerald-400" />
          </div>
          <div>
            <h1 className="text-lg font-black tracking-tight text-theme-heading flex items-center gap-1.5 font-display">
              AI Sustainability Coach <Badge variant="success" size="xs">Expert Mode</Badge>
            </h1>
            <p className="text-[11px] font-bold text-theme-muted mt-0.5 font-sans">
              Real-time behavior analysis and carbon footprint mitigation engine.
            </p>
          </div>
        </div>
        
        {/* Navigation Tabs */}
        <div className="flex bg-theme-base p-1 border border-theme-subtle rounded-2xl">
          {(["habits", "reports", "plan"] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-4 py-2 rounded-xl text-xs font-black uppercase tracking-wider transition-all cursor-pointer ${
                activeTab === tab 
                  ? "bg-emerald-950/40 text-theme-brand border border-emerald-500/20" 
                  : "text-theme-muted hover:text-theme-secondary"
              }`}
            >
              {tab}
            </button>
          ))}
        </div>
      </div>

      {/* Main Grid Content */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        
        {/* Left Side Tab Views */}
        <div className="lg:col-span-8 space-y-6">
          
          {isLoading ? (
            <div className="glass-premium rounded-3xl p-6 h-[400px] animate-pulse" />
          ) : (
            <AnimatePresence mode="wait">
              {activeTab === "habits" && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  className="space-y-6"
                >
                  {/* Habit Profiles */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    
                    {/* Energy card */}
                    <Card className="flex flex-col justify-between" hover={false}>
                      <div>
                        <div className="flex items-center gap-2.5 mb-3">
                          {getEnergyIcon(analysis?.energy?.finding ?? "")}
                          <h3 className="text-xs font-black uppercase tracking-wider text-theme-primary">Energy Habits</h3>
                        </div>
                        <p className="text-xs font-bold text-theme-secondary leading-relaxed">
                          {analysis?.energy?.finding ?? "No energy data available"}
                        </p>
                      </div>
                      <div className="border-t border-white/5 pt-3.5 mt-4 text-[10px] font-black uppercase text-theme-muted tracking-wider">
                        AC Usage: <span className="text-amber-400 font-black">{(safeAnalysis.energy?.ac_hours ?? 0).toFixed(1)} hrs/day</span>
                      </div>
                    </Card>

                    {/* Food card */}
                    <Card className="flex flex-col justify-between" hover={false}>
                      <div>
                        <div className="flex items-center gap-2.5 mb-3">
                          {getFoodIcon(safeAnalysis.food?.food_profile ?? "")}
                          <h3 className="text-xs font-black uppercase tracking-wider text-theme-primary">Food Habits</h3>
                        </div>
                        <p className="text-xs font-bold text-theme-secondary leading-relaxed">
                          {analysis?.food?.finding ?? "No food data available"}
                        </p>
                      </div>
                      <div className="border-t border-white/5 pt-3.5 mt-4 grid grid-cols-2 text-[10px] font-black uppercase text-theme-muted tracking-wider gap-2">
                        <div>Veg Ratio: <span className="text-theme-brand">{Math.round((safeAnalysis.food?.veg_ratio ?? 0) * 100)}%</span></div>
                        <div>Animal Ratio: <span className="text-rose-450">{Math.round((safeAnalysis.food?.animal_ratio ?? 0) * 100)}%</span></div>
                      </div>
                    </Card>

                    {/* Transport card */}
                    <Card className="flex flex-col justify-between" hover={false}>
                      <div>
                        <div className="flex items-center gap-2.5 mb-3">
                          {getTransportIcon(safeAnalysis.transport?.transport_profile ?? "")}
                          <h3 className="text-xs font-black uppercase tracking-wider text-theme-primary">Transport Habits</h3>
                        </div>
                        <p className="text-xs font-bold text-theme-secondary leading-relaxed">
                          {analysis?.transport?.finding ?? "No transport data available"}
                        </p>
                      </div>
                      <div className="border-t border-white/5 pt-3.5 mt-4 text-[10px] font-black uppercase text-theme-muted tracking-wider">
                        Public transit: <span className="text-sky-400 font-black">{Math.round((safeAnalysis.transport?.public_transport_ratio ?? 0) * 100)}%</span>
                      </div>
                    </Card>

                    {/* Waste card */}
                    <Card className="flex flex-col justify-between" hover={false}>
                      <div>
                        <div className="flex items-center gap-2.5 mb-3">
                          {getWasteIcon(safeAnalysis.waste?.waste_profile ?? "")}
                          <h3 className="text-xs font-black uppercase tracking-wider text-theme-primary">Waste Habits</h3>
                        </div>
                        <p className="text-xs font-bold text-theme-secondary leading-relaxed">
                          {analysis?.waste?.finding ?? "No waste data available"}
                        </p>
                      </div>
                      <div className="border-t border-white/5 pt-3.5 mt-4 text-[10px] font-black uppercase text-theme-muted tracking-wider">
                        Recycling frequency: <span className="text-rose-400 font-black">{safeAnalysis.waste?.recycling_frequency ?? 0} events</span>
                      </div>
                    </Card>

                  </div>

                  {/* Detected Patterns */}
                  {Array.isArray(analysis?.patterns) && analysis.patterns.length > 0 && (
                    <Card hover={false}>
                      <h3 className="text-xs font-black uppercase tracking-widest text-theme-muted mb-3.5">
                        Detected Pattern Signals
                      </h3>
                      <div className="space-y-2">
                        {(analysis.patterns ?? []).map((pat, idx) => (
                          <div key={idx} className="flex items-center justify-between p-3 border border-theme-subtle bg-white/[0.01] rounded-xl">
                            <span className="text-xs font-bold text-theme-primary uppercase tracking-wider">{pat.pattern.replace(/_/g, " ")}</span>
                            <Badge variant="success" size="xs">
                              Confidence {Math.round(pat.confidence * 100)}%
                            </Badge>
                          </div>
                        ))}
                      </div>
                    </Card>
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
                    <Card className="flex flex-col justify-between" hover={false}>
                      <div>
                        <span className="text-[9px] font-black uppercase tracking-widest text-theme-muted flex items-center gap-1.5 mb-3">
                          <Calendar className="w-3.5 h-3.5" />
                          Weekly Coach Report
                        </span>
                        
                        <div className="space-y-4">
                          <div>
                            <div className="text-2xl font-black text-theme-primary font-display">
                              {(weeklyReport?.weekly_carbon ?? 0.0).toFixed(1)} <span className="text-[11px] text-theme-muted font-bold uppercase">kg CO2e</span>
                            </div>
                            <span className="text-[9px] font-semibold text-theme-muted">Emissions last 7 days</span>
                          </div>
                          
                          <div className="p-3 bg-theme-base rounded-2xl space-y-2 border border-theme-subtle">
                            <div className="text-xs font-bold text-theme-secondary">
                              Peak Carbon: <span className="text-rose-450 font-extrabold">{weeklyReport?.top_source ?? "N/A"}</span>
                            </div>
                            <div className="text-xs font-bold text-theme-secondary">
                              Potential Savings: <span className="text-theme-brand font-extrabold">-{(weeklyReport?.potential_reduction ?? 0.0).toFixed(1)} kg</span>
                            </div>
                          </div>
                        </div>
                      </div>
                      
                      <p className="text-xs font-bold text-theme-secondary mt-4 leading-relaxed italic border-t border-white/5 pt-3">
                        &ldquo;{weeklyReport?.summary ?? "No summary available."}&rdquo;
                      </p>
                    </Card>

                    {/* Monthly Report Card */}
                    <Card className="flex flex-col justify-between" hover={false}>
                      <div>
                        <span className="text-[9px] font-black uppercase tracking-widest text-theme-muted flex items-center gap-1.5 mb-3">
                          <BarChart3 className="w-3.5 h-3.5" />
                          Monthly Coach Report
                        </span>
                        
                        <div className="space-y-3">
                          <div>
                            <div className="text-2xl font-black text-theme-primary font-display">
                              {(monthlyReport?.monthly_carbon ?? 0.0).toFixed(1)} <span className="text-[11px] text-theme-muted font-bold uppercase">kg CO2e</span>
                            </div>
                            <span className="text-[9px] font-semibold text-theme-muted">Emissions last 30 days</span>
                          </div>
                          
                          <div className="space-y-1.5">
                            <span className="text-[8px] font-black uppercase tracking-wider text-theme-muted block">Category Rankings</span>
                            {(monthlyReport?.category_ranking ?? []).map((item, idx) => (
                              <div key={idx} className="flex justify-between items-center text-[11px] font-bold text-theme-secondary">
                                <span className="capitalize">{item.category}</span>
                                <span>{(item.carbon ?? 0.0).toFixed(1)} kg</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      </div>

                      <div className="border-t border-white/5 pt-3 mt-4 space-y-1">
                        <span className="text-[8px] font-black uppercase tracking-wider text-theme-muted block">Behavior Insights</span>
                        {(monthlyReport?.behavior_changes ?? []).map((b, idx) => (
                          <p key={idx} className="text-[10px] font-bold text-theme-secondary leading-tight flex items-start gap-1">
                            <span>•</span> <span>{b}</span>
                          </p>
                        ))}
                      </div>
                    </Card>
                  </div>

                  {/* Achievements */}
                  {Array.isArray(monthlyReport?.achievements) && monthlyReport.achievements.length > 0 && (
                    <Card hover={false}>
                      <h3 className="text-xs font-black uppercase tracking-widest text-theme-muted mb-3">
                        Carbon Achievements Unlocked
                      </h3>
                      <div className="flex flex-wrap gap-2.5">
                        {(monthlyReport.achievements ?? []).map((ach, idx) => (
                          <div key={idx} className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-emerald-500/25 bg-emerald-500/5 text-theme-brand text-xs font-bold">
                            <Award className="w-4 h-4" />
                            <span className="capitalize">{(ach ?? "").replace(/_/g, " ")}</span>
                          </div>
                        ))}
                      </div>
                    </Card>
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
                  <Card hover={false} className="space-y-4">
                    <h3 className="text-xs font-black uppercase tracking-widest text-theme-muted flex items-center gap-1.5">
                      <TrendingDown className="w-4 h-4 text-theme-brand animate-pulse" />
                      7-Day Carbon Action Plan
                    </h3>
                    
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
                      {Array.isArray(monthlyReport?.recommendations) && monthlyReport.recommendations.length > 0 && (
                        <div className="sm:col-span-2 p-3 bg-theme-base border border-theme-subtle rounded-2xl text-xs font-bold text-theme-secondary flex items-start gap-2.5">
                          <CheckCircle2 className="w-4.5 h-4.5 text-theme-brand mt-0.5 flex-shrink-0" />
                          <div>
                            <span className="text-[10px] font-black uppercase tracking-wider text-theme-brand block mb-0.5">Primary Target Recommendation</span>
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
                        <div key={item.day} className="flex gap-3.5 p-3.5 border border-theme-subtle bg-white/[0.01] rounded-2xl items-center hover:border-emerald-500/10 transition-all duration-300">
                          <div className="w-8 h-8 rounded-full border border-emerald-500/25 bg-emerald-500/5 text-theme-brand flex items-center justify-center font-black text-xs">
                            {item.day}
                          </div>
                          <span className="text-xs font-bold text-theme-secondary leading-tight">{item.task}</span>
                        </div>
                      ))}
                    </div>
                  </Card>
                </motion.div>
              )}
            </AnimatePresence>
          )}
          
        </div>

        {/* Right Side Coach Chat Panel */}
        <div className="lg:col-span-4 space-y-6">
          <div className="glass-premium rounded-3xl border border-theme-subtle bg-white/[0.01] flex flex-col h-[520px] overflow-hidden">
            {/* Header info */}
            <div className="p-4 border-b border-theme-subtle bg-gradient-to-r from-emerald-950/10 to-teal-950/10 flex items-center gap-2.5">
              <MessageSquare className="w-5 h-5 text-theme-brand" />
              <div>
                <h4 className="text-xs font-black text-theme-heading uppercase tracking-wider">Coach Chat Companion</h4>
                <span className="text-[9px] font-bold text-theme-muted block leading-none mt-0.5">Deterministic Real Data Engine</span>
              </div>
            </div>
            
            {/* Messages box */}
            <div className="flex-1 overflow-y-auto p-4 space-y-3.5">
              {messages.map((m) => (
                <div key={m.id} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
                  <div className={`max-w-[90%] rounded-xl px-3.5 py-2.5 text-xs leading-normal font-semibold ${
                    m.role === "user" 
                      ? "bg-theme-brand text-white rounded-tr-sm border border-emerald-500/20 shadow-md"
                      : "bg-theme-base border border-theme-subtle text-theme-secondary rounded-tl-sm"
                  }`} style={m.role === "user" ? { backgroundColor: "var(--brand-primary)" } : {}}>
                    <p className="whitespace-pre-line leading-relaxed">{m.content}</p>
                  </div>
                </div>
              ))}
              {isChatLoading && (
                <div className="flex justify-start">
                  <div className="bg-theme-base border border-theme-subtle rounded-xl rounded-tl-sm px-3.5 py-2 flex items-center space-x-2">
                    <span className="w-1.5 h-1.5 bg-theme-brand rounded-full animate-pulse" />
                    <span className="text-[10px] font-black text-theme-muted uppercase tracking-widest">Coach Typing...</span>
                  </div>
                </div>
              )}
              <div ref={chatEndRef} />
            </div>

            {/* Suggested prompts */}
            <div className="px-4 pb-2 border-t border-theme-subtle pt-3 bg-theme-base">
              <span className="text-[8px] font-black uppercase tracking-wider text-theme-muted block mb-1.5">Coach Quick Queries</span>
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
                    className="text-[9px] font-black uppercase tracking-wider border border-theme-subtle hover:border-emerald-500/25 bg-white/5 hover:bg-emerald-500/5 text-theme-secondary hover:text-theme-brand px-2 py-1.5 rounded-lg transition-all cursor-pointer active:scale-95 disabled:opacity-40"
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
              className="p-3 border-t border-theme-subtle bg-theme-base flex items-center gap-2"
            >
              <input
                type="text"
                placeholder="Ask: 'how can I improve?'"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                disabled={isChatLoading}
                className="flex-1 bg-white/[0.01] border border-theme-subtle rounded-xl px-3 py-2 text-xs text-theme-primary placeholder-theme-muted focus:outline-none focus:border-[rgba(var(--brand-primary)/0.3)] transition-all font-semibold"
              />
              <Button
                type="submit"
                disabled={!inputValue.trim() || isChatLoading}
                size="xs"
                style={{ width: "32px", height: "32px", padding: 0 }}
              >
                <Send className="w-3.5 h-3.5" />
              </Button>
            </form>

          </div>
        </div>

      </div>
    </div>
  );
}
