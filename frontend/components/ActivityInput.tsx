"use client";

import React, { useState, useEffect } from "react";
import { Send, Sparkles, Calculator, Info, AlertTriangle, Mic } from "lucide-react";
import { api, ParseResult } from "../services/api";
import { useAIStore } from "../stores/aiStore";
import { getSafeCategory } from "../utils/safeCategory";
import { motion, AnimatePresence } from "framer-motion";
import { Card } from "./ui/Card";
import { Badge } from "./ui/Badge";
import { Button } from "./ui/Button";

interface ActivityInputProps {
  onActivityLogged: () => void;
  region: string;
}

const getFactor = (part: any) => {
  if (!part) return 0.0;
  const metadata = part.metadata || {};
  const parsed = part.parsed || {};
  const factor = metadata.emission_factor ?? metadata.factor ?? parsed.factor ?? parsed.food_co2_kg ?? parsed.shopping_co2_kg;
  if (factor !== undefined && factor !== null) {
    return parseFloat(factor);
  }
  return 0.0;
};

const getFormula = (part: any) => {
  if (!part) return "0.0";
  const metadata = part.metadata || {};
  const parsed = part.parsed || {};
  if (metadata.formula) return metadata.formula;
  if (parsed.formula) return parsed.formula;
  
  // Construct dynamically
  const qty = parsed.quantity ?? 1.0;
  const factor = getFactor(part);
  
  const qtyStr = Number.isInteger(qty) ? qty.toString() : qty.toFixed(2);
  const factorStr = factor.toString();
  return `${qtyStr} x ${factorStr}`;
};

export default function ActivityInput({ onActivityLogged, region }: ActivityInputProps) {
  const [inputText, setInputText] = useState("");
  const [parseResult, setParseResult] = useState<ParseResult | null>(null);
  const [parsing, setParsing] = useState(false);
  const [logging, setLogging] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [activeTab, setActiveTab] = useState("ai");
  const [loggedImpact, setLoggedImpact] = useState<{ value: number; item: string } | null>(null);
  
  const { logActivity } = useAIStore();

  // Debounced API call for real-time parsing preview
  useEffect(() => {
    if (!inputText.trim()) {
      setParseResult(null);
      setParsing(false);
      return;
    }

    setParsing(true);
    const delayDebounceFn = setTimeout(async () => {
      try {
        const result = await api.parseActivity(inputText, region);
        setParseResult(result);
      } catch (err) {
        console.error("Typing parse preview error:", err);
        setParseResult(null);
      } finally {
        setParsing(false);
      }
    }, 300);

    return () => clearTimeout(delayDebounceFn);
  }, [inputText, region]);

  // Handle global voice logging trigger
  useEffect(() => {
    const handleVoiceTrigger = () => {
      setActiveTab("ai");
      handleVoiceInput();
    };
    window.addEventListener("trigger-voice-log", handleVoiceTrigger);
    return () => window.removeEventListener("trigger-voice-log", handleVoiceTrigger);
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim() || logging) return;

    if (parseResult && parseResult.parsed) {
      setLoggedImpact({
        value: parseResult?.calculated_value ?? 0.0,
        item: parseResult?.parsed?.item ?? "Unknown"
      });
      setTimeout(() => setLoggedImpact(null), 10000);
    }

    setLogging(true);
    try {
      await logActivity(inputText, region);
      setInputText("");
      setParseResult(null);
    } catch (err: any) {
      console.error(err);
    } finally {
      setLogging(false);
    }
  };

  const handleVoiceInput = () => {
    if (isRecording) {
      setIsRecording(false);
      return;
    }

    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

    if (!SpeechRecognition) {
      alert("Web Speech API is not supported in this browser. Try Chrome or Safari.");
      return;
    }

    const rec = new SpeechRecognition();
    rec.continuous = false;
    rec.interimResults = false;
    rec.lang = "en-US";

    rec.onstart = () => {
      setIsRecording(true);
    };

    rec.onresult = (event: any) => {
      const resultText = event.results[0][0].transcript;
      setInputText(resultText);
    };

    rec.onerror = (err: any) => {
      console.error("Speech recognition error:", err);
      setIsRecording(false);
    };

    rec.onend = () => {
      setIsRecording(false);
    };

    rec.start();
  };

  const setExample = (text: string) => {
    setInputText(text);
  };

  const getCategoryColor = (category?: string | null) => {
    const colors: Record<string, string> = {
      food: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20",
      transport: "text-sky-400 bg-sky-500/10 border-sky-500/20",
      electricity: "text-amber-400 bg-amber-500/10 border-amber-500/20",
      appliances: "text-indigo-400 bg-indigo-500/10 border-indigo-500/20",
      shopping: "text-purple-400 bg-purple-500/10 border-purple-500/20",
      waste: "text-rose-450 bg-rose-500/10 border-rose-500/20",
      water: "text-cyan-400 bg-cyan-500/10 border-cyan-500/20",
      exercise: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20",
    };
    const safeCategory = getSafeCategory(category);
    return colors[safeCategory] || "text-emerald-450 bg-emerald-500/10 border-emerald-500/20";
  };

  const suggestions = [
    { label: "Travel", icon: "🚗", example: "drove 8 km in my car" },
    { label: "Food", icon: "🍔", example: "ate a vegetarian meal" },
    { label: "Energy", icon: "⚡", example: "used AC for 2 hours" },
    { label: "Shopping", icon: "🛍️", example: "bought cotton t-shirt" },
    { label: "Waste", icon: "🗑️", example: "composted 1 kg organic waste" }
  ];

  return (
    <div className="w-full">
      {/* Search Input Card */}
      <Card className="p-5 sm:p-6 select-none">
        {/* Tab headers */}
        <div className="flex items-center space-x-5 border-b border-white/5 pb-3 mb-4.5">
          <button
            type="button"
            onClick={() => setActiveTab("ai")}
            className={`text-xs font-black uppercase tracking-wider relative pb-3 flex items-center gap-1.5 cursor-pointer transition-colors ${
              activeTab === "ai" ? "text-theme-brand" : "text-theme-muted hover:text-theme-secondary"
            }`}
          >
            <Sparkles className="w-3.5 h-3.5" />
            AI Activity Tracker
            {activeTab === "ai" && (
              <motion.div 
                layoutId="activeInputTab" 
                className="absolute bottom-0 left-0 w-full h-[2px] bg-theme-brand" 
                style={{ backgroundColor: "var(--brand-primary)" }}
              />
            )}
          </button>
          
          <button
            type="button"
            onClick={() => setActiveTab("quick")}
            className={`text-xs font-black uppercase tracking-wider relative pb-3 flex items-center gap-1.5 cursor-pointer transition-colors ${
              activeTab === "quick" ? "text-theme-primary" : "text-theme-muted hover:text-theme-secondary"
            }`}
          >
            Quick Log
            {activeTab === "quick" && (
              <motion.div 
                layoutId="activeInputTab" 
                className="absolute bottom-0 left-0 w-full h-[2px]" 
                style={{ backgroundColor: "var(--brand-primary)" }}
              />
            )}
          </button>
        </div>

        {activeTab === "ai" ? (
          <form onSubmit={handleSubmit} className="relative mt-2">
            <textarea
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              placeholder={isRecording ? "Listening to dictation stream..." : "Describe activity: 'drove 8 km in car', 'ate vegan lunch', 'AC for 2 hours'..."}
              disabled={isRecording}
              rows={2}
              className="w-full pl-5 pr-28 py-3.5 rounded-2xl border border-theme-subtle bg-white/[0.01] text-theme-primary placeholder-theme-muted focus:outline-none focus:border-[rgba(var(--brand-primary)/0.3)] transition-all text-xs sm:text-sm font-semibold resize-none h-[76px]"
            />
            
            {/* Buttons */}
            <div className="absolute right-3.5 bottom-3.5 flex items-center space-x-2">
              <button
                type="button"
                onClick={handleVoiceInput}
                className={`w-11 h-11 rounded-xl border flex items-center justify-center transition-all active:scale-95 cursor-pointer ${
                  isRecording
                    ? "bg-rose-500/25 border-rose-500 text-rose-400 animate-pulse"
                    : "bg-white/5 border-white/5 text-theme-muted hover:text-theme-primary"
                }`}
                title="Start Dictation"
              >
                <Mic className="w-4 h-4" />
              </button>
              
              <Button
                type="submit"
                disabled={logging || !inputText.trim()}
                size="xs"
                style={{ width: "44px", height: "44px", padding: 0 }}
              >
                <Send className="w-4 h-4" />
              </Button>
            </div>
          </form>
        ) : (
          <div className="h-[76px] flex items-center justify-center bg-white/[0.01] border border-dashed border-theme rounded-2xl text-[11px] font-bold text-theme-muted uppercase tracking-wider">
            Quick Log categories are configured on mobile
          </div>
        )}

        {/* Suggestion Chips */}
        <div className="mt-3.5 flex flex-wrap items-center gap-1.5 text-[10px] font-bold text-theme-muted">
          <span className="mr-1">Suggestions:</span>
          {suggestions.map((s) => (
            <button
              key={s.label}
              type="button"
              onClick={() => setExample(s.example)}
              className="px-2.5 py-1 min-h-[44px] sm:min-h-0 rounded-lg border border-theme-subtle bg-white/[0.01] text-theme-secondary hover:bg-emerald-500/10 hover:text-theme-brand hover:border-emerald-500/20 transition-all active:scale-95 flex items-center gap-1 cursor-pointer font-bold"
            >
              <span>{s.icon}</span>
              <span>{s.label}</span>
            </button>
          ))}
          
          <button
            type="button"
            onClick={() => setExample("Flight from Chennai to Delhi")}
            className="px-2.5 py-1 min-h-[44px] sm:min-h-0 rounded-lg border border-theme-subtle bg-white/[0.01] text-theme-secondary hover:bg-emerald-500/10 hover:text-theme-brand transition-all active:scale-95 flex items-center gap-1 cursor-pointer font-bold"
          >
            <span>More</span>
            <span>∨</span>
          </button>
        </div>
      </Card>

      {/* Real-time NLP Live Preview */}
      <AnimatePresence>
        {inputText.trim() && (
          <motion.div 
            initial={{ opacity: 0, y: -12, height: 0 }}
            animate={{ opacity: 1, y: 0, height: "auto" }}
            exit={{ opacity: 0, y: -12, height: 0 }}
            transition={{ type: "spring", stiffness: 280, damping: 22 }}
            className="mt-4 glass-premium rounded-2xl p-5 overflow-hidden select-none"
          >
            <div className="flex items-center justify-between mb-3 border-b border-white/5 pb-2">
              <div className="flex items-center space-x-2">
                <Calculator className="w-3.5 h-3.5 text-emerald-450" />
                <span className="text-xs font-black text-theme-primary uppercase tracking-widest">
                  AI Parsing Engine
                </span>
              </div>
              {parsing && (
                <span className="text-[10px] text-theme-brand flex items-center space-x-1.5 font-bold uppercase tracking-wider animate-pulse">
                  <span>analyzing...</span>
                </span>
              )}
            </div>

            {parseResult ? (
              !parseResult.parsed || (parseResult as any).error ? (
                <div className="flex items-center space-x-2 text-rose-400 text-xs font-bold bg-rose-500/10 border border-rose-500/20 p-3.5 rounded-xl w-full">
                  <AlertTriangle className="w-4 h-4 shrink-0 text-rose-400" />
                  <span>
                    Unable to parse activity
                    {(parseResult as any).error ? `: ${String((parseResult as any).error).replace(/_/g, ' ')}` : ""}
                  </span>
                </div>
              ) : parseResult.parts && parseResult.parts.length > 1 ? (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-5 col-span-3">
                  {/* Left columns for list of entities */}
                  <div className="md:col-span-2 space-y-3">
                    <Badge variant="warning" size="xs" dot>Multi Entity</Badge>
                    {parseResult.parts.map((part, idx) => (
                      <div key={idx} className="space-y-1 bg-white/[0.01] border border-theme-subtle p-3 rounded-xl">
                        <div className="flex justify-between items-center mb-1.5">
                          <span className="capitalize text-theme-primary font-extrabold">{part.parsed?.item ?? "Unknown"}</span>
                          <span className={`px-1.5 py-0.5 rounded text-[9px] uppercase tracking-wider border leading-none font-black ${getCategoryColor(part.parsed?.category)}`}>
                            {part.parsed?.category ?? "Unknown"}
                          </span>
                        </div>
                        <div className="grid grid-cols-2 gap-x-4 gap-y-1 pl-1 text-[11px] font-bold text-theme-muted">
                          <div className="flex justify-between">
                            <span>Qty:</span>
                            <span className="text-theme-secondary">{part.parsed?.quantity ?? 1.0} {part.parsed?.unit ?? "unit"}</span>
                          </div>
                          <div className="flex justify-between">
                            <span>Factor:</span>
                            <span className="text-theme-secondary">{getFactor(part)}</span>
                          </div>
                          <div className="flex justify-between">
                            <span>Formula:</span>
                            <span className="text-theme-secondary">{getFormula(part)}</span>
                          </div>
                          <div className="flex justify-between">
                            <span>Subtotal:</span>
                            <span className="text-theme-brand">{part.calculated_value.toFixed(2)} kg CO₂</span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* Emissions Result Box */}
                  <div className="rounded-xl bg-emerald-500/5 border border-emerald-550/10 p-3 flex flex-col justify-between items-center text-center">
                    <div>
                      <span className="text-[9px] text-theme-brand font-extrabold uppercase tracking-widest block mb-0.5">
                        Total Carbon
                      </span>
                      <div className="text-xl font-black text-theme-primary font-sans">
                        {(parseResult?.calculated_value ?? 0.0).toFixed(2)} <span className="text-[10px] text-theme-muted uppercase">kg CO₂</span>
                      </div>
                    </div>
                    <Button variant="primary" size="sm" className="mt-4 w-full" onClick={handleSubmit}>
                      Log all activities
                    </Button>
                  </div>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
                  {/* Parsed Entities */}
                  <div className="space-y-1.5 font-bold text-xs">
                    <span className="text-[9px] uppercase font-black tracking-widest text-theme-muted">
                      Entities
                    </span>
                    <div className="space-y-1">
                      <div className="flex justify-between">
                        <span className="text-theme-muted">Activity:</span>
                        <span className="text-theme-primary capitalize truncate max-w-[100px]">{parseResult?.parsed?.item ?? "Unknown"}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-theme-muted">Category:</span>
                        <span className={`px-1.5 py-0.5 rounded text-[10px] border capitalize leading-none font-bold ${getCategoryColor(parseResult?.parsed?.category)}`}>
                          {parseResult?.parsed?.category ?? "Unknown"}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-theme-muted">Confidence:</span>
                        <span className={(parseResult?.parsed?.confidence ?? 0) >= 0.85 ? 'text-theme-brand' : 'text-amber-500'}>
                          {((parseResult?.parsed?.confidence ?? 0) * 100).toFixed(0)}%
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Formula Transparency */}
                  <div className="space-y-1.5 font-bold text-xs">
                    <span className="text-[9px] uppercase font-black tracking-widest text-theme-muted">
                      Formula
                    </span>
                    <div className="space-y-1">
                      <div className="flex justify-between">
                        <span className="text-theme-muted">Quantity:</span>
                        <span className="text-theme-primary">{parseResult?.parsed?.quantity ?? 1.0} {parseResult?.parsed?.unit ?? "unit"}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-theme-muted">Factor:</span>
                        <span className="text-theme-secondary">{getFactor(parseResult)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-theme-muted">Formula:</span>
                        <span className="text-theme-secondary">{getFormula(parseResult)}</span>
                      </div>
                    </div>
                  </div>

                  {/* Emissions Result Box */}
                  <div className="rounded-xl bg-emerald-500/5 border border-emerald-555/10 p-3 flex flex-col justify-between items-center text-center">
                    <div>
                      <span className="text-[9px] text-theme-brand font-extrabold uppercase tracking-widest block mb-0.5">
                        CO₂ Subtotal
                      </span>
                      <div className="text-xl font-black text-theme-primary font-sans">
                        {(parseResult?.calculated_value ?? 0.0).toFixed(2)} <span className="text-[10px] text-theme-muted uppercase">kg CO₂</span>
                      </div>
                      {parseResult?.parsed?.category === "exercise" && (
                        <span className="mt-1.5 inline-block">
                          <Badge variant="success" size="xs">🌱 Eco-Friendly</Badge>
                        </span>
                      )}
                    </div>
                    <Button variant="primary" size="sm" className="mt-2 w-full" onClick={handleSubmit}>
                      Log to History
                    </Button>
                  </div>
                </div>
              )
            ) : (
              <div className="flex items-center space-x-2 text-theme-muted text-xs font-bold">
                <Info className="w-3.5 h-3.5" />
                <span>Enter details above to calculate emissions...</span>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Comparison Success Box */}
      <AnimatePresence>
        {loggedImpact && (
          <motion.div 
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 12 }}
            className="mt-4 p-4.5 rounded-2xl bg-emerald-950/20 border border-emerald-500/20 text-theme-brand text-xs flex items-center justify-between"
          >
            <div>
              <h5 className="font-extrabold uppercase text-[9px] tracking-widest text-theme-brand mb-1 flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-theme-brand animate-pulse" />
                Logged successfully to database
              </h5>
              <p className="font-bold text-theme-secondary">
                Generated <span className="text-theme-primary font-extrabold">{loggedImpact.value.toFixed(2)} kg CO₂</span> for <span className="capitalize text-theme-primary">"{loggedImpact.item}"</span>.
              </p>
              <p className="text-[10px] text-theme-muted mt-1 leading-normal font-bold">
                Equivalent to charging <span className="text-theme-brand font-extrabold">{Math.round(loggedImpact.value * 120)}</span> smartphones, or running a standard fan for <span className="text-theme-brand font-extrabold">{Math.round(loggedImpact.value * 24)}</span> hours.
              </p>
            </div>
            <button 
              onClick={() => setLoggedImpact(null)} 
              className="text-theme-muted hover:text-theme-primary font-bold p-1 cursor-pointer transition-colors"
            >
              ✕
            </button>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
