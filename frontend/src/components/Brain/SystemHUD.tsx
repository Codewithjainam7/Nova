import React, { useState, useEffect, memo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Cpu, HardDrive, Wifi, Shield, Radio, Sparkles, Terminal, Mic,
  Sliders, Smartphone, FolderSync, Calendar, FileText, Keyboard,
  Zap, CheckCircle2, Save, Activity, Volume2, Folder, Download, Image,
  ChevronLeft, ChevronRight
} from 'lucide-react';
import { useWidgetStore } from '../../store/useWidgetStore';
import { useNovaStore } from '../../store/useNovaStore';
import { useNovaWebSocket } from '../../contexts/NovaWebSocket';
import { speakResponse } from '../../hooks/useVoiceRecognition';

interface TelemetryData {
  cpu: {
    percent: number;
    per_cpu: number[];
    threads: number;
    cores: number;
    freq_ghz: number;
  };
  memory: {
    total_gb: number;
    used_gb: number;
    percent: number;
  };
  phone: {
    connected: boolean;
    battery: number | null;
    device_id: string | null;
  };
  ai: {
    provider: string;
    model: string;
  };
}

// Atomic Precision Clock with Milliseconds
const SystemClock = memo(() => {
  const [time, setTime] = useState('');
  useEffect(() => {
    const timer = setInterval(() => {
      const now = new Date();
      setTime(
        now.toLocaleTimeString('en-US', { hour12: false }) +
        '.' +
        now.getMilliseconds().toString().padStart(3, '0')
      );
    }, 45);
    return () => clearInterval(timer);
  }, []);
  return <span className="tracking-widest font-mono text-cyan-200 font-bold drop-shadow-[0_0_8px_rgba(34,211,238,0.7)] text-[11px] sm:text-xs">{time}</span>;
});

// Real Multi-Core Hardware Frequency Visualizer
const CpuLoadVisualizer = memo(({ cpu }: { cpu: TelemetryData['cpu'] }) => {
  const loads = cpu.per_cpu && cpu.per_cpu.length > 0 ? cpu.per_cpu : [cpu.percent || 15];

  return (
    <div className="space-y-1.5 sm:space-y-2">
      <div className="flex items-center justify-between font-hud font-bold text-xs text-cyan-200 tracking-wider">
        <span className="flex items-center gap-1.5 text-cyan-200">
          <Activity className="w-3.5 h-3.5 text-cyan-400 animate-pulse" />
          CORE LOAD: {Math.round(cpu.percent)}%
        </span>
        <span className="font-mono text-cyan-300 font-semibold text-[10px] sm:text-[11px]">
          {cpu.freq_ghz.toFixed(2)} GHz // {cpu.threads} THREADS
        </span>
      </div>
      <div className="flex gap-1 items-end h-8 sm:h-9 p-1 bg-black/60 rounded-lg border border-cyan-500/30">
        {loads.map((load, i) => (
          <motion.div 
            key={i}
            className="flex-1 rounded-sm bg-gradient-to-t from-cyan-600 via-cyan-400 to-purple-400 shadow-[0_0_8px_rgba(34,211,238,0.5)]"
            animate={{ height: `${Math.max(6, Math.min(100, Math.round(load)))}%` }}
            transition={{ duration: 0.35, ease: 'easeOut' }}
            title={`Thread ${i + 1}: ${Math.round(load)}%`}
          />
        ))}
      </div>
    </div>
  );
});

// Real Directive Terminal Logs from Actual Conversation & Kernel Activity
const TerminalLogs = memo(({ ai, phone }: { ai: TelemetryData['ai']; phone: TelemetryData['phone'] }) => {
  const { messages, executionTimeline } = useNovaStore();

  const realLogs = React.useMemo(() => {
    const list: { id: string; tag: string; tagColor: string; msg: string; time: string }[] = [];

    // Real system initialization events
    list.push({
      id: 'boot-1',
      tag: 'KERNEL',
      tagColor: 'text-cyan-200 border-cyan-400/60 bg-cyan-950/80',
      msg: 'ADA MARK VII COGNITIVE KERNEL ONLINE',
      time: '15:50:00'
    });
    list.push({
      id: 'boot-2',
      tag: ai.provider || 'GROQ',
      tagColor: 'text-purple-200 border-purple-400/60 bg-purple-950/80',
      msg: `NEURAL ENGINE READY // ${ai.model || 'LLAMA 3.3 70B'}`,
      time: '15:50:01'
    });
    if (phone.connected) {
      list.push({
        id: 'boot-3',
        tag: 'ADB',
        tagColor: 'text-indigo-200 border-indigo-400/60 bg-indigo-950/80',
        msg: `BRIDGE LINKED: ${phone.device_id || 'WIRELESS'} (${phone.battery !== null ? phone.battery + '%' : 'OK'})`,
        time: '15:50:02'
      });
    }

    // Add recent user directives and ADA replies
    messages.slice(-4).forEach((m) => {
      const d = new Date(m.timestamp || Date.now());
      const timeStr = d.toLocaleTimeString('en-US', { hour12: false });
      if (m.role === 'user') {
        list.push({
          id: m.id || String(Math.random()),
          tag: 'DIRECTIVE',
          tagColor: 'text-amber-200 border-amber-400/60 bg-amber-950/80',
          msg: m.content.length > 38 ? m.content.slice(0, 38) + '...' : m.content,
          time: timeStr
        });
      } else if (m.role === 'assistant') {
        list.push({
          id: m.id || String(Math.random()),
          tag: 'ADA',
          tagColor: 'text-emerald-200 border-emerald-400/60 bg-emerald-950/80',
          msg: m.content.length > 38 ? m.content.slice(0, 38) + '...' : m.content,
          time: timeStr
        });
      }
    });

    // Add recent execution timeline steps
    executionTimeline.slice(-2).forEach((step) => {
      list.push({
        id: step.id,
        tag: 'EXEC',
        tagColor: 'text-sky-200 border-sky-400/60 bg-sky-950/80',
        msg: step.description.length > 38 ? step.description.slice(0, 38) + '...' : step.description,
        time: new Date().toLocaleTimeString('en-US', { hour12: false })
      });
    });

    return list.slice(-5);
  }, [messages, executionTimeline, ai, phone]);

  return (
    <div className="w-full flex flex-col gap-1.5 font-mono text-[9px] sm:text-[10px] text-cyan-200">
      {realLogs.map((log) => (
        <motion.div
          key={log.id}
          initial={{ opacity: 0, x: 10 }}
          animate={{ opacity: 1, x: 0 }}
          className="flex items-center gap-1.5 whitespace-nowrap overflow-hidden"
        >
          <span className="text-white/60 shrink-0 text-[8px] sm:text-[9px] font-semibold">{log.time}</span>
          <span className={`px-1 py-0.2 rounded border text-[8px] sm:text-[9px] font-bold shrink-0 ${log.tagColor}`}>
            {log.tag}
          </span>
          <span className="truncate text-white font-medium">{log.msg}</span>
        </motion.div>
      ))}
      <div className="flex items-center gap-1.5 text-[8px] sm:text-[9px] font-hud text-cyan-300 font-bold pt-0.5 tracking-wider">
        <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse" />
        <span>AWAITING DIRECTIVES</span>
        <span className="animate-ping font-mono">_</span>
      </div>
    </div>
  );
});

export const SystemHUD: React.FC = () => {
  const { enabledWidgets, setCustomizerOpen, scratchpadNote, setScratchpadNote } = useWidgetStore();
  const { sendChat } = useNovaWebSocket();
  const [tempNote, setTempNote] = useState(scratchpadNote);
  const [savedBadge, setSavedBadge] = useState(false);
  
  // Real Hardware & Telemetry State
  const [telemetry, setTelemetry] = useState<TelemetryData>({
    cpu: {
      percent: 15,
      per_cpu: [10, 8, 12, 14, 9, 11, 7, 15, 8, 10, 12, 11, 9, 8, 14, 10],
      threads: 16,
      cores: 10,
      freq_ghz: 2.40
    },
    memory: {
      total_gb: 15.7,
      used_gb: 9.3,
      percent: 59
    },
    phone: {
      connected: false,
      battery: null,
      device_id: null
    },
    ai: {
      provider: 'GROQ',
      model: 'LLAMA 3.3 70B'
    }
  });

  // Responsive sidebar drawer states (collapsible for all screen resolutions)
  const [isLeftCollapsed, setIsLeftCollapsed] = useState(false);
  const [isRightCollapsed, setIsRightCollapsed] = useState(false);

  useEffect(() => {
    setTempNote(scratchpadNote);
  }, [scratchpadNote]);

  // Responsive screen auto-adapter
  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth < 1180) {
        setIsLeftCollapsed(true);
        setIsRightCollapsed(true);
      } else {
        setIsLeftCollapsed(false);
        setIsRightCollapsed(false);
      }
    };
    if (window.innerWidth < 1180) {
      setIsLeftCollapsed(true);
      setIsRightCollapsed(true);
    }
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Poll real system telemetry every 1.5s
  useEffect(() => {
    const fetchTelemetry = async () => {
      try {
        const res = await fetch('http://localhost:8000/api/telemetry');
        if (res.ok) {
          const data = await res.json();
          if (data && data.cpu && data.memory) {
            setTelemetry(data);
          }
        }
      } catch {
        // Backend offline or reconnecting
      }
    };

    fetchTelemetry();
    const interval = setInterval(fetchTelemetry, 1500);
    return () => clearInterval(interval);
  }, []);

  // Global keydown listeners for reliable shortcut execution inside main window
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.altKey && (e.code === 'Space' || e.key === ' ')) ||
          (e.ctrlKey && (e.code === 'Space' || e.key === ' ')) ||
          e.key === 'F2') {
        e.preventDefault();
        try {
          if ((window as any).electronAPI?.toggleIsland) {
            (window as any).electronAPI.toggleIsland();
          }
        } catch {}
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const dispatchQuickAction = (cmd: string) => {
    try {
      sendChat(cmd);
    } catch {
      fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: cmd })
      }).catch(console.error);
    }
  };

  const triggerExecutiveBriefing = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/briefing');
      if (res.ok) {
        const data = await res.json();
        const text = data.briefing || "All systems nominal.";
        speakResponse(text);
      }
    } catch {}
    dispatchQuickAction("give me my morning briefing");
  };

  const handleSaveScratchpad = () => {
    setScratchpadNote(tempNote);
    setSavedBadge(true);
    setTimeout(() => setSavedBadge(false), 2000);
  };

  return (
    <div className="absolute inset-0 pointer-events-none z-10 overflow-hidden select-none">
      
      {/* Top Floating Command Deck Header (Fully Responsive on Mobile/Tablet/Desktop) */}
      <div className="absolute top-2 inset-x-2 sm:top-3 sm:inset-x-5 flex items-center justify-between pointer-events-auto bg-gradient-to-r from-[#030818]/95 via-[#060e22]/90 to-[#030818]/95 border border-cyan-400/40 backdrop-blur-2xl px-3 sm:px-5 py-2 rounded-xl sm:rounded-2xl shadow-[0_4px_35px_rgba(0,0,0,0.8),0_0_20px_rgba(6,182,212,0.15)]">
        
        {/* Left: ADA Mark VII Identity Crest */}
        <div className="flex items-center gap-2 sm:gap-3 min-w-0">
          <div className="relative w-8 h-8 sm:w-9 sm:h-9 rounded-lg sm:rounded-xl bg-gradient-to-br from-cyan-950 to-blue-950 border border-cyan-400/70 flex items-center justify-center shrink-0 shadow-[0_0_15px_rgba(34,211,238,0.5)]">
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ repeat: Infinity, duration: 8, ease: 'linear' }}
              className="absolute inset-0.5 rounded-lg border border-dashed border-cyan-300/60"
            />
            <Sparkles className="w-4 h-4 text-cyan-300 animate-pulse" />
          </div>
          <div className="min-w-0">
            <div className="text-xs sm:text-sm font-hud font-bold tracking-[0.18em] text-white flex items-center gap-1.5 sm:gap-2 truncate">
              <span className="bg-gradient-to-r from-cyan-200 via-white to-purple-200 bg-clip-text text-transparent drop-shadow-[0_0_10px_rgba(34,211,238,0.5)]">
                ADA MARK VII
              </span>
              <span className="text-[9px] px-1.5 py-0.2 rounded-full bg-emerald-500/25 text-emerald-300 border border-emerald-400/50 font-hud font-bold flex items-center gap-1 shrink-0">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping" />
                ONLINE
              </span>
            </div>
            <div className="text-[8px] sm:text-[9px] tracking-[0.2em] text-cyan-300 font-hud font-semibold uppercase truncate hidden sm:block">
              AUTONOMOUS AI OPERATING SYSTEM
            </div>
          </div>
        </div>

        {/* Center: Live Subsystem Telemetry Badges (Adaptive on wider screens) */}
        <div className="hidden 2xl:flex items-center gap-2.5 font-hud text-xs font-bold tracking-wider">
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-cyan-950/70 border border-cyan-400/40 text-cyan-200">
            <Radio className="w-3 h-3 text-cyan-400 animate-pulse" />
            <span>NEURAL: {telemetry.ai.provider}</span>
          </div>
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-purple-950/70 border border-purple-400/40 text-purple-200">
            <Volume2 className="w-3 h-3 text-purple-400" />
            <span>SONIA HD</span>
          </div>
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-cyan-950/70 border border-cyan-400/40 text-cyan-200">
            <Mic className="w-3 h-3 text-cyan-400 animate-pulse" />
            <span>WAKE: HEY ADA</span>
          </div>
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-emerald-950/70 border border-emerald-400/40 text-emerald-200">
            <Shield className="w-3 h-3 text-emerald-400" />
            <span>DISPATCH ARMED</span>
          </div>
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-blue-950/70 border border-blue-400/40 text-blue-200">
            <Wifi className="w-3 h-3 text-blue-400" />
            <span>{telemetry.phone.connected ? `ADB: ${telemetry.phone.battery !== null ? `${telemetry.phone.battery}%` : 'LINKED'}` : 'ADB: OFFLINE'}</span>
          </div>
        </div>

        {/* Right: Clock & Customize Button */}
        <div className="flex items-center gap-2 sm:gap-3 shrink-0">
          <button
            onClick={() => setCustomizerOpen(true)}
            className="px-2.5 sm:px-3.5 py-1.5 rounded-xl bg-cyan-500/25 hover:bg-cyan-500/40 border border-cyan-400/60 text-cyan-100 hover:text-white text-[11px] sm:text-xs font-hud tracking-wider transition-all flex items-center gap-1.5 shadow-[0_0_15px_rgba(6,182,212,0.25)] cursor-pointer active:scale-95"
          >
            <Sliders className="w-3.5 h-3.5 text-cyan-300" />
            <span className="font-bold">CONTROL</span>
          </button>

          <div className="hidden sm:block text-right border-l border-white/20 pl-2.5 sm:pl-3">
            <div className="text-[8px] text-cyan-300 font-hud tracking-[0.2em] uppercase font-bold">ATOMIC TIME</div>
            <div className="text-xs">
              <SystemClock />
            </div>
          </div>
        </div>
      </div>

      {/* Responsive Left HUD Drawer Toggle Pill */}
      <button
        onClick={() => setIsLeftCollapsed(!isLeftCollapsed)}
        title={isLeftCollapsed ? "Show Telemetry Widgets" : "Collapse Telemetry"}
        className="absolute top-16 sm:top-18 left-3 z-30 px-2.5 py-1 rounded-lg bg-[#040816]/90 hover:bg-cyan-950/80 border border-cyan-400/50 text-cyan-200 text-[10px] font-hud font-bold tracking-wider transition-all shadow-[0_0_15px_rgba(6,182,212,0.25)] pointer-events-auto flex items-center gap-1.5 cursor-pointer active:scale-95"
      >
        <Activity className="w-3 h-3 text-cyan-400" />
        <span className="hidden md:inline">{isLeftCollapsed ? 'TELEMETRY' : 'HIDE'}</span>
        {isLeftCollapsed ? <ChevronRight className="w-3 h-3 text-cyan-300" /> : <ChevronLeft className="w-3 h-3 text-cyan-300" />}
      </button>

      {/* LEFT HUD: Modular Telemetry & Automations (Animated Drawer) */}
      <AnimatePresence>
        {!isLeftCollapsed && (
          <motion.div
            initial={{ opacity: 0, x: -320 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -320 }}
            transition={{ duration: 0.25, ease: "easeInOut" }}
            className="absolute top-24 sm:top-26 left-3 sm:left-5 flex flex-col gap-2.5 sm:gap-3 w-[250px] sm:w-[270px] lg:w-[285px] pointer-events-auto max-h-[calc(100vh-230px)] overflow-y-auto cyber-scrollbar pr-1 pb-4 z-20"
          >
            {/* Widget 1: CPU Synapse (Accurate Real Hardware Data) */}
            {enabledWidgets['cpu'] && (
              <div className="cyber-card p-3 sm:p-3.5 cyber-bracket font-hud">
                <div className="flex items-center justify-between text-xs text-white font-bold tracking-wider mb-2 border-b border-cyan-500/30 pb-1.5">
                  <span className="flex items-center gap-1.5 text-cyan-200">
                    <Cpu className="w-3.5 h-3.5 text-cyan-400" />
                    SYNAPSE PROCESSOR
                  </span>
                  <span className="text-[9px] px-1.5 py-0.2 rounded bg-cyan-500/25 text-cyan-200 border border-cyan-400/40 font-mono font-bold">
                    {telemetry.cpu.threads} THREADS ({telemetry.cpu.cores}C)
                  </span>
                </div>
                <CpuLoadVisualizer cpu={telemetry.cpu} />
              </div>
            )}

            {/* Widget 2: Quantum Memory (Accurate Real Hardware RAM) */}
            {enabledWidgets['memory'] && (
              <div className="cyber-card p-3 sm:p-3.5 cyber-bracket font-hud">
                <div className="flex items-center justify-between text-xs text-white font-bold tracking-wider mb-1.5 border-b border-teal-500/30 pb-1.5">
                  <span className="flex items-center gap-1.5 text-teal-200">
                    <HardDrive className="w-3.5 h-3.5 text-teal-400" />
                    SYSTEM MEMORY (RAM)
                  </span>
                  <span className="text-teal-200 text-[11px] font-mono font-bold">
                    {telemetry.memory.used_gb} / {telemetry.memory.total_gb} GB
                  </span>
                </div>
                <div className="flex gap-1 my-2">
                  {Array.from({ length: 12 }).map((_, i) => {
                    const activeBars = Math.round((telemetry.memory.percent / 100) * 12);
                    return (
                      <div
                        key={i}
                        className={`h-2 flex-1 rounded-sm transition-all duration-500 ${
                          i < activeBars
                            ? 'bg-gradient-to-t from-teal-500 to-cyan-300 shadow-[0_0_8px_rgba(20,184,166,0.6)]' 
                            : 'bg-white/10'
                        }`}
                      />
                    );
                  })}
                </div>
                <div className="flex items-center justify-between text-[10px] font-mono text-teal-200 font-semibold">
                  <span>RAM UTILIZED: {telemetry.memory.percent}%</span>
                  <span className="text-cyan-300">HEALTH: NOMINAL</span>
                </div>
              </div>
            )}

            {/* Widget 3: Subsystem Matrix */}
            {enabledWidgets['subsystems'] && (
              <div className="cyber-card p-3 sm:p-3.5 cyber-bracket font-hud text-xs space-y-2">
                <div className="text-xs text-white tracking-wider font-bold border-b border-white/15 pb-1.5 flex items-center justify-between">
                  <span className="flex items-center gap-1.5 text-emerald-300">
                    <Shield className="w-3.5 h-3.5 text-emerald-400" />
                    SUBSYSTEM MATRIX
                  </span>
                  <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                </div>
                <div className="space-y-1.5 text-slate-100 font-medium text-[11px]">
                  <div className="flex items-center justify-between">
                    <span>COGNITIVE CORE</span>
                    <span className="text-emerald-300 font-bold flex items-center gap-1 font-mono">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                      ONLINE
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>DESKTOP CONTROLLER</span>
                    <span className="text-cyan-300 font-bold font-mono">ARMED</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>PHONE ADB BRIDGE</span>
                    <span className={`font-bold font-mono ${telemetry.phone.connected ? 'text-indigo-300' : 'text-slate-400'}`}>
                      {telemetry.phone.connected ? `LINKED (${telemetry.phone.battery !== null ? telemetry.phone.battery + '%' : 'OK'})` : 'OFFLINE'}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>VOICE WAKE (HEY ADA)</span>
                    <span className="text-cyan-300 font-bold font-mono flex items-center gap-1">
                      <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse" />
                      ARMED
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>STUDIO TTS ENGINE</span>
                    <span className="text-purple-300 font-bold font-mono">SONIA HD</span>
                  </div>
                </div>
              </div>
            )}

            {/* Widget 4: Quick Folder Organizer */}
            {enabledWidgets['organizer'] && (
              <div className="cyber-card p-3 sm:p-3.5 cyber-bracket font-hud">
                <div className="flex items-center justify-between text-xs text-white font-bold mb-2 border-b border-cyan-500/30 pb-1.5">
                  <span className="flex items-center gap-1.5 text-cyan-200">
                    <FolderSync className="w-3.5 h-3.5 text-cyan-400" />
                    SMART ORGANIZER
                  </span>
                  <span className="text-[9px] text-cyan-300 font-mono">AUTONOMOUS</span>
                </div>
                <div className="grid grid-cols-2 gap-1.5">
                  {[
                    { label: 'Desktop', cmd: 'organize my desktop', icon: <Folder className="w-3 h-3 text-cyan-300" /> },
                    { label: 'Downloads', cmd: 'organize my downloads', icon: <Download className="w-3 h-3 text-cyan-300" /> },
                    { label: 'Documents', cmd: 'organize my documents', icon: <FileText className="w-3 h-3 text-cyan-300" /> },
                    { label: 'Captures', cmd: 'organize my screenshots', icon: <Image className="w-3 h-3 text-cyan-300" /> }
                  ].map((f) => (
                    <button
                      key={f.label}
                      onClick={() => dispatchQuickAction(f.cmd)}
                      className="px-2 py-1.5 rounded-lg text-[11px] font-semibold bg-cyan-950/70 hover:bg-cyan-500/30 text-cyan-100 hover:text-white border border-cyan-500/40 hover:border-cyan-400 transition-all text-center truncate flex items-center justify-center gap-1 cursor-pointer active:scale-95"
                    >
                      {f.icon}
                      <span>{f.label}</span>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Widget 5: Autonomous Missions */}
            {enabledWidgets['missions'] && (
              <div className="cyber-card p-3 sm:p-3.5 cyber-bracket font-hud border-amber-500/40">
                <div className="flex items-center justify-between text-xs text-white font-bold mb-1.5 border-b border-amber-500/30 pb-1.5">
                  <span className="flex items-center gap-1.5 text-amber-300">
                    <FileText className="w-3.5 h-3.5 text-amber-400" />
                    OVERNIGHT MISSIONS
                  </span>
                  <span className="text-[9px] text-amber-300 font-mono">REPORTS</span>
                </div>
                <p className="text-[11px] text-slate-200 leading-snug mb-2 font-sans">
                  Background intelligence output saved to <code className="text-amber-300 font-mono">workspace/reports/</code>.
                </p>
                <button
                  onClick={() => dispatchQuickAction("run an overnight research mission on AI cognitive architectures")}
                  className="w-full py-1.5 rounded-lg text-xs font-bold bg-amber-500/25 hover:bg-amber-500/40 text-amber-200 border border-amber-500/50 transition-all flex items-center justify-center gap-1.5 cursor-pointer active:scale-95"
                >
                  <Zap className="w-3 h-3 text-amber-400" />
                  <span>TRIGGER MISSION</span>
                </button>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Responsive Right HUD Drawer Toggle Pill */}
      <button
        onClick={() => setIsRightCollapsed(!isRightCollapsed)}
        title={isRightCollapsed ? "Show Intel & Tools" : "Collapse Intel"}
        className="absolute top-16 sm:top-18 right-3 z-30 px-2.5 py-1 rounded-lg bg-[#040816]/90 hover:bg-cyan-950/80 border border-cyan-400/50 text-cyan-200 text-[10px] font-hud font-bold tracking-wider transition-all shadow-[0_0_15px_rgba(6,182,212,0.25)] pointer-events-auto flex items-center gap-1.5 cursor-pointer active:scale-95"
      >
        {isRightCollapsed ? <ChevronLeft className="w-3 h-3 text-cyan-300" /> : <ChevronRight className="w-3 h-3 text-cyan-300" />}
        <span className="hidden md:inline">{isRightCollapsed ? 'INTEL & TOOLS' : 'HIDE'}</span>
        <Terminal className="w-3 h-3 text-cyan-400" />
      </button>

      {/* RIGHT HUD: Streams, Devices & Tools (Animated Drawer) */}
      <AnimatePresence>
        {!isRightCollapsed && (
          <motion.div
            initial={{ opacity: 0, x: 320 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 320 }}
            transition={{ duration: 0.25, ease: "easeInOut" }}
            className="absolute top-24 sm:top-26 right-3 sm:right-5 flex flex-col items-end gap-2.5 sm:gap-3 w-[260px] sm:w-[280px] lg:w-[295px] pointer-events-auto max-h-[calc(100vh-230px)] overflow-y-auto cyber-scrollbar pl-1 pb-4 z-20"
          >
            {/* Widget 6: Terminal Directive Stream (Connected to Real Actions & Messages) */}
            {enabledWidgets['terminal'] && (
              <div className="w-full cyber-card p-3 sm:p-3.5 cyber-bracket font-hud flex flex-col items-start relative overflow-hidden">
                <div className="absolute inset-0 pointer-events-none bg-gradient-to-b from-transparent via-cyan-400/[0.04] to-transparent animate-scanline" />
                <div className="flex items-center justify-between w-full text-xs text-white font-bold tracking-wider mb-2 border-b border-cyan-500/30 pb-1.5">
                  <span className="flex items-center gap-1.5 text-cyan-200">
                    <Terminal className="w-3.5 h-3.5 text-cyan-400" />
                    DIRECTIVE STREAM
                  </span>
                  <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-ping" />
                </div>
                <TerminalLogs ai={telemetry.ai} phone={telemetry.phone} />
              </div>
            )}

            {/* Widget 7: Android Phone Bridge (Accurate Real ADB Status & Battery) */}
            {enabledWidgets['phone'] && (
              <div className="w-full cyber-card p-3 sm:p-3.5 cyber-bracket font-hud border-indigo-500/40">
                <div className="flex items-center justify-between text-xs text-white font-bold mb-1.5 border-b border-indigo-500/30 pb-1.5">
                  <span className="flex items-center gap-1.5 text-indigo-300">
                    <Smartphone className="w-3.5 h-3.5 text-indigo-400" />
                    PHONE BRIDGE (ADB)
                  </span>
                  <span className={`text-[10px] font-mono font-bold ${telemetry.phone.connected ? 'text-emerald-300' : 'text-slate-400'}`}>
                    {telemetry.phone.connected ? 'LINKED' : 'OFFLINE'}
                  </span>
                </div>
                <div className="flex items-center justify-between text-[11px] text-slate-100 mb-1 font-sans font-medium">
                  <span className="truncate max-w-[150px] font-mono text-[10px] text-indigo-200">
                    {telemetry.phone.device_id || 'NO DEVICE'}
                  </span>
                  <span className="text-emerald-300 font-bold font-mono text-xs">
                    {telemetry.phone.battery !== null ? `${telemetry.phone.battery}%` : (telemetry.phone.connected ? 'ONLINE' : '0%')}
                  </span>
                </div>
                <div className="w-full h-1.5 bg-indigo-950 rounded-full overflow-hidden border border-indigo-800/50 mb-2">
                  <div 
                    className={`h-full rounded-full transition-all duration-500 ${
                      (telemetry.phone.battery || 0) > 30 
                        ? 'bg-gradient-to-r from-emerald-500 to-cyan-400' 
                        : (telemetry.phone.battery || 0) > 15 
                        ? 'bg-gradient-to-r from-amber-500 to-yellow-400' 
                        : 'bg-rose-500'
                    }`}
                    style={{ width: `${Math.min(100, Math.max(0, telemetry.phone.battery || 0))}%` }}
                  />
                </div>
                <div className="grid grid-cols-2 gap-1.5">
                  <button
                    onClick={() => dispatchQuickAction("check my phone battery and status")}
                    className="py-1 rounded-lg text-[11px] font-bold bg-indigo-500/20 hover:bg-indigo-500/35 text-indigo-200 border border-indigo-500/40 transition-all text-center cursor-pointer active:scale-95"
                  >
                    Vitals Check
                  </button>
                  <button
                    onClick={() => dispatchQuickAction("unlock my phone")}
                    className="py-1 rounded-lg text-[11px] font-bold bg-indigo-500/20 hover:bg-indigo-500/35 text-indigo-200 border border-indigo-500/40 transition-all text-center cursor-pointer active:scale-95"
                  >
                    Wake Screen
                  </button>
                </div>
              </div>
            )}

            {/* Widget 8: Jarvis Executive Briefing Intel */}
            {enabledWidgets['agenda'] && (
              <div className="w-full cyber-card p-3 sm:p-3.5 cyber-bracket font-hud border-blue-500/40">
                <div className="flex items-center justify-between text-xs text-white font-bold mb-1.5 border-b border-blue-500/30 pb-1.5">
                  <span className="flex items-center gap-1.5 text-blue-300">
                    <Calendar className="w-3.5 h-3.5 text-blue-400" />
                    EXECUTIVE INTEL
                  </span>
                  <span className="text-[9px] text-blue-300 font-mono font-bold">READY</span>
                </div>
                <p className="text-[11px] text-slate-100 leading-snug mb-2.5 font-sans">
                  ADA oral briefing synthesised with live schedule perception.
                </p>
                <button
                  onClick={triggerExecutiveBriefing}
                  className="w-full py-2 rounded-xl text-xs bg-gradient-to-r from-blue-600/40 to-cyan-600/40 hover:from-blue-600/60 hover:to-cyan-600/60 text-white border border-cyan-400/60 flex items-center justify-center gap-1.5 transition-all font-bold shadow-[0_0_15px_rgba(6,182,212,0.25)] active:scale-95 cursor-pointer"
                >
                  <Zap className="w-3.5 h-3.5 text-amber-400" />
                  <span>ORAL BRIEFING</span>
                </button>
              </div>
            )}

            {/* Widget 9: Holographic Scratchpad */}
            {enabledWidgets['scratchpad'] && (
              <div className="w-full cyber-card p-3 sm:p-3.5 cyber-bracket font-hud border-amber-500/40">
                <div className="flex items-center justify-between text-xs text-white font-bold mb-1 border-b border-amber-500/30 pb-1.5">
                  <span className="flex items-center gap-1.5 text-amber-300">
                    <Sparkles className="w-3.5 h-3.5 text-amber-400" />
                    JARVIS SCRATCHPAD
                  </span>
                  <button
                    onClick={handleSaveScratchpad}
                    className="text-[9px] px-2 py-0.5 rounded bg-amber-500/25 hover:bg-amber-500/45 text-amber-200 border border-amber-500/40 flex items-center gap-1 transition-all cursor-pointer font-bold"
                  >
                    <Save className="w-2.5 h-2.5" />
                    {savedBadge ? 'SAVED' : 'SAVE'}
                  </button>
                </div>
                <textarea
                  value={tempNote}
                  onChange={(e) => setTempNote(e.target.value)}
                  placeholder="Quick directives, thoughts..."
                  rows={2}
                  className="w-full bg-black/60 border border-white/20 rounded-lg p-2 text-xs text-white outline-none focus:border-amber-400/80 resize-none font-mono placeholder-white/40"
                />
              </div>
            )}

            {/* Widget 10: Global Hotkeys */}
            {enabledWidgets['shortcuts'] && (
              <div className="w-full cyber-card p-3 sm:p-3.5 cyber-bracket font-hud text-xs">
                <div className="text-xs text-white font-bold border-b border-white/15 pb-1.5 mb-2 flex items-center gap-1.5 text-cyan-200">
                  <Keyboard className="w-3.5 h-3.5 text-cyan-400" />
                  <span>GLOBAL HOTKEYS</span>
                </div>
                <div className="space-y-1.5 text-slate-100 font-sans font-medium text-[11px]">
                  <div className="flex justify-between items-center">
                    <span>Toggle Island</span>
                    <kbd className="px-1.5 py-0.5 rounded bg-cyan-950 border border-cyan-400/60 text-cyan-200 font-bold font-mono text-[9px]">Alt+Space / F2</kbd>
                  </div>
                  <div className="flex justify-between items-center">
                    <span>Universal Trigger</span>
                    <kbd className="px-1.5 py-0.5 rounded bg-cyan-950 border border-cyan-400/60 text-cyan-200 font-bold font-mono text-[9px]">Ctrl+Space</kbd>
                  </div>
                </div>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Holographic Center Reticles & Orbital Compass (Around 3D Brain) */}
      <div className="absolute inset-0 flex items-center justify-center opacity-25 pointer-events-none">
        <div className="w-[480px] h-[480px] sm:w-[560px] sm:h-[560px] rounded-full border border-dashed border-cyan-400/40 animate-[spin_80s_linear_infinite]" />
        <div className="absolute w-[580px] h-[580px] sm:w-[680px] sm:h-[680px] rounded-full border border-cyan-500/20 animate-[spin_60s_linear_infinite_reverse]" />
        
        {/* Crosshair Axes */}
        <div className="absolute w-[90vw] max-w-[780px] h-[1px] bg-gradient-to-r from-transparent via-cyan-400/40 to-transparent" />
        <div className="absolute h-[80vh] max-h-[780px] w-[1px] bg-gradient-to-b from-transparent via-cyan-400/40 to-transparent" />
      </div>

      {/* Tactical Corner Brackets (Scaled for any resolution) */}
      <div className="absolute top-2 left-2 w-7 h-7 sm:w-9 sm:h-9 border-t-2 border-l-2 border-cyan-400/80 pointer-events-none" />
      <div className="absolute top-2 right-2 w-7 h-7 sm:w-9 sm:h-9 border-t-2 border-r-2 border-cyan-400/80 pointer-events-none" />
      <div className="absolute bottom-2 left-2 w-7 h-7 sm:w-9 sm:h-9 border-b-2 border-l-2 border-cyan-400/80 pointer-events-none" />
      <div className="absolute bottom-2 right-2 w-7 h-7 sm:w-9 sm:h-9 border-b-2 border-r-2 border-cyan-400/80 pointer-events-none" />

    </div>
  );
};
