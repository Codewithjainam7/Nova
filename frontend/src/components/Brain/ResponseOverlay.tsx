import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';

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
  return (
    <div className="absolute inset-0 pointer-events-none flex flex-col items-center justify-end pb-48 z-10">
      {/* Interim transcript (what user is saying) */}
      <AnimatePresence mode="wait">
        {isListening && interimTranscript && (
          <motion.div
            key="interim"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="mb-6 px-6 py-3 rounded-2xl border border-cyan-500/20 bg-cyan-950/30 backdrop-blur-sm max-w-2xl text-center"
          >
            <p className="text-xs text-cyan-400/60 uppercase tracking-widest mb-1 font-medium">You</p>
            <p className="text-cyan-100 text-lg font-light">{interimTranscript}</p>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Processing indicator */}
      <AnimatePresence>
        {isProcessing && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="mb-4"
          >
            <div className="flex items-center gap-2 px-5 py-2.5 rounded-full bg-purple-950/40 border border-purple-500/20 backdrop-blur-sm">
              <div className="flex gap-1">
                <div className="w-1.5 h-1.5 rounded-full bg-purple-400 animate-bounce" style={{ animationDelay: '0ms' }} />
                <div className="w-1.5 h-1.5 rounded-full bg-purple-400 animate-bounce" style={{ animationDelay: '150ms' }} />
                <div className="w-1.5 h-1.5 rounded-full bg-purple-400 animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
              <span className="text-purple-300 text-sm font-light">Processing...</span>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* ADA's response */}
      <AnimatePresence mode="wait">
        {response && !isListening && !isProcessing && (
          <motion.div
            key={response}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.5 }}
            className="px-8 py-4 rounded-2xl border border-blue-500/15 bg-slate-950/50 backdrop-blur-md max-w-2xl text-center"
          >
            <p className="text-xs text-blue-400/50 uppercase tracking-widest mb-2 font-medium">ADA</p>
            <p className="text-blue-50 text-base leading-relaxed font-light">{response}</p>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};
