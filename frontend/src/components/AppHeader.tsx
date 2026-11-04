import { BookOpen } from 'lucide-react';

export default function AppHeader({ onShowRules }: { onShowRules: () => void }) {
  return (
    <header className="sticky top-0 z-40 border-b-2 border-[#242426] bg-[#ECE8DE] px-4 py-2.5 shadow-sm">
      <div className="max-w-7xl mx-auto flex items-center justify-between gap-3">
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

        <button
          onClick={onShowRules}
          aria-label="Правила игры" // on a phone only the icon is shown
          className="flex items-center gap-1.5 text-xs font-bold px-3 py-1.5 rounded-xl border-2 border-[#242426] bg-[#FAF7F2] shadow-[2px_2px_0px_#242426] hover:bg-[#E4D976] transition-all cursor-pointer"
        >
          <BookOpen className="w-3.5 h-3.5 text-[#242426]" />
          <span className="hidden sm:inline">Правила игры</span>
        </button>
      </div>
    </header>
  );
}
