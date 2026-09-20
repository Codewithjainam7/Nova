import React, { useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { useNovaStore } from '../../store/useNovaStore';
import clsx from 'clsx';
import { Bot, User } from 'lucide-react';

export const MessageList: React.FC = () => {
  const { messages, isStreaming } = useNovaStore();
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Use 'auto' instead of 'smooth' to prevent jittery bouncing during fast token streaming
    bottomRef.current?.scrollIntoView({ behavior: 'auto' });
  }, [messages, isStreaming]);

  if (messages.length === 0) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center text-white/50 min-h-0">
        <Bot className="w-16 h-16 mb-4 opacity-20" />
        <h2 className="text-2xl font-semibold">How can I help you today?</h2>
        <p className="mt-2 text-sm">ADA Autonomous Agent is ready.</p>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto w-full scroll-smooth flex flex-col min-h-0">
      <div className="flex flex-col flex-1 max-w-3xl w-full mx-auto px-4 py-6">
        {/* Flexible spacer that pushes content to bottom when there are few messages */}
        <div className="flex-1" />
        
        <div className="flex flex-col space-y-6 w-full pt-8">
          {messages.map((msg, index) => (
            <div key={msg.id} className={clsx("flex gap-4 w-full", msg.role === 'user' ? "flex-row-reverse" : "flex-row")}>
              <div className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center bg-white/10 mt-1">
                {msg.role === 'user' ? <User className="w-5 h-5 text-white/80" /> : <Bot className="w-5 h-5 text-purple-400" />}
              </div>
              <div className={clsx("flex flex-col gap-1 max-w-[85%]", msg.role === 'user' ? "items-end" : "items-start")}>
                <span className="text-xs text-white/40 font-medium px-1">
                  {msg.role === 'user' ? 'You' : 'ADA'}
                </span>
                <div className={clsx(
                  "px-5 py-3 rounded-2xl text-[15px] leading-relaxed shadow-sm",
                  msg.role === 'user' 
                    ? "bg-blue-600 text-white rounded-tr-sm" 
                    : "bg-[#1e1f26] text-white/90 rounded-tl-sm"
                )}>
                  {msg.role === 'user' ? (
                    <div className="whitespace-pre-wrap">{msg.content}</div>
                  ) : (
                    <ReactMarkdown
                      components={{
                        code({node, inline, className, children, ...props}: any) {
                          const match = /language-(\w+)/.exec(className || '')
                          return !inline && match ? (
                            <SyntaxHighlighter
                              {...props}
                              children={String(children).replace(/\n$/, '')}
                              style={vscDarkPlus}
                              language={match[1]}
                              PreTag="div"
                              className="rounded-xl my-4 text-xs"
                            />
                          ) : (
                            <code {...props} className="bg-black/30 px-1.5 py-0.5 rounded text-pink-300">
                              {children}
                            </code>
                          )
                        }
                      }}
                    >
                      {msg.content}
                    </ReactMarkdown>
                  )}
                  {isStreaming && index === messages.length - 1 && msg.role === 'assistant' && (
                    <span className="inline-block w-2 h-4 ml-1 bg-white animate-pulse align-middle" />
                  )}
                </div>
              </div>
            </div>
          ))}
          <div ref={bottomRef} className="h-4" />
        </div>
      </div>
    </div>
  );
};
