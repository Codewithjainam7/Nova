import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNovaStore } from '../store/useNovaStore';
import { Mic, BrainCircuit, Globe, Monitor, ScanEye, CheckCircle, XCircle } from 'lucide-react';
import clsx from 'clsx';

export const DynamicIsland: React.FC = () => {
  const { islandState, islandMessage } = useNovaStore();
  const [expanded, setExpanded] = useState(false);

  if (islandState === 'idle') return null;

  const getIcon = () => {
    switch (islandState) {
      case 'listening': return <Mic className="w-5 h-5 text-blue-400 animate-pulse" />;
      case 'thinking': return <BrainCircuit className="w-5 h-5 text-purple-400 animate-pulse" />;
      case 'executing': return <CheckCircle className="w-5 h-5 text-green-400 animate-pulse" />;
      case 'browser': return <Globe className="w-5 h-5 text-blue-500 animate-pulse" />;
      case 'desktop': return <Monitor className="w-5 h-5 text-indigo-400 animate-pulse" />;
      case 'vision': return <ScanEye className="w-5 h-5 text-cyan-400 animate-pulse" />;
      case 'error': return <XCircle className="w-5 h-5 text-red-500" />;
      default: return null;
    }
  };

  const islandVariants = {
    collapsed: { width: 180, height: 48, borderRadius: 24 },
    expanded: { width: 320, height: 120, borderRadius: 32 }
  };

  return (
    <div className="fixed top-6 left-1/2 transform -translate-x-1/2 z-50 drop-shadow-2xl">
      <motion.div
        layout
        initial="collapsed"
        animate={expanded ? "expanded" : "collapsed"}
        variants={islandVariants}
        transition={{ type: "spring", stiffness: 300, damping: 24 }}
        onClick={() => setExpanded(!expanded)}
        className="bg-black/80 backdrop-blur-xl border border-white/10 text-white overflow-hidden cursor-pointer flex flex-col justify-center shadow-black/50 shadow-2xl"
      >
        <div className="flex items-center justify-between px-4 h-12 w-full">
          <div className="flex items-center gap-3">
            {getIcon()}
            <AnimatePresence mode="wait">
              <motion.span
                key={islandMessage}
                initial={{ opacity: 0, y: 5 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -5 }}
                className={clsx("text-sm font-medium", expanded ? "truncate max-w-[200px]" : "truncate max-w-[100px]")}
              >
                {islandMessage || 'Processing...'}
              </motion.span>
            </AnimatePresence>
          </div>
          
          {/* Example waveform if listening */}
          {islandState === 'listening' && !expanded && (
             <div className="flex gap-1 items-center h-4">
                <motion.div animate={{ height: [4, 12, 4] }} transition={{ repeat: Infinity, duration: 0.5 }} className="w-1 bg-blue-400 rounded-full"/>
                <motion.div animate={{ height: [8, 16, 8] }} transition={{ repeat: Infinity, duration: 0.6 }} className="w-1 bg-blue-400 rounded-full"/>
                <motion.div animate={{ height: [4, 12, 4] }} transition={{ repeat: Infinity, duration: 0.5 }} className="w-1 bg-blue-400 rounded-full"/>
             </div>
          )}
        </div>

        <AnimatePresence>
          {expanded && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="px-4 pb-4 flex flex-col gap-2"
            >
              <div className="h-[1px] w-full bg-white/10 my-1"></div>
              <p className="text-xs text-white/50">Current Phase:</p>
              <p className="text-sm font-semibold">{islandState.toUpperCase()}</p>
              <button 
                onClick={(e) => {
                  e.stopPropagation();
                  // Cancel logic here
                }}
                className="mt-1 w-full py-1.5 bg-red-500/20 hover:bg-red-500/40 text-red-400 rounded-lg text-xs font-medium transition-colors"
              >
                Cancel Task
              </button>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>
    </div>
  );
};
