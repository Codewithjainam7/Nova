import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { CheckCircle2, Link, Key, Activity, Play } from 'lucide-react';

interface Integration {
  id: string;
  name: string;
  type: 'oauth2' | 'api_key' | 'none';
  connected: boolean;
  lastSync?: string;
  tokenExpiry?: string;
  testStatus?: 'pass' | 'fail' | 'testing';
}

export const Integrations: React.FC = () => {
  const [integrations, setIntegrations] = useState<Integration[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchIntegrations = async () => {
    try {
      const res = await fetch('http://localhost:8000/integrations');
      const data = await res.json();
      setIntegrations(data);
    } catch (e) {
      console.error('Failed to fetch integrations', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchIntegrations();
    
    // Poll for OAuth completion every 3s
    const interval = setInterval(fetchIntegrations, 3000);
    return () => clearInterval(interval);
  }, []);

  const handleConnect = async (int: Integration) => {
    if (int.type === 'oauth2') {
      try {
        const res = await fetch(`http://localhost:8000/integrations/${int.id}/connect`, { 
          method: 'POST', 
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({})
        });
        const data = await res.json();
        if (data.status === 'redirect') {
          // Open OAuth popup
          window.open(data.url, 'oauthPopup', 'width=600,height=700');
        }
      } catch (e) {
        console.error(e);
      }
    } else if (int.type === 'api_key') {
      const key = prompt(`Enter API Key for ${int.name}:`);
      if (key) {
        try {
          await fetch(`http://localhost:8000/integrations/${int.id}/connect`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ api_key: key })
          });
          fetchIntegrations();
        } catch (e) {
          console.error(e);
        }
      }
    }
  };

  const handleDisconnect = async (id: string) => {
    try {
      await fetch(`http://localhost:8000/integrations/${id}/disconnect`, { method: 'POST' });
      fetchIntegrations();
    } catch (e) {
      console.error(e);
    }
  };

  const testConnection = async (id: string) => {
    setIntegrations(prev => prev.map(i => i.id === id ? { ...i, testStatus: 'testing' } : i));
    try {
      const res = await fetch(`http://localhost:8000/integrations/${id}/test`, { method: 'POST' });
      const data = await res.json();
      setIntegrations(prev => prev.map(i => i.id === id ? { ...i, testStatus: data.status } : i));
    } catch (e) {
      setIntegrations(prev => prev.map(i => i.id === id ? { ...i, testStatus: 'fail' } : i));
    }
  };

  const testAll = async () => {
    try {
      const res = await fetch('http://localhost:8000/integrations/test_all', { method: 'POST' });
      const data = await res.json();
      if (data.results) {
        setIntegrations(prev => prev.map(i => data.results[i.id] ? { ...i, testStatus: data.results[i.id] } : i));
      }
    } catch (e) {
      console.error(e);
    }
  };

  if (loading) return <div className="text-white p-6">Loading...</div>;

  return (
    <div className="flex flex-col space-y-6 text-white p-6 max-w-4xl mx-auto w-full">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">API Integrations</h2>
          <p className="text-sm text-white/60 mt-1">Connect official APIs to allow ADA to execute tasks silently in the background.</p>
        </div>
        <button 
          onClick={testAll}
          className="flex items-center space-x-2 px-4 py-2 bg-purple-500/20 text-purple-400 rounded-lg hover:bg-purple-500/30 transition-all"
        >
          <Activity size={16} />
          <span>Test All Integrations</span>
        </button>
      </div>

      <div className="grid grid-cols-1 gap-4">
        {integrations.map((int) => (
          <motion.div 
            key={int.id}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex items-center justify-between p-4 bg-white/5 border border-white/10 rounded-xl backdrop-blur-sm"
          >
            <div className="flex items-center space-x-4">
              <div className={`p-2 rounded-lg ${int.connected ? 'bg-green-500/20 text-green-400' : 'bg-white/10 text-white/40'}`}>
                {int.type === 'oauth2' ? <Link size={20} /> : int.type === 'api_key' ? <Key size={20} /> : <CheckCircle2 size={20} />}
              </div>
              
              <div>
                <h3 className="font-semibold flex items-center space-x-2">
                  <span>{int.name}</span>
                  {int.testStatus && (
                    <span className={`text-[10px] px-2 py-0.5 rounded-full uppercase ${int.testStatus === 'pass' ? 'bg-green-500/20 text-green-400' : int.testStatus === 'fail' ? 'bg-red-500/20 text-red-400' : 'bg-yellow-500/20 text-yellow-400'}`}>
                      {int.testStatus}
                    </span>
                  )}
                </h3>
                <div className="flex items-center space-x-2 text-xs text-white/50 mt-1">
                  <span className="capitalize">{int.type.replace('_', ' ')}</span>
                  {int.lastSync && (
                    <>
                      <span>•</span>
                      <span>Last sync: {int.lastSync}</span>
                    </>
                  )}
                  {int.tokenExpiry && (
                    <>
                      <span>•</span>
                      <span>Expires: {int.tokenExpiry}</span>
                    </>
                  )}
                </div>
              </div>
            </div>

            <div className="flex items-center space-x-3">
              {int.connected && int.type !== 'none' && (
                <button onClick={() => testConnection(int.id)} title="Test Connection" className="p-2 text-white/50 hover:text-white transition-colors">
                  <Play size={16} />
                </button>
              )}
              
              {int.type !== 'none' && (
                <button 
                  onClick={() => int.connected ? handleDisconnect(int.id) : handleConnect(int)}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                    int.connected 
                      ? 'bg-red-500/10 text-red-400 hover:bg-red-500/20' 
                      : 'bg-blue-500 text-white hover:bg-blue-600'
                  }`}
                >
                  {int.connected ? 'Disconnect' : 'Connect'}
                </button>
              )}
              {int.type === 'none' && (
                <span className="text-xs text-green-400 px-3 py-1 bg-green-500/10 rounded-full">
                  System Active
                </span>
              )}
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
};

