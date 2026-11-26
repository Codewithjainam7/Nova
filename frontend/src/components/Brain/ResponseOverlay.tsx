import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Volume2, X } from 'lucide-react';
import { useWidgetStore } from '../../store/useWidgetStore';

interface ResponseOverlayProps {
  response: string;
  interimTranscript: string;
  isListening: boolean;
  isProcessing: boolean;
}

export const ResponseOverlay: React.FC<ResponseOverlayProps> = ({ 
  response, 
  interimTranscript, 
  isListening, 
  isProcessing 
}) => {
  const { isCustomizerOpen } = useWidgetStore();
  const [dismissed, setDismissed] = React.useState(false);

  React.useEffect(() => {
    if (response) {
      setDismissed(false);
    }
  }, [response]);

  if (isCustomizerOpen) return null;

  return (
    <div className="absolute inset-0 pointer-events-none flex flex-col items-center justify-end pb-36 sm:pb-40 md:pb-44 z-20 px-3 sm:px-4">
      {/* Interim transcript (live speech visualizer) */}
      <AnimatePresence mode="wait">
        {isListening && interimTranscript && (
          <motion.div
            key="interim"
            initial={{ opacity: 0, y: 10, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -10, scale: 0.95 }}
            className="mb-3 px-4 sm:px-6 py-2.5 sm:py-3 rounded-2xl border border-cyan-400/50 bg-[#030612]/92 backdrop-blur-2xl max-w-md sm:max-w-lg md:max-w-xl text-center shadow-[0_0_35px_rgba(6,182,212,0.25)]"
          >
            <div className="flex items-center justify-center gap-1.5 mb-1">
              <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-ping" />
              <p className="text-[10px] text-cyan-300 uppercase tracking-widest font-hud font-bold">Live Speech Recognition</p>
            </div>
            <p className="text-cyan-100 text-xs sm:text-sm font-sans font-light tracking-wide">{interimTranscript}</p>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Futuristic Jarvis Cybernetic Neural Processing HUD */}
      <AnimatePresence>
        {isProcessing && (
          <motion.div
            initial={{ opacity: 0, scale: 0.88, y: 15 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.88, y: -10 }}
            transition={{ type: "spring", stiffness: 350, damping: 25 }}
            className="mb-3"
          >
            <div className="relative overflow-hidden flex items-center gap-3 sm:gap-4 px-4 sm:px-6 py-2.5 sm:py-3 rounded-full bg-gradient-to-r from-[#030612]/95 via-[#080e28]/95 to-[#030612]/95 border border-cyan-400/60 shadow-[0_0_40px_rgba(6,182,212,0.4),inset_0_0_20px_rgba(168,85,247,0.2)] backdrop-blur-2xl">
              
              {/* Animated Laser Scanline Sweep */}
              <motion.div
                animate={{ x: ['-100%', '300%'] }}
                transition={{ repeat: Infinity, duration: 2.2, ease: "linear" }}
                className="absolute inset-y-0 w-28 bg-gradient-to-r from-transparent via-cyan-400/30 to-transparent pointer-events-none"
              />

              {/* Orbital Cybernetic Arc Reactor */}
              <div className="relative w-6 h-6 sm:w-7 sm:h-7 flex items-center justify-center shrink-0">
                <motion.div
                  animate={{ rotate: 360 }}
                  transition={{ repeat: Infinity, duration: 3, ease: "linear" }}
                  className="absolute inset-0 rounded-full border-2 border-dashed border-cyan-400/80"
                />
                <motion.div
                  animate={{ rotate: -360 }}
                  transition={{ repeat: Infinity, duration: 1.8, ease: "linear" }}
                  className="absolute w-3.5 h-3.5 sm:w-4 sm:h-4 rounded-full border-2 border-purple-400/90 border-t-transparent border-b-transparent"
                />
                <motion.span
                  animate={{ scale: [0.75, 1.3, 0.75], opacity: [0.6, 1, 0.6] }}
                  transition={{ repeat: Infinity, duration: 1.2, ease: "easeInOut" }}
                  className="w-1.5 h-1.5 sm:w-2 sm:h-2 rounded-full bg-cyan-300 shadow-[0_0_10px_#22d3ee]"
                />
              </div>

              {/* Dynamic Neural Synapse Frequency Waveform */}
              <div className="flex items-center gap-1 h-4 sm:h-5 px-1 shrink-0">
                {[0.45, 0.9, 0.6, 1.0, 0.7, 0.35, 0.85, 0.55].map((multiplier, i) => (
                  <motion.span
                    key={i}
                    animate={{
                      height: [3, 16 * multiplier, 5, 18 * multiplier, 3],
                      backgroundColor: ['#22d3ee', '#c084fc', '#38bdf8', '#a855f7', '#22d3ee']
                    }}
                    transition={{
                      repeat: Infinity,
                      duration: 0.75 + i * 0.08,
                      ease: 'easeInOut'
                    }}
                    className="w-[2px] sm:w-[2.5px] rounded-full shadow-[0_0_8px_rgba(34,211,238,0.6)]"
                  />
                ))}
              </div>

              {/* Holographic Neural Typography */}
              <div className="flex flex-col items-start leading-none gap-0.5 sm:gap-1">
                <span className="text-[10px] sm:text-[11px] font-hud font-bold tracking-[0.2em] uppercase bg-gradient-to-r from-cyan-300 via-white to-purple-300 bg-clip-text text-transparent drop-shadow-[0_0_8px_rgba(34,211,238,0.4)]">
                  NEURAL SYNAPSE COGNITION
                </span>
                <div className="flex items-center gap-1 text-[8px] sm:text-[9px] font-mono text-cyan-300 tracking-wider">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping inline-block" />
                  <span>QUANTUM CORE // NEURAL ENGINE ACTIVE</span>
                </div>
              </div>

              {/* High-Tech Status Pill */}
              <div className="px-2 py-0.5 sm:px-2.5 sm:py-1 rounded-full bg-cyan-950/80 border border-cyan-400/40 text-[8px] sm:text-[9px] font-hud font-bold text-cyan-200 tracking-wider flex items-center gap-1 shadow-[0_0_12px_rgba(6,182,212,0.25)] shrink-0 ml-1 sm:ml-2">
                <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse" />
                <span>THINKING</span>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* ADA's Response Glass Card (Fully Responsive & Dismissible) */}
      <AnimatePresence mode="wait">
        {response && !isListening && !isProcessing && !dismissed && (
          <motion.div
            key={response}
            initial={{ opacity: 0, y: 15, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -10, scale: 0.98 }}
            transition={{ duration: 0.3 }}
            className="relative mx-4 px-6 sm:px-9 py-4 sm:py-5 rounded-2xl border border-cyan-400/40 bg-[#030612]/94 backdrop-blur-2xl w-[calc(100%-2rem)] max-w-md sm:max-w-lg md:max-w-xl max-h-[42vh] overflow-y-auto overflow-x-hidden text-center shadow-[0_0_45px_rgba(6,182,212,0.25)] pointer-events-auto cyber-bracket"
          >
            {/* Dismiss Button */}
            <button
              onClick={() => setDismissed(true)}
              className="absolute top-3 right-3 text-white/50 hover:text-white p-1 rounded-lg hover:bg-white/10 transition-colors cursor-pointer"
              title="Dismiss"
            >
              <X className="w-3.5 h-3.5 sm:w-4 sm:h-4" />
            </button>

            <div className="flex items-center justify-center gap-1.5 sm:gap-2 mb-2 px-6">
              <Volume2 className="w-3.5 h-3.5 sm:w-4 sm:h-4 text-cyan-400 animate-pulse shrink-0" />
              <p className="text-[10px] text-cyan-300 uppercase tracking-widest font-hud font-bold">ADA DIRECTIVE RESPONSE</p>
            </div>
            <p className="px-2 text-white/95 text-xs sm:text-sm leading-relaxed font-sans font-normal tracking-wide whitespace-pre-wrap break-words [overflow-wrap:anywhere]">{response}</p>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};
