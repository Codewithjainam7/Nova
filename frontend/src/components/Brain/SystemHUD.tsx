import React, { useState, useEffect, memo } from 'react';
import { motion } from 'framer-motion';

const SystemClock = memo(() => {
  const [time, setTime] = useState('');
  useEffect(() => {
    const timer = setInterval(() => {
      const now = new Date();
      setTime(now.toLocaleTimeString('en-US', { hour12: false }) + '.' + now.getMilliseconds().toString().padStart(3, '0'));
    }, 50);
    return () => clearInterval(timer);
  }, []);
  return <span className="tracking-widest">SYS.ONLINE // {time}</span>;
});

const CpuLoad = memo(() => {
  const [cpuLoad, setCpuLoad] = useState([20, 45, 10, 80, 50, 30, 90, 40]);
  useEffect(() => {
    const interval = setInterval(() => {
      setCpuLoad(prev => prev.map(() => Math.floor(Math.random() * 100)));
    }, 400);
    return () => clearInterval(interval);
  }, []);
  return (
    <div className="flex gap-1 items-end h-12">
      {cpuLoad.map((load, i) => (
        <motion.div 
          key={i}
          className="w-2 bg-cyan-500/50"
          animate={{ height: `${load}%` }}
          transition={{ duration: 0.3 }}
        />
      ))}
    </div>
  );
});

const TerminalLogs = memo(() => {
  const [logs, setLogs] = useState<string[]>([]);
  useEffect(() => {
    const messages = [
      "INITIALIZING NEURAL PATHWAYS...",
      "RECALIBRATING KERNEL MATRIX: OK",
      "ALLOCATING VRAM [==========  ] 84%",
      "BYPASSING SECURITY PROTOCOLS...",
      "ESTABLISHING SECURE HANDSHAKE",
      "SYNCING BIOMETRIC DATA",
      "QUANTUM ENCRYPTION ACTIVE",
      "NODE CLUSTER 7 RESPONDING",
      "AWAITING USER DIRECTIVE...",
      "RUNNING DIAGNOSTICS: NOMINAL"
    ];
    
    const interval = setInterval(() => {
      const msg = messages[Math.floor(Math.random() * messages.length)];
      const hash = Math.random().toString(36).substring(2, 10).toUpperCase();
      setLogs(prev => [...prev.slice(-12), `[${hash}] ${msg}`]);
    }, 800);
    
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="absolute bottom-32 right-8 w-64 flex flex-col gap-1 text-[8px] font-mono text-cyan-500/60 opacity-80 text-right">
      {logs.map((log, i) => (
        <motion.div
          key={i}
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          className="whitespace-nowrap"
        >
          {log}
        </motion.div>
      ))}
    </div>
  );
});

export const SystemHUD: React.FC = () => {
  return (
    <div className="absolute inset-0 pointer-events-none z-0 overflow-hidden">
      {/* Top Left: System Metrics */}
      <div className="absolute top-8 left-8 flex flex-col gap-4 text-cyan-500 font-mono text-xs opacity-70">
        <div className="flex items-center gap-3">
          <div className="w-2 h-2 bg-cyan-400 animate-pulse rounded-full" />
          <SystemClock />
        </div>
        
        <div className="space-y-2 mt-4">
          <div className="text-[10px] tracking-widest text-cyan-600">CORE PROCESSING</div>
          <CpuLoad />
        </div>

        <div className="space-y-1 mt-4">
          <div className="text-[10px] tracking-widest text-cyan-600">MEMORY ALLOCATION</div>
          <div className="w-48 h-2 bg-cyan-950 border border-cyan-800">
            <motion.div 
              className="h-full bg-cyan-500/60"
              animate={{ width: `${60 + Math.random() * 20}%` }}
              transition={{ duration: 1 }}
            />
          </div>
        </div>
      </div>

      {/* Top Right: Status */}
      <div className="absolute top-8 right-8 text-right font-mono opacity-70">
        <div className="text-cyan-500 tracking-widest text-xs">ADA // MARK IV</div>
        <div className="text-cyan-600 text-[10px] tracking-widest mt-1">AUTONOMOUS OS</div>
        
        <div className="mt-8 flex flex-col items-end gap-1">
          <div className="w-16 h-[1px] bg-cyan-500/40" />
          <div className="w-12 h-[1px] bg-cyan-500/40" />
          <div className="w-20 h-[1px] bg-cyan-500/40" />
        </div>
      </div>

      {/* Bottom Right: Terminal */}
      <TerminalLogs />

      {/* Center Framing / Reticle (UI Level) */}
      <div className="absolute inset-0 flex items-center justify-center opacity-20">
        <div className="w-[500px] h-[500px] rounded-full border border-dashed border-cyan-500/30 animate-[spin_60s_linear_infinite]" />
        <div className="absolute w-[600px] h-[600px] rounded-full border border-cyan-500/10 animate-[spin_40s_linear_infinite_reverse]" />
        
        {/* Crosshairs */}
        <div className="absolute w-[800px] h-[1px] bg-gradient-to-r from-transparent via-cyan-500/30 to-transparent" />
        <div className="absolute h-[800px] w-[1px] bg-gradient-to-b from-transparent via-cyan-500/30 to-transparent" />
      </div>

      {/* Corner Markers */}
      <div className="absolute top-4 left-4 w-12 h-12 border-t-2 border-l-2 border-cyan-500/40" />
      <div className="absolute top-4 right-4 w-12 h-12 border-t-2 border-r-2 border-cyan-500/40" />
      <div className="absolute bottom-4 left-4 w-12 h-12 border-b-2 border-l-2 border-cyan-500/40" />
      <div className="absolute bottom-4 right-4 w-12 h-12 border-b-2 border-r-2 border-cyan-500/40" />
    </div>
  );
};
