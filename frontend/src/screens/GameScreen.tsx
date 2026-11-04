import { ArrowUpCircle, CheckCircle, Crown, Flag, Hourglass, LogOut, Sparkles, Trophy, WifiOff } from 'lucide-react';
import { useState } from 'react';
import Avatar from '../components/Avatar';
import ChatPanel from '../components/ChatPanel';
import MemeCard from '../components/MemeCard';
import RoundTimer from '../components/RoundTimer';
import type { GameView, RoomPlayer, RoomState, Session } from '../protocol';

const QUICK_REPLIES = ['💀 Ору', '🗿 База', '🤡 Кринж', '🔥 В яблочко', '📉'];
const ROTATIONS = ['-rotate-2', 'rotate-1', '-rotate-1', 'rotate-2'];

interface GameScreenProps {
  me: Session;
  roomState: RoomState;
  game: GameView;
  onSelectCard: (cardId: number) => void;
  onChooseWinner: (cardId: number) => void;
  onSendMessage: (text: string) => void;
  onLeaveRoom: () => void;
  onEndGame: () => void;
}

export default function GameScreen({
  me,
  roomState,
  game,
  onSelectCard,
  onChooseWinner,
  onSendMessage,
  onLeaveRoom,
  onEndGame,
}: GameScreenProps) {
  // Only what the player has clicked but not sent yet lives here; everything else comes from the server
  const [pickedHandCardId, setPickedHandCardId] = useState<number | null>(null);
  const [pickedTableCardId, setPickedTableCardId] = useState<number | null>(null);

  const { room, players } = roomState;
  const phase = game.round_state;
  const iAmOwner = room.owner_id === me.player_id;
  const iAmLeader = game.leader_id === me.player_id;
  const iHavePlayed = game.submitted_player_ids.includes(me.player_id);
  const canPlayCard = phase === 'choosing_cards' && !iAmLeader && !iHavePlayed;
  // The winner is shown while the phase is still leader_choosing: `winner` is set and the timer stops
  const canChooseWinner = phase === 'leader_choosing' && iAmLeader && !game.winner;

  // A pick only counts while the card is still there: the hand and the table change with every snapshot
  const pickedHandCard = canPlayCard ? game.my_hand.find((card) => card.id === pickedHandCardId) : undefined;
  const pickedTableCard = canChooseWinner ? game.table.find((card) => card.id === pickedTableCardId) : undefined;

  const nameOf = (playerId: string | null | undefined) => players.find((p) => p.id === playerId)?.username ?? '???';

  return (
    <div className="max-w-[1920px] mx-auto px-3 sm:px-6 lg:px-10 xl:px-16 2xl:px-24 py-3 flex flex-col gap-3 lg:h-[calc(100dvh-3.5rem)]">
      {/* HUD */}
      <div className="shrink-0 rounded-2xl border-2 border-[#242426] bg-[#FAF7F2] px-4 py-2 shadow-[3px_3px_0px_#242426] flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2.5">
          <button
            onClick={onLeaveRoom}
            title="Выйти из игры"
            className="p-1.5 rounded-xl border border-[#242426]/30 hover:bg-[#ECE8DE] text-[#242426] transition-colors cursor-pointer"
          >
            <LogOut className="w-4 h-4" />
          </button>
          <span className="font-black text-base sm:text-lg text-[#242426] tracking-tight">
            РАУНД {game.round_number ?? '—'}
            {room.settings.max_rounds !== null && ` ИЗ ${room.settings.max_rounds}`}
          </span>
          {iAmOwner && (
            <button
              onClick={onEndGame}
              title="Завершить игру для всех"
              className="flex items-center gap-1 text-[11px] font-bold text-[#6D6960] hover:text-[#242426] underline cursor-pointer"
            >
              <Flag className="w-3 h-3" /> Завершить
            </button>
          )}
        </div>

        <StatusBanner game={game} iAmLeader={iAmLeader} iHavePlayed={iHavePlayed} nameOf={nameOf} />

        {game.ends_at && <RoundTimer endsAt={game.ends_at} serverTime={roomState.server_time} />}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-3 lg:flex-1 lg:min-h-0">
        {/* Table */}
        <div className="lg:col-span-9 2xl:col-span-10 flex flex-col gap-3 lg:min-h-0 rounded-3xl border-2 border-[#242426] bg-[#DDD7C7] p-3 sm:p-4 shadow-[4px_4px_0px_#242426] relative overflow-hidden">
          <div className="absolute inset-2 rounded-2xl border-2 border-dashed border-[#242426]/20 pointer-events-none" />

          {/* Players with scores and what they are doing */}
          <div className="relative z-10 shrink-0 flex items-center justify-center gap-2 flex-wrap">
            {players.map((player) => (
              <PlayerBadge
                key={player.id}
                player={player}
                isMe={player.id === me.player_id}
                isLeader={player.id === game.leader_id}
                hasPlayed={game.submitted_player_ids.includes(player.id)}
              />
            ))}
          </div>

          {/* Situation */}
          <div className="relative z-10 shrink-0 self-center w-full max-w-3xl rounded-2xl border-3 border-[#242426] bg-[#FAF7F2] px-5 py-3 shadow-[4px_4px_0px_#242426]">
            <p className="text-base sm:text-xl font-black leading-snug text-[#242426] text-center">
              {game.situation ? `«${game.situation.text}»` : 'Игра начинается...'}
            </p>
            <div className="mt-2 pt-1.5 border-t border-[#242426]/10 flex items-center justify-between text-[11px] text-[#716D64]">
              <span>
                Сдано мемов: {game.submitted_player_ids.length} из {players.length - 1}
              </span>
              <span className="font-bold text-[#242426]">Ведущий: {nameOf(game.leader_id)} 👑</span>
            </div>
          </div>

          {/* Cards on the table: as tall as the space left; many of them scroll sideways */}
          <div className="relative z-10 flex-1 min-h-44 lg:min-h-0 flex gap-3 sm:gap-4 justify-center-safe items-center overflow-x-auto px-2 py-2">
            {phase === 'choosing_cards'
              ? // Only who has played is known so far, not what: show the backs
                game.submitted_player_ids.map((playerId, index) => (
                  <MemeCard key={playerId} size="fill" className={ROTATIONS[index % ROTATIONS.length]} />
                ))
              : game.table.map((card, index) => {
                  const isWinner = game.winner?.card_id === card.id;
                  return (
                    <MemeCard
                      key={card.id}
                      card={card}
                      size="fill"
                      className={ROTATIONS[index % ROTATIONS.length]}
                      isSelected={card.id === pickedTableCard?.id}
                      isWinner={isWinner}
                      caption={
                        isWinner
                          ? `от ${nameOf(game.winner?.player_id)}`
                          : card.id === game.my_selected_card_id
                            ? 'твой мем'
                            : undefined
                      }
                      onClick={canChooseWinner ? () => setPickedTableCardId(card.id) : undefined}
                    />
                  );
                })}
            {phase === 'choosing_cards' && game.submitted_player_ids.length === 0 && (
              <p className="text-xs font-bold text-[#69655C]">Пока никто не сдал мем</p>
            )}
          </div>

          {pickedTableCard && (
            <div className="absolute z-20 bottom-4 inset-x-0 flex justify-center pointer-events-none">
              <button
                type="button"
                onClick={() => onChooseWinner(pickedTableCard.id)}
                className="pointer-events-auto px-4 py-2 rounded-xl border-2 border-[#242426] bg-[#E4D976] hover:bg-[#DDD166] font-black text-xs text-[#242426] shadow-[2px_2px_0px_#242426] flex items-center gap-1.5 cursor-pointer active:translate-y-0.5"
              >
                <Trophy className="w-3.5 h-3.5" />
                ЭТОТ МЕМ ПОБЕЖДАЕТ
              </button>
            </div>
          )}
        </div>

        {/* Chat: takes the height of the table, a long chat scrolls inside */}
        <div className="lg:col-span-3 2xl:col-span-2 relative h-[380px] lg:h-auto">
          <div className="absolute inset-0">
            <ChatPanel
              title="Чат игры"
              badge="Живое обсуждение"
              messages={roomState.chat ?? []}
              myId={me.player_id}
              quickReplies={QUICK_REPLIES}
              placeholder="Написать реакцию..."
              onSend={onSendMessage}
            />
          </div>
        </div>
      </div>

      {/* Hand: over a third of the window on a big screen */}
      <div className="shrink-0 lg:h-[38%] flex flex-col rounded-3xl border-2 border-[#242426] bg-[#FAF7F2] px-4 pt-2.5 pb-3 shadow-[4px_4px_0px_#242426]">
        <div className="shrink-0 flex flex-wrap items-center justify-between gap-2 px-1 min-h-8">
          <div className="flex items-center gap-2">
            <span className="font-black text-xs uppercase tracking-wider text-[#242426]">Твоя рука</span>
            <span className="text-[11px] bg-[#EAE5D9] px-2 py-0.5 rounded-full font-bold text-[#555148]">
              {game.my_hand.length} карт
            </span>
            <span className="text-[10px] text-[#706B62] font-semibold hidden md:inline">
              {canPlayCard ? '(Выбери мем и нажми «Сыграть»)' : iAmLeader ? '(Ведущий в этом раунде не играет)' : ''}
            </span>
          </div>

          {pickedHandCard && (
            <button
              type="button"
              onClick={() => onSelectCard(pickedHandCard.id)}
              className="px-3.5 py-1.5 rounded-xl border-2 border-[#242426] bg-[#E4D976] hover:bg-[#DDD166] font-black text-xs text-[#242426] shadow-[2px_2px_0px_#242426] flex items-center gap-1 cursor-pointer transition-all active:translate-y-0.5"
            >
              <ArrowUpCircle className="w-3.5 h-3.5" />
              <span>СЫГРАТЬ ЭТОТ МЕМ</span>
            </button>
          )}
        </div>

        {/* pt-4: room for the picked card, which rises a little. justify-center-safe: centered, but
            when the cards don't fit they start at the left edge, so none is cut off unreachable */}
        <div className="flex-1 min-h-0 flex items-stretch justify-center-safe gap-4 overflow-x-auto pt-4 pb-1 px-1">
          {game.my_hand.map((card, index) => (
            <MemeCard
              key={card.id}
              card={card}
              size="fill"
              className={`${ROTATIONS[index % ROTATIONS.length]} ${canPlayCard ? '' : 'opacity-70'}`}
              isSelected={card.id === pickedHandCard?.id}
              onClick={canPlayCard ? () => setPickedHandCardId(card.id) : undefined}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

interface StatusBannerProps {
  game: GameView;
  iAmLeader: boolean;
  iHavePlayed: boolean;
  nameOf: (playerId: string | null | undefined) => string;
}

// One line that tells the player what is going on and what to do
function StatusBanner({ game, iAmLeader, iHavePlayed, nameOf }: StatusBannerProps) {
  let icon = <Sparkles className="w-4 h-4" />;
  let text: string;
  let pulse = false;

  if (game.winner) {
    icon = <Trophy className="w-4 h-4" />;
    text = `Раунд забирает ${nameOf(game.winner.player_id)}!`;
  } else if (game.round_state === 'choosing_cards') {
    if (iAmLeader) {
      icon = <Hourglass className="w-4 h-4" />;
      text = 'ТЫ ВЕДУЩИЙ: ждём, пока все сдадут мемы';
    } else if (iHavePlayed) {
      icon = <CheckCircle className="w-4 h-4" />;
      text = 'ТВОЙ МЕМ СДАН! Ждём остальных';
    } else {
      text = 'ТВОЙ ХОД: выбери мем из руки внизу!';
      pulse = true;
    }
  } else if (game.round_state === 'leader_choosing') {
    text = iAmLeader ? 'ВЫБЕРИ ЛУЧШИЙ МЕМ НА СТОЛЕ!' : `${nameOf(game.leader_id)} выбирает лучший мем`;
    pulse = iAmLeader;
  } else if (game.round_state === 'round_ended') {
    text = 'Раунд без победителя';
  } else {
    text = 'Раздаём карты...';
  }

  return (
    <div
      className={`flex items-center gap-1.5 bg-[#E4D976] border-2 border-[#242426] px-3.5 py-1 rounded-xl shadow-[2px_2px_0px_#242426] text-xs font-black text-[#242426] ${
        pulse ? 'animate-pulse' : ''
      }`}
    >
      {icon}
      <span>{text}</span>
    </div>
  );
}

interface PlayerBadgeProps {
  player: RoomPlayer;
  isMe: boolean;
  isLeader: boolean;
  hasPlayed: boolean;
}

function PlayerBadge({ player, isMe, isLeader, hasPlayed }: PlayerBadgeProps) {
  return (
    <div
      className={`flex items-center gap-2 bg-[#FAF7F2] border-2 border-[#242426] rounded-2xl p-1.5 sm:px-3 sm:py-2 shadow-[2px_2px_0px_#242426] ${
        isMe ? 'ring-2 ring-[#E4D976]' : ''
      } ${player.is_connected ? '' : 'opacity-60'}`}
    >
      <div className="relative">
        <Avatar id={player.avatar_id} size="sm" />
        {isLeader && (
          <span
            title="Ведущий раунда"
            className="absolute -top-1.5 -right-1.5 w-4 h-4 rounded-full bg-[#E4D976] border border-[#242426] flex items-center justify-center"
          >
            <Crown className="w-2.5 h-2.5 text-[#242426]" />
          </span>
        )}
      </div>

      <div className="text-left">
        <div className="flex items-center gap-1">
          <span className="font-extrabold text-xs text-[#242426] truncate max-w-[85px] sm:max-w-[110px]">
            {player.username}
          </span>
          <span className="text-[10px] font-bold text-[#8C6F36]">🏆 {player.score}</span>
        </div>
        <div className="text-[9px] sm:text-[10px] font-bold flex items-center gap-1">
          {!player.is_connected ? (
            <span className="text-[#885A2B] flex items-center gap-0.5">
              <WifiOff className="w-2.5 h-2.5" /> Не в сети
            </span>
          ) : isLeader ? (
            <span className="text-[#8C6F36]">Судит раунд</span>
          ) : hasPlayed ? (
            <span className="text-[#2E5429]">Сдал мем ✓</span>
          ) : (
            <span className="text-[#885A2B] flex items-center gap-0.5">
              <Hourglass className="w-2.5 h-2.5 animate-spin" /> Думает...
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
