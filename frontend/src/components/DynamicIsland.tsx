import React, { useState, useEffect, useRef, useCallback } from 'react';
import { motion } from 'framer-motion';
import { useNovaStore } from '../store/useNovaStore';
import { useNovaWebSocket } from '../contexts/NovaWebSocket';
import { useVoiceRecognition } from '../hooks/useVoiceRecognition';
import {
  Mic, ArrowUp, ChevronUp,
  MessageSquare, Volume2,
  Smartphone, Shield, Sparkles,
  Play, Pause, SkipForward, SkipBack, Music,
  Palette, Activity, Wifi, Cpu, Laptop, Zap,
  Pin, PinOff, RotateCcw, Move
} from 'lucide-react';
import clsx from 'clsx';
import { SquigglyWave } from './SquigglyWave';

interface PhoneTelemetry {
  connected: boolean;
  battery: number | null;
  deviceId: string | null;
}

interface HardwareTelemetry {
  cpu: {
    percent: number;
    threads: number;
    cores: number;
    freq_ghz: number;
  };
  memory: {
    total_gb: number;
    used_gb: number;
    percent: number;
  };
  gpu: {
    name: string;
    temp: number;
    util: number;
  };
  laptop_battery: {
    percent: number;
    plugged: boolean;
  };
  display: {
    hz: number;
    resolution: string;
  };
  network: {
    sent_mb: number;
    recv_mb: number;
  };
}

interface MediaTrack {
  title: string;
  artist: string;
  album: string;
  status: 'playing' | 'paused' | 'stopped' | 'idle';
  app: string;
  position: number;
  duration: number;
  thumbnail: string | null;
}

type IslandTab = 'music' | 'gaming';

export const DynamicIsland: React.FC = () => {
  const { islandState, setIslandState } = useNovaStore();
  const { sendChat } = useNovaWebSocket();
  const [expanded, setExpanded] = useState(false);
  const [activeTab, setActiveTab] = useState<IslandTab>('music');
  const [inputValue, setInputValue] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [recentResponse, setRecentResponse] = useState<string | null>(null);
  const [currentTime, setCurrentTime] = useState('');
  const [paletteMode, setPaletteMode] = useState<'pink' | 'cyan' | 'amber'>('pink');
  const [isPinned, setIsPinned] = useState(false);
  
  // Media State
  const [currentMedia, setCurrentMedia] = useState<MediaTrack | null>(null);
  const [playbackPos, setPlaybackPos] = useState<number>(0);
  const [volumeLevel, setVolumeLevel] = useState<number>(50);

  // Live Telemetry
  const [telemetry, setTelemetry] = useState<HardwareTelemetry>({
    cpu: { percent: 18, threads: 16, cores: 10, freq_ghz: 2.4 },
    memory: { total_gb: 15.7, used_gb: 12.6, percent: 80 },
    gpu: { name: 'NVIDIA GeForce RTX 3050 6GB Laptop GPU', temp: 59, util: 0 },
    laptop_battery: { percent: 100, plugged: true },
    display: { hz: 144, resolution: '1920x1080' },
    network: { sent_mb: 0, recv_mb: 0 }
  });

  const [phoneStats, setPhoneStats] = useState<PhoneTelemetry>({
    connected: false,
    battery: null,
    deviceId: null
  });

  const inputRef = useRef<HTMLInputElement>(null);

  // Dragging state
  const isDraggingRef = useRef(false);
  const dragStartRef = useRef({ x: 0, y: 0 });

  // Voice Recognition Hook
  const {
    isListening,
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
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  // Poll Media Controller (Real Windows GSMTC)
  useEffect(() => {
    let isMounted = true;
    const fetchMedia = async () => {
      try {
        const res = await fetch('http://127.0.0.1:8000/api/system/media/current');
        if (!res.ok) return;
        const data = await res.json();
        if (isMounted) {
          const track = data.media || data;
          if (track && track.title) {
            setCurrentMedia(track);
            setPlaybackPos(track.position || 0);
          } else {
            setCurrentMedia(null);
          }
        }
      } catch {
        // Backend offline / media idle
      }
    };

    fetchMedia();
    const pollInterval = setInterval(fetchMedia, 2000);
    return () => {
      isMounted = false;
      clearInterval(pollInterval);
    };
  }, []);

  // Fetch initial master volume
  useEffect(() => {
    fetch('http://127.0.0.1:8000/api/system/volume')
      .then(r => r.json())
      .then(d => {
        if (typeof d.volume === 'number') {
          setVolumeLevel(d.volume);
        }
      })
      .catch(() => {});
  }, []);

  // Smooth 1-second client-side playback ticker
  useEffect(() => {
    if (!currentMedia || currentMedia.status !== 'playing') return;
    const ticker = setInterval(() => {
      setPlaybackPos((prev) => {
        if (currentMedia.duration > 0 && prev >= currentMedia.duration) {
          return currentMedia.duration;
        }
        return prev + 1;
      });
    }, 1000);
    return () => clearInterval(ticker);
  }, [currentMedia?.status, currentMedia?.duration]);

  // Poll Real Hardware Telemetry (psutil + nvidia-smi + windows display + phone)
  useEffect(() => {
    let isMounted = true;
    const fetchTelemetry = async () => {
      try {
        const res = await fetch('http://127.0.0.1:8000/api/telemetry');
        if (!res.ok) return;
        const data = await res.json();
        if (!isMounted) return;

        if (data.cpu || data.memory || data.gpu) {
          setTelemetry({
            cpu: data.cpu || { percent: 18, threads: 16, cores: 10, freq_ghz: 2.4 },
            memory: data.memory || { total_gb: 15.7, used_gb: 12.6, percent: 80 },
            gpu: data.gpu || { name: 'NVIDIA GeForce RTX 3050 6GB Laptop GPU', temp: 59, util: 0 },
            laptop_battery: data.laptop_battery || { percent: 100, plugged: true },
            display: data.display || { hz: 144, resolution: '1920x1080' },
            network: data.network || { sent_mb: 0, recv_mb: 0 }
          });
        }

        if (data.phone) {
          setPhoneStats({
            connected: !!data.phone.connected,
            battery: data.phone.battery ?? (data.phone.connected ? 80 : null),
            deviceId: data.phone.device_id || null
          });
        }
      } catch {
        // Fallback
      }
    };
    fetchTelemetry();
    const pollInterval = setInterval(fetchTelemetry, 2500);
    return () => {
      isMounted = false;
      clearInterval(pollInterval);
    };
  }, []);

  // Media Controls (Fixed: POST /api/system/media/control)
  const handleMediaControl = async (e: React.MouseEvent | undefined, action: 'toggle' | 'next' | 'prev') => {
    e?.stopPropagation();
    try {
      await fetch('http://127.0.0.1:8000/api/system/media/control', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action })
      });
      if (action === 'toggle' && currentMedia) {
        setCurrentMedia({
          ...currentMedia,
          status: currentMedia.status === 'playing' ? 'paused' : 'playing'
        });
      }
    } catch {
      // Backend offline
    }
  };

  // Seek Media Position via GSMTC
  const handleSeek = async (newProgress: number) => {
    if (!currentMedia || currentMedia.duration <= 0) return;
    const targetSeconds = newProgress * currentMedia.duration;
    setPlaybackPos(targetSeconds);
    try {
      await fetch('http://127.0.0.1:8000/api/system/media/seek', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ position: targetSeconds })
      });
    } catch {
      // Offline fallback
    }
  };

  // Adjust Master Windows Volume
  const handleVolumeChange = async (pct: number) => {
    setVolumeLevel(pct);
    try {
      await fetch('http://127.0.0.1:8000/api/system/volume', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ volume: pct })
      });
    } catch {
      // Offline fallback
    }
  };

  // Toggle Pinned Mode
  const togglePin = (e: React.MouseEvent) => {
    e.stopPropagation();
    const nextPin = !isPinned;
    setIsPinned(nextPin);
    try {
      if ((window as any).electronAPI?.setIslandPinned) {
        (window as any).electronAPI.setIslandPinned(nextPin);
      }
    } catch {}
  };

  // Reset Island Position to Top Center
  const handleResetPosition = (e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      if ((window as any).electronAPI?.resetIslandPosition) {
        (window as any).electronAPI.resetIslandPosition();
      }
    } catch {}
  };

  // Mouse Dragging for Window Repositioning
  const handleDragPointerDown = useCallback((e: React.PointerEvent) => {
    e.preventDefault();
    isDraggingRef.current = true;
    dragStartRef.current = { x: e.screenX, y: e.screenY };

    const handlePointerMove = (moveEvt: PointerEvent) => {
      if (!isDraggingRef.current) return;
      const dx = moveEvt.screenX - dragStartRef.current.x;
      const dy = moveEvt.screenY - dragStartRef.current.y;
      dragStartRef.current = { x: moveEvt.screenX, y: moveEvt.screenY };

      try {
        if ((window as any).electronAPI?.moveIsland) {
          (window as any).electronAPI.moveIsland(dx, dy);
        }
      } catch {}
    };

    const handlePointerUp = () => {
      isDraggingRef.current = false;
      window.removeEventListener('pointermove', handlePointerMove);
      window.removeEventListener('pointerup', handlePointerUp);
    };

    window.addEventListener('pointermove', handlePointerMove);
    window.addEventListener('pointerup', handlePointerUp);
  }, []);

  // Launch Wireless Touchpad on Phone
  const handleLaunchTouchpad = async (e?: React.MouseEvent) => {
    e?.stopPropagation();
    try {
      const res = await fetch('http://127.0.0.1:8000/api/devices/touchpad/launch', { method: 'POST' });
      if (res.ok) {
        setRecentResponse("Wireless Trackpad opened on POCO phone!");
      }
    } catch {
      // Offline fallback
    }
  };

  // Expanded height: 425px gives generous clearance for all 4 cards, input bar, and chips
  const expandedHeight = activeTab === 'gaming' ? 425 : 335;

  // Inform Electron of dynamic bounds
  useEffect(() => {
    try {
      if (typeof window !== 'undefined' && (window as any).electronAPI) {
        if (expanded) {
          (window as any).electronAPI.setIslandExpanded(true, expandedHeight);
        } else {
          (window as any).electronAPI.setIslandExpanded(false, 44);
        }
      }
    } catch {
      // Browser preview context
    }
    if (expanded && inputRef.current && !recentResponse) {
      setTimeout(() => inputRef.current?.focus(), 120);
    }
  }, [expanded, expandedHeight, recentResponse]);

  // Global shortcuts
  useEffect(() => {
    if (typeof window !== 'undefined' && (window as any).electronAPI?.onShortcutTriggered) {
      (window as any).electronAPI.onShortcutTriggered((action: string) => {
        if (action === 'toggle') {
          setExpanded((prev) => !prev);
        } else if (action === 'expand') {
          setExpanded(true);
        } else if (action === 'collapse') {
          setExpanded(false);
          setRecentResponse(null);
        }
      });
    }

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' || (e.altKey && (e.code === 'Space' || e.key === ' '))) {
        e.preventDefault();
        setExpanded(false);
        setRecentResponse(null);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const handleDispatch = async (text: string) => {
    if (!text.trim() || isSubmitting) return;
    setIsSubmitting(true);
    setRecentResponse(null);
    setIslandState('thinking', `Processing: "${text.slice(0, 24)}..."`);

    try {
      const res = await fetch('http://127.0.0.1:8000/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text })
      });
      if (res.ok) {
        const data = await res.json();
        const responseText = data.response || "Task executed successfully.";
        setRecentResponse(responseText);
        setIslandState('executing', responseText);
        setInputValue('');
      } else {
        setIslandState('idle', 'Execution completed.');
      }
    } catch {
      sendChat(text);
      setRecentResponse("Action dispatched to ADA kernel.");
      setIslandState('idle');
      setInputValue('');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    handleDispatch(inputValue);
  };

  const formatTime = (secs: number) => {
    const s = Math.max(0, Math.floor(secs));
    const m = Math.floor(s / 60);
    const rem = s % 60;
    return `${m}:${rem < 10 ? '0' : ''}${rem}`;
  };

  const isVoiceActive = islandState === 'voice-listening' || isListening;
  const themeColor = paletteMode === 'pink' ? '#f472b6' : paletteMode === 'cyan' ? '#22d3ee' : '#f59e0b';
  const themeAccentClass = paletteMode === 'pink' ? 'text-rose-400' : paletteMode === 'cyan' ? 'text-cyan-400' : 'text-amber-400';

  return (
    <div className="fixed top-0 left-0 w-full flex justify-center pointer-events-none z-[999999] select-none font-sans">
      <motion.div
        layout
        initial={{ y: -50, opacity: 0, scale: 0.96 }}
        animate={{
          y: 6,
          opacity: 1,
          scale: 1,
          width: expanded ? 516 : (currentMedia ? 336 : 240), // More compact idle pill
          height: expanded ? expandedHeight : 44
        }}
        transition={{
          type: 'spring',
          stiffness: 420,
          damping: 36,
          mass: 0.8
        }}
        className={clsx(
          "pointer-events-auto overflow-hidden relative flex flex-col justify-start",
          "rounded-[26px] border border-white/12 shadow-[0_25px_60px_rgba(0,0,0,0.98)]",
          "bg-[#0a0b10] text-white", // Solid OLED Dark (NO transparency)
          expanded ? "ring-1 ring-white/15" : "hover:border-white/25 transition-all cursor-pointer"
        )}
        style={{ transformOrigin: "top center" }}
        onClick={() => !expanded && setExpanded(true)}
      >
        {/* Ambient Top Glow Accent */}
        <div
          className="absolute -top-10 left-1/2 -translate-x-1/2 w-48 h-12 rounded-full blur-2xl pointer-events-none opacity-30 transition-colors duration-500"
          style={{ backgroundColor: themeColor }}
        />

        {/* ---------------- COLLAPSED PILL STATE ---------------- */}
        {!expanded ? (
          <div className="w-full h-11 px-3 flex items-center justify-between gap-2 select-none">
            {/* Movable Drag Grip on Left */}
            <div
              onPointerDown={handleDragPointerDown}
              className="p-1 text-white/30 hover:text-white/80 cursor-grab active:cursor-grabbing transition-colors"
              title="Drag to reposition Dynamic Island anywhere"
              style={{ WebkitAppRegion: 'no-drag' } as any}
            >
              <Move className="w-3 h-3" />
            </div>

            {/* Middle: Indicator or Album Art */}
            <div className="flex items-center gap-2 min-w-0 flex-1">
              {currentMedia ? (
                <div className="w-6 h-6 rounded-lg overflow-hidden bg-zinc-900 border border-white/10 shrink-0 flex items-center justify-center relative">
                  {currentMedia.thumbnail ? (
                    <img src={currentMedia.thumbnail} alt={currentMedia.title} className="w-full h-full object-cover" />
                  ) : (
                    <div className="w-full h-full bg-gradient-to-tr from-purple-600 to-pink-500 flex items-center justify-center">
                      <Music className="w-3 h-3 text-white" />
                    </div>
                  )}
                  <span className={clsx(
                    "w-1.5 h-1.5 rounded-full absolute bottom-0.5 right-0.5 ring-1 ring-black",
                    currentMedia.status === 'playing' ? "bg-emerald-400" : "bg-amber-400"
                  )} />
                </div>
              ) : (
                <span className={clsx(
                  "w-2 h-2 rounded-full shrink-0",
                  isVoiceActive ? "bg-cyan-400 animate-ping" : "bg-cyan-400 shadow-[0_0_8px_#22d3ee]"
                )} />
              )}

              <span className="text-[12px] font-semibold text-white/90 truncate tracking-tight">
                {currentMedia ? currentMedia.title : "ADA • NEURAL LINK"}
              </span>
            </div>

            {/* Right: Sound Wave or Shortcut Hint */}
            <div className="flex items-center gap-1.5 shrink-0" style={{ WebkitAppRegion: 'no-drag' } as any}>
              {currentMedia && currentMedia.status === 'playing' ? (
                <div className="flex gap-0.5 items-end h-3 px-1">
                  {[0.5, 0.7, 0.45, 0.65].map((dur, i) => (
                    <motion.span
                      key={i}
                      animate={{ height: [3, 10, 4, 12, 3] }}
                      transition={{ repeat: Infinity, duration: dur, ease: "easeInOut" }}
                      className="w-[2px] rounded-full"
                      style={{ backgroundColor: themeColor }}
                    />
                  ))}
                </div>
              ) : (
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    toggleListening();
                  }}
                  className={clsx(
                    "p-1 rounded-full transition-colors cursor-pointer",
                    isVoiceActive ? "bg-cyan-500/20 text-cyan-300" : "hover:bg-white/10 text-white/60"
                  )}
                >
                  <Mic className="w-3.5 h-3.5" />
                </button>
              )}

              <span className="text-[9px] font-mono font-medium px-1.5 py-0.5 rounded-md bg-white/[0.08] text-white/50 border border-white/[0.06]">
                Alt+Space
              </span>
            </div>
          </div>
        ) : (
          /* ---------------- EXPANDED ISLAND STATE ---------------- */
          <div className="w-full flex-1 flex flex-col p-3 overflow-hidden select-none">
            {/* 0. MOVABLE DRAG GRIP BAR (DRAG TO MOVE ISLAND ANYWHERE ON SCREEN) */}
            <div
              onPointerDown={handleDragPointerDown}
              className="w-full flex justify-center pb-1 -mt-1 cursor-grab active:cursor-grabbing group select-none"
              title="Click & Drag to reposition Dynamic Island. Double-click to re-center."
              onDoubleClick={handleResetPosition}
              style={{ WebkitAppRegion: 'no-drag' } as any}
            >
              <div className="w-16 h-1.5 bg-white/25 rounded-full group-hover:bg-white/50 transition-colors flex items-center justify-center">
                <span className="w-1 h-1 rounded-full bg-white/40" />
              </div>
            </div>

            {/* 1. CLEAN TOP TABS BAR (MUSIC & GAMING/STATS ONLY) */}
            <div
              className="flex items-center justify-between pb-2 mb-2 border-b border-white/[0.07] text-white/50"
              style={{ WebkitAppRegion: 'no-drag' } as any}
            >
              <div className="flex items-center gap-2">
                {/* Tab 1: Music Player */}
                <button
                  type="button"
                  onClick={(e) => { e.stopPropagation(); setActiveTab('music'); }}
                  className={clsx(
                    "px-3 py-1 rounded-full text-xs font-semibold flex items-center gap-1.5 transition-all cursor-pointer pointer-events-auto",
                    activeTab === 'music'
                      ? "bg-white/15 text-white border border-white/20 shadow-sm"
                      : "text-white/60 hover:text-white hover:bg-white/5"
                  )}
                >
                  <Music className="w-3.5 h-3.5" />
                  Now Playing
                </button>

                {/* Tab 2: Gaming HUD & Performance */}
                <button
                  type="button"
                  onClick={(e) => { e.stopPropagation(); setActiveTab('gaming'); }}
                  className={clsx(
                    "px-3 py-1 rounded-full text-xs font-semibold flex items-center gap-1.5 transition-all cursor-pointer pointer-events-auto",
                    activeTab === 'gaming'
                      ? "bg-white/15 text-white border border-white/20 shadow-sm"
                      : "text-white/60 hover:text-white hover:bg-white/5"
                  )}
                >
                  <Activity className="w-3.5 h-3.5 text-emerald-400" />
                  Gaming & Stats
                </button>
              </div>

              {/* Far Right: Pin, Palette Theme Pill & Collapse */}
              <div className="flex items-center gap-1.5">
                {/* Pin Island (Keep Open during games) */}
                <button
                  type="button"
                  onClick={togglePin}
                  className={clsx(
                    "p-1.5 rounded-full text-xs transition-all cursor-pointer",
                    isPinned ? "bg-cyan-500/25 text-cyan-300 border border-cyan-400/40" : "bg-white/[0.07] hover:bg-white/[0.14] text-white/60 hover:text-white"
                  )}
                  title={isPinned ? "Pinned (Stays on screen over games)" : "Pin Island (Keep open)"}
                >
                  {isPinned ? <PinOff className="w-3 h-3 text-cyan-300" /> : <Pin className="w-3 h-3" />}
                </button>

                {/* Re-center Position */}
                <button
                  type="button"
                  onClick={handleResetPosition}
                  className="p-1.5 rounded-full bg-white/[0.07] hover:bg-white/[0.14] text-white/60 hover:text-white transition-all cursor-pointer"
                  title="Reset to Top-Center"
                >
                  <RotateCcw className="w-3 h-3" />
                </button>

                {/* Accent Palette */}
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    setPaletteMode(prev => prev === 'pink' ? 'cyan' : prev === 'cyan' ? 'amber' : 'pink');
                  }}
                  className="p-1.5 rounded-full bg-white/[0.07] hover:bg-white/[0.14] text-white/70 hover:text-white transition-all cursor-pointer"
                  title="Switch Accent Theme"
                >
                  <Palette className="w-3 h-3" />
                </button>

                {/* Collapse */}
                <button
                  type="button"
                  onClick={(e) => { e.stopPropagation(); setExpanded(false); }}
                  className="p-1.5 rounded-full hover:bg-white/10 text-white/50 hover:text-white transition-colors cursor-pointer"
                  title="Collapse (Esc)"
                >
                  <ChevronUp className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>

            {/* 2. DYNAMIC CONTENT SECTION */}
            <div className="flex-1 min-h-0 flex flex-col justify-start" style={{ WebkitAppRegion: 'no-drag' } as any}>
              {/* ---------------- TAB 1: MUSIC PLAYER ---------------- */}
              {activeTab === 'music' && (
                <div className="flex flex-col gap-2.5 px-1 py-1">
                  {/* Top Row: Album Art + Song Info + Transport Controls */}
                  <div className="flex items-center gap-3.5">
                    {/* Album Art with Floating Music Badge */}
                    <div className="relative shrink-0">
                      <div className="w-[54px] h-[54px] rounded-2xl overflow-hidden bg-zinc-900 border border-white/10 shadow-lg flex items-center justify-center">
                        {currentMedia?.thumbnail ? (
                          <img src={currentMedia.thumbnail} alt={currentMedia.title} className="w-full h-full object-cover" />
                        ) : (
                          <div className="w-full h-full bg-gradient-to-b from-purple-700 via-pink-600 to-amber-400 flex items-center justify-center relative overflow-hidden">
                            <div className="w-6 h-6 rounded-full bg-amber-200/90 shadow-md shadow-amber-300/40" />
                          </div>
                        )}
                      </div>
                      {/* Floating Rounded Music Badge */}
                      <div
                        className="w-5 h-5 rounded-lg flex items-center justify-center absolute -bottom-1 -right-1 shadow-md shadow-black/80"
                        style={{ backgroundColor: themeColor }}
                      >
                        <Music className="w-3 h-3 text-black fill-black" />
                      </div>
                    </div>

                    {/* Title & Artist */}
                    <div className="flex-1 min-w-0 flex flex-col justify-center">
                      <span className="text-[14px] font-bold text-white tracking-tight truncate leading-tight">
                        {currentMedia?.title || "No Media Playing"}
                      </span>
                      <span className={clsx("text-[12px] font-medium truncate mt-0.5", themeAccentClass)}>
                        {currentMedia?.artist || (currentMedia ? currentMedia.app : "Spotify • YouTube • Browser")}
                      </span>
                    </div>

                    {/* Apple Style Transport Controls */}
                    <div className="flex items-center gap-3 shrink-0 pr-1">
                      <button
                        type="button"
                        onClick={(e) => handleMediaControl(e, 'prev')}
                        title="Previous Track"
                        className="text-white/60 hover:text-white transition-all active:scale-90 cursor-pointer p-1.5"
                      >
                        <SkipBack className="w-5 h-5 fill-current" />
                      </button>
                      <button
                        type="button"
                        onClick={(e) => handleMediaControl(e, 'toggle')}
                        title={currentMedia?.status === 'playing' ? "Pause" : "Play"}
                        className="p-2.5 rounded-full bg-white text-black hover:scale-105 active:scale-95 transition-all shadow-md shadow-white/20 cursor-pointer"
                      >
                        {currentMedia?.status === 'playing' ? (
                          <Pause className="w-4 h-4 fill-black" />
                        ) : (
                          <Play className="w-4 h-4 fill-black ml-0.5" />
                        )}
                      </button>
                      <button
                        type="button"
                        onClick={(e) => handleMediaControl(e, 'next')}
                        title="Next Track"
                        className="text-white/60 hover:text-white transition-all active:scale-90 cursor-pointer p-1.5"
                      >
                        <SkipForward className="w-5 h-5 fill-current" />
                      </button>
                    </div>
                  </div>

                  {/* Middle Row: Signature Animated Squiggly Wave Scrubber (With Real Seeking) */}
                  <div className="w-full px-0.5 pt-1">
                    <SquigglyWave
                      progress={currentMedia && currentMedia.duration > 0 ? playbackPos / currentMedia.duration : 0.28}
                      isPlaying={currentMedia?.status === 'playing'}
                      color={themeColor}
                      width={484}
                      onSeek={handleSeek}
                    />
                  </div>

                  {/* Bottom Row: Elapsed Time + Master Volume Slider + Remaining Time */}
                  <div className="flex items-center justify-between text-[11px] font-mono text-zinc-400 px-0.5">
                    <span>{formatTime(playbackPos || 0)}</span>

                    {/* Windows Master Volume Slider */}
                    <div className="flex items-center gap-2 group">
                      <Volume2 className="w-3.5 h-3.5 text-zinc-400 group-hover:text-white transition-colors" />
                      <div
                        className="w-28 h-1.5 bg-white/20 rounded-full overflow-hidden relative cursor-pointer"
                        title={`Windows Volume: ${volumeLevel}%`}
                        onClick={(e) => {
                          e.stopPropagation();
                          const rect = e.currentTarget.getBoundingClientRect();
                          const pct = Math.max(0, Math.min(100, Math.round(((e.clientX - rect.left) / rect.width) * 100)));
                          handleVolumeChange(pct);
                        }}
                      >
                        <div
                          className="h-full bg-white rounded-full transition-all"
                          style={{ width: `${volumeLevel}%` }}
                        />
                      </div>
                      <span className="text-[10px] text-white/50 w-6 text-right">{volumeLevel}%</span>
                    </div>

                    <span>
                      {currentMedia && currentMedia.duration > 0
                        ? `-${formatTime(Math.max(0, currentMedia.duration - playbackPos))}`
                        : "-0:00"}
                    </span>
                  </div>
                </div>
              )}

              {/* ---------------- TAB 2: GAMING HUD & REAL HARDWARE TELEMETRY ---------------- */}
              {activeTab === 'gaming' && (
                <div className="grid grid-cols-2 gap-2 relative py-0.5">
                  {/* Card 1: Live Display & Frame Target */}
                  <div className="p-2.5 rounded-2xl bg-white/[0.04] border border-white/[0.07] flex flex-col justify-between h-[96px]">
                    <div className="flex items-center justify-between">
                      <span className="text-[11px] font-semibold text-white/80">GAME OVERLAY</span>
                      <span className="px-1.5 py-0.2 rounded text-[9px] font-mono font-bold bg-emerald-500/20 text-emerald-300">
                        {telemetry.display.hz} Hz
                      </span>
                    </div>
                    <div className="flex items-baseline gap-1.5">
                      <span className="text-2xl font-bold font-mono text-emerald-400 tracking-tight">
                        {telemetry.display.hz}
                      </span>
                      <span className="text-xs font-mono text-white/50">FPS TARGET</span>
                    </div>
                    <div className="flex items-center justify-between text-[10px] font-mono text-white/50 border-t border-white/[0.05] pt-1">
                      <span>Res: {telemetry.display.resolution}</span>
                      <span>Frame: {roundTo(1000 / (telemetry.display.hz || 60), 1)}ms</span>
                    </div>
                  </div>

                  {/* Card 2: Real Hardware Telemetry (CPU & GPU Load + Real NVIDIA Temp) */}
                  <div className="p-2.5 rounded-2xl bg-white/[0.04] border border-white/[0.07] flex flex-col justify-between h-[96px]">
                    <div className="flex items-center justify-between">
                      <span className="text-[11px] font-semibold text-white/80 truncate pr-1">
                        {telemetry.gpu.name.includes('3050') ? 'RTX 3050 GPU' : 'HARDWARE'}
                      </span>
                      <Cpu className="w-3.5 h-3.5 text-cyan-400 shrink-0" />
                    </div>
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="text-[10px] text-white/50 font-mono">CPU LOAD</div>
                        <div className="text-base font-bold font-mono text-cyan-300">
                          {Math.round(telemetry.cpu.percent)}%
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-[10px] text-white/50 font-mono">GPU TEMP</div>
                        <div className="text-base font-bold font-mono text-amber-300">
                          {telemetry.gpu.temp}°C
                        </div>
                      </div>
                    </div>
                    <div className="w-full h-1 bg-white/10 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-cyan-400 rounded-full transition-all duration-500"
                        style={{ width: `${Math.min(100, Math.max(5, telemetry.cpu.percent))}%` }}
                      />
                    </div>
                  </div>

                  {/* Card 3: Memory & Architecture */}
                  <div className="p-2.5 rounded-2xl bg-white/[0.04] border border-white/[0.07] flex flex-col justify-between h-[96px]">
                    <div className="flex items-center justify-between">
                      <span className="text-[11px] font-semibold text-white/80">MEMORY & SPEED</span>
                      <Wifi className="w-3.5 h-3.5 text-purple-400" />
                    </div>
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="text-[10px] text-white/50 font-mono">CPU FREQ</div>
                        <div className="text-xs font-bold font-mono text-purple-300">{telemetry.cpu.freq_ghz} GHz</div>
                      </div>
                      <div className="text-right">
                        <div className="text-[10px] text-white/50 font-mono">RAM USED</div>
                        <div className="text-xs font-bold font-mono text-white/80">
                          {telemetry.memory.percent}% ({telemetry.memory.used_gb}G)
                        </div>
                      </div>
                    </div>
                    <div className="w-full h-1 bg-white/10 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-purple-400 rounded-full transition-all duration-500"
                        style={{ width: `${telemetry.memory.percent}%` }}
                      />
                    </div>
                  </div>

                  {/* Card 4: Device Ecosystem & Batteries */}
                  <div className="p-2.5 rounded-2xl bg-white/[0.04] border border-white/[0.07] flex flex-col justify-between h-[96px]">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-1.5">
                        <Laptop className="w-3.5 h-3.5 text-white/70" />
                        <span className="text-[11px] font-semibold text-white/90">This PC</span>
                      </div>
                      <span className="text-[11px] font-mono font-bold text-emerald-400">
                        {telemetry.laptop_battery.percent}% {telemetry.laptop_battery.plugged ? '⚡' : ''}
                      </span>
                    </div>
                    <div className="w-full h-1 bg-white/10 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-emerald-400 rounded-full"
                        style={{ width: `${telemetry.laptop_battery.percent}%` }}
                      />
                    </div>
                    <div className="flex items-center justify-between text-[10px] text-white/50 font-mono">
                      <span>POCO X6 Neo 5G:</span>
                      <span className="text-emerald-400 font-semibold">
                        {phoneStats.connected ? `${phoneStats.battery || 80}% Linked` : 'Offline'}
                      </span>
                    </div>
                  </div>
                </div>
              )}

              {/* ---------------- COMMAND INPUT BAR (100% VISIBLE WITH GENEROUS SPACING) ---------------- */}
              <form onSubmit={handleSubmit} className="relative w-full mt-2.5" style={{ WebkitAppRegion: 'no-drag' } as any}>
                <div className="relative flex items-center">
                  <input
                    ref={inputRef}
                    type="text"
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    placeholder="Ask ADA anything (e.g. organize desktop, briefing, lock laptop)..."
                    className="w-full h-8 pl-8 pr-16 bg-white/[0.06] border border-white/[0.08] focus:border-white/20 rounded-xl text-xs text-white placeholder-white/40 focus:outline-none transition-all shadow-inner"
                  />
                  <Sparkles className="w-3.5 h-3.5 text-white/40 absolute left-2.5 pointer-events-none" />
                  <div className="absolute right-1.5 flex items-center gap-1">
                    <button
                      type="button"
                      onClick={(e) => { e.stopPropagation(); toggleListening(); }}
                      className={clsx(
                        "p-1 rounded-lg transition-colors cursor-pointer",
                        isVoiceActive ? "bg-cyan-500/20 text-cyan-300" : "hover:bg-white/10 text-white/40"
                      )}
                    >
                      <Mic className="w-3.5 h-3.5" />
                    </button>
                    <button
                      type="submit"
                      disabled={!inputValue.trim() || isSubmitting}
                      className={clsx(
                        "p-1 rounded-lg transition-colors cursor-pointer",
                        inputValue.trim() ? "bg-white text-black hover:scale-105" : "text-white/20 cursor-not-allowed"
                      )}
                    >
                      <ArrowUp className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              </form>

              {/* Fast Action Chips (Touchpad, Briefing, Phone, Message, Lock PC) - 100% VISIBLE */}
              <div
                className="flex items-center gap-1.5 overflow-x-auto no-scrollbar pt-2"
                style={{ WebkitAppRegion: 'no-drag' } as any}
              >
                <button
                  type="button"
                  onClick={(e) => { e.stopPropagation(); handleDispatch("give me my morning briefing"); }}
                  className="px-2.5 py-1 rounded-lg text-[10px] font-medium bg-white/[0.05] hover:bg-amber-500/20 text-white/80 hover:text-amber-300 border border-white/[0.08] flex items-center gap-1 shrink-0 transition-all cursor-pointer"
                >
                  <Zap className="w-2.5 h-2.5 text-amber-400" />
                  Briefing
                </button>
                <button
                  type="button"
                  onClick={(e) => { e.stopPropagation(); handleLaunchTouchpad(e); }}
                  className="px-2.5 py-1 rounded-lg text-[10px] font-medium bg-cyan-500/10 hover:bg-cyan-500/25 text-cyan-300 border border-cyan-500/30 flex items-center gap-1 shrink-0 transition-all shadow-sm cursor-pointer"
                  title="Turn POCO Phone into Wireless Laptop Trackpad"
                >
                  <Smartphone className="w-2.5 h-2.5 text-cyan-400" />
                  Touchpad
                </button>
                <button
                  type="button"
                  onClick={(e) => { e.stopPropagation(); handleDispatch("check my phone status"); }}
                  className="px-2.5 py-1 rounded-lg text-[10px] font-medium bg-white/[0.05] hover:bg-emerald-500/20 text-white/80 hover:text-emerald-300 border border-white/[0.08] flex items-center gap-1 shrink-0 transition-all cursor-pointer"
                >
                  <Smartphone className="w-2.5 h-2.5 text-emerald-400" />
                  Phone: {phoneStats.connected ? `${phoneStats.battery || 80}%` : 'Linked'}
                </button>
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    setInputValue("msg ");
                    inputRef.current?.focus();
                  }}
                  className="px-2.5 py-1 rounded-lg text-[10px] font-medium bg-white/[0.05] hover:bg-green-500/20 text-white/80 hover:text-green-300 border border-white/[0.08] flex items-center gap-1 shrink-0 transition-all cursor-pointer"
                >
                  <MessageSquare className="w-2.5 h-2.5 text-green-400" />
                  Message
                </button>
                <button
                  type="button"
                  onClick={(e) => { e.stopPropagation(); handleDispatch("lock my laptop"); }}
                  className="px-2.5 py-1 rounded-lg text-[10px] font-medium bg-rose-500/10 hover:bg-rose-500/25 text-rose-300 border border-rose-500/20 flex items-center gap-1 shrink-0 ml-auto transition-all cursor-pointer"
                >
                  <Shield className="w-2.5 h-2.5 text-rose-400" />
                  Lock PC
                </button>
              </div>
            </div>

            {/* 3. CLEAN MICRO-TELEMETRY FOOTER */}
            <div
              className="flex items-center justify-between text-[10px] text-white/40 pt-2 mt-auto border-t border-white/[0.06] font-mono"
              style={{ WebkitAppRegion: 'no-drag' } as any}
            >
              <span className="flex items-center gap-1.5">
                <span className={clsx(
                  "w-1.5 h-1.5 rounded-full",
                  isVoiceActive ? "bg-cyan-400 animate-ping" : "bg-cyan-400 shadow-[0_0_6px_#22d3ee]"
                )} />
                <span className="text-white/60">SYS:</span>
                <span className="text-cyan-400 uppercase font-semibold">
                  {isVoiceActive ? "VOICE ACTIVE" : isPinned ? "PINNED" : recentResponse ? "INTEL READY" : islandState}
                </span>
              </span>

              <span>{currentTime}</span>
              <span className="text-white/40 font-mono font-medium">ADA v1.0</span>
            </div>
          </div>
        )}
      </motion.div>
    </div>
  );
};

function roundTo(num: number, dec: number): number {
  const factor = Math.pow(10, dec);
  return Math.round(num * factor) / factor;
}
