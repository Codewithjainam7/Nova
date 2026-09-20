import React, { useState, useEffect } from 'react';
import { BrainScene } from './components/Brain/BrainScene';
import { NovaWebSocketProvider } from './contexts/NovaWebSocket';
import { OnboardingModal } from './components/Settings/OnboardingModal';
import { WorkspaceOverlay } from './components/HUD/WorkspaceOverlay';

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

  return (
    <NovaWebSocketProvider>
      <div className="fixed inset-0 bg-[#030508] overflow-hidden">
        <BrainScene />
        <WorkspaceOverlay />
        <OnboardingModal isOpen={showOnboarding} onClose={() => setShowOnboarding(false)} />
      </div>
    </NovaWebSocketProvider>
  );
};

export default App;
