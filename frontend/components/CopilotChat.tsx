"use client";

import React, { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { 
  MessageSquare, Send, X, Mic, Sparkles, AlertTriangle, 
  HelpCircle, ChevronRight, Activity, Leaf, Eye, HelpCircle as HelpIcon 
} from "lucide-react";
import { useAIStore } from "../stores/aiStore";

export default function CopilotChat() {
  const [isOpen, setIsOpen] = useState(false);
  const [inputMsg, setInputMsg] = useState("");
  const { 
    chatMessages, chatLoading, sendChatMessage, isRecording, setIsRecording, 
    transcript, setTranscript, submitCorrection, metrics
  } = useAIStore();
  
  const chatEndRef = useRef<HTMLDivElement>(null);
  const [showCorrectionForm, setShowCorrectionForm] = useState(false);
  const [origText, setOrigText] = useState("");
  const [corrText, setCorrText] = useState("");
  const [corrSuccess, setCorrSuccess] = useState(false);

  // Auto-scroll to bottom of chat
  useEffect(() => {
    if (chatEndRef.current) {
      chatEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [chatMessages, chatLoading]);

  // Handle Voice Recognition inside Chat
  useEffect(() => {
    if (transcript && isOpen) {
      setInputMsg(transcript);
    }
  }, [transcript, isOpen]);

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
      setTranscript("");
    };

    rec.onresult = (event: any) => {
      const resultText = event.results[0][0].transcript;
      setTranscript(resultText);
      setInputMsg(resultText);
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
    <>
      {/* Floating Launcher Button */}
      <div className="fixed bottom-6 right-6 z-40">
        <motion.button
          whileHover={{ scale: 1.06 }}
          whileTap={{ scale: 0.94 }}
          onClick={() => setIsOpen(true)}
          className="relative flex items-center justify-center w-14 h-14 rounded-full bg-forest-600 hover:bg-forest-500 text-white shadow-xl shadow-forest-600/35 cursor-pointer overflow-hidden border border-forest-500/30 glow-btn"
        >
          <MessageSquare className="w-6 h-6" />
          {metrics && metrics.total_user_corrections > 0 && (
            <span className="absolute top-1 right-1 bg-amber-500 text-black text-[10px] font-black w-4 h-4 rounded-full flex items-center justify-center">
              {metrics.total_user_corrections}
            </span>
          )}
        </motion.button>
      </div>

      <AnimatePresence>
        {isOpen && (
          <div className="fixed inset-0 z-50 flex justify-end pointer-events-none">
            {/* Backdrop Layer */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setIsOpen(false)}
              className="absolute inset-0 bg-black/50 backdrop-blur-md pointer-events-auto"
            />

            {/* Sliding Chat Panel */}
            <motion.div
              initial={{ x: "100%" }}
              animate={{ x: 0 }}
              exit={{ x: "100%" }}
              transition={{ type: "spring", damping: 26, stiffness: 220 }}
              className="relative w-full max-w-md h-full bg-stone-900/80 dark:bg-stone-950/80 backdrop-blur-xl border-l border-white/10 shadow-2xl flex flex-col pointer-events-auto text-stone-100"
            >
              {/* Header */}
              <div className="p-5 border-b border-white/10 flex items-center justify-between bg-gradient-to-r from-forest-950/40 to-emerald-950/40">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 rounded-xl bg-forest-600/20 border border-forest-500/20 flex items-center justify-center">
                    <Leaf className="w-5 h-5 text-forest-400 animate-pulse" />
                  </div>
                  <div>
                    <h4 className="font-extrabold text-sm text-forest-100 flex items-center gap-1">
                      AI Sustainability Companion
                      <Sparkles className="w-3.5 h-3.5 text-amber-500" />
                    </h4>
                    <span className="text-[10px] text-stone-400 flex items-center gap-1">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-ping" />
                      Memory &amp; Context Enabled
                    </span>
                  </div>
                </div>
                <button
                  onClick={() => setIsOpen(false)}
                  className="p-2 hover:bg-white/10 rounded-xl transition-all cursor-pointer"
                >
                  <X className="w-5 h-5 text-stone-400 hover:text-white" />
                </button>
              </div>

              {/* Chat messages */}
              <div className="flex-1 overflow-y-auto p-5 space-y-4">
                {chatMessages.length === 0 ? (
                  <div className="flex flex-col items-center justify-center h-full text-center space-y-4 px-4">
                    <HelpCircle className="w-12 h-12 text-forest-500/40" />
                    <div>
                      <h5 className="font-bold text-sm text-stone-300">Start the Conversation</h5>
                      <p className="text-xs text-stone-500 mt-1 max-w-[260px]">
                        Ask me about your lifestyle metrics, carbon spikes, or reduction advice.
                      </p>
                    </div>
                  </div>
                ) : (
                  chatMessages.map((msg) => (
                    <motion.div
                      initial={{ opacity: 0, y: 12, scale: 0.97 }}
                      animate={{ opacity: 1, y: 0, scale: 1 }}
                      transition={{ type: "spring", stiffness: 350, damping: 24 }}
                      key={msg.id}
                      className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
                    >
                      <div
                        className={`max-w-[85%] rounded-2xl px-4 py-3 text-xs leading-relaxed ${
                          msg.role === "user"
                            ? "bg-forest-600 text-white rounded-tr-sm shadow-lg shadow-forest-650/20 border border-forest-550/15"
                            : "bg-white/5 dark:bg-white/[0.03] border border-white/10 text-stone-200 rounded-tl-sm shadow-md backdrop-blur-sm"
                        }`}
                      >
                        {/* Message content */}
                        <div className="whitespace-pre-line font-medium">{msg.content}</div>

                        {/* Context Tags if Assistant */}
                        {msg.role === "assistant" && msg.context_tags && msg.context_tags.length > 0 && (
                          <div className="flex flex-wrap gap-1.5 mt-3 pt-2 border-t border-white/5">
                            {msg.context_tags.map((tag) => (
                              <span
                                key={tag}
                                className="px-1.5 py-0.5 rounded bg-forest-950/40 text-forest-400 text-[9px] font-bold uppercase tracking-wider border border-forest-500/10"
                              >
                                #{tag}
                              </span>
                            ))}
                          </div>
                        )}
                        <span className="block text-[8px] text-stone-500 mt-1 text-right">
                          {new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </span>
                      </div>
                    </motion.div>
                  ))
                )}
                
                {chatLoading && (
                  <div className="flex justify-start">
                    <div className="bg-white/5 border border-white/10 rounded-2xl rounded-tl-sm p-4 text-xs text-stone-400 flex items-center space-x-2">
                      <div className="flex space-x-1">
                        <span className="w-1.5 h-1.5 bg-stone-500 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                        <span className="w-1.5 h-1.5 bg-stone-500 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                        <span className="w-1.5 h-1.5 bg-stone-500 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
                      </div>
                      <span className="font-semibold tracking-wider text-[10px] uppercase">AI Thinking...</span>
                    </div>
                  </div>
                )}
                
                <div ref={chatEndRef} />
              </div>

              {/* Quick Suggestion Prompts */}
              {chatMessages.length <= 2 && (
                <div className="px-5 pb-3">
                  <p className="text-[10px] uppercase tracking-widest text-stone-500 font-bold mb-2">Suggested Queries</p>
                  <div className="space-y-2">
                    {presetQueries.map((q) => (
                      <button
                        key={q.text}
                        onClick={() => {
                          setInputMsg(q.text);
                          sendChatMessage(q.text);
                        }}
                        className="w-full text-left p-2.5 rounded-xl border border-white/5 bg-white/5 hover:bg-forest-650/10 hover:border-forest-500/20 transition-all text-xs text-stone-300 font-semibold flex items-center justify-between cursor-pointer"
                      >
                        <span>{q.text}</span>
                        <ChevronRight className="w-3.5 h-3.5 text-stone-500" />
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Human correction drawer / toggle */}
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
                      <p className="text-[10px] text-amber-400 font-bold">Help train the carbon parser:</p>
                      <input
                        type="text"
                        placeholder="Original text (e.g. '1 plate curd ric')"
                        value={origText}
                        onChange={(e) => setOrigText(e.target.value)}
                        className="w-full bg-black/40 border border-white/10 rounded-lg p-2 text-xs text-stone-200 focus:outline-none focus:border-amber-500/50"
                        required
                      />
                      <input
                        type="text"
                        placeholder="Corrected formulation (e.g. '1 plate curd rice')"
                        value={corrText}
                        onChange={(e) => setCorrText(e.target.value)}
                        className="w-full bg-black/40 border border-white/10 rounded-lg p-2 text-xs text-stone-200 focus:outline-none focus:border-amber-500/50"
                        required
                      />
                      <button
                        type="submit"
                        className="w-full py-1.5 bg-amber-600 hover:bg-amber-500 text-black font-extrabold text-[10px] uppercase rounded-lg transition-all cursor-pointer"
                      >
                        Submit Correction
                      </button>
                      {corrSuccess && (
                        <p className="text-[10px] text-center text-emerald-400 font-black animate-pulse">Correction Recorded!</p>
                      )}
                    </motion.form>
                  )}
                </AnimatePresence>
              </div>

              {/* Chat Input form */}
              <form onSubmit={handleSend} className="p-4 border-t border-white/10 bg-stone-950 flex items-center space-x-2">
                <button
                  type="button"
                  onClick={handleVoiceInput}
                  className={`p-2.5 rounded-xl border transition-all cursor-pointer ${
                    isRecording 
                      ? "bg-rose-500/25 border-rose-500 text-rose-400 animate-pulse" 
                      : "bg-white/5 border-white/10 text-stone-400 hover:text-white"
                  }`}
                  title="Dictate message"
                >
                  <Mic className="w-4 h-4" />
                </button>
                
                <input
                  type="text"
                  placeholder={isRecording ? "Listening..." : "Message AI Copilot..."}
                  value={inputMsg}
                  onChange={(e) => setInputMsg(e.target.value)}
                  disabled={isRecording}
                  className="flex-1 bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-xs text-stone-200 placeholder-stone-500 focus:outline-none focus:border-forest-500 focus:bg-white/10 transition-all font-semibold"
                />
                
                <button
                  type="submit"
                  disabled={!inputMsg.trim() || chatLoading}
                  className="p-2.5 rounded-xl bg-forest-600 text-white hover:bg-forest-500 transition-all disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
                >
                  <Send className="w-4 h-4" />
                </button>
              </form>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </>
  );
}
