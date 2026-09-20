import { create } from 'zustand';

export type Role = 'user' | 'assistant' | 'system';

export interface Message {
  id: string;
  role: Role;
  content: string;
  timestamp: number;
}

export interface ExecutionStep {
  id: string;
  status: 'pending' | 'active' | 'completed' | 'error';
  description: string;
}

export type IslandState = 'idle' | 'listening' | 'thinking' | 'executing' | 'browser' | 'desktop' | 'vision' | 'error';

interface NovaState {
  messages: Message[];
  executionTimeline: ExecutionStep[];
  islandState: IslandState;
  islandMessage: string;
  isStreaming: boolean;
  workspaceData: any;
  
  // Actions
  addMessage: (msg: Message) => void;
  updateLastMessage: (content: string) => void;
  replaceLastMessage: (content: string) => void;
  addExecutionStep: (step: ExecutionStep) => void;
  updateExecutionStep: (id: string, status: ExecutionStep['status']) => void;
  clearExecutionTimeline: () => void;
  setIslandState: (state: IslandState, message?: string) => void;
  setStreaming: (streaming: boolean) => void;
  setWorkspaceData: (data: any) => void;
}

export const useNovaStore = create<NovaState>((set) => ({
  messages: [],
  executionTimeline: [],
  islandState: 'idle',
  islandMessage: '',
  isStreaming: false,
  workspaceData: null,
  
  setWorkspaceData: (data) => set({ workspaceData: data }),
  
  addMessage: (msg) => set((state) => ({ messages: [...state.messages, msg] })),
  
  updateLastMessage: (content) => set((state) => {
    const msgs = [...state.messages];
    if (msgs.length > 0) {
      msgs[msgs.length - 1].content += content;
    }
    return { messages: msgs };
  }),
  
  replaceLastMessage: (content) => set((state) => {
    const msgs = [...state.messages];
    if (msgs.length > 0) {
      msgs[msgs.length - 1].content = content;
    }
    return { messages: msgs };
  }),
  
  addExecutionStep: (step) => set((state) => ({
    executionTimeline: [...state.executionTimeline, step]
  })),
  
  updateExecutionStep: (id, status) => set((state) => ({
    executionTimeline: state.executionTimeline.map(step => 
      step.id === id ? { ...step, status } : step
    )
  })),
  
  clearExecutionTimeline: () => set({ executionTimeline: [] }),
  
  setIslandState: (state, message = '') => set({ 
    islandState: state, 
    islandMessage: message 
  }),
  
  setStreaming: (streaming) => set({ isStreaming: streaming }),
}));
