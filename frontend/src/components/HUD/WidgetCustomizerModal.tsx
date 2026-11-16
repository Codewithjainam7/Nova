import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { useWidgetStore, AVAILABLE_WIDGETS } from '../../store/useWidgetStore';
import {
  X, Check, Plus, Trash2, Sliders, Layers, Sparkles, RotateCcw,
  Cpu, HardDrive, Shield, Terminal, Smartphone, Calendar, FileText,
  FolderSync, Keyboard, Volume2
} from 'lucide-react';
import clsx from 'clsx';

export const WidgetCustomizerModal: React.FC = () => {
  const {
    isCustomizerOpen,
    setCustomizerOpen,
    enabledWidgets,
    toggleWidget,
    resetToDefaults,
    customDirectives,
    addCustomDirective,
    removeCustomDirective
  } = useWidgetStore();

  const [activeTab, setActiveTab] = useState<'widgets' | 'directives'>('widgets');
  const [newLabel, setNewLabel] = useState('');
  const [newCmd, setNewCmd] = useState('');
  const [newColor, setNewColor] = useState('cyan');

  if (!isCustomizerOpen) return null;

  const getWidgetIcon = (id: string) => {
    switch (id) {
      case 'cpu': return <Cpu className="w-4 h-4 text-cyan-300" />;
      case 'memory': return <HardDrive className="w-4 h-4 text-teal-300" />;
      case 'subsystems': return <Shield className="w-4 h-4 text-emerald-300" />;
      case 'organizer': return <FolderSync className="w-4 h-4 text-cyan-200" />;
      case 'missions': return <FileText className="w-4 h-4 text-amber-300" />;
      case 'terminal': return <Terminal className="w-4 h-4 text-purple-300" />;
      case 'phone': return <Smartphone className="w-4 h-4 text-indigo-300" />;
      case 'agenda': return <Calendar className="w-4 h-4 text-blue-300" />;
      case 'scratchpad': return <Sparkles className="w-4 h-4 text-amber-300" />;
      case 'shortcuts': return <Keyboard className="w-4 h-4 text-slate-200" />;
      default: return <Layers className="w-4 h-4 text-cyan-300" />;
    }
  };

  const handleCreateDirective = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newLabel.trim() || !newCmd.trim()) return;

    const colorMap: Record<string, string> = {
      cyan: 'text-cyan-300 border-cyan-400/50 bg-cyan-950/60',
      emerald: 'text-emerald-300 border-emerald-400/50 bg-emerald-950/60',
      amber: 'text-amber-300 border-amber-400/50 bg-amber-950/60',
      purple: 'text-purple-300 border-purple-400/50 bg-purple-950/60',
      indigo: 'text-indigo-300 border-indigo-400/50 bg-indigo-950/60',
    };

    addCustomDirective({
      label: newLabel.trim(),
      cmd: newCmd.trim(),
      color: colorMap[newColor] || colorMap.cyan,
    });

    setNewLabel('');
    setNewCmd('');
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/85 backdrop-blur-2xl animate-fade-in pointer-events-auto">
      <motion.div
        initial={{ opacity: 0, scale: 0.95, y: 15 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95, y: 15 }}
        className="relative w-full max-w-2xl bg-[#070b14] border-2 border-cyan-400/50 rounded-3xl p-6 shadow-[0_0_80px_rgba(6,182,212,0.35)] flex flex-col max-h-[80vh] overflow-hidden"
      >
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-white/15">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-cyan-950 border border-cyan-400/50 text-cyan-300 shadow-[0_0_15px_rgba(6,182,212,0.4)]">
              <Sliders className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-mono font-bold tracking-wider text-white uppercase flex items-center gap-2">
                HUD Customizer // Control Center
              </h2>
              <p className="text-xs text-slate-300 font-mono mt-0.5">
                Toggle HUD telemetry widgets or create custom action directives.
              </p>
            </div>
          </div>
          
          <button
            onClick={() => setCustomizerOpen(false)}
            className="p-2 rounded-xl text-white/70 hover:text-white hover:bg-white/10 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tab Navigation */}
        <div className="flex items-center gap-2 pt-4 pb-2">
          <button
            onClick={() => setActiveTab('widgets')}
            className={clsx(
              "px-4 py-2 rounded-xl text-xs font-mono font-bold tracking-wider transition-all",
              activeTab === 'widgets'
                ? "bg-cyan-500/25 text-cyan-300 border-2 border-cyan-400 shadow-[0_0_15px_rgba(6,182,212,0.3)]"
                : "text-slate-300 hover:text-white hover:bg-white/[0.06] border border-white/10"
            )}
          >
            Active HUD Widgets ({Object.values(enabledWidgets).filter(Boolean).length})
          </button>
          <button
            onClick={() => setActiveTab('directives')}
            className={clsx(
              "px-4 py-2 rounded-xl text-xs font-mono font-bold tracking-wider transition-all",
              activeTab === 'directives'
                ? "bg-cyan-500/25 text-cyan-300 border-2 border-cyan-400 shadow-[0_0_15px_rgba(6,182,212,0.3)]"
                : "text-slate-300 hover:text-white hover:bg-white/[0.06] border border-white/10"
            )}
          >
            Command Directives ({customDirectives.length})
          </button>
          
          <div className="ml-auto flex items-center gap-2">
            <button
              onClick={() => {
                try {
                  const audio = new Audio('/sounds/startup.wav');
                  audio.volume = 0.85;
                  audio.play();
                } catch {}
              }}
              className="text-xs font-hud font-bold text-cyan-200 hover:text-white flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-cyan-950/70 border border-cyan-400/50 hover:bg-cyan-500/25 transition-all shadow-[0_0_12px_rgba(6,182,212,0.2)] cursor-pointer"
            >
              <Volume2 className="w-3.5 h-3.5 text-cyan-400" />
              <span>TEST STARTUP AUDIO</span>
            </button>

            <button
              onClick={resetToDefaults}
              className="text-xs font-mono text-cyan-300 hover:text-white flex items-center gap-1.5 px-3 py-1.5 rounded-lg hover:bg-cyan-950/50 border border-cyan-500/30 transition-all font-semibold cursor-pointer"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              Reset Defaults
            </button>
          </div>
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto pr-1 space-y-3 my-2 no-scrollbar">
          {activeTab === 'widgets' ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {AVAILABLE_WIDGETS.map((widget) => {
                const isEnabled = !!enabledWidgets[widget.id];
                return (
                  <div
                    key={widget.id}
                    onClick={() => toggleWidget(widget.id)}
                    className={clsx(
                      "p-3.5 rounded-2xl cursor-pointer transition-all flex items-start gap-3 select-none",
                      isEnabled
                        ? "bg-[#0f1b32] border-2 border-cyan-400 shadow-[0_0_20px_rgba(6,182,212,0.2)]"
                        : "bg-[#0b101c] border border-white/20 hover:border-white/40"
                    )}
                  >
                    <div className="p-2.5 rounded-xl bg-white/[0.08] border border-white/15 shrink-0">
                      {getWidgetIcon(widget.id)}
                    </div>
                    
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between gap-1">
                        <span className="text-sm font-bold text-white tracking-wide truncate">
                          {widget.name}
                        </span>
                        <span className={clsx(
                          "w-5 h-5 rounded-full flex items-center justify-center shrink-0 text-xs font-bold transition-all",
                          isEnabled ? "bg-cyan-400 text-black shadow-[0_0_10px_#22d3ee]" : "border border-white/30 text-transparent"
                        )}>
                          {isEnabled && <Check className="w-3.5 h-3.5 stroke-[3]" />}
                        </span>
                      </div>
                      
                      {/* High contrast, clearly readable description text */}
                      <p className="text-xs text-slate-200 leading-relaxed mt-1">
                        {widget.description}
                      </p>
                      
                      {/* Distinct, readable badges */}
                      <div className="flex items-center gap-2 mt-2.5">
                        <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-500/50">
                          {widget.category.toUpperCase()}
                        </span>
                        <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded bg-amber-950/70 text-amber-300 border border-amber-500/40">
                          {widget.column === 'left' ? 'LEFT HUD' : 'RIGHT HUD'}
                        </span>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="space-y-4">
              {/* Directive List */}
              <div className="space-y-2">
                <p className="text-xs font-mono font-semibold text-slate-200">Current Action Directives (Bottom Command Deck):</p>
                <div className="flex flex-wrap gap-2">
                  {customDirectives.map((d) => (
                    <div
                      key={d.id}
                      className={clsx(
                        "px-3 py-1.5 rounded-xl text-xs font-mono font-semibold tracking-wider border flex items-center gap-2 shadow-md",
                        d.color
                      )}
                    >
                      <span>{d.label}</span>
                      <button
                        onClick={() => removeCustomDirective(d.id)}
                        className="text-white/60 hover:text-rose-400 transition-colors p-0.5"
                      >
                        <Trash2 className="w-3 h-3" />
                      </button>
                    </div>
                  ))}
                </div>
              </div>

              {/* Add New Directive Form */}
              <form onSubmit={handleCreateDirective} className="p-4 rounded-2xl bg-[#0a101d] border-2 border-cyan-500/30 space-y-3">
                <p className="text-xs font-mono text-cyan-300 font-bold flex items-center gap-1.5">
                  <Plus className="w-4 h-4" />
                  Add Custom Directive Button
                </p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  <div>
                    <label className="text-[10px] font-mono text-slate-300 font-semibold block mb-1">BUTTON LABEL</label>
                    <input
                      value={newLabel}
                      onChange={(e) => setNewLabel(e.target.value)}
                      placeholder="e.g. Clean Temp Files"
                      className="w-full h-8 px-3 rounded-lg bg-black/60 border border-white/20 text-xs text-white outline-none focus:border-cyan-400"
                    />
                  </div>
                  <div>
                    <label className="text-[10px] font-mono text-slate-300 font-semibold block mb-1">ADA COMMAND / DIRECTIVE</label>
                    <input
                      value={newCmd}
                      onChange={(e) => setNewCmd(e.target.value)}
                      placeholder="e.g. clean temporary files"
                      className="w-full h-8 px-3 rounded-lg bg-black/60 border border-white/20 text-xs text-white outline-none focus:border-cyan-400"
                    />
                  </div>
                </div>

                <div className="flex items-center justify-between pt-1">
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-mono text-slate-300 font-semibold">COLOR:</span>
                    {['cyan', 'emerald', 'amber', 'purple', 'indigo'].map((color) => (
                      <button
                        key={color}
                        type="button"
                        onClick={() => setNewColor(color)}
                        className={clsx(
                          "w-5 h-5 rounded-full border transition-all",
                          color === 'cyan' && 'bg-cyan-500',
                          color === 'emerald' && 'bg-emerald-500',
                          color === 'amber' && 'bg-amber-500',
                          color === 'purple' && 'bg-purple-500',
                          color === 'indigo' && 'bg-indigo-500',
                          newColor === color ? 'border-white scale-110 shadow-lg' : 'border-transparent opacity-60'
                        )}
                      />
                    ))}
                  </div>

                  <button
                    type="submit"
                    disabled={!newLabel.trim() || !newCmd.trim()}
                    className="px-4 py-1.5 rounded-lg text-xs font-mono font-bold bg-cyan-400 hover:bg-cyan-300 text-black transition-all disabled:opacity-40 shadow-[0_0_12px_#06b6d4]"
                  >
                    + Add Directive
                  </button>
                </div>
              </form>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="pt-3 border-t border-white/15 flex items-center justify-between">
          <span className="text-[10px] font-mono text-slate-400">
            PREFERENCES PERSIST IN LOCAL STORAGE
          </span>
          <button
            onClick={() => setCustomizerOpen(false)}
            className="px-6 py-2.5 rounded-xl bg-cyan-400 hover:bg-cyan-300 text-black text-xs font-mono font-bold transition-all shadow-[0_0_20px_#06b6d4]"
          >
            Save & Close
          </button>
        </div>
      </motion.div>
    </div>
  );
};
