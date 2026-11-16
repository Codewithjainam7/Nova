import React, { useState, useEffect } from 'react';
import { BrainScene } from './components/Brain/BrainScene';
import { NovaWebSocketProvider } from './contexts/NovaWebSocket';
import { OnboardingModal } from './components/Settings/OnboardingModal';
import { WorkspaceOverlay } from './components/HUD/WorkspaceOverlay';
import { StartupOverlay } from './components/HUD/StartupOverlay';

const App: React.FC = () => {
  const [showOnboarding, setShowOnboarding] = useState(false);

  useEffect(() => {
    fetch('http://localhost:8000/integrations')
      .then(res => res.json())
      .then(data => {
        const anyConnected = data.some((int: any) => int.connected);
        if (!anyConnected) {
          setShowOnboarding(true);
        }
      })
      .catch(() => {
        // Backend not available, skip onboarding
      });
  }, []);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.altKey && (e.code === 'Space' || e.key === ' ')) ||
          (e.ctrlKey && (e.code === 'Space' || e.key === ' ')) ||
          e.key === 'F2') {
        e.preventDefault();
        try {
          if ((window as any).electronAPI?.toggleIsland) {
            (window as any).electronAPI.toggleIsland();
          }
        } catch {}
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  return (
    <NovaWebSocketProvider>
      <div className="fixed inset-0 bg-[#030508] overflow-hidden">
        <StartupOverlay />
        <BrainScene />
        <WorkspaceOverlay />
        <OnboardingModal isOpen={showOnboarding} onClose={() => setShowOnboarding(false)} />
      </div>
    </NovaWebSocketProvider>
  );
};

export default App;
