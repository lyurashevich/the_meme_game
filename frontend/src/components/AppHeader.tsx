import { BookOpen, Volume2, VolumeX } from 'lucide-react';
import { useSoundStore } from '../store/soundStore';

const HEADER_BUTTON =
  'flex items-center gap-1.5 text-xs font-bold px-3 py-1.5 rounded-xl border-2 border-[#242426] bg-[#FAF7F2] shadow-[2px_2px_0px_#242426] hover:bg-[#E4D976] transition-all cursor-pointer';

export default function AppHeader({ onShowRules }: { onShowRules: () => void }) {
  const muted = useSoundStore((state) => state.muted);
  const toggleMuted = useSoundStore((state) => state.toggleMuted);
  const SoundIcon = muted ? VolumeX : Volume2;
  const soundLabel = muted ? 'Включить звук' : 'Выключить звук';

  return (
    <header className="sticky top-0 z-40 h-14 border-b-2 border-[#242426] bg-[#ECE8DE] px-3 sm:px-6 lg:px-10 xl:px-16 2xl:px-24 shadow-sm flex items-center">
      <div className="w-full max-w-[1920px] mx-auto flex items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-xl border-2 border-[#242426] bg-[#E4D976] shadow-[2px_2px_0px_#242426] flex items-center justify-center font-black text-sm">
            C?
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <span className="font-extrabold text-base tracking-tight text-[#242426]">СИТУАЦИИ</span>
              <span className="text-[10px] px-1.5 rounded font-bold uppercase tracking-wider bg-[#242426] text-[#FAF7F2]">
                online
              </span>
            </div>
            <p className="text-[11px] text-[#636058] font-medium hidden sm:block">Мультиплеерная карточная игра</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button onClick={toggleMuted} aria-label={soundLabel} title={soundLabel} className={HEADER_BUTTON}>
            <SoundIcon className="w-3.5 h-3.5 text-[#242426]" />
          </button>

          <button
            onClick={onShowRules}
            aria-label="Правила игры" // on a phone only the icon is shown
            className={HEADER_BUTTON}
          >
            <BookOpen className="w-3.5 h-3.5 text-[#242426]" />
            <span className="hidden sm:inline">Правила игры</span>
          </button>
        </div>
      </div>
    </header>
  );
}
