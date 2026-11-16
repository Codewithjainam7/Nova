import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Sparkles, Shield, Cpu, Volume2, CheckCircle2 } from 'lucide-react';

interface StartupOverlayProps {
  onComplete?: () => void;
  forceShow?: boolean;
}

export const StartupOverlay: React.FC<StartupOverlayProps> = ({ onComplete, forceShow = false }) => {
  const [visible, setVisible] = useState(true);
  const [progress, setProgress] = useState(0);
  const [currentStep, setCurrentStep] = useState(0);

  const steps = [
    { label: "QUANTUM KERNEL CORE", status: "INITIALIZED", icon: <Cpu className="w-3.5 h-3.5 text-cyan-400" /> },
    { label: "DUAL-HEMISPHERE CORTEX", status: "SYNAPSED // 120B", icon: <Sparkles className="w-3.5 h-3.5 text-purple-400" /> },
    { label: "ADA V2 STUDIO AUDIO (SONIA)", status: "ONLINE // 48kHz", icon: <Volume2 className="w-3.5 h-3.5 text-pink-400" /> },
    { label: "MARK VII DISPATCH MATRIX", status: "ARMED // NOMINAL", icon: <Shield className="w-3.5 h-3.5 text-emerald-400" /> }
  ];

  useEffect(() => {
    // Check if startup already played in this browser session (unless forced)
    if (!forceShow) {
      const alreadyPlayed = sessionStorage.getItem('ada_startup_played');
      if (alreadyPlayed) {
        setVisible(false);
        onComplete?.();
        return;
      }
    }
    sessionStorage.setItem('ada_startup_played', 'true');

    // Play synthesized Jarvis Mark VII startup sound
    try {
      const audio = new Audio('/sounds/startup.wav');
      audio.volume = 0.85;
      audio.play().catch(() => {
        // Autoplay may be restricted until user interacts
      });
    } catch {}

    // Animate progress and step sequence
    const stepInterval = setInterval(() => {
      setCurrentStep(prev => Math.min(prev + 1, steps.length - 1));
    }, 420);

    const progressInterval = setInterval(() => {
      setProgress(prev => {
        if (prev >= 100) {
          clearInterval(progressInterval);
          return 100;
        }
        return prev + 5;
      });
    }, 90);

    // End startup sequence after 2.6 seconds
    const exitTimer = setTimeout(() => {
      setVisible(false);
      onComplete?.();
    }, 2600);

    return () => {
      clearInterval(stepInterval);
      clearInterval(progressInterval);
      clearTimeout(exitTimer);
    };
  }, [forceShow]);

  if (!visible) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 1 }}
        exit={{ opacity: 0, scale: 1.05 }}
        transition={{ duration: 0.5, ease: "easeInOut" }}
        className="fixed inset-0 z-[200] bg-[#020409] flex flex-col items-center justify-center p-6 select-none overflow-hidden"
      >
        {/* Deep Space Radial Glow */}
        <div 
          className="absolute inset-0 pointer-events-none"
          style={{
            background: 'radial-gradient(circle at 50% 50%, rgba(10, 32, 64, 0.6) 0%, rgba(2, 6, 18, 0.95) 70%, #020409 100%)'
          }}
        />

        {/* Ambient Laser Scanline */}
        <div className="absolute inset-0 pointer-events-none bg-gradient-to-b from-transparent via-cyan-400/[0.06] to-transparent animate-scanline" />

        {/* Precision Targeting Corner Brackets */}
        <motion.div 
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.6 }}
          className="absolute inset-8 sm:inset-14 border border-cyan-500/20 pointer-events-none"
        >
          <div className="absolute -top-1 -left-1 w-8 h-8 border-t-2 border-l-2 border-cyan-400" />
          <div className="absolute -top-1 -right-1 w-8 h-8 border-t-2 border-r-2 border-cyan-400" />
          <div className="absolute -bottom-1 -left-1 w-8 h-8 border-b-2 border-l-2 border-cyan-400" />
          <div className="absolute -bottom-1 -right-1 w-8 h-8 border-b-2 border-r-2 border-cyan-400" />
        </motion.div>

        {/* Center Quantum Arc Reactor Boot Core */}
        <div className="relative flex items-center justify-center mb-8">
          {/* Outer Dashed Gyro Ring */}
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ repeat: Infinity, duration: 6, ease: "linear" }}
            className="w-36 h-36 sm:w-44 sm:h-44 rounded-full border-2 border-dashed border-cyan-400/60 shadow-[0_0_30px_rgba(34,211,238,0.3)]"
          />

          {/* Middle Counter-Rotating Violet Halo */}
          <motion.div
            animate={{ rotate: -360 }}
            transition={{ repeat: Infinity, duration: 4, ease: "linear" }}
            className="absolute w-28 h-28 sm:w-34 sm:h-34 rounded-full border border-purple-400/80 border-t-transparent border-b-transparent"
          />

          {/* Inner Pulsing Plasma Core */}
          <motion.div
            animate={{ scale: [0.85, 1.25, 0.85], opacity: [0.7, 1, 0.7] }}
            transition={{ repeat: Infinity, duration: 1.2, ease: "easeInOut" }}
            className="absolute w-16 h-16 sm:w-20 sm:h-20 rounded-full bg-gradient-to-tr from-cyan-500 to-blue-400 flex items-center justify-center shadow-[0_0_40px_#22d3ee]"
          >
            <Sparkles className="w-8 h-8 text-black animate-pulse" />
          </motion.div>
        </div>

        {/* Main Title & Architecture Readout */}
        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ duration: 0.5, delay: 0.2 }}
          className="text-center space-y-2 z-10 max-w-md w-full"
        >
          <div className="flex items-center justify-center gap-2">
            <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping" />
            <h1 className="text-xl sm:text-2xl font-hud font-bold tracking-[0.25em] text-white uppercase bg-gradient-to-r from-cyan-200 via-white to-purple-200 bg-clip-text text-transparent drop-shadow-[0_0_15px_rgba(34,211,238,0.6)]">
              ADA MARK VII
            </h1>
          </div>
          <p className="text-xs font-hud font-bold tracking-[0.3em] text-cyan-300 uppercase">
            AUTONOMOUS COGNITIVE OS // SYSTEM BOOT
          </p>

          {/* Charging Progress Bar */}
          <div className="w-full bg-black/60 border border-cyan-500/40 rounded-full h-2 my-4 overflow-hidden p-0.5">
            <motion.div 
              className="h-full bg-gradient-to-r from-cyan-500 via-blue-400 to-purple-400 rounded-full shadow-[0_0_10px_#22d3ee]"
              style={{ width: `${progress}%` }}
              transition={{ ease: "easeOut" }}
            />
          </div>

          {/* System Diagnostic Sequence Ticker */}
          <div className="space-y-1.5 pt-2 font-mono text-[11px] text-left">
            {steps.map((step, idx) => (
              <motion.div
                key={step.label}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: idx <= currentStep ? 1 : 0.2, x: 0 }}
                className="flex items-center justify-between text-slate-200 bg-white/[0.03] px-3 py-1 rounded border border-white/[0.08]"
              >
                <span className="flex items-center gap-2">
                  {step.icon}
                  <span className="font-hud font-semibold tracking-wider">{step.label}</span>
                </span>
                <span className="text-emerald-300 font-bold flex items-center gap-1 font-mono text-[10px]">
                  {idx <= currentStep ? (
                    <>
                      <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                      <span>{step.status}</span>
                    </>
                  ) : (
                    <span className="text-white/30">PENDING...</span>
                  )}
                </span>
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* Footer Hotkey & Security Tag */}
        <div className="absolute bottom-6 inset-x-0 text-center font-hud text-[11px] text-cyan-400/80 tracking-[0.2em] uppercase font-bold">
          SECURITY PROTOCOL AES-256 ACTIVE // QUANTUM SYNAPSE ARMED
        </div>
      </motion.div>
    </AnimatePresence>
  );
};
