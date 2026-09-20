import React, { createContext, useContext, useEffect, useRef } from 'react';
import { useNovaStore } from '../store/useNovaStore';

interface NovaWebSocketContextType {
  sendChat: (message: string) => void;
  sendAction: (action: string, payload?: any) => void;
}

const NovaWebSocketContext = createContext<NovaWebSocketContextType | null>(null);

export const useNovaWebSocket = () => {
  const context = useContext(NovaWebSocketContext);
  if (!context) {
    throw new Error('useNovaWebSocket must be used within a NovaWebSocketProvider');
  }
  return context;
};

export const NovaWebSocketProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const wsChat = useRef<WebSocket | null>(null);
  const wsEvents = useRef<WebSocket | null>(null);
  
  const { 
    addMessage, 
    replaceLastMessage,
    setIslandState, 
    addExecutionStep,
    setStreaming,
    clearExecutionTimeline
  } = useNovaStore();

  const messageQueue = useRef<string[]>([]);

  useEffect(() => {
    let reconnectTimerChat: ReturnType<typeof setTimeout>;
    let reconnectTimerEvents: ReturnType<typeof setTimeout>;

    const connectChat = () => {
      wsChat.current = new WebSocket('ws://localhost:8000/ws/chat');
      
      wsChat.current.onopen = () => {
        while(messageQueue.current.length > 0) {
          const msg = messageQueue.current.shift();
          if (msg) wsChat.current?.send(msg);
        }
      };
      
      wsChat.current.onmessage = (event) => {
        const data = JSON.parse(event.data);
        const { messages } = useNovaStore.getState();
        if (data.type === 'message_chunk' || data.type === 'message_complete') {
          if (messages.length === 0) {
            addMessage({
              id: data.message.id || Date.now().toString(),
              role: data.message.role || 'assistant',
              content: data.message.content,
              timestamp: Date.now()
            });
          } else {
            replaceLastMessage(data.message.content);
          }
          if (data.type === 'message_complete') {
            setStreaming(false);
            setIslandState('idle');
          }
        }
      };

      wsChat.current.onclose = () => {
        reconnectTimerChat = setTimeout(connectChat, 2000);
      };
    };

    const connectEvents = () => {
      wsEvents.current = new WebSocket('ws://localhost:8000/ws/events');
      
      wsEvents.current.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        switch(data.type) {
          case 'KERNEL_STARTED':
          case 'REQUEST_RECEIVED':
            setIslandState('thinking', 'Processing Request...');
            clearExecutionTimeline();
            break;
          case 'PLANNING_STARTED':
            setIslandState('thinking', 'Planning execution...');
            addExecutionStep({ id: Date.now().toString(), status: 'active', description: 'Planning execution' });
            break;
          case 'EXECUTION_STARTED':
            setIslandState('executing', 'Executing plan...');
            break;
          case 'STREAM_CHUNK':
            addExecutionStep({ id: Date.now().toString(), status: 'active', description: data.content });
            setIslandState('executing', data.content);
            
            if (data.content.toLowerCase().includes('browser')) {
               setIslandState('browser', data.content);
            } else if (data.content.toLowerCase().includes('desktop')) {
               setIslandState('desktop', data.content);
            } else if (data.content.toLowerCase().includes('vision')) {
               setIslandState('vision', data.content);
            }
            break;
          case 'PROVIDER_INVOKED':
            setIslandState('thinking', 'Generating answer...');
            setStreaming(true);
            break;
          case 'WORKSPACE_RENDER':
            useNovaStore.getState().setWorkspaceData(data.payload);
            break;
          case 'RESPONSE_COMPLETED':
            setIslandState('idle', '');
            break;
          case 'ERROR':
            setIslandState('error', data.payload || 'An error occurred');
            break;
        }
      };

      wsEvents.current.onclose = () => {
        reconnectTimerEvents = setTimeout(connectEvents, 2000);
      };
    };

    connectChat();
    connectEvents();

    return () => {
      clearTimeout(reconnectTimerChat);
      clearTimeout(reconnectTimerEvents);
      
      if (wsChat.current) {
        wsChat.current.onclose = null;
        wsChat.current.close();
      }
      if (wsEvents.current) {
        wsEvents.current.onclose = null;
        wsEvents.current.close();
      }
    };
  }, []);

  const sendChat = (message: string) => {
    addMessage({
      id: Date.now().toString(),
      role: 'user',
      content: message,
      timestamp: Date.now()
    });
    
    // Add empty assistant message to stream into
    addMessage({
      id: (Date.now() + 1).toString(),
      role: 'assistant',
      content: '',
      timestamp: Date.now()
    });
    
    if (wsChat.current && wsChat.current.readyState === WebSocket.OPEN) {
      wsChat.current.send(message);
    } else {
      // If WS is still connecting, queue the message
      messageQueue.current.push(message);
    }
  };

  const sendAction = (action: string, payload?: any) => {
    if (wsEvents.current && wsEvents.current.readyState === WebSocket.OPEN) {
        wsEvents.current.send(JSON.stringify({ action, payload }));
    }
  };

  return (
    <NovaWebSocketContext.Provider value={{ sendChat, sendAction }}>
      {children}
    </NovaWebSocketContext.Provider>
  );
};
