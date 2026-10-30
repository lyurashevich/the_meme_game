import { ChevronLeft, ChevronRight, Info, Sparkles } from 'lucide-react';
import type { ScreenId } from '../types';

// Mockup tool: lets you click through the screens while they still run on mock data.
// Once the screens follow the server state, the screen is no longer picked by hand.
const SCREENS: { id: ScreenId; number: number; title: string }[] = [
  { id: 'screen1', number: 1, title: 'Создание игрока' },
  { id: 'screen2', number: 2, title: 'Выбор комнаты' },
  { id: 'screen3', number: 3, title: 'Лобби до начала' },
  { id: 'screen4', number: 4, title: 'Активная игра' },
];

interface MockupHeaderProps {
  currentScreen: ScreenId;
  onSelectScreen: (screen: ScreenId) => void;
  onToggleSpecs: () => void;
}

export default function MockupHeader({ currentScreen, onSelectScreen, onToggleSpecs }: MockupHeaderProps) {
  const currentIndex = SCREENS.findIndex((s) => s.id === currentScreen);

  return (
    <header className="sticky top-0 z-50 border-b-2 border-[#242426] bg-[#ECE8DE] px-4 py-2.5 shadow-sm">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-3">
        {/* Logo and game identity */}
        <div className="flex items-center gap-3 w-full md:w-auto justify-between md:justify-start">
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
            onClick={onToggleSpecs}
            className="md:hidden flex items-center gap-1 text-xs font-semibold px-2.5 py-1.5 rounded-lg border border-[#242426] bg-[#FAF7F2] hover:bg-[#EAE5D9] transition-colors"
          >
            <Info className="w-3.5 h-3.5" />
            <span>Стиль</span>
          </button>
        </div>

        {/* Screen switcher */}
        <nav className="flex items-center gap-1.5 bg-[#DFD9CD] p-1 rounded-xl border border-[#242426]/30 overflow-x-auto max-w-full">
          {SCREENS.map((s) => {
            const isCurrent = s.id === currentScreen;
            return (
              <button
                key={s.id}
                onClick={() => onSelectScreen(s.id)}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition-all whitespace-nowrap cursor-pointer ${
                  isCurrent
                    ? 'bg-[#FAF7F2] text-[#242426] border border-[#242426] shadow-[2px_2px_0px_#242426]'
                    : 'text-[#58554E] hover:text-[#242426] hover:bg-[#ECE8DE]'
                }`}
              >
                <span
                  className={`w-4 h-4 rounded-full text-[10px] flex items-center justify-center font-black ${
                    isCurrent ? 'bg-[#E4D976] text-[#242426]' : 'bg-[#CAC3B4] text-[#4F4C45]'
                  }`}
                >
                  {s.number}
                </span>
                <span>{s.title}</span>
              </button>
            );
          })}
        </nav>

        {/* Quick stepper + specs button */}
        <div className="hidden md:flex items-center gap-2">
          <div className="flex items-center gap-1 border border-[#242426]/20 bg-[#FAF7F2] rounded-lg p-0.5">
            <button
              onClick={() => onSelectScreen(SCREENS[currentIndex - 1].id)}
              disabled={currentIndex === 0}
              title="Предыдущий экран"
              className="p-1 rounded hover:bg-[#EAE5D9] disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
            >
              <ChevronLeft className="w-4 h-4 text-[#242426]" />
            </button>
            <span className="text-[11px] font-bold px-1.5 text-[#55524B]">
              {currentIndex + 1} / {SCREENS.length}
            </span>
            <button
              onClick={() => onSelectScreen(SCREENS[currentIndex + 1].id)}
              disabled={currentIndex === SCREENS.length - 1}
              title="Следующий экран"
              className="p-1 rounded hover:bg-[#EAE5D9] disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
            >
              <ChevronRight className="w-4 h-4 text-[#242426]" />
            </button>
          </div>

          <button
            onClick={onToggleSpecs}
            className="flex items-center gap-1.5 text-xs font-bold px-3 py-1.5 rounded-xl border-2 border-[#242426] bg-[#FAF7F2] shadow-[2px_2px_0px_#242426] hover:bg-[#E4D976] hover:shadow-[3px_3px_0px_#242426] transition-all cursor-pointer"
          >
            <Sparkles className="w-3.5 h-3.5 text-[#242426]" />
            <span>Концепт стиля</span>
          </button>
        </div>
      </div>
    </header>
  );
}
