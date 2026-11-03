import { Loader2, Wifi, WifiOff } from 'lucide-react';
import { useGameStore } from '../store/gameStore';

const LOOKS = {
  online: { text: 'В сети', icon: Wifi, className: 'bg-[#C8D7C5] text-[#2C442A]' },
  connecting: { text: 'Подключаемся...', icon: Loader2, className: 'bg-[#E4D976] text-[#242426]' },
  offline: { text: 'Нет связи, переподключаемся', icon: WifiOff, className: 'bg-[#E8BAA8] text-[#52291E]' },
};

export default function ConnectionIndicator() {
  // Subscribe to one field only: the indicator re-renders when the connection changes, not on every snapshot
  const connection = useGameStore((state) => state.connection);
  const look = LOOKS[connection];
  const Icon = look.icon;

  return (
    <div
      role="status"
      className={`fixed bottom-4 left-4 z-50 flex items-center gap-1.5 px-3 py-1.5 rounded-xl border-2 border-[#242426] shadow-[2px_2px_0px_#242426] text-xs font-bold ${look.className}`}
    >
      <Icon className={`w-3.5 h-3.5 ${connection === 'connecting' ? 'animate-spin' : ''}`} />
      <span>{look.text}</span>
    </div>
  );
}
