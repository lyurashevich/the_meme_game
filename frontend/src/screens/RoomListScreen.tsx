import { ArrowRight, Clock, Flame, Plus, RefreshCw, Search, Sparkles, Users } from 'lucide-react';
import { useState, type FormEvent } from 'react';
import Avatar from '../components/Avatar';
import type { RoomSummary, Session } from '../protocol';

const MIN_PLAYERS = 3; // the server's limits for max_players
const MAX_PLAYERS = 10;
const MAX_ROOM_NAME_LENGTH = 64;

interface RoomListScreenProps {
  me: Session;
  rooms: RoomSummary[];
  onJoinRoom: (roomId: string) => void;
  onCreateRoom: (options: { name?: string; max_players: number }) => void;
  onEditProfile: () => void;
}

export default function RoomListScreen({ me, rooms, onJoinRoom, onCreateRoom, onEditProfile }: RoomListScreenProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);

  // Filtering is cheap, so the visible list is simply recomputed on every render
  const query = searchTerm.trim().toLowerCase();
  const visibleRooms = rooms.filter(
    (room) => room.name.toLowerCase().includes(query) || (room.owner_name ?? '').toLowerCase().includes(query),
  );

  return (
    <div className="max-w-7xl mx-auto px-4 py-6 sm:px-6 sm:py-8">
      {/* Title and profile */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl sm:text-3xl font-black tracking-tight text-[#242426]">ВЫБОР КОМНАТЫ</h1>
            <span className="bg-[#E4D976] border-2 border-[#242426] px-2.5 py-0.5 rounded-full text-xs font-bold text-[#242426] shadow-[2px_2px_0px_#242426]">
              ЭКРАН 2
            </span>
          </div>
          <p className="text-sm text-[#666259] font-medium mt-1">
            Выбери подходящую тусовку или создай свою комнату с блэкджеком и котами
          </p>
        </div>

        <div className="flex items-center gap-3 bg-[#FAF7F2] border-2 border-[#242426] p-2 pr-4 rounded-2xl shadow-[3px_3px_0px_#242426] self-start md:self-auto">
          <Avatar id={me.avatar_id} size="sm" />
          <div>
            <div className="flex items-center gap-1.5">
              <span className="font-extrabold text-sm text-[#242426]">{me.username}</span>
              <span className="text-[10px] bg-[#EAE5D9] px-1.5 py-0.5 rounded text-[#57534A] font-bold">В сети</span>
            </div>
            <p className="text-[11px] text-[#78746B]">Готов деградировать</p>
          </div>
          <button
            onClick={onEditProfile}
            title="Изменить аватар или ник"
            className="ml-1 text-xs font-bold text-[#555148] hover:text-[#242426] underline cursor-pointer"
          >
            Изменить
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left column: create a room, tip */}
        <div className="lg:col-span-4 flex flex-col gap-5">
          <div className="rounded-3xl border-2 border-[#242426] bg-[#FAF7F2] p-5 shadow-[4px_4px_0px_#242426]">
            <div className="flex items-center gap-2 mb-2">
              <Sparkles className="w-5 h-5 text-[#242426]" />
              <h2 className="font-extrabold text-base text-[#242426]">Своя компания?</h2>
            </div>
            <p className="text-xs text-[#66625A] mb-4">
              Создай комнату, настрой время на ход и число раундов, и зови друзей.
            </p>
            <button
              type="button"
              id="create-room-button"
              onClick={() => setShowCreateModal(true)}
              className="w-full rounded-2xl border-2 border-[#242426] bg-[#E4D976] hover:bg-[#DDD166] active:translate-y-0.5 p-3.5 font-black text-sm text-[#242426] shadow-[3px_3px_0px_#242426] flex items-center justify-center gap-2 cursor-pointer transition-all"
            >
              <Plus className="w-5 h-5 stroke-[2.5]" />
              <span>СОЗДАТЬ КОМНАТУ</span>
            </button>
          </div>

          <div className="text-xs text-[#5D5950] bg-[#F2EEE4] p-4 rounded-2xl border-2 border-[#242426]/20">
            <p className="font-bold text-[#242426] mb-0.5">💡 Мемный этикет:</p>
            <p className="italic text-[11px]">«Если шутка не зашла, сделай вид, что это был сарказм над зумерами».</p>
          </div>
        </div>

        {/* Right column: search and rooms */}
        <div className="lg:col-span-8 flex flex-col gap-4">
          <div className="flex items-center gap-3">
            <div className="relative flex-1">
              <Search className="w-4 h-4 text-[#7A766D] absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
              <input
                type="text"
                value={searchTerm}
                onChange={(event) => setSearchTerm(event.target.value)}
                placeholder="Поиск по названию или владельцу..."
                className="w-full rounded-2xl border-2 border-[#242426] bg-[#FAF7F2] pl-10 pr-4 py-2.5 text-sm font-semibold text-[#242426] placeholder-[#9B958A] focus:outline-none focus:ring-2 focus:ring-[#242426] shadow-[2px_2px_0px_#242426]"
              />
            </div>
            <button
              onClick={() => setSearchTerm('')}
              title="Сбросить поиск"
              className="p-2.5 rounded-2xl border-2 border-[#242426] bg-[#FAF7F2] hover:bg-[#EAE5D9] shadow-[2px_2px_0px_#242426] text-[#242426] cursor-pointer"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>

          <p className="text-[11px] text-[#7A766D] font-medium px-1">Комнат: {visibleRooms.length}</p>

          {visibleRooms.length === 0 ? (
            <div className="rounded-3xl border-2 border-dashed border-[#242426]/40 p-10 text-center bg-[#FAF7F2]/60">
              <p className="font-bold text-base text-[#4E4B43]">Комнаты не найдены :(</p>
              <p className="text-xs text-[#7A766E] mt-1 mb-4">
                Попробуйте изменить поисковый запрос или создайте свою!
              </p>
              <button
                onClick={() => setShowCreateModal(true)}
                className="px-4 py-2 rounded-xl border-2 border-[#242426] bg-[#E4D976] text-xs font-black shadow-[2px_2px_0px_#242426] cursor-pointer"
              >
                Создать новую
              </button>
            </div>
          ) : (
            visibleRooms.map((room) => <RoomRow key={room.id} room={room} onJoin={() => onJoinRoom(room.id)} />)
          )}
        </div>
      </div>

      {/* The modal is in the page only while it's open, so its form starts fresh every time */}
      {showCreateModal && (
        <CreateRoomModal
          defaultName={`Комната ${me.username}`}
          onCancel={() => setShowCreateModal(false)}
          onCreate={(options) => {
            setShowCreateModal(false);
            onCreateRoom(options);
          }}
        />
      )}
    </div>
  );
}

function RoomRow({ room, onJoin }: { room: RoomSummary; onJoin: () => void }) {
  const isFull = room.players_count >= room.max_players;
  const isPlaying = room.status === 'playing';
  const canJoin = !isFull && !isPlaying; // the server refuses both
  const oneSeatLeft = canJoin && room.players_count === room.max_players - 1;

  return (
    <div className="group rounded-3xl border-2 border-[#242426] bg-[#FAF7F2] p-4 sm:p-5 shadow-[4px_4px_0px_#242426] hover:shadow-[5px_5px_0px_#242426] transition-all flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
      <div className="flex-1">
        <div className="flex items-center gap-2 flex-wrap mb-1.5">
          <span className="font-extrabold text-base text-[#242426] group-hover:text-[#5A5128] transition-colors">
            {room.name}
          </span>
          {oneSeatLeft && (
            <span className="text-[10px] font-black px-2 py-0.5 rounded-full bg-[#E8BAA8] text-[#52291E] border border-[#242426]/30 flex items-center gap-1">
              <Flame className="w-3 h-3" />
              Осталось 1 место!
            </span>
          )}
          {isPlaying && (
            <span className="text-[10px] font-black px-2 py-0.5 rounded-full bg-[#DDD9CE] text-[#55524B] border border-[#242426]/30">
              Идёт игра
            </span>
          )}
        </div>

        <div className="flex items-center gap-4 text-xs text-[#636058] font-medium flex-wrap">
          <span className="flex items-center gap-1">
            <span className="text-[#88847A]">Владелец:</span>
            <strong className="text-[#242426]">{room.owner_name ?? '—'}</strong>
          </span>
          <span className="flex items-center gap-1">
            <Clock className="w-3.5 h-3.5 text-[#88847A]" />
            <span>{room.round_time_limit} сек/ход</span>
          </span>
          <span>• {room.max_rounds === null ? 'без лимита раундов' : `${room.max_rounds} раундов`}</span>
        </div>
      </div>

      <div className="flex items-center gap-3 w-full sm:w-auto justify-between sm:justify-end pt-2 sm:pt-0 border-t sm:border-t-0 border-[#242426]/10">
        <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-[#242426]/30 bg-[#ECE8DE]">
          <Users className="w-4 h-4 text-[#44413A]" />
          <span className="text-xs font-black text-[#242426]">{room.players_count}</span>
          <span className="text-xs text-[#6D695F]">/ {room.max_players}</span>
        </div>

        <button
          type="button"
          disabled={!canJoin}
          onClick={onJoin}
          className={`px-4 py-2 rounded-xl border-2 border-[#242426] text-xs font-black transition-all flex items-center gap-1.5 ${
            canJoin
              ? 'bg-[#C8D7C5] hover:bg-[#B5C8B1] active:translate-y-0.5 text-[#242426] shadow-[3px_3px_0px_#242426] cursor-pointer'
              : 'bg-[#DDD9CE] text-[#868278] cursor-not-allowed'
          }`}
        >
          <span>{isPlaying ? 'Уже играют' : isFull ? 'Заполнено' : 'Залететь'}</span>
          {canJoin && <ArrowRight className="w-3.5 h-3.5" />}
        </button>
      </div>
    </div>
  );
}

interface CreateRoomModalProps {
  defaultName: string;
  onCancel: () => void;
  onCreate: (options: { name?: string; max_players: number }) => void;
}

function CreateRoomModal({ defaultName, onCancel, onCreate }: CreateRoomModalProps) {
  const [name, setName] = useState(defaultName);
  const [maxPlayers, setMaxPlayers] = useState(6);

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    // An empty name is fine: the server makes one up
    onCreate({ name: name.trim() || undefined, max_players: maxPlayers });
  };

  // [3, 4, ..., 10]
  const playerOptions = Array.from({ length: MAX_PLAYERS - MIN_PLAYERS + 1 }, (_, i) => MIN_PLAYERS + i);

  return (
    <div className="fixed inset-0 z-50 bg-[#242426]/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="w-full max-w-md bg-[#FAF7F2] border-2 border-[#242426] rounded-3xl p-6 shadow-[6px_6px_0px_#242426]">
        <h3 className="text-xl font-black text-[#242426] mb-1">Создать новую комнату</h3>
        <p className="text-xs text-[#66625A] mb-4">Время на ход и число раундов настроишь в лобби</p>

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div>
            <label
              htmlFor="room-name-input"
              className="text-xs font-bold text-[#44413A] uppercase tracking-wide block mb-1"
            >
              Название комнаты:
            </label>
            <input
              id="room-name-input"
              type="text"
              maxLength={MAX_ROOM_NAME_LENGTH}
              value={name}
              onChange={(event) => setName(event.target.value)}
              className="w-full rounded-xl border-2 border-[#242426] bg-[#F5F2EA] px-3.5 py-2 text-sm font-bold text-[#242426] focus:outline-none focus:bg-[#FAF7F2]"
            />
          </div>

          <div>
            <label htmlFor="max-players-select" className="text-xs font-bold text-[#44413A] block mb-1">
              Макс. игроков:
            </label>
            <select
              id="max-players-select"
              value={maxPlayers}
              // A <select> always gives a string; turn it back into a number
              onChange={(event) => setMaxPlayers(Number(event.target.value))}
              className="w-full rounded-xl border-2 border-[#242426] bg-[#F5F2EA] px-3 py-2 text-sm font-bold text-[#242426]"
            >
              {playerOptions.map((count) => (
                <option key={count} value={count}>
                  {count} {count < 5 ? 'игрока' : 'игроков'}
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-center gap-3 mt-4 pt-3 border-t border-[#242426]/15">
            <button
              type="button"
              onClick={onCancel}
              className="flex-1 py-2.5 rounded-xl border-2 border-[#242426] bg-[#ECE8DE] font-bold text-xs text-[#44413A] hover:bg-[#E2DDD2] cursor-pointer"
            >
              Отмена
            </button>
            <button
              type="submit"
              className="flex-1 py-2.5 rounded-xl border-2 border-[#242426] bg-[#E4D976] font-black text-xs text-[#242426] shadow-[2px_2px_0px_#242426] hover:bg-[#DDD166] cursor-pointer"
            >
              Создать и войти →
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
