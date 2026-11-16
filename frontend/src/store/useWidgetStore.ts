import { create } from 'zustand';

export interface CustomDirective {
  id: string;
  label: string;
  cmd: string;
  color: string;
}

export interface WidgetDefinition {
  id: string;
  name: string;
  category: 'Telemetry' | 'System' | 'Automation' | 'Devices' | 'Productivity';
  description: string;
  column: 'left' | 'right';
  defaultEnabled: boolean;
}

export const AVAILABLE_WIDGETS: WidgetDefinition[] = [
  {
    id: 'cpu',
    name: 'Synapse 16-Core CPU',
    category: 'Telemetry',
    description: 'Live multi-threaded synaptic processor loads and frequency monitors.',
    column: 'left',
    defaultEnabled: true,
  },
  {
    id: 'memory',
    name: 'Quantum Buffer RAM',
    category: 'Telemetry',
    description: 'Real-time VRAM and semantic vector buffer allocation.',
    column: 'left',
    defaultEnabled: true,
  },
  {
    id: 'subsystems',
    name: 'Subsystem Health Matrix',
    category: 'System',
    description: 'Live operational status of Kernel, Desktop Controllers, and Phone Bridge.',
    column: 'left',
    defaultEnabled: true,
  },
  {
    id: 'organizer',
    name: 'Smart Folder Organizer',
    category: 'Automation',
    description: 'Instant 1-click organizer for Desktop, Downloads, and Documents.',
    column: 'left',
    defaultEnabled: true,
  },
  {
    id: 'missions',
    name: 'Autonomous Mission Deliverables',
    category: 'Automation',
    description: 'Latest autonomous reports and overnight research outputs.',
    column: 'left',
    defaultEnabled: false,
  },
  {
    id: 'terminal',
    name: 'Neural Directive Stream',
    category: 'System',
    description: 'Real-time AI thought stream and cognitive execution logs.',
    column: 'right',
    defaultEnabled: true,
  },
  {
    id: 'phone',
    name: 'Android Wireless ADB Bridge',
    category: 'Devices',
    description: 'Device connection status, battery percentage, and wireless pairing.',
    column: 'right',
    defaultEnabled: true,
  },
  {
    id: 'agenda',
    name: 'Jarvis Executive Briefing Intel',
    category: 'Productivity',
    description: 'Daily executive greeting, current routine perception, and system status.',
    column: 'right',
    defaultEnabled: true,
  },
  {
    id: 'scratchpad',
    name: 'Holographic Quick Scratchpad',
    category: 'Productivity',
    description: 'Interactive notepad to jot down thoughts, tasks, and ideas.',
    column: 'right',
    defaultEnabled: false,
  },
  {
    id: 'shortcuts',
    name: 'Global Keybinding Matrix',
    category: 'System',
    description: 'Quick reference for Alt+Space, Ctrl+Space, and workspace hotkeys.',
    column: 'right',
    defaultEnabled: false,
  },
];

interface WidgetStore {
  enabledWidgets: Record<string, boolean>;
  customDirectives: CustomDirective[];
  isCustomizerOpen: boolean;
  scratchpadNote: string;
  
  // Actions
  toggleWidget: (id: string) => void;
  setWidgetEnabled: (id: string, enabled: boolean) => void;
  setCustomizerOpen: (open: boolean) => void;
  addCustomDirective: (directive: Omit<CustomDirective, 'id'>) => void;
  removeCustomDirective: (id: string) => void;
  setScratchpadNote: (note: string) => void;
  resetToDefaults: () => void;
}

const STORAGE_KEY_WIDGETS = 'ada_enabled_widgets_v1';
const STORAGE_KEY_DIRECTIVES = 'ada_custom_directives_v1';
const STORAGE_KEY_SCRATCHPAD = 'ada_scratchpad_note_v1';

const getInitialEnabledWidgets = (): Record<string, boolean> => {
  try {
    const saved = localStorage.getItem(STORAGE_KEY_WIDGETS);
    if (saved) return JSON.parse(saved);
  } catch {}
  
  const defaults: Record<string, boolean> = {};
  AVAILABLE_WIDGETS.forEach(w => {
    defaults[w.id] = w.defaultEnabled;
  });
  return defaults;
};

const getInitialDirectives = (): CustomDirective[] => {
  try {
    const saved = localStorage.getItem(STORAGE_KEY_DIRECTIVES);
    if (saved) return JSON.parse(saved);
  } catch {}
  return [
    { id: '1', label: 'Morning Briefing', cmd: 'give me my morning briefing', color: 'text-amber-400 border-amber-500/30 bg-amber-500/10' },
    { id: '2', label: 'Organize Desktop', cmd: 'organize my desktop', color: 'text-cyan-400 border-cyan-500/30 bg-cyan-500/10' },
    { id: '3', label: 'Message', cmd: 'msg ', color: 'text-emerald-400 border-emerald-500/30 bg-emerald-500/10' },
    { id: '4', label: 'Phone Bridge', cmd: 'check phone battery and status', color: 'text-indigo-400 border-indigo-500/30 bg-indigo-500/10' },
    { id: '5', label: 'Deep Research', cmd: 'search the web for ', color: 'text-purple-400 border-purple-500/30 bg-purple-500/10' },
  ];
};

export const useWidgetStore = create<WidgetStore>((set) => ({
  enabledWidgets: getInitialEnabledWidgets(),
  customDirectives: getInitialDirectives(),
  isCustomizerOpen: false,
  scratchpadNote: localStorage.getItem(STORAGE_KEY_SCRATCHPAD) || 'ADA OS Directives: System Green.',

  toggleWidget: (id: string) => {
    set((state) => {
      const next = { ...state.enabledWidgets, [id]: !state.enabledWidgets[id] };
      try {
        localStorage.setItem(STORAGE_KEY_WIDGETS, JSON.stringify(next));
      } catch {}
      return { enabledWidgets: next };
    });
  },

  setWidgetEnabled: (id: string, enabled: boolean) => {
    set((state) => {
      const next = { ...state.enabledWidgets, [id]: enabled };
      try {
        localStorage.setItem(STORAGE_KEY_WIDGETS, JSON.stringify(next));
      } catch {}
      return { enabledWidgets: next };
    });
  },

  setCustomizerOpen: (open: boolean) => set({ isCustomizerOpen: open }),

  addCustomDirective: (directive) => {
    set((state) => {
      const newDirective: CustomDirective = {
        ...directive,
        id: Date.now().toString(),
      };
      const next = [...state.customDirectives, newDirective];
      try {
        localStorage.setItem(STORAGE_KEY_DIRECTIVES, JSON.stringify(next));
      } catch {}
      return { customDirectives: next };
    });
  },

  removeCustomDirective: (id: string) => {
    set((state) => {
      const next = state.customDirectives.filter((d) => d.id !== id);
      try {
        localStorage.setItem(STORAGE_KEY_DIRECTIVES, JSON.stringify(next));
      } catch {}
      return { customDirectives: next };
    });
  },

  setScratchpadNote: (note: string) => {
    try {
      localStorage.setItem(STORAGE_KEY_SCRATCHPAD, note);
    } catch {}
    set({ scratchpadNote: note });
  },

  resetToDefaults: () => {
    const defaults: Record<string, boolean> = {};
    AVAILABLE_WIDGETS.forEach(w => {
      defaults[w.id] = w.defaultEnabled;
    });
    try {
      localStorage.setItem(STORAGE_KEY_WIDGETS, JSON.stringify(defaults));
    } catch {}
    set({ enabledWidgets: defaults });
  },
}));
