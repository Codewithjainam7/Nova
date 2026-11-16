import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNovaStore } from '../store/useNovaStore';
import { useNovaWebSocket } from '../contexts/NovaWebSocket';
import { useVoiceRecognition, speakResponse } from '../hooks/useVoiceRecognition';
import {
  Mic, BrainCircuit, Globe, Monitor, ScanEye, CheckCircle,
  XCircle, ExternalLink, ArrowUp, ChevronUp, ChevronDown,
  MessageSquare, Zap, FolderSync, Volume2, X, Clock
} from 'lucide-react';
import clsx from 'clsx';

export const DynamicIsland: React.FC = () => {
  const { islandState, islandMessage, setIslandState } = useNovaStore();
  const { sendChat } = useNovaWebSocket();
  const [expanded, setExpanded] = useState(false);
  const [inputValue, setInputValue] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showFolderPicker, setShowFolderPicker] = useState(false);
  const [recentResponse, setRecentResponse] = useState<string | null>(null);
  const [currentTime, setCurrentTime] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);

  // Voice Recognition Hook
  const {
    isListening,
    interimTranscript,
    amplitude,
    toggleListening
  } = useVoiceRecognition({
    onResult: (result) => {
      if (result.transcript && result.transcript.trim()) {
        const text = result.transcript.trim();
        setInputValue(text);
        handleDispatch(text);
      }
    }
  });

  // Keep time updated
  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setCurrentTime(now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }));
    };
    updateTime();
    const interval = setInterval(updateTime, 10000);
    return () => clearInterval(interval);
  }, []);

  // Tell Electron what height to set based on state
  useEffect(() => {
    try {
      if (typeof window !== 'undefined' && (window as any).electronAPI) {
        if (expanded) {
          (window as any).electronAPI.setIslandExpanded(true, 300);
        } else {
          (window as any).electronAPI.setIslandExpanded(false, 44);
        }
      }
    } catch {
      // Browser context
    }
    if (expanded && inputRef.current && !recentResponse) {
      setTimeout(() => inputRef.current?.focus(), 140);
    }
  }, [expanded, showFolderPicker, recentResponse]);

  // Automatically expand capsule when wake word triggers voice-listening
  useEffect(() => {
    if (islandState === 'voice-listening') {
      setExpanded(true);
    }
  }, [islandState]);

  // Global shortcuts and auto-collapse handlers
  useEffect(() => {
    if (typeof window !== 'undefined' && (window as any).electronAPI?.onShortcutTriggered) {
      (window as any).electronAPI.onShortcutTriggered((action: string) => {
        if (action === 'toggle') {
          setExpanded((prev) => !prev);
        } else if (action === 'expand') {
          setExpanded(true);
        } else if (action === 'collapse') {
          setExpanded(false);
          setShowFolderPicker(false);
          setRecentResponse(null);
        }
      });
    }

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' || (e.altKey && (e.code === 'Space' || e.key === ' '))) {
        e.preventDefault();
        setExpanded(false);
        setShowFolderPicker(false);
        setRecentResponse(null);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const handleDispatch = async (cmd: string) => {
    if (!cmd.trim() || isSubmitting) return;

    const query = cmd.trim();
    setInputValue('');
    setIsSubmitting(true);
    setShowFolderPicker(false);
    setIslandState('thinking', `Processing: ${query.slice(0, 26)}...`);

    try {
      const isBriefing = query.toLowerCase().includes('briefing') || query.toLowerCase().includes('brief me');
      if (isBriefing) {
        setIslandState('thinking', 'Synthesizing Executive Briefing...');
        const res = await fetch('http://localhost:8000/api/briefing');
        if (res.ok) {
          const data = await res.json();
          const briefingText = data.briefing || "All systems nominal, Boss.";
          setRecentResponse(briefingText);
          setIslandState('idle', 'Briefing delivered');
          speakResponse(briefingText);
          setIsSubmitting(false);
          return;
        }
      }

      const res = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: query })
      });

      if (res.ok) {
        const data = await res.json();
        const respText = data.response || "Task executed successfully.";
        setRecentResponse(respText);
        setIslandState('idle', 'Complete');
        speakResponse(respText);
      } else {
        sendChat(query);
      }
    } catch (err) {
      console.warn('Dispatching via websocket fallback:', err);
      try {
        sendChat(query);
      } catch {}
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim() || isSubmitting) return;
    handleDispatch(inputValue);
  };

  const openMainDashboard = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (typeof window !== 'undefined' && (window as any).electronAPI) {
      (window as any).electronAPI.showMainWindow();
    }
  };

  const toggleVoiceMode = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (!expanded) {
      setExpanded(true);
    }
    toggleListening();
  };

  const getStatusIcon = () => {
    if (isListening || islandState === 'voice-listening') {
      return <Mic className="w-3.5 h-3.5 text-cyan-400 animate-pulse" />;
    }
    switch (islandState) {
      case 'listening':
        return <Mic className="w-3.5 h-3.5 text-blue-400 animate-pulse" />;
      case 'thinking':
        return <BrainCircuit className="w-3.5 h-3.5 text-purple-400 animate-spin" />;
      case 'executing':
        return <CheckCircle className="w-3.5 h-3.5 text-emerald-400 animate-pulse" />;
      case 'browser':
        return <Globe className="w-3.5 h-3.5 text-cyan-400 animate-pulse" />;
      case 'desktop':
        return <Monitor className="w-3.5 h-3.5 text-indigo-400 animate-pulse" />;
      case 'vision':
        return <ScanEye className="w-3.5 h-3.5 text-cyan-300 animate-pulse" />;
      case 'error':
        return <XCircle className="w-3.5 h-3.5 text-rose-500" />;
      default:
        return (
          <div className="relative flex items-center justify-center">
            <span className="w-2.5 h-2.5 rounded-full bg-cyan-400 shadow-[0_0_8px_#22d3ee] animate-pulse" />
            <span className="absolute w-4 h-4 rounded-full bg-cyan-400/20 animate-ping" />
          </div>
        );
    }
  };

  const expandedHeight = recentResponse ? 182 : showFolderPicker ? 196 : 166;

  return (
    <div className="w-full h-full m-0 p-0 overflow-hidden bg-transparent select-none flex items-start justify-center pt-1">
      {/* Liquid Capsule Morph Container */}
      <motion.div
        layout
        initial={false}
        animate={
          expanded
            ? { width: 480, height: expandedHeight, borderRadius: 26 }
            : { width: 320, height: 42, borderRadius: 21 }
        }
        transition={{
          type: "spring",
          stiffness: 410,
          damping: 32,
          mass: 0.8
        }}
        onClick={() => !expanded && setExpanded(true)}
        className={clsx(
          "relative overflow-hidden cursor-pointer flex flex-col justify-between",
          "bg-[#03060a] border border-cyan-400/40",
          "shadow-[inset_0_1px_1px_rgba(255,255,255,0.22),inset_0_0_15px_rgba(6,182,212,0.1)]",
          "before:absolute before:inset-x-8 before:top-0 before:h-[1px] before:bg-gradient-to-r before:from-transparent before:via-cyan-400/60 before:to-transparent"
        )}
      >
        {/* Top Header / Collapsed Capsule Bar */}
        <div className="flex items-center justify-between px-3 h-[42px] w-full shrink-0">
          <div className="flex items-center gap-2 overflow-hidden">
            <div className="w-5 h-5 flex items-center justify-center shrink-0">
              {getStatusIcon()}
            </div>

            <AnimatePresence mode="wait">
              <motion.span
                key={
                  isListening
                    ? 'voice-listening'
                    : islandState === 'idle'
                    ? 'idle-text'
                    : (islandMessage || islandState)
                }
                initial={{ opacity: 0, y: 3 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -3 }}
                transition={{ duration: 0.15 }}
                className={clsx(
                  "font-medium tracking-wide truncate",
                  expanded ? "text-xs text-white max-w-[240px]" : "text-xs text-white max-w-[150px]"
                )}
              >
                {isListening || islandState === 'voice-listening' ? (
                  <span className="text-cyan-300 font-semibold animate-pulse">
                    {islandMessage || (isListening ? "Listening..." : "Listening to you, Boss...")}
                  </span>
                ) : islandState === 'idle' ? (
                  <span className="bg-gradient-to-r from-white via-slate-100 to-cyan-300 bg-clip-text text-transparent font-semibold">
                    ADA • Online
                  </span>
                ) : (
                  <span className="text-cyan-300">
                    {islandMessage || islandState.toUpperCase()}
                  </span>
                )}
              </motion.span>
            </AnimatePresence>
          </div>

          {/* Right Header Controls */}
          {!expanded ? (
            <div className="flex items-center gap-1.5">
              <button
                onClick={toggleVoiceMode}
                title="Voice Command"
                className={clsx(
                  "p-1 rounded-full transition-all",
                  isListening
                    ? "bg-cyan-500/30 text-cyan-300"
                    : "text-white/60 hover:text-cyan-300"
                )}
              >
                <Mic className="w-3.5 h-3.5" />
              </button>

              <div className="flex gap-0.5 items-end h-3 px-1">
                <motion.span
                  animate={{ height: (isListening || islandState === 'voice-listening') ? [6, 14, 8, 16, 6] : [3, 10, 5, 8, 3] }}
                  transition={{ repeat: Infinity, duration: (isListening || islandState === 'voice-listening') ? 0.6 : 1.2 }}
                  className="w-[2px] rounded-full bg-cyan-400"
                />
                <motion.span
                  animate={{ height: (isListening || islandState === 'voice-listening') ? [10, 6, 16, 8, 10] : [6, 3, 12, 5, 6] }}
                  transition={{ repeat: Infinity, duration: (isListening || islandState === 'voice-listening') ? 0.5 : 1.0 }}
                  className="w-[2px] rounded-full bg-blue-400"
                />
                <motion.span
                  animate={{ height: (isListening || islandState === 'voice-listening') ? [8, 16, 6, 12, 8] : [4, 11, 6, 9, 4] }}
                  transition={{ repeat: Infinity, duration: (isListening || islandState === 'voice-listening') ? 0.7 : 1.4 }}
                  className="w-[2px] rounded-full bg-purple-400"
                />
              </div>

              <kbd className="text-[10px] text-cyan-200 font-mono font-bold px-2 py-0.5 rounded-full bg-cyan-950 border border-cyan-400/60">
                Alt+Space / F2
              </kbd>
            </div>
          ) : (
            <div className="flex items-center gap-1" onClick={(e) => e.stopPropagation()}>
              <button
                onClick={toggleVoiceMode}
                title={isListening ? "Stop Voice" : "Start Voice"}
                className={clsx(
                  "px-2 py-1 rounded-lg text-[10px] font-semibold transition-all flex items-center gap-1",
                  isListening
                    ? "bg-cyan-500/30 text-cyan-300 border border-cyan-400/40 animate-pulse"
                    : "text-white/60 hover:text-cyan-300 hover:bg-white/10"
                )}
              >
                <Mic className="w-3 h-3" />
                <span>{isListening ? "Listening" : "Voice"}</span>
              </button>

              <button
                onClick={openMainDashboard}
                title="Open Dashboard"
                className="p-1 rounded-lg text-white/50 hover:text-cyan-300 hover:bg-white/10"
              >
                <ExternalLink className="w-3.5 h-3.5" />
              </button>

              <button
                onClick={() => {
                  setExpanded(false);
                  setShowFolderPicker(false);
                  setRecentResponse(null);
                }}
                title="Minimize Island"
                className="p-1 rounded-lg text-white/50 hover:text-white hover:bg-white/10"
              >
                <ChevronUp className="w-3.5 h-3.5" />
              </button>
            </div>
          )}
        </div>

        {/* Expanded Body: Command Input, Waveform, Quick Chips */}
        <AnimatePresence>
          {expanded && (
            <motion.div
              initial={{ opacity: 0, scale: 0.96, y: -6 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.96, y: -6 }}
              transition={{ duration: 0.18, ease: "easeOut" }}
              className="flex-1 px-3 pb-2.5 flex flex-col justify-between"
              onClick={(e) => e.stopPropagation()}
            >
              {/* Live Audio Visualizer (When Voice is Active) */}
              {isListening && (
                <div className="mb-1 px-2.5 py-1.5 rounded-xl bg-cyan-950/40 border border-cyan-500/30 flex items-center justify-between">
                  <div className="flex items-center gap-2 overflow-hidden">
                    <div className="flex gap-0.5 items-end h-3.5 shrink-0">
                      {[0.4, 0.8, 0.5, 1.0, 0.6, 0.9, 0.3, 0.7, 0.4].map((scale, i) => (
                        <motion.span
                          key={i}
                          animate={{
                            height: Math.max(3, Math.round((amplitude * 28 + 3) * scale))
                          }}
                          transition={{ duration: 0.08 }}
                          className="w-[2.5px] bg-cyan-400 rounded-full"
                        />
                      ))}
                    </div>
                    <span className="text-[11px] text-cyan-200 truncate">
                      {interimTranscript || "Listening... Speak your directive"}
                    </span>
                  </div>
                  <button
                    onClick={toggleListening}
                    className="px-2 py-0.5 rounded text-[10px] bg-cyan-500/20 text-cyan-300 font-medium shrink-0"
                  >
                    Done
                  </button>
                </div>
              )}

              {/* Contextual Presentation 1: Dedicated Response & Briefing View (Zero Clipping, 100% Encapsulated) */}
              {recentResponse ? (
                <div className="flex flex-col gap-2 my-auto">
                  <div className="p-3 rounded-2xl bg-gradient-to-r from-cyan-950/40 via-cyan-900/20 to-purple-950/30 border border-cyan-500/30 flex items-start justify-between gap-2.5">
                    <div className="flex items-start gap-2.5 overflow-hidden">
                      <Volume2 className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5 animate-pulse" />
                      <p className="text-[12px] text-white/95 leading-relaxed font-sans font-normal line-clamp-3 select-text">
                        {recentResponse}
                      </p>
                    </div>
                    <button
                      onClick={() => setRecentResponse(null)}
                      title="Dismiss"
                      className="text-white/40 hover:text-white p-1 rounded-lg hover:bg-white/10 shrink-0"
                    >
                      <X className="w-3.5 h-3.5" />
                    </button>
                  </div>

                  <div className="flex items-center gap-2 overflow-x-auto no-scrollbar">
                    <button
                      onClick={() => {
                        setRecentResponse(null);
                        if (inputRef.current) setTimeout(() => inputRef.current?.focus(), 80);
                      }}
                      className="px-2.5 py-1 rounded-lg text-[11px] font-medium bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-300 border border-cyan-500/30 flex items-center gap-1.5 shrink-0"
                    >
                      <ArrowUp className="w-3 h-3 rotate-45" />
                      Ask Follow-up
                    </button>

                    <button
                      onClick={() => handleDispatch("give me my morning briefing")}
                      className="px-2.5 py-1 rounded-lg text-[11px] font-medium bg-white/[0.05] hover:bg-amber-500/20 text-white/80 hover:text-amber-300 border border-white/[0.08] flex items-center gap-1.5 shrink-0"
                    >
                      <Zap className="w-3 h-3 text-amber-400" />
                      Refresh Briefing
                    </button>

                    <button
                      onClick={openMainDashboard}
                      className="px-2.5 py-1 rounded-lg text-[11px] font-medium bg-white/[0.05] hover:bg-white/10 text-white/80 hover:text-white border border-white/[0.08] flex items-center gap-1.5 shrink-0 ml-auto"
                    >
                      <ExternalLink className="w-3 h-3 text-cyan-400" />
                      Dashboard
                    </button>
                  </div>
                </div>
              ) : (
                /* Contextual Presentation 2: Spotlight Command Input & Quick Chips */
                <>
                  {/* Spotlight Command Input */}
                  <form onSubmit={handleSubmit} className="relative w-full">
                    <input
                      ref={inputRef}
                      type="text"
                      value={inputValue}
                      onChange={(e) => setInputValue(e.target.value)}
                      placeholder="Ask ADA anything (e.g. organize desktop, message someone, briefing)..."
                      className={clsx(
                        "w-full h-8 pl-3 pr-14 text-xs rounded-xl text-white placeholder-white/40",
                        "bg-white/[0.06] border border-white/[0.12]",
                        "focus:outline-none focus:border-cyan-400/70 focus:ring-1 focus:ring-cyan-400/40"
                      )}
                    />
                    <div className="absolute right-1 top-1 flex items-center gap-0.5">
                      <button
                        type="button"
                        onClick={toggleVoiceMode}
                        className={clsx(
                          "w-6 h-6 rounded-lg flex items-center justify-center transition-all",
                          isListening
                            ? "bg-cyan-500 text-black"
                            : "text-white/40 hover:text-cyan-300"
                        )}
                      >
                        <Mic className="w-3 h-3" />
                      </button>
                      <button
                        type="submit"
                        disabled={!inputValue.trim() || isSubmitting}
                        className={clsx(
                          "w-6 h-6 rounded-lg flex items-center justify-center transition-all",
                          inputValue.trim()
                            ? "bg-cyan-500 text-black hover:bg-cyan-400 shadow-[0_0_8px_#06b6d4]"
                            : "bg-white/5 text-white/30 cursor-not-allowed"
                        )}
                      >
                        <ArrowUp className="w-3 h-3" />
                      </button>
                    </div>
                  </form>

                  {/* Drawer 1: Folder Selector */}
                  {showFolderPicker && (
                    <div className="py-1 flex items-center gap-1.5 overflow-x-auto no-scrollbar">
                      <span className="text-[10px] text-white/50 shrink-0 font-medium">Target:</span>
                      {[
                        { label: 'Desktop', cmd: 'organize my desktop' },
                        { label: 'Downloads', cmd: 'organize my downloads' },
                        { label: 'Documents', cmd: 'organize my documents' },
                        { label: 'All Folders', cmd: 'organize my files' }
                      ].map((folder) => (
                        <button
                          key={folder.label}
                          onClick={() => handleDispatch(folder.cmd)}
                          className="px-2 py-0.5 rounded-md text-[10px] bg-cyan-950/70 hover:bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 shrink-0"
                        >
                          {folder.label}
                        </button>
                      ))}
                      <button
                        onClick={() => setShowFolderPicker(false)}
                        className="p-0.5 text-white/40 hover:text-white shrink-0 ml-auto"
                      >
                        <X className="w-3 h-3" />
                      </button>
                    </div>
                  )}

                  {/* Quick Action Jarvis Chips */}
                  <div className="flex items-center gap-1.5 overflow-x-auto pt-0.5 no-scrollbar">
                    <button
                      onClick={() => setShowFolderPicker(!showFolderPicker)}
                      className={clsx(
                        "px-2.5 py-1 rounded-lg text-[11px] font-medium border transition-all flex items-center gap-1.5 shrink-0",
                        showFolderPicker
                          ? "bg-cyan-500/25 text-cyan-300 border-cyan-400/50"
                          : "bg-white/[0.05] hover:bg-cyan-500/20 text-white/80 hover:text-cyan-300 border-white/[0.08]"
                      )}
                    >
                      <FolderSync className="w-3 h-3 text-cyan-400" />
                      Organize
                      {showFolderPicker ? <ChevronUp className="w-2.5 h-2.5" /> : <ChevronDown className="w-2.5 h-2.5" />}
                    </button>

                    <button
                      onClick={() => {
                        setInputValue("msg ");
                        setShowFolderPicker(false);
                        inputRef.current?.focus();
                      }}
                      className="px-2.5 py-1 rounded-lg text-[11px] font-medium bg-white/[0.05] hover:bg-emerald-500/20 text-white/80 hover:text-emerald-300 border border-white/[0.08] flex items-center gap-1.5 shrink-0"
                    >
                      <MessageSquare className="w-3 h-3 text-emerald-400" />
                      Message
                    </button>

                    <button
                      onClick={() => handleDispatch("give me my morning briefing")}
                      className="px-2.5 py-1 rounded-lg text-[11px] font-medium bg-white/[0.05] hover:bg-amber-500/20 text-white/80 hover:text-amber-300 border border-white/[0.08] flex items-center gap-1.5 shrink-0"
                    >
                      <Zap className="w-3 h-3 text-amber-400" />
                      Briefing
                    </button>

                    <button
                      onClick={openMainDashboard}
                      className="px-2.5 py-1 rounded-lg text-[11px] font-medium bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-300 border border-cyan-500/30 flex items-center gap-1.5 shrink-0 ml-auto"
                    >
                      <ExternalLink className="w-3 h-3 text-cyan-400" />
                      Dashboard
                    </button>
                  </div>
                </>
              )}

              {/* Micro Status Bar */}
              <div className="flex items-center justify-between text-[10px] text-white/40 pt-1 border-t border-white/[0.06] font-mono">
                <span className="flex items-center gap-1.5">
                  <span className={clsx(
                    "w-1.5 h-1.5 rounded-full",
                    isListening ? "bg-cyan-400 animate-ping" : "bg-cyan-400"
                  )} />
                  STATUS: <span className="text-cyan-400 uppercase font-semibold">
                    {isListening ? "VOICE ACTIVE" : recentResponse ? "INTEL DELIVERED" : islandState}
                  </span>
                </span>

                <span className="flex items-center gap-2 text-white/30">
                  {currentTime && (
                    <span className="flex items-center gap-1 text-white/50">
                      <Clock className="w-2.5 h-2.5" />
                      {currentTime}
                    </span>
                  )}
                  <span>ADA v1.0 • NEURAL</span>
                </span>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>
    </div>
  );
};
