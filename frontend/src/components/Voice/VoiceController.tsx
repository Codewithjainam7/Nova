import React, { useState, useCallback } from 'react';
import { Mic, MicOff, ArrowUp, Sliders, Zap, FolderSync, MessageSquare, Smartphone, Globe, Sparkles } from 'lucide-react';
import { useWidgetStore } from '../../store/useWidgetStore';
import clsx from 'clsx';
import { motion } from 'framer-motion';

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
  const [textInput, setTextInput] = useState('');
  const { customDirectives, setCustomizerOpen, isCustomizerOpen } = useWidgetStore();

  const handleSend = useCallback((text?: string) => {
    const query = (text !== undefined ? text : textInput).trim();
    if (query) {
      onSendText(query);
      setTextInput('');
    }
  }, [textInput, onSendText]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const getDirectiveIcon = (label: string) => {
    const l = label.toLowerCase();
    if (l.includes('brief') || l.includes('morning')) return <Zap className="w-4 h-4 text-amber-400 shrink-0" />;
    if (l.includes('organize') || l.includes('file')) return <FolderSync className="w-4 h-4 text-cyan-400 shrink-0" />;
    if (l.includes('msg') || l.includes('message') || l.includes('whatsapp')) return <MessageSquare className="w-4 h-4 text-emerald-400 shrink-0" />;
    if (l.includes('phone') || l.includes('battery')) return <Smartphone className="w-4 h-4 text-indigo-400 shrink-0" />;
    if (l.includes('research') || l.includes('web') || l.includes('search')) return <Globe className="w-4 h-4 text-purple-400 shrink-0" />;
    return <Sparkles className="w-4 h-4 text-cyan-400 shrink-0" />;
  };

  if (isCustomizerOpen) return null;

  return (
    <div className="absolute bottom-2 sm:bottom-4 left-1/2 -translate-x-1/2 z-30 flex flex-col items-center gap-1.5 sm:gap-2 w-[95vw] sm:w-[92vw] max-w-lg md:max-w-xl lg:max-w-2xl px-1 sm:px-2 pointer-events-none select-none">
      
      {/* Quick Action Jarvis Directives (Never clips, responsive wrap, zero emojis) */}
      <div className="flex flex-wrap items-center justify-center gap-1.5 sm:gap-2 pointer-events-auto w-full px-1 py-0.5 no-scrollbar">
        {customDirectives.map((d) => (
          <button
            key={d.id}
            onClick={() => {
              if (d.cmd.endsWith(' ')) {
                setTextInput(d.cmd);
              } else {
                handleSend(d.cmd);
              }
            }}
            className={clsx(
              "px-3 py-1.5 rounded-xl text-xs font-hud font-bold tracking-wider border transition-all flex items-center gap-1.5 shrink-0 backdrop-blur-xl shadow-md cursor-pointer",
              d.color,
              "hover:scale-105 hover:brightness-125 active:scale-95"
            )}
          >
            {getDirectiveIcon(d.label)}
            <span>{d.label}</span>
          </button>
        ))}

        {/* Quick Customize Button */}
        <button
          onClick={() => setCustomizerOpen(true)}
          title="Customize Directives & Widgets"
          className="px-3 py-1.5 rounded-xl text-xs font-hud font-bold text-cyan-200 hover:text-white border border-cyan-400/50 hover:border-cyan-300 bg-cyan-950/60 hover:bg-cyan-500/25 transition-all flex items-center gap-1.5 shrink-0 shadow-[0_0_15px_rgba(6,182,212,0.2)] cursor-pointer active:scale-95"
        >
          <Sliders className="w-3.5 h-3.5 text-cyan-300" />
          <span>MORE</span>
        </button>
      </div>

      {/* Main Holographic Command Bar */}
      <div className="w-full flex items-center gap-3 bg-[#030713]/95 border-2 border-cyan-400/50 backdrop-blur-2xl rounded-2xl p-2.5 shadow-[0_0_45px_rgba(6,182,212,0.25),inset_0_0_20px_rgba(6,182,212,0.08)] pointer-events-auto">
        
        {/* Glowing Neural Mic Trigger */}
        <button
          onClick={onToggleListening}
          disabled={isProcessing}
          title={isListening ? "Stop Listening" : "Start Voice Input"}
          className={clsx(
            "relative p-3 rounded-xl transition-all duration-300 shrink-0 cursor-pointer flex items-center justify-center",
            isListening 
              ? "bg-gradient-to-r from-cyan-400 to-cyan-500 text-black shadow-[0_0_30px_#06b6d4] scale-105" 
              : "bg-white/[0.08] text-white hover:text-cyan-200 hover:bg-white/15 border border-white/15 hover:border-cyan-400/60 shadow-inner"
          )}
        >
          {isListening ? (
            <>
              {/* Expanding Concentric Sonar Rings */}
              <motion.span 
                animate={{ scale: [1, 1.8], opacity: [0.8, 0] }}
                transition={{ repeat: Infinity, duration: 1.2, ease: "easeOut" }}
                className="absolute inset-0 rounded-xl border-2 border-cyan-300 pointer-events-none" 
              />
              <MicOff className="w-5 h-5 relative z-10" />
            </>
          ) : (
            <Mic className="w-5 h-5 text-cyan-300" />
          )}
        </button>

        {/* Input Text Area */}
        <div className="flex-1 relative">
          <input
            value={textInput}
            onChange={(e) => setTextInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={isListening ? "Listening to your voice directive..." : "Type directive or press Mic for Voice..."}
            className={clsx(
              "w-full bg-transparent text-white placeholder-white/50 outline-none px-2 text-sm font-sans tracking-wide font-normal",
              isListening && "animate-pulse text-cyan-300 placeholder-cyan-400/80"
            )}
          />
        </div>

        {/* Submit Arrow Button */}
        <button
          onClick={() => handleSend()}
          disabled={!textInput.trim() || isProcessing}
          className={clsx(
            "p-3 rounded-xl transition-all duration-200 shrink-0 flex items-center justify-center cursor-pointer",
            textInput.trim()
              ? "bg-gradient-to-r from-cyan-400 to-blue-500 text-black hover:brightness-110 shadow-[0_0_25px_#06b6d4] scale-100 active:scale-95"
              : "bg-white/[0.05] text-white/30 cursor-not-allowed scale-95"
          )}
        >
          <ArrowUp className="w-5 h-5 stroke-[2.5]" />
        </button>
      </div>

      {/* Micro Status Hint Line */}
      <div className="flex items-center justify-between w-full px-3 text-[11px] font-hud text-cyan-300 font-bold tracking-[0.16em]">
        <span className="flex items-center gap-1.5">
          <span className="px-2 py-0.5 rounded bg-cyan-950 border border-cyan-400/50 text-cyan-200 text-[10px] font-mono">ALT+SPACE / F2</span>
          <span>DYNAMIC ISLAND</span>
        </span>
        <span className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
          <span>ADA MARK VII COGNITIVE ARCHITECTURE // NEURAL READY</span>
        </span>
      </div>

    </div>
  );
};
