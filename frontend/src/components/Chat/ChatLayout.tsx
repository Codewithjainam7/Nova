import React from 'react';
import { MessageList } from './MessageList';
import { ChatInput } from './ChatInput';

export const ChatLayout: React.FC = () => {
  return (
    <div className="flex flex-col w-full h-full relative bg-transparent overflow-hidden">
      {/* Scrollable message area with padding at the bottom so messages don't hide behind input */}
      <div className="flex-1 min-h-0 overflow-hidden">
        <MessageList />
      </div>

      {/* Input bar — always pinned to the bottom */}
      <div className="w-full shrink-0 flex flex-col items-center justify-center pb-6 pt-2 bg-gradient-to-t from-[#0f1115] via-[#0f1115]/90 to-transparent">
        <ChatInput />
      </div>
    </div>
  );
};
