import React from 'react';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

const queryClient = new QueryClient();

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <div className="min-h-screen bg-black text-white flex items-center justify-center font-sans">
          <h1 className="text-4xl font-bold">NOVA AI</h1>
        </div>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
