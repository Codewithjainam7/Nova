import React from 'react';
import { ShieldAlert } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface PermissionDialogProps {
  isOpen: boolean;
  resourceType: 'Browser' | 'Desktop' | 'Vision' | 'Voice' | 'Filesystem';
  actionDescription: string;
  onDecision: (decision: 'allow_once' | 'allow_always' | 'deny') => void;
}

export const PermissionDialog: React.FC<PermissionDialogProps> = ({
  isOpen,
  resourceType,
  actionDescription,
  onDecision,
}) => {
  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.9, opacity: 0 }}
            className="w-full max-w-md bg-[#1a1c23] border border-white/10 rounded-2xl shadow-2xl p-6"
          >
            <div className="flex items-center gap-4 mb-4">
              <div className="w-12 h-12 rounded-full bg-red-500/20 flex items-center justify-center shrink-0">
                <ShieldAlert className="w-6 h-6 text-red-500" />
              </div>
              <div>
                <h2 className="text-lg font-bold text-white">Permission Required</h2>
                <p className="text-sm text-white/50">{resourceType} Access</p>
              </div>
            </div>

            <p className="text-white/80 text-sm mb-6 leading-relaxed">
              ADA Autonomous Agent is requesting access to perform the following action:
              <br />
              <strong className="text-white block mt-2 p-2 bg-black/30 rounded border border-white/5">
                {actionDescription}
              </strong>
            </p>

            <div className="flex flex-col gap-2">
              <button
                onClick={() => onDecision('allow_once')}
                className="w-full py-2.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-medium transition-colors"
              >
                Allow Once
              </button>
              <button
                onClick={() => onDecision('allow_always')}
                className="w-full py-2.5 rounded-lg bg-white/10 hover:bg-white/20 text-white font-medium transition-colors"
              >
                Always Allow for this Session
              </button>
              <button
                onClick={() => onDecision('deny')}
                className="w-full py-2.5 rounded-lg bg-red-500/10 hover:bg-red-500/20 text-red-400 font-medium transition-colors mt-2"
              >
                Deny
              </button>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
};
