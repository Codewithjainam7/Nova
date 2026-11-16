import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './index.css'

import { DynamicIsland } from './components/DynamicIsland'
import { NovaWebSocketProvider } from './contexts/NovaWebSocket'

const isIslandMode = typeof window !== 'undefined' && window.location.search.includes('island=true');

if (isIslandMode && typeof document !== 'undefined') {
  document.documentElement.style.backgroundColor = 'transparent';
  document.documentElement.style.background = 'transparent';
  document.body.style.backgroundColor = 'transparent';
  document.body.style.background = 'transparent';
}

const RootComponent = () => {
  if (isIslandMode) {
    return (
      <NovaWebSocketProvider>
        <div className="w-screen h-screen overflow-hidden bg-transparent m-0 p-0 border-0 outline-none select-none">
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
