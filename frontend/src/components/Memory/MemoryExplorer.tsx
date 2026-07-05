import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Database, Search, Trash2, Edit2, X } from 'lucide-react';

interface MemoryExplorerProps {
  isOpen: boolean;
  onClose: () => void;
}

export const MemoryExplorer: React.FC<MemoryExplorerProps> = ({ isOpen, onClose }) => {
  const [search, setSearch] = useState('');

  // Mock data for UI preview
  const memories = [
    { id: '1', type: 'semantic', content: 'User prefers dark mode.', timestamp: '2 mins ago' },
    { id: '2', type: 'episodic', content: 'Discussed Python async patterns.', timestamp: '1 hour ago' },
    { id: '3', type: 'fact', content: 'Favourite programming language is Rust.', timestamp: 'Yesterday' },
  ];

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="absolute inset-0 bg-black/60 backdrop-blur-sm"
          />
          
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            className="relative w-full max-w-5xl h-[800px] max-h-[90vh] bg-[#0f1115]/95 backdrop-blur-2xl border border-white/10 rounded-2xl shadow-2xl flex flex-col overflow-hidden"
          >
            <div className="p-6 border-b border-white/10 flex items-center justify-between bg-black/20">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-blue-500/20 flex items-center justify-center">
                  <Database className="w-5 h-5 text-blue-400" />
                </div>
                <div>
                  <h2 className="text-xl font-bold text-white tracking-wide">Memory Explorer</h2>
                  <p className="text-sm text-white/50">Manage long-term knowledge and contextual facts.</p>
                </div>
              </div>
              <button 
                onClick={onClose}
                className="p-2 text-white/50 hover:text-white bg-black/20 hover:bg-black/40 rounded-full transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-6">
              <div className="relative mb-6">
                <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 w-5 h-5 text-white/30" />
                <input 
                  type="text" 
                  placeholder="Search SQLite or ChromaDB..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="w-full bg-black/40 border border-white/10 rounded-xl pl-12 pr-4 py-3 text-white placeholder-white/30 focus:outline-none focus:border-blue-500 transition-colors"
                />
              </div>

              <div className="space-y-3 overflow-y-auto max-h-[500px] pr-2">
                {memories.map((mem) => (
                  <div key={mem.id} className="p-4 bg-white/5 border border-white/5 hover:border-white/20 rounded-xl transition-all group flex items-start justify-between">
                    <div>
                      <span className="text-[10px] uppercase font-bold tracking-wider text-blue-400 mb-1 block">
                        {mem.type}
                      </span>
                      <p className="text-white/90 text-sm leading-relaxed">{mem.content}</p>
                      <span className="text-xs text-white/30 mt-2 block">{mem.timestamp}</span>
                    </div>
                    <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                      <button className="p-2 text-white/40 hover:text-blue-400 bg-black/40 rounded-lg">
                        <Edit2 className="w-4 h-4" />
                      </button>
                      <button className="p-2 text-white/40 hover:text-red-400 bg-black/40 rounded-lg">
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
};
