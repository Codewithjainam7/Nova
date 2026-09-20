import React, { useState, useCallback } from 'react';
import { Mic, MicOff, Keyboard } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface VoiceControllerProps {
  isListening: boolean;
  onToggleListening: () => void;
  onSendText: (text: string) => void;
  isProcessing: boolean;
}

export const VoiceController: React.FC<VoiceControllerProps> = ({ 
  isListening, 
  onToggleListening, 
  onSendText,
  isProcessing 
}) => {
  const [showTextInput, setShowTextInput] = useState(false);
  const [textInput, setTextInput] = useState('');

  const handleTextSend = useCallback(() => {
    if (textInput.trim()) {
      onSendText(textInput.trim());
      setTextInput('');
      setShowTextInput(false);
    }
  }, [textInput, onSendText]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleTextSend();
    }
    if (e.key === 'Escape') {
      setShowTextInput(false);
    }
  };

  return (
    <div className="absolute bottom-8 left-1/2 -translate-x-1/2 z-20 flex flex-col items-center gap-4">
      {/* Text input toggle */}
      <AnimatePresence>
        {showTextInput && (
          <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.95 }}
            className="flex items-center gap-2 bg-black/50 backdrop-blur-xl border border-white/10 rounded-2xl p-2 w-[500px]"
          >
            <input
              autoFocus
              value={textInput}
              onChange={(e) => setTextInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Type a message..."
              className="flex-1 bg-transparent text-white placeholder-white/30 outline-none px-4 py-2.5 text-sm"
            />
            <button 
              onClick={handleTextSend}
              className="px-5 py-2.5 bg-blue-500 hover:bg-blue-600 text-white rounded-xl text-sm font-medium transition-colors"
            >
              Send
            </button>
          </motion.div>
        )}
      </AnimatePresence>

      <div className="flex items-center gap-4">
        {/* Keyboard toggle */}
        <button
          onClick={() => setShowTextInput(!showTextInput)}
          className="p-3 rounded-full bg-white/5 hover:bg-white/10 border border-white/10 text-white/50 hover:text-white transition-all"
        >
          <Keyboard className="w-5 h-5" />
        </button>

        {/* Main mic button */}
        <button
          onClick={onToggleListening}
          disabled={isProcessing}
          className={`relative p-6 rounded-full transition-all duration-300 disabled:opacity-50 ${
            isListening 
              ? 'bg-cyan-500/20 border-2 border-cyan-400 text-cyan-400 shadow-lg shadow-cyan-500/20' 
              : 'bg-white/5 border-2 border-white/20 text-white/70 hover:border-white/40 hover:text-white'
          }`}
        >
          {/* Pulsing ring when listening */}
          {isListening && (
            <>
              <span className="absolute inset-0 rounded-full border-2 border-cyan-400 animate-ping opacity-20" />
              <span className="absolute inset-[-8px] rounded-full border border-cyan-400/30 animate-pulse" />
            </>
          )}
          {isListening ? <MicOff className="w-7 h-7 relative z-10" /> : <Mic className="w-7 h-7" />}
        </button>

        {/* Status text */}
        <div className="w-24">
          <p className={`text-xs font-medium tracking-wide ${isListening ? 'text-cyan-400' : isProcessing ? 'text-purple-400' : 'text-white/30'}`}>
            {isListening ? 'Listening...' : isProcessing ? 'Thinking...' : 'Tap to talk'}
          </p>
        </div>
      </div>
    </div>
  );
};
