import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNovaStore } from '../store/useNovaStore';
import { useNovaWebSocket } from '../contexts/NovaWebSocket';
import { useVoiceRecognition, speakResponse } from '../hooks/useVoiceRecognition';
import {
  Mic, BrainCircuit, Globe, Monitor, ScanEye, CheckCircle,
  XCircle, ExternalLink, ArrowUp, ChevronUp, ChevronDown,
  MessageSquare, Zap, FolderSync, Volume2, X, Clock,
  Smartphone, Shield, Copy, Check, Sparkles
} from 'lucide-react';
import clsx from 'clsx';

interface PhoneTelemetry {
  connected: boolean;
  battery: number | null;
  deviceId: string | null;
}

export const DynamicIsland: React.FC = () => {
  const { islandState, islandMessage, setIslandState } = useNovaStore();
  const { sendChat } = useNovaWebSocket();
  const [expanded, setExpanded] = useState(false);
  const [inputValue, setInputValue] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showFolderPicker, setShowFolderPicker] = useState(false);
  const [recentResponse, setRecentResponse] = useState<string | null>(null);
  const [currentTime, setCurrentTime] = useState('');
  const [copied, setCopied] = useState(false);
  const [phoneStats, setPhoneStats] = useState<PhoneTelemetry>({
    connected: false,
    battery: null,
    deviceId: null
  });
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
      setCurrentTime(now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }));
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  // Poll real hardware & phone telemetry
  useEffect(() => {
    const fetchTelemetry = async () => {
      try {
        const res = await fetch('http://localhost:8000/api/telemetry');
        if (res.ok) {
          const data = await res.json();
          if (data.phone) {
            setPhoneStats({
              connected: Boolean(data.phone.connected),
              battery: data.phone.battery ?? null,
              deviceId: data.phone.device_id ?? null
            });
          }
        }
      } catch {
        // Backend temporarily busy
      }
    };
    fetchTelemetry();
    const telInterval = setInterval(fetchTelemetry, 15000);
    return () => clearInterval(telInterval);
  }, []);

  // Tell Electron what height to set based on state
  useEffect(() => {
    try {
      if (typeof window !== 'undefined' && (window as any).electronAPI) {
        if (expanded) {
          (window as any).electronAPI.setIslandExpanded(true, 300);
        } else {
          (window as any).electronAPI.setIslandExpanded(false, 52);
        }
      }
    } catch {
      // Browser context
    }
    if (expanded && inputRef.current && !recentResponse) {
      setTimeout(() => inputRef.current?.focus(), 120);
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

  const copyRecentResponse = () => {
    if (!recentResponse) return;
    navigator.clipboard.writeText(recentResponse);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
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
      return (
        <div className="relative flex items-center justify-center">
          <Mic className="w-3.5 h-3.5 text-cyan-300 animate-pulse" />
          <span className="absolute -inset-1 rounded-full bg-cyan-400/30 animate-ping" />
        </div>
      );
    }
    switch (islandState) {
      case 'listening':
        return <Mic className="w-3.5 h-3.5 text-cyan-400 animate-pulse" />;
      case 'thinking':
        return <BrainCircuit className="w-3.5 h-3.5 text-purple-400 animate-spin" />;
      case 'executing':
        return <CheckCircle className="w-3.5 h-3.5 text-emerald-400 animate-pulse" />;
      case 'browser':
        return <Globe className="w-3.5 h-3.5 text-sky-400 animate-pulse" />;
      case 'desktop':
        return <Monitor className="w-3.5 h-3.5 text-indigo-400 animate-pulse" />;
      case 'vision':
        return <ScanEye className="w-3.5 h-3.5 text-cyan-300 animate-pulse" />;
      case 'error':
        return <XCircle className="w-3.5 h-3.5 text-rose-500 animate-bounce" />;
      default:
        return (
          <div className="relative flex items-center justify-center">
            <span className="w-2.5 h-2.5 rounded-full bg-gradient-to-tr from-cyan-500 to-cyan-300 shadow-[0_0_10px_#22d3ee] animate-pulse" />
            <span className="absolute w-4 h-4 rounded-full bg-cyan-400/20 animate-ping" />
          </div>
        );
    }
  };

  // Dynamic Height calculation
  const expandedHeight = recentResponse ? 215 : showFolderPicker ? 220 : 188;

  // Spring physics constants
  const springTransition = {
    type: "spring" as const,
    stiffness: 410,
    damping: 30,
    mass: 0.8
  };

  const isVoiceActive = isListening || islandState === 'voice-listening';

  return (
    <div className="w-full h-full m-0 p-0 overflow-hidden bg-transparent select-none flex items-center justify-center">
      {/* Liquid Capsule Morph Container */}
      <motion.div
        layout
        initial={false}
        animate={
          expanded
            ? { width: 490, height: expandedHeight, borderRadius: 24 }
            : { width: 330, height: 44, borderRadius: 22 }
        }
        transition={springTransition}
        onClick={() => !expanded && setExpanded(true)}
        className={clsx(
          "relative overflow-hidden cursor-pointer flex flex-col justify-between",
          "bg-[#03060a] transition-colors duration-200",
          isVoiceActive
            ? "border border-cyan-400 shadow-[inset_0_1px_2px_rgba(255,255,255,0.35),inset_0_0_15px_rgba(6,182,212,0.25)]"
            : islandState === 'thinking'
            ? "border border-purple-400 shadow-[inset_0_1px_2px_rgba(255,255,255,0.35),inset_0_0_15px_rgba(168,85,247,0.25)]"
            : islandState === 'executing'
            ? "border border-emerald-400 shadow-[inset_0_1px_2px_rgba(255,255,255,0.35),inset_0_0_15px_rgba(16,185,129,0.25)]"
            : "border border-cyan-400/50 hover:border-cyan-400/80 shadow-[inset_0_1px_1.5px_rgba(255,255,255,0.22),inset_0_0_12px_rgba(6,182,212,0.1)]",
          "before:absolute before:inset-x-8 before:top-0 before:h-[1px] before:bg-gradient-to-r before:from-transparent before:via-cyan-300/70 before:to-transparent"
        )}
      >
        {/* Top Header / Collapsed Capsule Bar */}
        <div className="flex items-center justify-between px-3.5 h-[44px] w-full shrink-0">
          {/* Left: Status Icon & Live Label */}
          <div className="flex items-center gap-2.5 overflow-hidden">
            <div className="w-5 h-5 flex items-center justify-center shrink-0">
              {getStatusIcon()}
            </div>

            <AnimatePresence mode="wait">
              <motion.div
                key={
                  isVoiceActive
                    ? 'voice-listening'
                    : islandState === 'idle'
                    ? 'idle-text'
                    : (islandMessage || islandState)
                }
                initial={{ opacity: 0, y: 4 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -4 }}
                transition={{ duration: 0.16 }}
                className={clsx(
                  "font-medium tracking-wide truncate flex items-center gap-1.5",
                  expanded ? "text-xs text-white max-w-[260px]" : "text-xs text-white max-w-[170px]"
                )}
              >
                {isVoiceActive ? (
                  <span className="text-cyan-300 font-semibold flex items-center gap-1.5 animate-pulse">
                    <span className="w-1.5 h-1.5 rounded-full bg-cyan-400" />
                    {islandMessage || (isListening ? "Listening..." : "Listening to you, Boss...")}
                  </span>
                ) : islandState === 'idle' ? (
                  <span className="bg-gradient-to-r from-white via-slate-100 to-cyan-300 bg-clip-text text-transparent font-semibold flex items-center gap-1.5">
                    <span>ADA</span>
                    <span className="text-cyan-500/80">•</span>
                    <span className="text-cyan-200/90 font-normal">NEURAL LINK</span>
                  </span>
                ) : (
                  <span className="text-cyan-300 font-semibold truncate">
                    {islandMessage || islandState.toUpperCase()}
                  </span>
                )}
              </motion.div>
            </AnimatePresence>
          </div>

          {/* Right Header Controls */}
          {!expanded ? (
            <div className="flex items-center gap-2">
              {/* Interactive Voice Mic Button */}
              <button
                onClick={toggleVoiceMode}
                title="Trigger Voice Directive"
                className={clsx(
                  "p-1.5 rounded-full transition-all duration-200 flex items-center justify-center",
                  isListening
                    ? "bg-cyan-500/30 text-cyan-300 shadow-[0_0_12px_#06b6d4]"
                    : "text-white/60 hover:text-cyan-300 hover:bg-white/10"
                )}
              >
                <Mic className="w-3.5 h-3.5" />
              </button>

              {/* 5-Bar Liquid Dancing Equalizer */}
              <div className="flex gap-1 items-end h-3.5 px-0.5">
                {[
                  { color: "bg-cyan-400", activeDur: 0.45, idleDur: 1.1, activeH: [4, 15, 6, 17, 4], idleH: [3, 9, 4, 8, 3] },
                  { color: "bg-sky-400", activeDur: 0.55, idleDur: 1.3, activeH: [8, 4, 16, 7, 8], idleH: [5, 3, 11, 4, 5] },
                  { color: "bg-indigo-400", activeDur: 0.4, idleDur: 1.0, activeH: [14, 6, 18, 5, 14], idleH: [7, 12, 5, 9, 7] },
                  { color: "bg-purple-400", activeDur: 0.6, idleDur: 1.4, activeH: [6, 17, 5, 13, 6], idleH: [4, 7, 10, 3, 4] },
                  { color: "bg-cyan-300", activeDur: 0.5, idleDur: 1.2, activeH: [10, 5, 15, 8, 10], idleH: [3, 8, 4, 11, 3] }
                ].map((bar, idx) => (
                  <motion.span
                    key={idx}
                    animate={{ height: isVoiceActive ? bar.activeH : bar.idleH }}
                    transition={{ repeat: Infinity, duration: isVoiceActive ? bar.activeDur : bar.idleDur, ease: "easeInOut" }}
                    className={clsx("w-[2px] rounded-full", bar.color)}
                  />
                ))}
              </div>

              {/* Hotkey Badge */}
              <kbd className="text-[10px] text-cyan-200 font-mono font-semibold px-2 py-0.5 rounded-full bg-cyan-950/80 border border-cyan-500/40 shadow-[0_0_8px_rgba(6,182,212,0.15)]">
                Alt+Space
              </kbd>
            </div>
          ) : (
            <div className="flex items-center gap-1.5" onClick={(e) => e.stopPropagation()}>
              {/* Voice toggle pill */}
              <button
                onClick={toggleVoiceMode}
                title={isListening ? "Mute Voice" : "Activate Voice"}
                className={clsx(
                  "px-2.5 py-1 rounded-lg text-[10px] font-semibold transition-all flex items-center gap-1.5",
                  isListening
                    ? "bg-cyan-500/30 text-cyan-300 border border-cyan-400/50 shadow-[0_0_12px_rgba(6,182,212,0.3)] animate-pulse"
                    : "text-white/70 hover:text-cyan-300 hover:bg-white/10 border border-transparent"
                )}
              >
                <Mic className="w-3 h-3" />
                <span>{isListening ? "Listening" : "Voice"}</span>
              </button>

              {/* Open Dashboard button */}
              <button
                onClick={openMainDashboard}
                title="Open Master HUD Dashboard"
                className="p-1.5 rounded-lg text-white/50 hover:text-cyan-300 hover:bg-white/10 transition-colors"
              >
                <ExternalLink className="w-3.5 h-3.5" />
              </button>

              {/* Minimize Island */}
              <button
                onClick={() => {
                  setExpanded(false);
                  setShowFolderPicker(false);
                  setRecentResponse(null);
                }}
                title="Minimize Capsule (Esc)"
                className="p-1.5 rounded-lg text-white/50 hover:text-white hover:bg-white/10 transition-colors"
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
              initial={{ opacity: 0, scale: 0.97, y: -4 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.97, y: -4 }}
              transition={{ duration: 0.18, ease: "easeOut" }}
              className="flex-1 px-3.5 pb-2.5 flex flex-col justify-between"
              onClick={(e) => e.stopPropagation()}
            >
              {/* Live Audio Reactive Visualizer (When Voice is Active) */}
              {isListening && (
                <div className="mb-1.5 px-3 py-1.5 rounded-xl bg-gradient-to-r from-cyan-950/50 via-slate-900/60 to-purple-950/40 border border-cyan-500/35 flex items-center justify-between shadow-[0_0_15px_rgba(6,182,212,0.12)]">
                  <div className="flex items-center gap-2.5 overflow-hidden">
                    <div className="flex gap-0.5 items-end h-4 shrink-0">
                      {[0.3, 0.6, 0.9, 0.5, 1.0, 0.7, 0.4, 0.8, 0.6, 0.9, 0.3, 0.7, 0.5, 0.4].map((scale, i) => (
                        <motion.span
                          key={i}
                          animate={{
                            height: Math.max(3, Math.round((amplitude * 32 + 3) * scale))
                          }}
                          transition={{ duration: 0.07 }}
                          className="w-[2px] bg-gradient-to-t from-cyan-500 to-cyan-300 rounded-full"
                        />
                      ))}
                    </div>
                    <span className="text-[11px] text-cyan-200 font-mono truncate">
                      {interimTranscript || "Listening... Speak your command"}
                    </span>
                  </div>
                  <button
                    onClick={toggleListening}
                    className="px-2 py-0.5 rounded text-[10px] bg-cyan-500/25 hover:bg-cyan-500/40 text-cyan-300 font-semibold border border-cyan-500/40 shrink-0 transition-colors"
                  >
                    Done
                  </button>
                </div>
              )}

              {/* Contextual Presentation 1: Dedicated Response & Briefing View */}
              {recentResponse ? (
                <div className="flex flex-col gap-2 my-auto">
                  <div className="p-3 rounded-xl bg-gradient-to-r from-cyan-950/45 via-slate-900/70 to-purple-950/40 border border-cyan-500/35 shadow-[inset_0_1px_1px_rgba(255,255,255,0.15)] flex items-start justify-between gap-3">
                    <div className="flex items-start gap-2.5 overflow-hidden">
                      <div className="p-1 rounded-lg bg-cyan-500/20 border border-cyan-500/30 shrink-0 mt-0.5">
                        <Volume2 className="w-3.5 h-3.5 text-cyan-300 animate-pulse" />
                      </div>
                      <p className="text-[12px] text-white/95 leading-relaxed font-sans font-normal line-clamp-3 select-text">
                        {recentResponse}
                      </p>
                    </div>
                    <div className="flex items-center gap-1 shrink-0">
                      <button
                        onClick={copyRecentResponse}
                        title="Copy Response"
                        className="text-white/40 hover:text-cyan-300 p-1 rounded-lg hover:bg-white/10 transition-colors"
                      >
                        {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                      </button>
                      <button
                        onClick={() => setRecentResponse(null)}
                        title="Dismiss"
                        className="text-white/40 hover:text-white p-1 rounded-lg hover:bg-white/10 transition-colors"
                      >
                        <X className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 overflow-x-auto no-scrollbar">
                    <motion.button
                      whileHover={{ scale: 1.03 }}
                      whileTap={{ scale: 0.96 }}
                      onClick={() => {
                        setRecentResponse(null);
                        if (inputRef.current) setTimeout(() => inputRef.current?.focus(), 80);
                      }}
                      className="px-2.5 py-1 rounded-lg text-[11px] font-semibold bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-300 border border-cyan-500/40 flex items-center gap-1.5 shrink-0 transition-colors"
                    >
                      <ArrowUp className="w-3 h-3 rotate-45" />
                      Follow-up
                    </motion.button>

                    <motion.button
                      whileHover={{ scale: 1.03 }}
                      whileTap={{ scale: 0.96 }}
                      onClick={() => handleDispatch("give me my morning briefing")}
                      className="px-2.5 py-1 rounded-lg text-[11px] font-medium bg-amber-500/15 hover:bg-amber-500/25 text-amber-300 border border-amber-500/30 flex items-center gap-1.5 shrink-0 transition-colors"
                    >
                      <Zap className="w-3 h-3 text-amber-400" />
                      Refresh Briefing
                    </motion.button>

                    {phoneStats.connected && (
                      <motion.button
                        whileHover={{ scale: 1.03 }}
                        whileTap={{ scale: 0.96 }}
                        onClick={() => handleDispatch("check my phone status")}
                        className="px-2.5 py-1 rounded-lg text-[11px] font-medium bg-emerald-500/15 hover:bg-emerald-500/25 text-emerald-300 border border-emerald-500/30 flex items-center gap-1.5 shrink-0 transition-colors"
                      >
                        <Smartphone className="w-3 h-3 text-emerald-400" />
                        Phone: {phoneStats.battery ? `${phoneStats.battery}%` : 'Linked'}
                      </motion.button>
                    )}

                    <motion.button
                      whileHover={{ scale: 1.03 }}
                      whileTap={{ scale: 0.96 }}
                      onClick={openMainDashboard}
                      className="px-2.5 py-1 rounded-lg text-[11px] font-medium bg-white/[0.05] hover:bg-white/10 text-white/80 hover:text-white border border-white/[0.1] flex items-center gap-1.5 shrink-0 ml-auto transition-colors"
                    >
                      <ExternalLink className="w-3 h-3 text-cyan-400" />
                      Dashboard
                    </motion.button>
                  </div>
                </div>
              ) : (
                /* Contextual Presentation 2: Spotlight Command Input & Quick Chips */
                <>
                  {/* Spotlight Command Input Bar */}
                  <form onSubmit={handleSubmit} className="relative w-full">
                    <div className="relative flex items-center">
                      <input
                        ref={inputRef}
                        type="text"
                        value={inputValue}
                        onChange={(e) => setInputValue(e.target.value)}
                        placeholder="Ask ADA anything (e.g. organize desktop, briefing, lock laptop)..."
                        className={clsx(
                          "w-full h-8 pl-3.5 pr-16 text-xs rounded-xl text-white placeholder-white/40 font-sans",
                          "bg-white/[0.06] border border-white/[0.12] backdrop-blur-md",
                          "focus:outline-none focus:border-cyan-400/80 focus:ring-1 focus:ring-cyan-400/50 focus:shadow-[0_0_15px_rgba(6,182,212,0.25)]",
                          "transition-all duration-200"
                        )}
                      />
                      <div className="absolute right-1.5 flex items-center gap-1">
                        <button
                          type="button"
                          onClick={toggleVoiceMode}
                          title="Voice input"
                          className={clsx(
                            "w-6 h-6 rounded-lg flex items-center justify-center transition-all",
                            isListening
                              ? "bg-cyan-500 text-black shadow-[0_0_8px_#06b6d4]"
                              : "text-white/50 hover:text-cyan-300 hover:bg-white/10"
                          )}
                        >
                          <Mic className="w-3 h-3" />
                        </button>
                        <button
                          type="submit"
                          disabled={!inputValue.trim() || isSubmitting}
                          title="Execute directive (Enter)"
                          className={clsx(
                            "w-6 h-6 rounded-lg flex items-center justify-center transition-all",
                            inputValue.trim()
                              ? "bg-gradient-to-tr from-cyan-500 to-cyan-400 text-black hover:scale-105 shadow-[0_0_10px_#06b6d4]"
                              : "bg-white/5 text-white/20 cursor-not-allowed"
                          )}
                        >
                          <ArrowUp className="w-3.5 h-3.5 stroke-[2.5]" />
                        </button>
                      </div>
                    </div>
                  </form>

                  {/* Folder Selector Sub-Drawer */}
                  <AnimatePresence>
                    {showFolderPicker && (
                      <motion.div
                        initial={{ opacity: 0, height: 0, y: -4 }}
                        animate={{ opacity: 1, height: 'auto', y: 0 }}
                        exit={{ opacity: 0, height: 0, y: -4 }}
                        className="py-1 flex items-center gap-1.5 overflow-x-auto no-scrollbar"
                      >
                        <span className="text-[10px] text-white/60 shrink-0 font-medium">Target:</span>
                        {[
                          { label: 'Desktop', cmd: 'organize my desktop' },
                          { label: 'Downloads', cmd: 'organize my downloads' },
                          { label: 'Documents', cmd: 'organize my documents' },
                          { label: 'All Folders', cmd: 'organize my files' }
                        ].map((folder) => (
                          <motion.button
                            key={folder.label}
                            whileHover={{ scale: 1.04 }}
                            whileTap={{ scale: 0.95 }}
                            onClick={() => handleDispatch(folder.cmd)}
                            className="px-2 py-0.5 rounded-md text-[10px] font-medium bg-cyan-950/70 hover:bg-cyan-500/25 text-cyan-300 border border-cyan-500/40 shrink-0 transition-colors"
                          >
                            {folder.label}
                          </motion.button>
                        ))}
                        <button
                          onClick={() => setShowFolderPicker(false)}
                          className="p-1 text-white/40 hover:text-white shrink-0 ml-auto"
                        >
                          <X className="w-3 h-3" />
                        </button>
                      </motion.div>
                    )}
                  </AnimatePresence>

                  {/* Quick Action Smart Chips */}
                  <div className="flex items-center gap-1.5 overflow-x-auto pt-0.5 no-scrollbar">
                    {/* Organize Chip */}
                    <motion.button
                      whileHover={{ scale: 1.03 }}
                      whileTap={{ scale: 0.96 }}
                      onClick={() => setShowFolderPicker(!showFolderPicker)}
                      className={clsx(
                        "px-2.5 py-1 rounded-lg text-[11px] font-medium border transition-all flex items-center gap-1.5 shrink-0",
                        showFolderPicker
                          ? "bg-cyan-500/25 text-cyan-300 border-cyan-400/60 shadow-[0_0_10px_rgba(6,182,212,0.2)]"
                          : "bg-white/[0.05] hover:bg-cyan-500/20 text-white/85 hover:text-cyan-300 border-white/[0.1] hover:border-cyan-500/40"
                      )}
                    >
                      <FolderSync className="w-3 h-3 text-cyan-400" />
                      Organize
                      {showFolderPicker ? <ChevronUp className="w-2.5 h-2.5" /> : <ChevronDown className="w-2.5 h-2.5" />}
                    </motion.button>

                    {/* Briefing Chip */}
                    <motion.button
                      whileHover={{ scale: 1.03 }}
                      whileTap={{ scale: 0.96 }}
                      onClick={() => handleDispatch("give me my morning briefing")}
                      className="px-2.5 py-1 rounded-lg text-[11px] font-medium bg-white/[0.05] hover:bg-amber-500/20 text-white/85 hover:text-amber-300 border border-white/[0.1] hover:border-amber-500/40 flex items-center gap-1.5 shrink-0 transition-all"
                    >
                      <Zap className="w-3 h-3 text-amber-400" />
                      Briefing
                    </motion.button>

                    {/* Phone Bridge Live Chip */}
                    <motion.button
                      whileHover={{ scale: 1.03 }}
                      whileTap={{ scale: 0.96 }}
                      onClick={() => {
                        if (phoneStats.connected) {
                          handleDispatch("check my phone status");
                        } else {
                          handleDispatch("connect to my phone");
                        }
                      }}
                      className={clsx(
                        "px-2.5 py-1 rounded-lg text-[11px] font-medium border flex items-center gap-1.5 shrink-0 transition-all",
                        phoneStats.connected
                          ? "bg-emerald-950/40 hover:bg-emerald-500/20 text-emerald-300 border-emerald-500/40"
                          : "bg-white/[0.05] hover:bg-white/10 text-white/70 border-white/[0.1]"
                      )}
                    >
                      <Smartphone className={clsx("w-3 h-3", phoneStats.connected ? "text-emerald-400" : "text-white/50")} />
                      {phoneStats.connected ? (
                        <span>Phone: {phoneStats.battery ? `${phoneStats.battery}%` : 'Linked'}</span>
                      ) : (
                        <span>Link Phone</span>
                      )}
                    </motion.button>

                    {/* WhatsApp Fast Message Chip */}
                    <motion.button
                      whileHover={{ scale: 1.03 }}
                      whileTap={{ scale: 0.96 }}
                      onClick={() => {
                        setInputValue("msg ");
                        setShowFolderPicker(false);
                        inputRef.current?.focus();
                      }}
                      className="px-2.5 py-1 rounded-lg text-[11px] font-medium bg-white/[0.05] hover:bg-green-500/20 text-white/85 hover:text-green-300 border border-white/[0.1] hover:border-green-500/40 flex items-center gap-1.5 shrink-0 transition-all"
                    >
                      <MessageSquare className="w-3 h-3 text-green-400" />
                      Message
                    </motion.button>

                    {/* Fast Lock Workstation Chip */}
                    <motion.button
                      whileHover={{ scale: 1.03 }}
                      whileTap={{ scale: 0.96 }}
                      onClick={() => handleDispatch("lock my laptop")}
                      title="Sub-Second Lock Laptop"
                      className="px-2.5 py-1 rounded-lg text-[11px] font-medium bg-rose-500/10 hover:bg-rose-500/25 text-rose-300 border border-rose-500/30 flex items-center gap-1.5 shrink-0 transition-all ml-auto"
                    >
                      <Shield className="w-3 h-3 text-rose-400" />
                      Lock PC
                    </motion.button>
                  </div>
                </>
              )}

              {/* Futuristic Micro-Telemetry Footer */}
              <div className="flex items-center justify-between text-[10px] text-white/40 pt-1.5 border-t border-white/[0.08] font-mono">
                <span className="flex items-center gap-1.5">
                  <span className={clsx(
                    "w-1.5 h-1.5 rounded-full",
                    isVoiceActive ? "bg-cyan-400 animate-ping" : "bg-cyan-400 shadow-[0_0_6px_#22d3ee]"
                  )} />
                  <span className="text-white/60">SYS:</span>
                  <span className="text-cyan-400 uppercase font-semibold">
                    {isVoiceActive ? "VOICE ACTIVE" : recentResponse ? "INTEL READY" : islandState}
                  </span>
                </span>

                <span className="flex items-center gap-1 text-cyan-300/70">
                  <Sparkles className="w-2.5 h-2.5 text-cyan-400" />
                  <span>SUB-1S FAST-PATH</span>
                </span>

                <span className="flex items-center gap-2 text-white/40">
                  {currentTime && (
                    <span className="flex items-center gap-1 text-white/60">
                      <Clock className="w-2.5 h-2.5 text-cyan-400" />
                      {currentTime}
                    </span>
                  )}
                  <span className="text-cyan-400/80 font-bold">ADA v1.0</span>
                </span>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>
    </div>
  );
};
