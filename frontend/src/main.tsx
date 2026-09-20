import React, { useState, useEffect } from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './index.css'

import { DynamicIsland } from './components/DynamicIsland'
import { NovaWebSocketProvider } from './contexts/NovaWebSocket'

const RootComponent = () => {
  const [isIsland, setIsIsland] = useState(false);

  useEffect(() => {
    try {
      if (typeof window !== 'undefined' && window.location.search.includes('island=true')) {
        setIsIsland(true);
      }
    } catch {
      // Browser context
    }
  }, []);

  if (isIsland) {
    return (
      <NovaWebSocketProvider>
        <div className="w-screen h-screen overflow-hidden bg-transparent">
          <DynamicIsland />
        </div>
      </NovaWebSocketProvider>
    );
  }

  return <App />;
};

ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>
    <RootComponent />
  </React.StrictMode>,
)
