import React from 'react';
import { useNovaStore } from '../../store/useNovaStore';

export const WorkspaceOverlay: React.FC = () => {
  const { workspaceData, setWorkspaceData } = useNovaStore();

  if (!workspaceData) return null;

  return (
    <div className="absolute inset-0 bottom-24 pointer-events-none z-40 flex items-center justify-center p-8">
      {/* Neon glowing borders and glassmorphism */}
      <div className="pointer-events-auto w-full max-w-6xl h-full max-h-[70vh] bg-cyan-900/10 backdrop-blur-md border border-cyan-500/30 rounded-3xl shadow-[0_0_50px_rgba(0,255,255,0.1)] p-8 flex flex-col gap-6 animate-fade-in relative">
        
        {/* Close Button */}
        <button 
          onClick={() => setWorkspaceData(null)}
          className="absolute -top-4 -right-4 w-10 h-10 bg-[#030508] border-2 border-cyan-500 text-cyan-500 rounded-full flex items-center justify-center hover:bg-cyan-500 hover:text-white transition-colors cursor-pointer shadow-[0_0_20px_rgba(0,255,255,0.5)] z-50"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
        </button>

        {/* Header */}
        <div className="flex justify-between items-center border-b border-cyan-500/30 pb-4">
          <h2 className="text-cyan-400 font-mono text-2xl tracking-widest uppercase">
            Workspace // {workspaceData.query}
          </h2>
          <div className="flex gap-2">
            <div className="w-3 h-3 rounded-full bg-cyan-400/50 animate-pulse"></div>
            <div className="w-3 h-3 rounded-full bg-cyan-400/50 animate-pulse delay-75"></div>
            <div className="w-3 h-3 rounded-full bg-cyan-400/50 animate-pulse delay-150"></div>
          </div>
        </div>

        {/* Grid Layout */}
        <div className="flex-1 grid grid-cols-12 gap-6 h-full min-h-0">
          
          {/* Main Visuals (Map / Video mock) */}
          <div className="col-span-8 bg-black/40 border border-cyan-500/20 rounded-2xl relative overflow-hidden flex flex-col group hover:border-cyan-400/50 transition-colors">
            <div className="absolute inset-0 bg-gradient-to-t from-cyan-900/20 to-transparent z-10 pointer-events-none"></div>
            {workspaceData.maps?.map((map: any, i: number) => (
              <div key={i} className="flex-1 flex items-center justify-center relative">
                 {/* Map Grid overlay */}
                 <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI0MCIgaGVpZ2h0PSI0MCI+PHBhdGggZD0iTTAgMGg0MHY0MEgweiIgZmlsbD0ibm9uZSIvPjxwYXRoIGQ9Ik0wIDM5LjVMMzkuNSAzOS41TDM5LjUgMCIgZmlsbD0ibm9uZSIgc3Ryb2tlPSJyZ2JhKDAsMjU1LDI1NSwwLjEpIiBzdHJva2Utd2lkdGg9IjEiLz48L3N2Zz4=')] opacity-30"></div>
                 <div className="text-center z-20">
                    <div className="w-32 h-32 mx-auto rounded-full border-4 border-cyan-500 border-t-transparent animate-spin opacity-50 mb-4"></div>
                    <p className="text-cyan-300 font-mono tracking-widest uppercase text-sm">Rendering {map.title}...</p>
                 </div>
              </div>
            ))}
            <div className="absolute top-4 left-4 z-20">
              <span className="bg-cyan-500/20 text-cyan-300 text-xs px-2 py-1 rounded border border-cyan-500/30 uppercase tracking-widest font-mono">LIVE FEED</span>
            </div>
          </div>

          {/* Sidebar Data (News) */}
          <div className="col-span-4 flex flex-col gap-6">
            {workspaceData.news?.map((news: any, i: number) => (
              <div key={i} className="flex-1 bg-black/40 border border-cyan-500/20 rounded-2xl p-6 relative overflow-hidden group hover:border-cyan-400/50 transition-colors">
                 <div className="absolute top-0 right-0 p-4 opacity-10">
                   <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1" strokeLinecap="round" strokeLinejoin="round" className="text-cyan-400"><path d="M4 22h16a2 2 0 0 0 2-2V4a2 2 0 0 0-2-2H8l-4 4v14a2 2 0 0 0 2 2z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
                 </div>
                 <h3 className="text-cyan-500 text-xs font-mono mb-2 uppercase tracking-widest">{news.source}</h3>
                 <p className="text-cyan-100 text-lg leading-snug">{news.title}</p>
                 <div className="mt-4 flex gap-2">
                    <span className="w-8 h-1 bg-cyan-500/50 rounded-full"></span>
                    <span className="w-4 h-1 bg-cyan-500/30 rounded-full"></span>
                    <span className="w-2 h-1 bg-cyan-500/20 rounded-full"></span>
                 </div>
              </div>
            ))}
          </div>

        </div>
        
        {/* Footer info */}
        <div className="text-right">
          <span className="text-cyan-500/50 font-mono text-xs tracking-widest">ADA OS // HOLOGRAPHIC PROJECTION V1.0</span>
        </div>
      </div>
    </div>
  );
};
