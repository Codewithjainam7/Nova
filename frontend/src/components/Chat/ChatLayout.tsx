import React from 'react';
import { MessageList } from './MessageList';
import { ChatInput } from './ChatInput';

export const ChatLayout: React.FC = () => {
  return (
    <div className="flex flex-col h-full w-full bg-transparent relative min-h-0">
      <div className="flex-1 overflow-hidden min-h-0 flex flex-col">
        <MessageList />
      </div>
      <div className="shrink-0 w-full bg-gradient-to-t from-black/80 via-black/40 to-transparent pt-12 pb-6">
        <ChatInput />
      </div>
    </div>
  );
};
