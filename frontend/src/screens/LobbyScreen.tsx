import { Clock, Crown, LogOut, Play, Settings, Sparkles, Trophy, Users, WifiOff } from 'lucide-react';
import type { ReactNode } from 'react';
import Avatar from '../components/Avatar';
import ChatPanel from '../components/ChatPanel';
import { ROUND_TIME_LIMITS, type GameSettings, type RoomPlayer, type RoomState, type Session } from '../protocol';

const MIN_PLAYERS_TO_START = 3; // the server's rule
const MAX_ROUNDS_OPTIONS = [null, 5, 10, 15, 20];
const SCORE_TO_WIN_OPTIONS = [null, 3, 5, 10];
const QUICK_REPLIES = ['🗿', '🤡', '💀', '🍿', '📉', '🔥'];

interface LobbyScreenProps {
  me: Session;
  roomState: RoomState;
  onStartGame: () => void;
  onLeaveRoom: () => void;
  onUpdateSettings: (settings: GameSettings) => void;
  onSendMessage: (text: string) => void;
}

export default function LobbyScreen({
  me,
  roomState,
  onStartGame,
  onLeaveRoom,
  onUpdateSettings,
  onSendMessage,
}: LobbyScreenProps) {
  const { room, players } = roomState;
  const isOwner = room.owner_id === me.player_id;
  const owner = players.find((p) => p.id === room.owner_id);
  const others = players.filter((p) => p.id !== me.player_id);
  const canStart = players.length >= MIN_PLAYERS_TO_START;

  return (
    <div className="max-w-7xl mx-auto px-3 sm:px-6 py-4 flex flex-col min-h-[calc(100vh-70px)]">
      {/* Room header */}
      <div className="rounded-2xl border-2 border-[#242426] bg-[#FAF7F2] px-4 py-2.5 shadow-[3px_3px_0px_#242426] mb-4 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2.5">
          <button
            onClick={onLeaveRoom}
            title="Выйти в меню комнат"
            className="p-1.5 rounded-xl border border-[#242426]/30 hover:bg-[#ECE8DE] text-[#242426] transition-colors cursor-pointer"
          >
            <LogOut className="w-4 h-4" />
          </button>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="font-black text-base sm:text-lg text-[#242426] tracking-tight">{room.name}</h2>
              <span className="text-[10px] bg-[#E4D976] border border-[#242426] px-2 py-0.5 rounded-full font-bold">
                ЭКРАН 3: ЛОББИ
              </span>
            </div>
            <p className="text-[11px] text-[#6E6A61] font-medium">
              Владелец: <strong>{owner?.username ?? '—'}</strong>
            </p>
          </div>
        </div>

        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-xl border border-[#242426] bg-[#FAF7F2] text-xs font-extrabold text-[#242426]">
          <Users className="w-3.5 h-3.5" />
          <span>
            {players.length}/{room.max_players}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 flex-1 items-stretch">
        {/* Table */}
        <div className="lg:col-span-8 xl:col-span-9 flex flex-col justify-between gap-4 rounded-3xl border-2 border-[#242426] bg-[#E7E2D4] p-4 sm:p-6 shadow-[4px_4px_0px_#242426] relative overflow-hidden">
          {/* Playmat stitched border */}
          <div className="absolute inset-2.5 rounded-2xl border-2 border-dashed border-[#242426]/20 pointer-events-none" />

          {/* Other players around the table */}
          <div className="relative z-10 flex flex-wrap items-start justify-center gap-3 sm:gap-5 pt-1">
            {others.length === 0 && (
              <p className="text-xs font-bold text-[#69655C] py-6">Пока никого. Позови друзей!</p>
            )}
            {others.map((player) => (
              <PlayerSeat key={player.id} player={player} isOwner={player.id === room.owner_id} />
            ))}
          </div>

          {/* Center of the table */}
          <div className="relative z-10 flex flex-col items-center">
            <div className="w-full max-w-md rounded-2xl border-2 border-dashed border-[#242426]/40 bg-[#DCD6C5]/70 p-5 text-center flex flex-col items-center">
              <div className="w-48 h-24 rounded-xl border-2 border-dashed border-[#242426]/50 bg-[#F4F1EA]/80 flex flex-col items-center justify-center p-3 mb-3 -rotate-1">
                <div className="text-xl mb-1">🃏</div>
                <span className="text-xs font-black uppercase tracking-wider text-[#35322D]">Карта ситуации</span>
                <span className="text-[10px] text-[#69655C] leading-tight mt-0.5">
                  Будет выложена в центр после старта
                </span>
              </div>

              <div className="bg-[#FAF7F2] border-2 border-[#242426] px-4 py-2 rounded-xl shadow-[2px_2px_0px_#242426]">
                <p className="text-xs font-bold text-[#242426] flex items-center justify-center gap-1.5">
                  <Sparkles className="w-4 h-4 text-[#B5A528]" />
                  <span>ИГРА ЕЩЁ НЕ НАЧАЛАСЬ</span>
                </p>
                <p className="text-[11px] text-[#69655D] mt-0.5">
                  {isOwner
                    ? canStart
                      ? 'Все в сборе? Жми «Начать игру»'
                      : `Нужно хотя бы ${MIN_PLAYERS_TO_START} игрока`
                    : 'Ждём, когда владелец начнёт игру'}
                </p>
              </div>

              {isOwner && (
                <button
                  type="button"
                  id="start-game-button"
                  onClick={onStartGame}
                  disabled={!canStart}
                  className="mt-4 rounded-2xl border-2 border-[#242426] bg-[#E4D976] hover:bg-[#DDD166] active:translate-y-0.5 px-6 py-2.5 font-black text-sm text-[#242426] shadow-[3px_3px_0px_#242426] flex items-center gap-2 cursor-pointer transition-all disabled:bg-[#DDD9CE] disabled:text-[#868278] disabled:shadow-none disabled:cursor-not-allowed"
                >
                  <Play className="w-4 h-4 fill-current" />
                  <span>НАЧАТЬ ИГРУ →</span>
                </button>
              )}
            </div>
          </div>

          {/* You and the settings */}
          <div className="relative z-10 flex flex-col sm:flex-row items-center sm:items-end justify-between gap-3">
            <div className="flex items-center gap-2.5 bg-[#FAF7F2] border-2 border-[#242426] px-4 py-1.5 rounded-2xl shadow-[2px_2px_0px_#242426]">
              <Avatar id={me.avatar_id} size="sm" />
              <span className="font-black text-xs text-[#242426]">
                {me.username} (Вы){isOwner && ' 👑'}
              </span>
            </div>

            <SettingsPanel settings={room.settings} canEdit={isOwner} onChange={onUpdateSettings} />
          </div>
        </div>

        {/* Chat */}
        <div className="lg:col-span-4 xl:col-span-3 flex flex-col">
          <ChatPanel
            title="Чат комнаты"
            badge={`${players.filter((p) => p.is_connected).length} онлайн`}
            messages={roomState.chat ?? []}
            myId={me.player_id}
            quickReplies={QUICK_REPLIES}
            placeholder="Сообщение в чат..."
            onSend={onSendMessage}
          />
        </div>
      </div>
    </div>
  );
}

function PlayerSeat({ player, isOwner }: { player: RoomPlayer; isOwner: boolean }) {
  return (
    <div
      className={`flex flex-col items-center bg-[#FAF7F2] border-2 border-[#242426] rounded-2xl p-2 sm:px-4 sm:py-2.5 shadow-[3px_3px_0px_#242426] ${
        player.is_connected ? '' : 'opacity-60'
      }`}
    >
      <div className="relative">
        <Avatar id={player.avatar_id} size="md" />
        {isOwner && (
          <span
            title="Владелец комнаты"
            className="absolute -top-2.5 -right-2.5 w-6 h-6 rounded-full bg-[#E4D976] border-2 border-[#242426] flex items-center justify-center shadow-[1px_1px_0px_#242426]"
          >
            <Crown className="w-3.5 h-3.5 text-[#242426]" />
          </span>
        )}
      </div>
      <span className="font-extrabold text-xs sm:text-sm text-[#242426] mt-1 truncate max-w-[110px]">
        {player.username}
      </span>
      {player.is_connected ? (
        <span className="text-[10px] font-bold px-2 py-0.5 rounded-full mt-0.5 bg-[#C8D7C5] border border-[#242426]/30 text-[#2C442A]">
          В СЕТИ
        </span>
      ) : (
        <span className="text-[10px] font-bold px-2 py-0.5 rounded-full mt-0.5 bg-[#E8BAA8] border border-[#242426]/30 text-[#52291E] flex items-center gap-1">
          <WifiOff className="w-3 h-3" /> НЕ В СЕТИ
        </span>
      )}
    </div>
  );
}

interface SettingsPanelProps {
  settings: GameSettings;
  canEdit: boolean;
  onChange: (settings: GameSettings) => void;
}

// The owner changes the settings, everybody else sees them
function SettingsPanel({ settings, canEdit, onChange }: SettingsPanelProps) {
  // The server expects all the settings at once, so send the current ones with one value replaced
  const change = (changes: Partial<GameSettings>) => onChange({ ...settings, ...changes });

  return (
    <div className="w-full sm:w-auto bg-[#FAF7F2] border-2 border-[#242426] rounded-2xl px-4 py-3 shadow-[2px_2px_0px_#242426] text-xs">
      <div className="flex items-center gap-1.5 font-black uppercase tracking-wider text-[#242426] mb-2">
        <Settings className="w-3.5 h-3.5" />
        Настройки игры
      </div>

      <div className="flex flex-col gap-2">
        <div className="flex items-center justify-between gap-3">
          <span className="flex items-center gap-1 font-bold text-[#55524B]">
            <Clock className="w-3.5 h-3.5" /> Время на ход
          </span>
          <div className="flex gap-1">
            {ROUND_TIME_LIMITS.map((seconds) => (
              <button
                key={seconds}
                type="button"
                disabled={!canEdit}
                onClick={() => change({ round_time_limit: seconds })}
                className={`px-2 py-0.5 rounded-lg border font-bold transition-all ${
                  settings.round_time_limit === seconds
                    ? 'bg-[#E4D976] border-[#242426] text-[#242426]'
                    : 'bg-[#ECE8DE] border-[#242426]/30 text-[#55524B]'
                } ${canEdit ? 'cursor-pointer hover:border-[#242426]' : 'cursor-default'}`}
              >
                {seconds}с
              </button>
            ))}
          </div>
        </div>

        <LimitSelect
          label="Раундов"
          icon={<Sparkles className="w-3.5 h-3.5" />}
          value={settings.max_rounds}
          options={MAX_ROUNDS_OPTIONS}
          disabled={!canEdit}
          onChange={(max_rounds) => change({ max_rounds })}
        />
        <LimitSelect
          label="Очков до победы"
          icon={<Trophy className="w-3.5 h-3.5" />}
          value={settings.score_to_win}
          options={SCORE_TO_WIN_OPTIONS}
          disabled={!canEdit}
          onChange={(score_to_win) => change({ score_to_win })}
        />
      </div>
    </div>
  );
}

interface LimitSelectProps {
  label: string;
  icon: ReactNode;
  value: number | null;
  options: (number | null)[];
  disabled: boolean;
  onChange: (value: number | null) => void;
}

// A dropdown for an optional limit; "" in the <select> stands for "no limit" (null)
function LimitSelect({ label, icon, value, options, disabled, onChange }: LimitSelectProps) {
  // The server may hold a value that isn't in our list - still show it
  const values = options.includes(value) ? options : [...options, value];

  return (
    <label className="flex items-center justify-between gap-3">
      <span className="flex items-center gap-1 font-bold text-[#55524B]">
        {icon} {label}
      </span>
      <select
        value={value ?? ''}
        disabled={disabled}
        onChange={(event) => onChange(event.target.value === '' ? null : Number(event.target.value))}
        className="rounded-lg border border-[#242426]/40 bg-[#ECE8DE] px-1.5 py-0.5 font-bold text-[#242426] disabled:opacity-100 disabled:appearance-none"
      >
        {values.map((option) => (
          <option key={option ?? 'none'} value={option ?? ''}>
            {option ?? 'без лимита'}
          </option>
        ))}
      </select>
    </label>
  );
}
