import { useState, useRef, useEffect } from 'react';
import { Send, Sparkles } from 'lucide-react';
import { useGuidedSetupStore } from '../../stores/guidedSetupStore';

interface ChatPanelProps {
  onSend: (message: string) => Promise<void>;
  isLoading: boolean;
}

function TypingIndicator() {
  return (
    <div className="flex items-end gap-2 justify-start">
      <div className="w-7 h-7 rounded-full bg-violet-100 dark:bg-violet-900/40 flex items-center justify-center shrink-0">
        <Sparkles className="w-4 h-4 text-violet-500" />
      </div>
      <div className="bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-2xl rounded-bl-md px-4 py-3">
        <div className="flex items-center gap-1">
          <span className="w-2 h-2 bg-gray-400 dark:bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0ms', animationDuration: '0.6s' }} />
          <span className="w-2 h-2 bg-gray-400 dark:bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0.15s', animationDuration: '0.6s' }} />
          <span className="w-2 h-2 bg-gray-400 dark:bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0.3s', animationDuration: '0.6s' }} />
        </div>
      </div>
    </div>
  );
}

export function ChatPanel({ onSend, isLoading }: ChatPanelProps): React.ReactElement {
  const [input, setInput] = useState('');
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const { conversationHistory, progress } = useGuidedSetupStore();

  useEffect(() => {
    const container = messagesContainerRef.current;
    if (!container) return;
    // Use requestAnimationFrame to ensure DOM has updated before scrolling
    const raf = requestAnimationFrame(() => {
      container.scrollTop = container.scrollHeight;
    });
    return () => cancelAnimationFrame(raf);
  }, [conversationHistory]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;
    const message = input.trim();
    setInput('');
    await onSend(message);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className="flex flex-col h-full bg-white dark:bg-gray-900 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-violet-500" />
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              Story Architect
            </h2>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-sm text-gray-500 dark:text-gray-400">
              {Math.round(progress)}% complete
            </span>
            <div className="w-24 h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-violet-500 to-purple-500 rounded-full transition-all duration-300"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div ref={messagesContainerRef} className="flex-1 overflow-y-auto p-4 space-y-3">
        {conversationHistory.length === 0 && (
          <div className="text-center py-8">
            <Sparkles className="w-12 h-12 text-violet-300 dark:text-violet-600 mx-auto mb-3" />
            <p className="text-gray-600 dark:text-gray-400">
              I'll help you set up your writing project. Just answer my questions naturally.
            </p>
          </div>
        )}

        {conversationHistory.map((msg, i) => (
          <div
            key={i}
            className={`flex items-end gap-2 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            {msg.role === 'system' && (
              <div className="w-7 h-7 rounded-full bg-violet-100 dark:bg-violet-900/40 flex items-center justify-center shrink-0">
                <Sparkles className="w-4 h-4 text-violet-500" />
              </div>
            )}
            <div
              className={`max-w-[75%] rounded-2xl px-4 py-2.5 ${
                msg.role === 'user'
                  ? 'bg-violet-500 text-white rounded-br-md'
                  : 'bg-gray-100 dark:bg-gray-800 text-gray-800 dark:text-gray-200 border border-gray-200 dark:border-gray-700 rounded-bl-md'
              }`}
            >
              <p className="text-sm whitespace-pre-wrap leading-relaxed">{msg.content}</p>
            </div>
            {msg.role === 'user' && (
              <div className="w-7 h-7 rounded-full bg-gray-200 dark:bg-gray-700 flex items-center justify-center shrink-0 text-xs font-medium text-gray-500 dark:text-gray-400">
                U
              </div>
            )}
          </div>
        ))}

        {isLoading && <TypingIndicator />}
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="p-4 border-t border-gray-200 dark:border-gray-700">
        <div className="flex gap-2">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type your answer... (Enter to send, Shift+Enter for new line)"
            rows={1}
            disabled={isLoading}
            className="flex-1 resize-none rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-4 py-2 text-sm text-gray-900 dark:text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-transparent disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            className="px-4 py-2 bg-violet-500 text-white rounded-lg hover:bg-violet-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
      </form>
    </div>
  );
}
