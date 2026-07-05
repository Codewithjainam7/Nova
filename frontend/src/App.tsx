import React from 'react';
import { Sidebar } from './components/Sidebar';
import { ChatLayout } from './components/Chat/ChatLayout';
import { DynamicIsland } from './components/DynamicIsland';
import { ExecutionTimeline } from './components/Timeline/ExecutionTimeline';
import { NovaWebSocketProvider } from './contexts/NovaWebSocket';

const App: React.FC = () => {
  return (
    <NovaWebSocketProvider>
      <div className="flex h-screen w-screen bg-[#0f1115] text-white overflow-hidden relative font-sans selection:bg-blue-500/30">
        {/* Abstract Background Elements */}
        <div className="absolute top-[-20%] left-[-10%] w-[50%] h-[50%] bg-blue-600/20 rounded-full blur-[120px] pointer-events-none" />
        <div className="absolute bottom-[-20%] right-[-10%] w-[50%] h-[50%] bg-purple-600/20 rounded-full blur-[120px] pointer-events-none" />

        <DynamicIsland />
        
        <Sidebar />
        
        <main className="flex-1 relative h-full flex flex-col z-10">
          <ChatLayout />
        </main>
        
        <ExecutionTimeline />
      </div>
    </NovaWebSocketProvider>
  );
};

export default App;
