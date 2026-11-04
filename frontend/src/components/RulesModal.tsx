import { Clock, Flag, Info, Sparkles, Users, X } from 'lucide-react';
import type { ReactNode } from 'react';
import { useCloseOnEscape } from '../hooks/useCloseOnEscape';

// The rules of the game, opened from the header. The numbers are the server's
// (app/services/game_service.py, app/schemas/game.py): change them together.
interface RulesModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function RulesModal({ isOpen, onClose }: RulesModalProps) {
  useCloseOnEscape(isOpen, onClose);

  if (!isOpen) {
    return null;
  }

  return (
    <div
      className="fixed inset-0 z-50 bg-[#242426]/60 backdrop-blur-sm flex items-center justify-center p-4"
      onClick={onClose} // a click on the dimmed background closes it...
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="rules-title"
        className="w-full max-w-2xl bg-[#FAF7F2] border-[3px] border-[#242426] rounded-3xl p-6 sm:p-7 shadow-[6px_6px_0px_#242426] max-h-[90vh] overflow-y-auto"
        onClick={(event) => event.stopPropagation()} // ...a click inside doesn't
      >
        <div className="flex items-center justify-between pb-3 border-b-2 border-[#242426]/15 mb-4">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-xl bg-[#E4D976] border-2 border-[#242426] flex items-center justify-center font-black text-xs">
              ?
            </div>
            <div>
              <h2 id="rules-title" className="font-black text-lg text-[#242426] leading-tight">
                Правила игры
              </h2>
              <p className="text-xs text-[#6E6A62]">Подбери мем к ситуации смешнее, чем друзья</p>
            </div>
          </div>
          <button
            onClick={onClose}
            aria-label="Закрыть"
            className="p-1.5 rounded-xl border-2 border-[#242426] bg-[#ECE8DE] hover:bg-[#E4D976] text-[#242426] transition-colors cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="space-y-4 text-xs text-[#423F39] leading-relaxed">
          <Section icon={<Sparkles className="w-4 h-4 text-[#8C7624]" />} title="Суть">
            <p>
              На столе — карта с жизненной ситуацией. Каждый игрок подбирает к ней самый подходящий мем из своей руки, а
              ведущий решает, чей мем смешнее. Побеждает тот, кто наберёт больше всего очков.
            </p>
          </Section>

          <Section icon={<Users className="w-4 h-4 text-[#8C7624]" />} title="Перед игрой">
            <ul className="list-disc pl-4 space-y-1">
              <li>
                В комнате от <strong>3 до 10</strong> игроков.
              </li>
              <li>
                Создатель комнаты выбирает время на ход (<strong>60, 90 или 120 секунд</strong>) и, если хочет, лимит
                раундов или очков. Он же запускает игру.
              </li>
              <li>
                Каждый получает <strong>6 карт-мемов</strong>. Первым ведущим становится создатель комнаты.
              </li>
            </ul>
          </Section>

          <Section icon={<Clock className="w-4 h-4 text-[#8C7624]" />} title="Как идёт раунд">
            <ol className="list-decimal pl-4 space-y-1">
              <li>Открывается новая ситуация.</li>
              <li>
                Все, кроме ведущего, выбирают из руки по одному мему, пока не кончилось время. Кто не успел, в этом
                раунде не участвует.
              </li>
              <li>
                Ведущий видит сыгранные мемы без имён авторов и за <strong>30 секунд</strong> выбирает лучший. Его автор
                получает <strong>+1 очко</strong>. Не успел выбрать — очков в этом раунде не получает никто.
              </li>
              <li>
                Каждый, кто сыграл мем, получает новую карту, и ведущим становится следующий игрок по кругу. Если мем не
                сыграл никто, сразу начинается следующий раунд.
              </li>
            </ol>
          </Section>

          <Section icon={<Flag className="w-4 h-4 text-[#8C7624]" />} title="Конец игры">
            <p className="mb-1">Игра заканчивается, когда:</p>
            <ul className="list-disc pl-4 space-y-1">
              <li>сыграно заданное число раундов или кто-то набрал заданное число очков;</li>
              <li>создатель комнаты завершил игру;</li>
              <li>в комнате осталось меньше 3 игроков;</li>
              <li>закончились карты.</li>
            </ul>
            <p className="mt-1">После этого все видят итоговый счёт.</p>
          </Section>

          <Section icon={<Info className="w-4 h-4 text-[#8C7624]" />} title="Мелочи">
            <ul className="list-disc pl-4 space-y-1">
              <li>
                Сыгранный мем возвращается в колоду через <strong>10 раундов</strong>, ситуация — через{' '}
                <strong>20</strong>, так что повторы будут нечасто.
              </li>
              <li>Имена в комнате не повторяются, регистр не важен: «Neo» и «neo» — одно имя.</li>
              <li>
                Пропала связь? У тебя есть <strong>60 секунд</strong>, чтобы вернуться и сохранить место и очки.
              </li>
              <li>Когда все вышли, комната исчезает.</li>
            </ul>
          </Section>
        </div>

        <div className="mt-5 pt-3 border-t border-[#242426]/15 flex justify-end">
          <button
            onClick={onClose}
            className="px-5 py-2 rounded-xl border-2 border-[#242426] bg-[#E4D976] font-black text-xs text-[#242426] shadow-[2px_2px_0px_#242426] hover:bg-[#DDD166] cursor-pointer"
          >
            Понятно, играем
          </button>
        </div>
      </div>
    </div>
  );
}

function Section({ icon, title, children }: { icon: ReactNode; title: string; children: ReactNode }) {
  return (
    <div className="p-3.5 rounded-2xl border-2 border-[#242426] bg-[#F4F1EA]">
      <h3 className="font-black text-sm text-[#242426] mb-1.5 flex items-center gap-1.5">
        {icon}
        {title}
      </h3>
      {children}
    </div>
  );
}
