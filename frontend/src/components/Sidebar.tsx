import React from 'react';
import { Bot, MessageSquare, Database, Settings, Activity, FolderGit2 } from 'lucide-react';
import clsx from 'clsx';

export const Sidebar: React.FC = () => {
  const [active, setActive] = React.useState('chat');

  const navItems = [
    { id: 'chat', icon: <MessageSquare className="w-5 h-5" />, label: 'Chat' },
    { id: 'memory', icon: <Database className="w-5 h-5" />, label: 'Memory' },
    { id: 'plugins', icon: <FolderGit2 className="w-5 h-5" />, label: 'Plugins' },
    { id: 'logs', icon: <Activity className="w-5 h-5" />, label: 'Logs' },
    { id: 'settings', icon: <Settings className="w-5 h-5" />, label: 'Settings' },
  ];

  return (
    <div className="w-16 h-full bg-black/40 backdrop-blur-3xl border-r border-white/5 flex flex-col items-center py-6 gap-8 z-10 shrink-0">
      <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-purple-600 to-blue-500 flex items-center justify-center shadow-lg shadow-purple-500/20">
        <Bot className="w-6 h-6 text-white" />
      </div>

      <div className="flex flex-col gap-4 w-full px-2">
        {navItems.map(item => (
          <button
            key={item.id}
            onClick={() => setActive(item.id)}
            className={clsx(
              "w-full aspect-square rounded-xl flex items-center justify-center transition-all duration-300 relative group",
              active === item.id 
                ? "bg-white/10 text-white" 
                : "text-white/40 hover:text-white/80 hover:bg-white/5"
            )}
          >
            {item.icon}
            
            {/* Tooltip */}
            <div className="absolute left-full ml-4 px-2 py-1 bg-white/10 backdrop-blur-md rounded border border-white/10 text-xs font-medium text-white opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity whitespace-nowrap z-50">
              {item.label}
            </div>
            
            {active === item.id && (
              <div className="absolute left-0 w-1 h-1/2 bg-blue-400 rounded-r-full" />
            )}
          </button>
        ))}
      </div>
    </div>
  );
};
