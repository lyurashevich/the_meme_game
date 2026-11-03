import { MessageSquare, Send } from 'lucide-react';
import { useEffect, useRef, useState, type FormEvent } from 'react';
import type { ChatMessage } from '../protocol';

const MAX_MESSAGE_LENGTH = 500; // the server's limit

interface ChatPanelProps {
  title: string;
  badge: string;
  messages: ChatMessage[];
  myId: string;
  quickReplies: string[];
  placeholder: string;
  onSend: (text: string) => void;
}

const formatTime = (timestamp: string) =>
  new Date(timestamp).toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' });

export default function ChatPanel({ title, badge, messages, myId, quickReplies, placeholder, onSend }: ChatPanelProps) {
  const [text, setText] = useState('');

  // A ref gives access to the real DOM element, here to scroll the message list
  const listRef = useRef<HTMLDivElement>(null);

  // An effect runs after React has updated the page. With [messages.length] it runs
  // only when the number of messages changes: then scroll down to the newest one.
  useEffect(() => {
    const list = listRef.current;
    if (list) list.scrollTop = list.scrollHeight;
  }, [messages.length]);

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    const trimmed = text.trim();
    if (!trimmed) return;
    onSend(trimmed);
    setText('');
  };

  return (
    <div className="rounded-3xl border-2 border-[#242426] bg-[#FAF7F2] p-4 shadow-[4px_4px_0px_#242426] flex flex-col h-[380px] lg:h-auto lg:min-h-0">
      {/* Header */}
      <div className="flex items-center justify-between pb-2.5 border-b-2 border-[#242426]/15">
        <div className="flex items-center gap-2">
          <MessageSquare className="w-4 h-4 text-[#242426]" />
          <span className="font-extrabold text-sm text-[#242426]">{title}</span>
        </div>
        <span className="text-[10px] bg-[#EAE5D9] px-2 py-0.5 rounded-full font-bold text-[#555148]">{badge}</span>
      </div>

      {/* Messages */}
      <div ref={listRef} className="flex-1 overflow-y-auto my-2 space-y-2.5 pr-1 text-xs lg:max-h-[420px]">
        {messages.length === 0 && (
          <p className="text-center text-[11px] text-[#88837A] italic mt-4">Пока тихо. Напиши первым!</p>
        )}
        {messages.map((message, index) => (
          // Messages have no id of their own; they are only ever appended, so the position is stable
          <div
            key={index}
            className={`p-2 rounded-xl border ${
              message.player_id === myId ? 'bg-[#F3EDC8] border-[#242426]/30' : 'bg-[#F4F1EA] border-[#242426]/20'
            }`}
          >
            <div className="flex items-center justify-between mb-0.5">
              <span className="font-extrabold text-[#242426]">{message.username}</span>
              <span className="text-[10px] text-[#88837A]">{formatTime(message.timestamp)}</span>
            </div>
            <p className="text-[#35322E] font-medium leading-relaxed break-words">{message.text}</p>
          </div>
        ))}
      </div>

      {/* Quick replies and input */}
      <div>
        <div className="flex items-center gap-1.5 mb-2 overflow-x-auto pb-1">
          {quickReplies.map((reply) => (
            <button
              key={reply}
              type="button"
              onClick={() => onSend(reply)}
              className="px-2 py-1 rounded-lg border border-[#242426]/20 bg-[#ECE8DE] hover:bg-[#E4D976] text-xs font-bold text-[#3B3831] whitespace-nowrap transition-colors cursor-pointer"
            >
              {reply}
            </button>
          ))}
        </div>

        <form onSubmit={handleSubmit} className="flex items-center gap-1.5">
          <input
            type="text"
            value={text}
            maxLength={MAX_MESSAGE_LENGTH}
            onChange={(event) => setText(event.target.value)}
            placeholder={placeholder}
            className="flex-1 min-w-0 rounded-xl border-2 border-[#242426] bg-[#F5F2EA] px-3 py-2 text-xs font-semibold text-[#242426] placeholder-[#9E988D] focus:outline-none focus:bg-[#FAF7F2]"
          />
          <button
            type="submit"
            aria-label="Отправить"
            className="p-2 rounded-xl border-2 border-[#242426] bg-[#E4D976] hover:bg-[#DDD166] text-[#242426] cursor-pointer shadow-[2px_2px_0px_#242426]"
          >
            <Send className="w-3.5 h-3.5" />
          </button>
        </form>
      </div>
    </div>
  );
}
