import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Settings2, Key, MonitorSmartphone, Brain, Shield, Blocks } from 'lucide-react';
import clsx from 'clsx';

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const SettingsModal: React.FC<SettingsModalProps> = ({ isOpen, onClose }) => {
  const [activeTab, setActiveTab] = useState('general');

  const tabs = [
    { id: 'general', label: 'General', icon: <Settings2 className="w-4 h-4" /> },
    { id: 'keys', label: 'API Keys', icon: <Key className="w-4 h-4" /> },
    { id: 'models', label: 'Models', icon: <Brain className="w-4 h-4" /> },
    { id: 'permissions', label: 'Permissions', icon: <Shield className="w-4 h-4" /> },
    { id: 'plugins', label: 'Plugins', icon: <Blocks className="w-4 h-4" /> },
    { id: 'theme', label: 'Theme', icon: <MonitorSmartphone className="w-4 h-4" /> },
  ];

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6">
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="absolute inset-0 bg-black/60 backdrop-blur-sm"
          />
          
          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            className="relative w-full max-w-4xl h-[700px] max-h-[90vh] bg-[#0f1115]/90 backdrop-blur-2xl border border-white/10 rounded-2xl shadow-2xl flex overflow-hidden"
          >
            {/* Sidebar */}
            <div className="w-64 bg-black/40 border-r border-white/10 flex flex-col">
              <div className="p-6">
                <h2 className="text-xl font-bold text-white tracking-wide">Settings</h2>
              </div>
              <div className="flex flex-col gap-1 px-3">
                {tabs.map((tab) => (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={clsx(
                      "flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm font-medium transition-all duration-200",
                      activeTab === tab.id 
                        ? "bg-blue-600/20 text-blue-400" 
                        : "text-white/60 hover:bg-white/5 hover:text-white"
                    )}
                  >
                    {tab.icon}
                    {tab.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Content Area */}
            <div className="flex-1 flex flex-col relative">
              <button 
                onClick={onClose}
                className="absolute top-4 right-4 p-2 text-white/50 hover:text-white bg-black/20 hover:bg-black/40 rounded-full transition-colors z-10"
              >
                <X className="w-5 h-5" />
              </button>

              <div className="flex-1 overflow-y-auto p-8">
                {activeTab === 'general' && (
                  <div className="space-y-6">
                    <h3 className="text-lg font-semibold text-white border-b border-white/10 pb-2">General Settings</h3>
                    {/* Checkboxes / Toggles would go here */}
                    <p className="text-sm text-white/50">NOVA System preferences and startup behavior.</p>
                  </div>
                )}
                {activeTab === 'keys' && (
                  <div className="space-y-6">
                    <h3 className="text-lg font-semibold text-white border-b border-white/10 pb-2">API Configuration</h3>
                    <div className="space-y-4">
                      <div>
                        <label className="block text-sm font-medium text-white/80 mb-1">Gemini API Key</label>
                        <input type="password" placeholder="AIzaSy..." className="w-full bg-black/50 border border-white/10 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-blue-500 transition-colors" />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-white/80 mb-1">Groq API Key</label>
                        <input type="password" placeholder="gsk_..." className="w-full bg-black/50 border border-white/10 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-blue-500 transition-colors" />
                      </div>
                    </div>
                  </div>
                )}
                {activeTab === 'permissions' && (
                  <div className="space-y-6">
                    <h3 className="text-lg font-semibold text-white border-b border-white/10 pb-2">System Access & Permissions</h3>
                    <p className="text-sm text-white/50">Configure global rules for Desktop and Browser automation.</p>
                  </div>
                )}
                {/* Other tabs follow similar structure... */}
              </div>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
};
