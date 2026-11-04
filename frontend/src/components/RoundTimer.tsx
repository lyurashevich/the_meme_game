import { Clock } from 'lucide-react';
import { useEffect, useState } from 'react';

const HURRY_UP_SECONDS = 15;

interface RoundTimerProps {
  endsAt: string; // ISO deadline from the server
  serverTime: string; // the server's clock when it sent the snapshot
}

// Counts down to the phase deadline. The browser's clock may be off by minutes,
// so take only the difference between the two server times and count it down locally.
export default function RoundTimer({ endsAt, serverTime }: RoundTimerProps) {
  const [secondsLeft, setSecondsLeft] = useState<number | null>(null);

  useEffect(() => {
    // Runs right after a new snapshot is shown, so "now" is when it arrived
    const deadline = Date.now() + (Date.parse(endsAt) - Date.parse(serverTime));
    const tick = () => setSecondsLeft(Math.max(0, Math.ceil((deadline - Date.now()) / 1000)));

    tick();
    const timer = setInterval(tick, 250);
    // The cleanup runs before the next run and when the timer leaves the page:
    // without it, old intervals would keep ticking in the background
    return () => clearInterval(timer);
  }, [endsAt, serverTime]);

  if (secondsLeft === null) return null;

  const minutes = Math.floor(secondsLeft / 60);
  const seconds = String(secondsLeft % 60).padStart(2, '0');
  const hurry = secondsLeft < HURRY_UP_SECONDS;

  return (
    <div
      className={`flex items-center gap-1.5 px-3 py-1 rounded-xl border-2 border-[#242426] font-black text-xs shadow-[2px_2px_0px_#242426] tabular-nums ${
        hurry ? 'bg-[#E8BAA8] text-[#551E14] animate-pulse' : 'bg-[#FAF7F2] text-[#242426]'
      }`}
    >
      <Clock className="w-3.5 h-3.5" />
      <span>
        {minutes}:{seconds}
      </span>
    </div>
  );
}
