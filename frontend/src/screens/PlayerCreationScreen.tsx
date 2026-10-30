import { Check, ChevronLeft, ChevronRight, Dices, Smile } from 'lucide-react';
import { useState, type FormEvent } from 'react';
import { AVATAR_OPTIONS } from '../avatars';
import Avatar from '../components/Avatar';
import type { PlayerProfile } from '../types';

const FUN_NICKNAMES = [
  'Дед_Инсайд',
  'Кринж_Мастер',
  'Кот_В_Шоке',
  'Капибара_Босс',
  'Пятничный_Баг',
  'Толян_Мемолог',
  'Чайный_Пакет',
  'Главный_Клоун',
  'Постиронист',
];

interface PlayerCreationScreenProps {
  player: PlayerProfile;
  onUpdatePlayer: (changes: Partial<PlayerProfile>) => void;
  onConfirm: () => void;
}

export default function PlayerCreationScreen({ player, onUpdatePlayer, onConfirm }: PlayerCreationScreenProps) {
  // What is being typed lives here until the player confirms it
  const [nickname, setNickname] = useState(player.username || 'Мемный чел');
  const [isConfirming, setIsConfirming] = useState(false);

  // Derived from props on every render, so it always matches the chosen avatar
  const avatarIndex = Math.max(
    0,
    AVATAR_OPTIONS.findIndex((a) => a.id === player.avatarId),
  );
  const avatar = AVATAR_OPTIONS[avatarIndex];

  const selectAvatar = (step: number) => {
    const next = (avatarIndex + step + AVATAR_OPTIONS.length) % AVATAR_OPTIONS.length;
    onUpdatePlayer({ avatarId: AVATAR_OPTIONS[next].id });
  };

  const pickRandomNickname = () => {
    setNickname(FUN_NICKNAMES[Math.floor(Math.random() * FUN_NICKNAMES.length)]);
  };

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault(); // a form would otherwise reload the page
    onUpdatePlayer({ username: nickname.trim() || 'Анонимный_Мем' });
    setIsConfirming(true);
    setTimeout(onConfirm, 300); // let the "done" state show for a moment
  };

  return (
    <div className="relative min-h-[calc(100vh-65px)] flex flex-col items-center justify-center p-4 sm:p-6 bg-[#F4F1EA]">
      {/* Decorative stickers */}
      <div className="absolute top-8 left-8 hidden lg:block opacity-40 select-none pointer-events-none -rotate-6">
        <div className="border-2 border-dashed border-[#242426]/40 rounded-xl px-3 py-1.5 text-xs font-bold text-[#55524B] bg-[#ECE8DE]">
          «Мемы спасут мир (но это не точно)»
        </div>
      </div>
      <div className="absolute bottom-8 right-8 hidden lg:block opacity-40 select-none pointer-events-none rotate-3">
        <div className="border-2 border-dashed border-[#242426]/40 rounded-xl px-3 py-1.5 text-xs font-bold text-[#55524B] bg-[#ECE8DE]">
          Экран 1: Профиль игрока
        </div>
      </div>

      <div className="w-full max-w-md mx-auto flex flex-col items-center">
        {/* Title */}
        <div className="text-center mb-6 select-none">
          <div className="inline-block bg-[#E4D976] border-2 border-[#242426] px-3.5 py-1 rounded-full text-xs font-extrabold uppercase tracking-widest text-[#242426] shadow-[2px_2px_0px_#242426] mb-3 -rotate-1">
            Карточная веб-игра
          </div>
          <h1 className="text-4xl sm:text-5xl font-black tracking-tight text-[#242426] leading-none">СИТУАЦИИ</h1>
          <p className="mt-2 text-sm text-[#66635C] font-medium">Создай своего персонажа перед входом в комнату</p>
        </div>

        {/* Profile card */}
        <div className="w-full rounded-3xl border-2 border-[#242426] bg-[#FAF7F2] p-6 sm:p-8 shadow-[5px_5px_0px_#242426] flex flex-col items-center relative">
          <div className="absolute -top-3.5 bg-[#FAF7F2] border-2 border-[#242426] px-3 py-0.5 rounded-full text-[11px] font-bold text-[#44423E] shadow-[2px_2px_0px_#242426]">
            ШАГ 1 ИЗ 4 • ВЫБОР АВАТАРА
          </div>

          {/* Avatar selector */}
          <div className="flex items-center justify-center gap-4 sm:gap-6 my-4 w-full">
            <button
              type="button"
              onClick={() => selectAvatar(-1)}
              aria-label="Предыдущий аватар"
              className="w-12 h-12 rounded-2xl border-2 border-[#242426] bg-[#ECE8DE] hover:bg-[#E4D976] active:translate-y-0.5 shadow-[3px_3px_0px_#242426] flex items-center justify-center transition-all cursor-pointer group"
            >
              <ChevronLeft className="w-6 h-6 text-[#242426] group-hover:-translate-x-0.5 transition-transform" />
            </button>

            <div
              className="relative group cursor-pointer"
              onClick={() => selectAvatar(1)}
              title="Нажмите, чтобы сменить"
            >
              <Avatar id={avatar.id} size="xl" className="hover:scale-[1.02]" />
              <span className="absolute -bottom-2 -right-2 bg-[#242426] text-[#FAF7F2] text-[10px] font-bold px-2 py-0.5 rounded-md border border-[#FAF7F2]">
                {avatarIndex + 1}/{AVATAR_OPTIONS.length}
              </span>
            </div>

            <button
              type="button"
              onClick={() => selectAvatar(1)}
              aria-label="Следующий аватар"
              className="w-12 h-12 rounded-2xl border-2 border-[#242426] bg-[#ECE8DE] hover:bg-[#E4D976] active:translate-y-0.5 shadow-[3px_3px_0px_#242426] flex items-center justify-center transition-all cursor-pointer group"
            >
              <ChevronRight className="w-6 h-6 text-[#242426] group-hover:translate-x-0.5 transition-transform" />
            </button>
          </div>

          {/* Avatar name and mood */}
          <div className="text-center mt-1 mb-5">
            <h3 className="font-extrabold text-lg text-[#242426]">{avatar.name}</h3>
            <p className="text-xs text-[#5D5950] italic mt-0.5 px-4 font-medium">{avatar.mood}</p>
          </div>

          {/* Nickname form */}
          <form onSubmit={handleSubmit} className="w-full flex flex-col gap-4">
            <div>
              <div className="flex items-center justify-between mb-1.5 px-1">
                <label htmlFor="nickname-input" className="text-xs font-bold uppercase tracking-wider text-[#4E4B44]">
                  Твой никнейм в игре:
                </label>
                <button
                  type="button"
                  onClick={pickRandomNickname}
                  className="text-xs font-bold text-[#6D685E] hover:text-[#242426] flex items-center gap-1 cursor-pointer transition-colors"
                  title="Случайный никнейм"
                >
                  <Dices className="w-3.5 h-3.5" />
                  <span>Случайный</span>
                </button>
              </div>

              <input
                id="nickname-input"
                type="text"
                maxLength={32}
                value={nickname}
                onChange={(event) => setNickname(event.target.value)}
                placeholder="Введи никнейм..."
                className="w-full rounded-2xl border-2 border-[#242426] bg-[#F5F2EA] px-4 py-3 text-base font-bold text-[#242426] placeholder-[#9E988D] focus:outline-none focus:bg-[#FAF7F2] focus:ring-2 focus:ring-[#242426] shadow-[2px_2px_0px_#242426] transition-all"
              />
            </div>

            <button
              type="submit"
              id="confirm-player-button"
              className={`w-full mt-2 rounded-2xl border-2 border-[#242426] py-3.5 px-6 font-black text-base text-[#242426] shadow-[4px_4px_0px_#242426] transition-all cursor-pointer flex items-center justify-center gap-2 ${
                isConfirming
                  ? 'bg-[#C8D7C5] translate-y-1 shadow-[1px_1px_0px_#242426]'
                  : 'bg-[#E4D976] hover:bg-[#DDD166] active:translate-y-1 active:shadow-[1px_1px_0px_#242426]'
              }`}
            >
              {isConfirming ? (
                <>
                  <Check className="w-5 h-5" />
                  <span>ГОТОВО! ПЕРЕХОДИМ...</span>
                </>
              ) : (
                <>
                  <span>ОК</span>
                  <span className="text-sm font-semibold opacity-75">-&gt; к комнатам</span>
                </>
              )}
            </button>
          </form>

          {/* Footer */}
          <div className="mt-5 pt-3 border-t border-[#242426]/15 w-full flex items-center justify-between text-[11px] text-[#78746B]">
            <span className="flex items-center gap-1">
              <Smile className="w-3.5 h-3.5" />
              Без регистрации и смс
            </span>
            <span>Статус: готов шутить</span>
          </div>
        </div>

        <p className="mt-4 text-xs text-[#7A766E] text-center max-w-xs">
          Нажми <strong>«ОК»</strong>, чтобы подтвердить профиль и перейти к выбору комнаты (Экран 2).
        </p>
      </div>
    </div>
  );
}
