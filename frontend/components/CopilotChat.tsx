"use client";

import React, { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { 
  Send, X, Mic, Sparkles, AlertTriangle, 
  HelpCircle, ChevronRight, Leaf
} from "lucide-react";
import { useAIStore } from "../stores/aiStore";
import logger from "../utils/logger";
import { Badge } from "./ui/Badge";
import { Button } from "./ui/Button";
import { Card } from "./ui/Card";
import { Input } from "./ui/Input";

export default function CopilotChat({ onClose }: { onClose: () => void }) {
  const [inputMsg, setInputMsg] = useState("");
  const { 
    chatMessages, chatLoading, sendChatMessage, isRecording, setIsRecording, 
    transcript, setTranscript, submitCorrection, metrics, systemHealth
  } = useAIStore();
  
  const isBackendUnreachable = systemHealth?.failed === true || systemHealth?.backend === "offline";
  const aiDegraded = systemHealth?.ai === "degraded";
  
  const chatEndRef = useRef<HTMLDivElement>(null);
  const [showCorrectionForm, setShowCorrectionForm] = useState(false);
  const [origText, setOrigText] = useState("");
  const [corrText, setCorrText] = useState("");
  const [corrSuccess, setCorrSuccess] = useState(false);

  const effectiveMessages = isBackendUnreachable
    ? [
        ...chatMessages,
        {
          id: -999,
          role: "assistant" as const,
          content: "Local AI Engine is temporarily reconnecting.",
          created_at: new Date().toISOString(),
        },
      ]
    : chatMessages;

  // Auto-scroll to bottom of chat
  useEffect(() => {
    if (chatEndRef.current) {
      chatEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [effectiveMessages, chatLoading]);

  // Handle Voice Recognition inside Chat
  useEffect(() => {
    if (transcript) {
      setInputMsg(transcript);
    }
  }, [transcript]);

  const handleVoiceInput = () => {
    if (isRecording) {
      setIsRecording(false);
      return;
    }

    const SpeechRecognition = 
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
      
    if (!SpeechRecognition) {
      logger.warn("CopilotChat", "Web Speech API not supported in this browser");
      return;
    }

    const rec = new SpeechRecognition();
    rec.continuous = false;
    rec.interimResults = false;
    rec.lang = "en-US";

    rec.onstart = () => {
      setIsRecording(true);
      setTranscript("");
    };

    rec.onresult = (event: any) => {
      const resultText = event.results[0][0].transcript;
      setTranscript(resultText);
      setInputMsg(resultText);
    };

    rec.onerror = (err: any) => {
      logger.error("CopilotChat", "Speech recognition error", err);
      setIsRecording(false);
    };

    rec.onend = () => {
      setIsRecording(false);
    };

    rec.start();
  };

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputMsg.trim()) return;
    
    const msgToSend = inputMsg;
    setInputMsg("");
    await sendChatMessage(msgToSend);
  };

  const handleCorrectionSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!origText.trim() || !corrText.trim()) return;
    
    await submitCorrection(origText, corrText, "nlp_parse");
    setCorrSuccess(true);
    setOrigText("");
    setCorrText("");
    setTimeout(() => {
      setCorrSuccess(false);
      setShowCorrectionForm(false);
    }, 2000);
  };

  const presetQueries = [
    { text: "Why did my emissions increase this week?", label: "Footprint Spike" },
    { text: "Analyze my travel habits.", label: "Travel Patterns" },
    { text: "Suggest realistic sustainability improvements.", label: "AI Coaching" }
  ];

  return (
    <div className="fixed inset-0 z-50 flex justify-end pointer-events-none">
      {/* Backdrop Layer */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        onClick={onClose}
        className="absolute inset-0 bg-black/50 backdrop-blur-md pointer-events-auto cursor-pointer"
      />

      {/* Sliding Chat Panel */}
      <motion.div
        initial={{ x: "100%" }}
        animate={{ x: 0 }}
        exit={{ x: "100%" }}
        transition={{ type: "spring", damping: 26, stiffness: 220 }}
        className="relative w-full max-w-md h-full bg-theme-surface border-l border-theme-subtle shadow-2xl flex flex-col pointer-events-auto text-theme-primary"
      >
        {/* Header */}
        <div className="p-5 border-b border-theme-subtle flex items-center justify-between bg-gradient-to-r from-emerald-950/10 to-teal-950/10">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-forest-600/20 border border-forest-500/20 flex items-center justify-center">
              <Leaf className="w-5 h-5 text-theme-brand animate-pulse" />
            </div>
            <div>
              <h4 className="font-extrabold text-sm text-theme-primary flex items-center gap-2 font-display">
                AI Assistant
                <Badge variant="success" size="xs" dot>Local Mode</Badge>
              </h4>
              <span className="text-[10px] text-theme-muted flex items-center gap-1 font-sans">
                Offline • Fast • Private
              </span>
              {aiDegraded && (
                <span className="text-[9px] text-amber-400 flex items-center gap-1 mt-0.5 font-black uppercase tracking-wider animate-pulse">
                  ⚠️ Running in degraded mode.
                </span>
              )}
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-white/5 rounded-xl transition-all cursor-pointer"
          >
            <X className="w-5 h-5 text-theme-muted hover:text-theme-primary" />
          </button>
        </div>

        {/* Chat messages */}
        <div className="flex-1 overflow-y-auto p-5 space-y-4">
          {effectiveMessages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center space-y-4 px-4 font-sans">
              <HelpCircle className="w-12 h-12 text-theme-muted opacity-40" />
              <div>
                <h5 className="font-bold text-sm text-theme-secondary">Start the Conversation</h5>
                <p className="text-xs text-theme-muted mt-1 max-w-[260px]">
                  Ask me about your lifestyle metrics, carbon spikes, or reduction advice.
                </p>
              </div>
            </div>
          ) : (
            effectiveMessages.map((msg) => (
              <motion.div
                initial={{ opacity: 0, y: 12, scale: 0.97 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                transition={{ type: "spring", stiffness: 350, damping: 24 }}
                key={msg.id}
                className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
              >
                <div
                  className={`max-w-[85%] rounded-2xl px-4 py-3 text-xs leading-relaxed font-sans ${
                    msg.role === "user"
                      ? "text-white rounded-tr-sm shadow-lg shadow-forest-650/20 border border-forest-550/15"
                      : "bg-theme-base border border-theme-subtle text-theme-secondary rounded-tl-sm shadow-md"
                  }`}
                  style={msg.role === "user" ? { backgroundColor: "var(--brand-primary)" } : {}}
                >
                  <div className="whitespace-pre-line font-semibold">{msg.content}</div>

                  {msg.role === "assistant" && msg.context_tags && msg.context_tags.length > 0 && (
                    <div className="flex flex-wrap gap-1.5 mt-3 pt-2 border-t border-white/5">
                      {msg.context_tags.map((tag) => (
                        <span
                          key={tag}
                          className="px-1.5 py-0.5 rounded bg-forest-950/40 text-theme-brand text-[9px] font-bold uppercase tracking-wider border border-forest-500/10"
                        >
                          #{tag}
                        </span>
                      ))}
                    </div>
                  )}
                  <span className="block text-[8px] text-theme-muted mt-1 text-right">
                    {new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                </div>
              </motion.div>
            ))
          )}
          
          {chatLoading && (
            <div className="flex justify-start">
              <div className="bg-theme-base border border-theme-subtle rounded-2xl rounded-tl-sm p-4 text-xs text-theme-muted flex items-center space-x-2">
                <div className="flex space-x-1">
                  <span className="w-1.5 h-1.5 bg-theme-muted rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                  <span className="w-1.5 h-1.5 bg-theme-muted rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                  <span className="w-1.5 h-1.5 bg-theme-muted rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
                </div>
                <span className="font-semibold tracking-wider text-[10px] uppercase">AI Thinking...</span>
              </div>
            </div>
          )}
          
          <div ref={chatEndRef} />
        </div>

        {/* Suggested Prompts */}
        {chatMessages.length <= 2 && (
          <div className="px-5 pb-3">
            <p className="text-[10px] uppercase tracking-widest text-theme-muted font-bold mb-2">Suggested Queries</p>
            <div className="space-y-2">
              {presetQueries.map((q) => (
                <button
                  key={q.text}
                  onClick={() => {
                    setInputMsg(q.text);
                    sendChatMessage(q.text);
                  }}
                  className="w-full text-left p-2.5 rounded-xl border border-theme-subtle bg-white/[0.01] hover:bg-white/[0.03] transition-all text-xs text-theme-secondary font-semibold flex items-center justify-between cursor-pointer"
                >
                  <span>{q.text}</span>
                  <ChevronRight className="w-3.5 h-3.5 text-theme-muted" />
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Human correction */}
        <div className="px-5 pb-2">
          <button
            onClick={() => setShowCorrectionForm(!showCorrectionForm)}
            className="text-[10px] flex items-center space-x-1 text-amber-500/80 hover:text-amber-400 font-bold uppercase tracking-wide transition-all cursor-pointer"
          >
            <AlertTriangle className="w-3.5 h-3.5" />
            <span>Report Translation/Parsing Correction</span>
          </button>
          
          <AnimatePresence>
            {showCorrectionForm && (
              <motion.form
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: "auto", opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                onSubmit={handleCorrectionSubmit}
                className="mt-2 p-3 bg-amber-500/5 border border-amber-500/20 rounded-xl space-y-2 overflow-hidden"
              >
                <p className="text-[10px] text-amber-405 font-bold">Help train the carbon parser:</p>
                <Input 
                  label="Original text"
                  value={origText}
                  onChange={(e) => setOrigText(e.target.value)}
                  placeholder="e.g. '1 plate curd ric'"
                  required
                />
                <Input 
                  label="Corrected formulation"
                  value={corrText}
                  onChange={(e) => setCorrText(e.target.value)}
                  placeholder="e.g. '1 plate curd rice'"
                  required
                />
                <Button
                  type="submit"
                  size="xs"
                  className="w-full"
                >
                  Submit Correction
                </Button>
                {corrSuccess && (
                  <p className="text-[10px] text-center text-emerald-450 font-black animate-pulse">Correction Recorded!</p>
                )}
              </motion.form>
            )}
          </AnimatePresence>
        </div>

        {/* Chat Input form */}
        <form onSubmit={handleSend} className="p-4 border-t border-theme-subtle bg-theme-base flex items-center space-x-2">
          <button
            type="button"
            onClick={handleVoiceInput}
            disabled={isBackendUnreachable}
            className={`p-2.5 rounded-xl border transition-all cursor-pointer ${
              isRecording 
                ? "bg-rose-500/25 border-rose-500 text-rose-455 animate-pulse" 
                : "bg-white/5 border-white/10 text-theme-muted hover:text-theme-primary"
            } ${isBackendUnreachable ? "opacity-55 cursor-not-allowed" : ""}`}
            title="Dictate message"
          >
            <Mic className="w-4 h-4" />
          </button>
          
          <input
            type="text"
            placeholder={isBackendUnreachable ? "AI Engine is reconnecting..." : isRecording ? "Listening..." : "Message AI Copilot..."}
            value={inputMsg}
            onChange={(e) => setInputMsg(e.target.value)}
            disabled={isRecording || isBackendUnreachable}
            className="flex-1 bg-white/5 border border-theme-subtle rounded-xl px-4 py-2.5 text-xs text-theme-primary placeholder-theme-muted focus:outline-none focus:border-[rgba(var(--brand-primary)/0.3)] transition-all font-semibold"
          />
          
          <Button
            type="submit"
            disabled={!inputMsg.trim() || chatLoading || isBackendUnreachable}
            size="xs"
            style={{ width: "36px", height: "36px", padding: 0 }}
          >
            <Send className="w-4 h-4" />
          </Button>
        </form>
      </motion.div>
    </div>
  );
}
