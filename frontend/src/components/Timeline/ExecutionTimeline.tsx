import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNovaStore } from '../../store/useNovaStore';
import { CheckCircle2, CircleDashed, XCircle } from 'lucide-react';
import clsx from 'clsx';

export const ExecutionTimeline: React.FC = () => {
  const { executionTimeline } = useNovaStore();

  if (executionTimeline.length === 0) return null;

  return (
    <div className="absolute right-6 top-24 w-80 bg-black/60 backdrop-blur-xl border border-white/10 rounded-2xl p-4 shadow-2xl flex flex-col gap-3 max-h-[60vh] overflow-y-auto">
      <h3 className="text-white/80 text-sm font-semibold mb-2 uppercase tracking-wider">Live Execution</h3>
      <div className="flex flex-col gap-3">
        <AnimatePresence>
          {executionTimeline.map((step, index) => (
            <motion.div
              key={step.id}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, scale: 0.9 }}
              className="flex items-start gap-3 relative"
            >
              {/* Connecting line */}
              {index !== executionTimeline.length - 1 && (
                <div className="absolute left-[9px] top-6 bottom-[-16px] w-[2px] bg-white/10" />
              )}
              
              <div className="mt-0.5 relative z-10 bg-black">
                {step.status === 'completed' && <CheckCircle2 className="w-5 h-5 text-green-400" />}
                {step.status === 'active' && <CircleDashed className="w-5 h-5 text-blue-400 animate-spin" />}
                {step.status === 'pending' && <div className="w-5 h-5 rounded-full border-2 border-white/20" />}
                {step.status === 'error' && <XCircle className="w-5 h-5 text-red-500" />}
              </div>
              
              <div className="flex flex-col">
                <span className={clsx(
                  "text-sm font-medium",
                  step.status === 'active' ? "text-white" : "text-white/60"
                )}>
                  {step.description}
                </span>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </div>
  );
};
