import React, { useState } from 'react';
import { Send, Paperclip, Mic } from 'lucide-react';
import { useNovaWebSocket } from '../../contexts/NovaWebSocket';
import { useNovaStore } from '../../store/useNovaStore';

export const ChatInput: React.FC = () => {
  const [input, setInput] = useState('');
  const { sendChat } = useNovaWebSocket();
  const { isStreaming } = useNovaStore();

  const handleSend = () => {
    if (input.trim() && !isStreaming) {
      sendChat(input.trim());
      setInput('');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="w-full max-w-4xl mx-auto p-4">
      <div className="relative flex items-end gap-2 bg-black/40 backdrop-blur-xl border border-white/10 rounded-3xl p-2 shadow-2xl transition-all focus-within:border-white/30 focus-within:bg-black/60">
        
        <button className="p-3 text-white/50 hover:text-white/90 hover:bg-white/5 rounded-full transition-colors flex-shrink-0">
          <Paperclip className="w-5 h-5" />
        </button>

        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask ADA anything or request an action..."
          className="flex-1 max-h-32 min-h-[44px] bg-transparent text-white placeholder-white/30 resize-none outline-none py-3 px-2 text-sm"
          rows={1}
        />

        {input.trim() ? (
          <button 
            onClick={handleSend}
            disabled={isStreaming}
            className="p-3 bg-white text-black hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed rounded-full transition-colors flex-shrink-0"
          >
            <Send className="w-5 h-5" />
          </button>
        ) : (
          <button className="p-3 text-white hover:bg-white/10 rounded-full transition-colors flex-shrink-0">
            <Mic className="w-5 h-5" />
          </button>
        )}
      </div>
      <div className="text-center mt-2">
        <p className="text-[10px] text-white/30 tracking-wide font-medium">ADA CAN MAKE MISTAKES. VERIFY IMPORTANT INFORMATION.</p>
      </div>
    </div>
  );
};
