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

export type PaletteThemeKey = 'pink' | 'cyan' | 'purple' | 'emerald' | 'amber' | 'orange' | 'crimson' | 'silver';

export interface ThemeConfig {
  key: PaletteThemeKey;
  name: string;
  color: string;
  accentClass: string;
}

export const THEMES: Record<PaletteThemeKey, ThemeConfig> = {
  pink: { key: 'pink', name: 'Sakura Pink', color: '#f472b6', accentClass: 'text-rose-400' },
  cyan: { key: 'cyan', name: 'Cyber Cyan', color: '#22d3ee', accentClass: 'text-cyan-400' },
  purple: { key: 'purple', name: 'Electric Violet', color: '#a855f7', accentClass: 'text-purple-400' },
  emerald: { key: 'emerald', name: 'Matrix Emerald', color: '#10b981', accentClass: 'text-emerald-400' },
  amber: { key: 'amber', name: 'Sunset Gold', color: '#f59e0b', accentClass: 'text-amber-400' },
  orange: { key: 'orange', name: 'Blaze Coral', color: '#ff6b4a', accentClass: 'text-orange-400' },
  crimson: { key: 'crimson', name: 'Crimson Ruby', color: '#ef4444', accentClass: 'text-rose-500' },
  silver: { key: 'silver', name: 'Ice Titanium', color: '#e2e8f0', accentClass: 'text-slate-200' },
};

export const THEME_KEYS: PaletteThemeKey[] = ['pink', 'cyan', 'purple', 'emerald', 'amber', 'orange', 'crimson', 'silver'];

export const DynamicIsland: React.FC = () => {
  const { islandState, setIslandState } = useNovaStore();
  const { sendChat } = useNovaWebSocket();
  const [expanded, setExpanded] = useState(false);
  const [activeTab, setActiveTab] = useState<IslandTab>('music');
  const [inputValue, setInputValue] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [recentResponse, setRecentResponse] = useState<string | null>(null);
  const [currentTime, setCurrentTime] = useState('');
  const [paletteMode, setPaletteMode] = useState<PaletteThemeKey>('pink');
  const [isPinned, setIsPinned] = useState(false);
  
  // Media State & High-Precision Audio Sync Clock
  const [currentMedia, setCurrentMedia] = useState<MediaTrack | null>(null);
  const [playbackPos, setPlaybackPos] = useState<number>(0);
  const lastSyncRef = useRef<{ title: string; pos: number; ts: number }>({ title: '', pos: 0, ts: Date.now() });
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

  // Poll Media Controller (Real Windows GSMTC) with Intelligent Clock Sync
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
            const now = Date.now();
            const incomingPos = typeof track.position === 'number' ? track.position : 0;

            // If new song started, sync immediately
            if (track.title !== lastSyncRef.current.title) {
              lastSyncRef.current = { title: track.title, pos: incomingPos, ts: now };
              setPlaybackPos(incomingPos);
            } else {
              // Expected position based on continuous local clock
              const expectedPos = lastSyncRef.current.pos + (track.status === 'playing' ? (now - lastSyncRef.current.ts) / 1000 : 0);
              const drift = Math.abs(incomingPos - expectedPos);

              // Only snap if drift is significant (e.g. user scrubbed on Spotify/YouTube or loop restart)
              if (drift > 2.0) {
                lastSyncRef.current = { title: track.title, pos: incomingPos, ts: now };
                setPlaybackPos(incomingPos);
              } else {
                // Smooth micro-calibration without sudden jumping
                lastSyncRef.current = { title: track.title, pos: incomingPos, ts: now };
              }
            }
          } else {
            setCurrentMedia(null);
            setPlaybackPos(0);
            lastSyncRef.current = { title: '', pos: 0, ts: Date.now() };
          }
        }
      } catch {
        // Backend offline / media idle
      }
    };

    fetchMedia();
    const pollInterval = setInterval(fetchMedia, 1500);
    return () => {
      isMounted = false;
      clearInterval(pollInterval);
    };
  }, []);

  // Live Bidirectional Volume Sync with Windows Master Volume
  useEffect(() => {
    let isMounted = true;
    const syncVolume = () => {
      fetch('http://127.0.0.1:8000/api/system/volume')
        .then(r => r.json())
        .then(d => {
          if (isMounted && typeof d.volume === 'number') {
            setVolumeLevel(Math.round(d.volume));
          }
        })
        .catch(() => {});
    };

    syncVolume();
    const volInterval = setInterval(syncVolume, 1200);
    return () => {
      isMounted = false;
      clearInterval(volInterval);
    };
  }, []);

  // Smooth 100ms client-side playback ticker for fluid scrubber progress (Continuous sub-second glide)
  useEffect(() => {
    if (!currentMedia || currentMedia.status !== 'playing') return;
    const ticker = setInterval(() => {
      const now = Date.now();
      if (lastSyncRef.current && lastSyncRef.current.title === currentMedia.title) {
        const elapsed = (now - lastSyncRef.current.ts) / 1000;
        const currentCalculatedPos = lastSyncRef.current.pos + elapsed;
        if (currentMedia.duration > 0 && currentCalculatedPos >= currentMedia.duration) {
          setPlaybackPos(currentMedia.duration);
        } else {
          setPlaybackPos(currentCalculatedPos);
        }
      }
    }, 100);
    return () => clearInterval(ticker);
  }, [currentMedia?.status, currentMedia?.duration, currentMedia?.title]);

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
    lastSyncRef.current = { title: currentMedia.title, pos: targetSeconds, ts: Date.now() };
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

  // Mouse Dragging for Window Repositioning with Smooth 60fps RAF Throttle
  const rafIdRef = useRef<number | null>(null);
  const pendingDeltaRef = useRef({ dx: 0, dy: 0 });

  const handleDragPointerDown = useCallback((e: React.PointerEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    isDraggingRef.current = true;
    dragStartRef.current = { x: e.screenX, y: e.screenY };

    const handlePointerMove = (moveEvt: PointerEvent) => {
      if (!isDraggingRef.current) return;
      if (moveEvt.buttons === 0) {
        handlePointerUp();
        return;
      }
      pendingDeltaRef.current.dx += moveEvt.screenX - dragStartRef.current.x;
      pendingDeltaRef.current.dy += moveEvt.screenY - dragStartRef.current.y;
      dragStartRef.current = { x: moveEvt.screenX, y: moveEvt.screenY };

      if (rafIdRef.current === null) {
        rafIdRef.current = requestAnimationFrame(() => {
          if (pendingDeltaRef.current.dx !== 0 || pendingDeltaRef.current.dy !== 0) {
            try {
              if ((window as any).electronAPI?.moveIsland) {
                (window as any).electronAPI.moveIsland(
                  pendingDeltaRef.current.dx,
                  pendingDeltaRef.current.dy
                );
              }
            } catch {}
            pendingDeltaRef.current.dx = 0;
            pendingDeltaRef.current.dy = 0;
          }
          rafIdRef.current = null;
        });
      }
    };

    const handlePointerUp = () => {
      isDraggingRef.current = false;
      if (rafIdRef.current !== null) {
        cancelAnimationFrame(rafIdRef.current);
        rafIdRef.current = null;
      }
      window.removeEventListener('pointermove', handlePointerMove);
      window.removeEventListener('pointerup', handlePointerUp);
      window.removeEventListener('pointercancel', handlePointerUp);
    };

    window.addEventListener('pointermove', handlePointerMove);
    window.addEventListener('pointerup', handlePointerUp);
    window.addEventListener('pointercancel', handlePointerUp);
  }, []);

  // Launch Wireless Touchpad on Phone
  const handleLaunchTouchpad = async (e?: React.MouseEvent) => {
    e?.stopPropagation();
    try {
      setIslandState('executing', 'Opening Ultra Touchpad on Phone...');
      const res = await fetch('http://127.0.0.1:8000/api/devices/touchpad/launch', { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        if (data.status === 'SUCCESS') {
          setRecentResponse("Wireless Trackpad opened on phone!");
          setIslandState('idle', 'Touchpad active');
        } else {
          setRecentResponse(data.message || "Could not launch touchpad.");
          setIslandState('idle');
        }
      }
    } catch {
      setRecentResponse("Backend offline: cannot open touchpad.");
      setIslandState('idle');
    }
  };

  // Expanded height: Generous clearance so no element or border is ever clipped
  const expandedHeight = activeTab === 'gaming' ? 440 : (currentMedia && currentMedia.title ? 360 : 320);

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
    const cmd = text.trim();
    if (!cmd || isSubmitting) return;

    // Immediately clear input field so Enter feels instant
    setInputValue('');
    if (inputRef.current) {
      inputRef.current.value = '';
    }

    setIsSubmitting(true);
    setRecentResponse(null);
    setIslandState('thinking', `Processing: "${cmd.slice(0, 24)}..."`);

    try {
      const res = await fetch('http://127.0.0.1:8000/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: cmd })
      });
      if (res.ok) {
        const data = await res.json();
        const responseText = data.response || "Task executed successfully.";
        setRecentResponse(responseText);
        setIslandState('idle', responseText);
      } else {
        setIslandState('idle', 'Execution completed.');
      }
    } catch {
      sendChat(cmd);
      setRecentResponse("Action dispatched to ADA kernel.");
      setIslandState('idle');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputValue.trim()) {
      handleDispatch(inputValue);
    }
  };

  const formatTime = (secs: number) => {
    const s = Math.max(0, Math.floor(secs));
    const m = Math.floor(s / 60);
    const rem = s % 60;
    return `${m}:${rem < 10 ? '0' : ''}${rem}`;
  };

  const isVoiceActive = islandState === 'voice-listening' || isListening;
  const currentTheme = THEMES[paletteMode] || THEMES.pink;
  const themeColor = currentTheme.color;
  const themeAccentClass = currentTheme.accentClass;

  return (
    <div className="fixed top-0 left-0 w-full flex justify-center pointer-events-none z-[999999] select-none font-sans">
      <motion.div
        initial={{ y: -50, opacity: 0 }}
        animate={{
          y: 0,
          opacity: 1,
          width: expanded ? 516 : (currentMedia ? 336 : 240),
          height: expanded ? expandedHeight : 44,
          borderRadius: expanded ? 14 : 22
        }}
        transition={{
          type: "spring",
          stiffness: 300,
          damping: 28,
          mass: 0.8
        }}
        className={clsx(
          "pointer-events-auto overflow-hidden relative flex flex-col justify-start",
          "border border-white/15",
          expanded ? "border-white/20 shadow-none" : "shadow-none hover:border-white/30 transition-colors cursor-pointer",
          "bg-[#0a0b10] text-white", // Solid OLED Dark
        )}
        style={{ transformOrigin: "top center" }}
        onClick={() => !expanded && setExpanded(true)}
      >
        {/* Apple Style Smooth Radial Glow Accent (Pure vector gradient, zero blur filter bleeding) */}
        <div
          className="absolute top-0 left-0 right-0 h-20 pointer-events-none opacity-20 transition-opacity duration-500 z-0"
          style={{
            background: `radial-gradient(ellipse 80% 50% at 50% 0%, ${themeColor} 0%, transparent 100%)`
          }}
        />

        {/* ---------------- COLLAPSED PILL STATE (Fluid absolute overlay) ---------------- */}
        <div
          className={clsx(
            "w-full h-11 px-3 flex items-center justify-between gap-2 select-none absolute top-0 left-0 z-10",
            "transition-[opacity,transform] duration-200 ease-out",
            expanded
              ? "opacity-0 pointer-events-none scale-95"
              : "opacity-100 pointer-events-auto scale-100 delay-100"
          )}
        >
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
                  isVoiceActive ? "bg-cyan-400 animate-ping" : "bg-cyan-400 ring-2 ring-cyan-400/50"
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

        {/* ---------------- EXPANDED ISLAND STATE (Snappy clean transition) ---------------- */}
        <div
          className={clsx(
            "w-full flex-1 flex flex-col p-3 overflow-hidden select-none relative z-10",
            "transition-[opacity,transform] duration-240 ease-[cubic-bezier(0.16,1,0.3,1)]",
            expanded
              ? "opacity-100 pointer-events-auto translate-y-0 scale-100 delay-100"
              : "opacity-0 pointer-events-none translate-y-2 scale-[0.98]"
          )}
        >
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
                      ? "bg-white/15 text-white border border-white/20"
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
                      ? "bg-white/15 text-white border border-white/20"
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

                {/* Accent Palette (Cycles through 8 vibrant color themes) */}
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    setPaletteMode(prev => {
                      const idx = THEME_KEYS.indexOf(prev);
                      return THEME_KEYS[(idx + 1) % THEME_KEYS.length];
                    });
                  }}
                  className="p-1.5 rounded-full bg-white/[0.07] hover:bg-white/[0.14] text-white/70 hover:text-white transition-all cursor-pointer flex items-center gap-1.5"
                  title={`Switch Theme: ${currentTheme.name} (${THEME_KEYS.indexOf(paletteMode) + 1}/${THEME_KEYS.length})`}
                >
                  <span
                    className="w-2 h-2 rounded-full border border-white/40 shadow-sm"
                    style={{ backgroundColor: currentTheme.color }}
                  />
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
                      <div className="w-[54px] h-[54px] rounded-2xl overflow-hidden bg-zinc-900 border border-white/10 flex items-center justify-center">
                        {currentMedia?.thumbnail ? (
                          <img src={currentMedia.thumbnail} alt={currentMedia.title} className="w-full h-full object-cover" />
                        ) : (
                          <div className="w-full h-full bg-gradient-to-b from-purple-700 via-pink-600 to-amber-400 flex items-center justify-center relative overflow-hidden">
                            <div className="w-6 h-6 rounded-full bg-amber-200/90 " />
                          </div>
                        )}
                      </div>
                      {/* Floating Rounded Music Badge */}
                      <div
                        className="w-5 h-5 rounded-lg flex items-center justify-center absolute -bottom-1 -right-1 "
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
                        className="p-2.5 rounded-full bg-white text-black hover:scale-105 active:scale-95 transition-all  cursor-pointer"
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

                  {/* Middle Row: Signature Animated Squiggly Wave Scrubber (Only when playing/available!) */}
                  {currentMedia && currentMedia.duration > 0 ? (
                    <div className="w-full px-0.5 pt-1">
                      <SquigglyWave
                        progress={playbackPos / currentMedia.duration}
                        isPlaying={currentMedia?.status === 'playing'}
                        color={themeColor}
                        width={484}
                        onSeek={handleSeek}
                      />
                    </div>
                  ) : (
                    <div className="w-full h-[1px] bg-white/[0.06] my-1" />
                  )}

                  {/* Bottom Row: Elapsed Time + Master Volume Slider + Remaining Time */}
                  <div className="flex items-center justify-between text-[11px] font-mono text-zinc-400 px-0.5">
                    <span>{currentMedia && currentMedia.duration > 0 ? formatTime(playbackPos) : "0:00"}</span>

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

              {/* ---------------- LIVE RESPONSE PREVIEW CARD ---------------- */}
              {recentResponse && (
                <div className="w-full p-2.5 mb-2 rounded-xl bg-white/[0.07] border border-white/10 flex items-start justify-between gap-2 text-xs backdrop-blur-md">
                  <div className="flex-1 max-h-24 overflow-y-auto no-scrollbar text-white/90 leading-relaxed select-text">
                    <span className="text-cyan-400 font-semibold mr-1.5">ADA:</span>
                    {recentResponse}
                  </div>
                  <button
                    type="button"
                    onClick={(e) => { e.stopPropagation(); setRecentResponse(null); }}
                    className="p-1 text-white/40 hover:text-white rounded-lg hover:bg-white/10 transition-colors shrink-0"
                    title="Dismiss"
                  >
                    ✕
                  </button>
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
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        if (inputValue.trim()) {
                          handleDispatch(inputValue);
                        }
                      }
                    }}
                    placeholder="Ask ADA anything (e.g. organize desktop, briefing, lock laptop)..."
                    className="w-full h-8 pl-8 pr-16 bg-white/[0.06] border border-white/[0.08] focus:border-white/20 rounded-xl text-xs text-white placeholder-white/40 focus:outline-none transition-all "
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
                  className="px-2.5 py-1 rounded-lg text-[10px] font-medium bg-cyan-500/10 hover:bg-cyan-500/25 text-cyan-300 border border-cyan-500/30 flex items-center gap-1 shrink-0 transition-all cursor-pointer"
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
                  isVoiceActive ? "bg-cyan-400 animate-ping" : "bg-cyan-400 ring-2 ring-cyan-400/50"
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
      </motion.div>
    </div>
  );
};

function roundTo(num: number, dec: number): number {
  const factor = Math.pow(10, dec);
  return Math.round(num * factor) / factor;
}
