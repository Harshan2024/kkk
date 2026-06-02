"use client";

import React, { useState, useEffect } from "react";
import { Send, Sparkles, Calculator, Info, AlertTriangle, Mic } from "lucide-react";
import { api, ParseResult } from "../services/api";
import { useAIStore } from "../stores/aiStore";
import { getSafeCategory } from "../utils/safeCategory";
import { motion, AnimatePresence } from "framer-motion";

interface ActivityInputProps {
  onActivityLogged: () => void;
  region: string;
}

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

    if (parseResult) {
      setLoggedImpact({
        value: parseResult.calculated_value,
        item: parseResult.parsed.item
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
      food: "text-emerald-500 bg-emerald-500/10 border-emerald-500/20",
      transport: "text-sky-500 bg-sky-500/10 border-sky-500/20",
      electricity: "text-amber-500 bg-amber-500/10 border-amber-500/20",
      appliances: "text-indigo-500 bg-indigo-500/10 border-indigo-500/20",
      shopping: "text-purple-500 bg-purple-500/10 border-purple-500/20",
      waste: "text-rose-500 bg-rose-500/10 border-rose-500/20",
      water: "text-cyan-500 bg-cyan-500/10 border-cyan-500/20",
    };
    const safeCategory = getSafeCategory(category);
    return colors[safeCategory] || "text-emerald-500 bg-emerald-500/10 border-emerald-500/20";
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
      <div className="glass-card rounded-3xl p-5 sm:p-6 transition-all duration-300 select-none">
        {/* Tab headers */}
        <div className="flex items-center space-x-5 border-b border-white/5 pb-3 mb-4.5">
          <button
            type="button"
            onClick={() => setActiveTab("ai")}
            className={`text-xs font-black uppercase tracking-wider relative pb-3 flex items-center gap-1.5 cursor-pointer transition-colors ${
              activeTab === "ai" ? "text-amber-400" : "text-stone-500 hover:text-stone-300"
            }`}
          >
            <Sparkles className="w-3.5 h-3.5" />
            AI Activity Tracker
            {activeTab === "ai" && (
              <motion.div 
                layoutId="activeInputTab" 
                className="absolute bottom-0 left-0 w-full h-[2px] bg-amber-400" 
              />
            )}
          </button>
          
          <button
            type="button"
            onClick={() => setActiveTab("quick")}
            className={`text-xs font-black uppercase tracking-wider relative pb-3 flex items-center gap-1.5 cursor-pointer transition-colors ${
              activeTab === "quick" ? "text-stone-300" : "text-stone-500 hover:text-stone-300"
            }`}
          >
            Quick Log
            {activeTab === "quick" && (
              <motion.div 
                layoutId="activeInputTab" 
                className="absolute bottom-0 left-0 w-full h-[2px] bg-stone-300" 
              />
            )}
          </button>
        </div>

        {activeTab === "ai" ? (
          <form onSubmit={handleSubmit} className="relative mt-2">
            <textarea
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              placeholder={isRecording ? "Listening to your dictation..." : "Describe your activity naturally...\ne.g., drove 8 km in my car, ate a veg meal, used AC for 2 hours"}
              disabled={isRecording}
              rows={2}
              className="w-full pl-5 pr-28 py-3.5 rounded-2xl border border-white/5 bg-white/[0.01] text-white placeholder-stone-605 focus:outline-none focus:border-emerald-500/30 transition-all text-xs sm:text-sm font-semibold resize-none h-[76px]"
            />
            
            {/* Buttons alignment */}
            <div className="absolute right-3.5 bottom-3.5 flex items-center space-x-2">
              <button
                type="button"
                onClick={handleVoiceInput}
                className={`w-8 h-8 rounded-xl border flex items-center justify-center transition-all active:scale-95 cursor-pointer ${
                  isRecording
                    ? "bg-rose-500/25 border-rose-500 text-rose-450 animate-pulse"
                    : "bg-white/5 border-white/5 text-stone-400 hover:text-white"
                }`}
                title="Start Dictation"
              >
                <Mic className="w-3.5 h-3.5" />
              </button>
              
              <button
                type="submit"
                disabled={logging || !inputText.trim()}
                className="w-8 h-8 rounded-xl bg-amber-400 hover:bg-amber-455 text-black flex items-center justify-center transition-all active:scale-95 disabled:opacity-40 cursor-pointer shadow shadow-amber-400/10"
              >
                <Send className="w-3.5 h-3.5 fill-black/10" />
              </button>
            </div>
          </form>
        ) : (
          <div className="h-[76px] flex items-center justify-center bg-white/[0.01] border border-dashed border-white/5 rounded-2xl text-[11px] font-bold text-stone-500 uppercase tracking-wider">
            Quick Log categories are synced from mobile
          </div>
        )}

        {/* Suggestion Chips */}
        <div className="mt-3.5 flex flex-wrap items-center gap-1.5 text-[10px] font-bold text-stone-500">
          <span className="mr-1">Suggestions:</span>
          {suggestions.map((s) => (
            <button
              key={s.label}
              type="button"
              onClick={() => setExample(s.example)}
              className="px-2.5 py-1 rounded-lg border border-white/5 bg-white/[0.01] text-stone-400 hover:bg-emerald-500/10 hover:text-emerald-400 hover:border-emerald-500/20 transition-all active:scale-95 flex items-center gap-1 cursor-pointer font-bold"
            >
              <span>{s.icon}</span>
              <span>{s.label}</span>
            </button>
          ))}
          
          {/* More dropdown */}
          <div className="relative">
            <button
              type="button"
              onClick={() => setExample("Flight from Chennai to Delhi")}
              className="px-2.5 py-1 rounded-lg border border-white/5 bg-white/[0.01] text-stone-400 hover:bg-emerald-500/10 hover:text-emerald-400 transition-all active:scale-95 flex items-center gap-1 cursor-pointer font-bold"
            >
              <span>More</span>
              <span>∨</span>
            </button>
          </div>
        </div>
      </div>

      {/* Real-time NLP Live Preview */}
      <AnimatePresence>
        {inputText.trim() && (
          <motion.div 
            initial={{ opacity: 0, y: -12, height: 0 }}
            animate={{ opacity: 1, y: 0, height: "auto" }}
            exit={{ opacity: 0, y: -12, height: 0 }}
            transition={{ type: "spring", stiffness: 280, damping: 22 }}
            className="mt-4 glass-card rounded-2xl p-5 overflow-hidden select-none"
          >
            <div className="flex items-center justify-between mb-3 border-b border-white/5 pb-2">
              <div className="flex items-center space-x-2">
                <Calculator className="w-3.5 h-3.5 text-emerald-400" />
                <span className="text-xs font-black text-stone-300 uppercase tracking-widest">
                  AI Parsing Engine
                </span>
              </div>
              {parsing && (
                <span className="text-[10px] text-emerald-400 flex items-center space-x-1.5 font-bold uppercase tracking-wider">
                  <span className="w-1.5 h-1.5 bg-emerald-450 rounded-full animate-ping"></span>
                  <span>analyzing...</span>
                </span>
              )}
            </div>

            {parseResult ? (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
                {/* Parsed Entities */}
                <div className="space-y-1.5 font-bold text-xs">
                  <span className="text-[9px] uppercase font-black tracking-widest text-stone-500">
                    Entities
                  </span>
                  <div className="space-y-1">
                    <div className="flex justify-between">
                      <span className="text-stone-500">Activity:</span>
                      <span className="text-white capitalize truncate max-w-[100px]">{parseResult.parsed.item}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-stone-500">Category:</span>
                      <span className={`px-1.5 py-0.5 rounded text-[10px] border capitalize leading-none font-bold ${getCategoryColor(parseResult.parsed.category)}`}>
                        {parseResult.parsed.category}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-stone-500">Confidence:</span>
                      <span className={parseResult.parsed.confidence >= 0.85 ? 'text-emerald-450' : 'text-amber-500'}>
                        {(parseResult.parsed.confidence * 100).toFixed(0)}%
                      </span>
                    </div>
                  </div>
                </div>

                {/* Scientific Conversions */}
                <div className="space-y-1.5 font-bold text-xs">
                  <span className="text-[9px] uppercase font-black tracking-widest text-stone-500">
                    Metrics
                  </span>
                  <div className="space-y-1">
                    <div className="flex justify-between">
                      <span className="text-stone-500">Quantity:</span>
                      <span className="text-white">{parseResult.parsed.quantity} {parseResult.parsed.unit}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-stone-500">Factor:</span>
                      <span className="text-stone-400 truncate max-w-[90px]">
                        {parseResult.metadata.emission_factor !== undefined 
                          ? `${parseResult.metadata.emission_factor} kg` 
                          : "dynamic"}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-stone-500">Method:</span>
                      <span className="text-stone-400 truncate max-w-[90px] capitalize">
                        {parseResult.metadata.calculation_type?.replace("_", " ") || "standard"}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Emissions Result Box */}
                <div className="rounded-xl bg-emerald-500/5 border border-emerald-500/10 p-3 flex flex-col justify-between items-center text-center">
                  <div>
                    <span className="text-[9px] text-emerald-400 font-extrabold uppercase tracking-widest block mb-0.5">
                      CO₂ Output
                    </span>
                    <div className="text-xl font-black text-white font-sans">
                      {parseResult.calculated_value.toFixed(1)} <span className="text-[10px] text-stone-500 uppercase">kg</span>
                    </div>
                  </div>
                  <button
                    onClick={handleSubmit}
                    disabled={logging}
                    className="mt-2 w-full py-1.5 bg-emerald-500 hover:bg-emerald-450 text-[#080d0a] rounded-lg text-[10px] font-black uppercase transition-all tracking-wider active:scale-95 cursor-pointer shadow shadow-emerald-500/10"
                  >
                    Log to History
                  </button>
                </div>
              </div>
            ) : (
              <div className="flex items-center space-x-2 text-stone-500 text-xs font-bold">
                <Info className="w-3.5 h-3.5 text-stone-605" />
                <span>Enter details above to calculate emissions...</span>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Educational comparison panel */}
      <AnimatePresence>
        {loggedImpact && (
          <motion.div 
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 12 }}
            className="mt-4 p-4.5 rounded-2xl bg-emerald-950/20 border border-emerald-500/20 text-emerald-450 text-xs flex items-center justify-between"
          >
            <div>
              <h5 className="font-extrabold uppercase text-[9px] tracking-widest text-emerald-405 mb-1 flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                Logged successfully to cloud database
              </h5>
              <p className="font-bold text-stone-300">
                Generated <span className="text-white font-extrabold">{loggedImpact.value.toFixed(2)} kg CO₂</span> for <span className="capitalize text-white">"{loggedImpact.item}"</span>.
              </p>
              <p className="text-[10px] text-stone-500 mt-1 leading-normal font-bold">
                Equivalent to: charging <span className="text-emerald-400 font-extrabold">{Math.round(loggedImpact.value * 120)}</span> smartphones, or running a standard electric fan for <span className="text-emerald-400 font-extrabold">{Math.round(loggedImpact.value * 24)}</span> hours.
              </p>
            </div>
            <button 
              onClick={() => setLoggedImpact(null)} 
              className="text-stone-550 hover:text-white font-bold p-1 cursor-pointer transition-colors"
            >
              ✕
            </button>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
