import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, ArrowRight, Zap, CheckCircle2 } from 'lucide-react';

interface Integration {
  id: string;
  name: string;
  type: string;
  connected: boolean;
}

interface OnboardingModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const OnboardingModal: React.FC<OnboardingModalProps> = ({ isOpen, onClose }) => {
  const [integrations, setIntegrations] = useState<Integration[]>([]);

  useEffect(() => {
    if (isOpen) {
      fetch('http://localhost:8000/integrations')
        .then(res => res.json())
        .then(data => setIntegrations(data))
        .catch(console.error);
    }
  }, [isOpen]);

  const handleConnect = async (id: string, type: string, name: string) => {
    if (type === 'oauth2') {
      try {
        const res = await fetch(`http://localhost:8000/integrations/${id}/connect`, { 
          method: 'POST', 
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({})
        });
        const data = await res.json();
        if (data.status === 'redirect') {
          window.open(data.url, 'oauthPopup', 'width=600,height=700');
        }
      } catch (e) {
        console.error(e);
      }
    } else if (type === 'api_key') {
      const key = prompt(`Enter API Key for ${name}:`);
      if (key) {
        try {
          await fetch(`http://localhost:8000/integrations/${id}/connect`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ api_key: key })
          });
          // Update local state to show connected
          setIntegrations(prev => prev.map(i => i.id === id ? { ...i, connected: true } : i));
        } catch (e) {
          console.error(e);
        }
      }
    }
  };

  const recommendList = ['gmail', 'calendar', 'spotify', 'github'];
  const recommended = integrations.filter(i => recommendList.includes(i.id));

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            className="bg-[#1a1a1a] border border-white/10 rounded-2xl shadow-2xl w-full max-w-lg overflow-hidden"
          >
            <div className="p-6 relative">
              <button 
                onClick={onClose}
                className="absolute top-4 right-4 text-white/50 hover:text-white transition-colors"
              >
                <X size={20} />
              </button>

              <div className="flex justify-center mb-6">
                <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center shadow-lg shadow-purple-500/20">
                  <Zap size={32} className="text-white" />
                </div>
              </div>

              <h2 className="text-2xl font-bold text-center text-white mb-2">
                Supercharge ADA
              </h2>
              <p className="text-center text-white/60 mb-8 text-sm px-4">
                Connect external capabilities to allow ADA to assist you across desktop and mobile.
              </p>

              <div className="space-y-3">
                <div className="text-xs font-semibold text-white/40 uppercase tracking-wider mb-2">
                  Recommended Integrations
                </div>
                
                {recommended.map(int => (
                  <div key={int.id} className="flex items-center justify-between p-3 rounded-xl bg-white/5 border border-white/5 hover:border-white/10 transition-colors">
                    <div className="flex items-center space-x-3">
                      {int.connected ? (
                        <CheckCircle2 size={20} className="text-green-400" />
                      ) : (
                        <div className="w-5 h-5 rounded-full border-2 border-white/20" />
                      )}
                      <span className="text-white font-medium">{int.name}</span>
                    </div>
                    
                    {!int.connected && (
                      <button 
                        onClick={() => handleConnect(int.id, int.type, int.name)}
                        className="px-3 py-1.5 rounded-lg bg-blue-500 hover:bg-blue-600 text-white text-xs font-medium transition-colors"
                      >
                        Connect
                      </button>
                    )}
                  </div>
                ))}
              </div>

              <div className="mt-8">
                <button 
                  onClick={onClose}
                  className="w-full py-3 rounded-xl bg-white text-black font-semibold flex items-center justify-center space-x-2 hover:bg-white/90 transition-colors"
                >
                  <span>Continue to ADA</span>
                  <ArrowRight size={18} />
                </button>
              </div>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
};
