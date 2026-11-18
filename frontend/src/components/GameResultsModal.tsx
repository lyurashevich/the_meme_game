import { Play, Trophy } from 'lucide-react';
import { MIN_PLAYERS_TO_START, type GameEnded, type RoomPlayer } from '../protocol';
import Avatar from './Avatar';
import Confetti from './Confetti';

// A long rain for the game's winner: the window stays until it's closed
const GAME_CONFETTI = { count: 120, spreadSeconds: 2.5 };

const REASONS: Record<GameEnded['reason'], string> = {
  owner_ended: 'Владелец завершил игру',
  limit_reached: 'Достигнут лимит раундов или очков',
  not_enough_players: 'Осталось слишком мало игроков',
  out_of_cards: 'Закончились карты',
};

interface GameResultsModalProps {
  results: GameEnded;
  players: RoomPlayer[]; // for names and avatars; scores are taken from the results
  myId: string;
  isOwner: boolean; // only the owner can start the next game
  onPlayAgain: () => void;
  onClose: () => void;
}

export default function GameResultsModal({
  results,
  players,
  myId,
  isOwner,
  onPlayAgain,
  onClose,
}: GameResultsModalProps) {
  // Object.entries turns { id: score } into [[id, score], ...]; sort by score, best first
  const rows = Object.entries(results.final_scores)
    .map(([playerId, score]) => ({ playerId, score, player: players.find((p) => p.id === playerId) }))
    .sort((a, b) => b.score - a.score);
  const iWon = results.winner_ids.includes(myId);
  // Counted like the server does: everyone in the room, connected or not
  const canPlayAgain = players.length >= MIN_PLAYERS_TO_START;

  return (
    <div className="fixed inset-0 z-50 bg-[#242426]/60 backdrop-blur-sm flex items-center justify-center p-4">
      {iWon && <Confetti {...GAME_CONFETTI} />}
      <div className="w-full max-w-md bg-[#FAF7F2] border-2 border-[#242426] rounded-3xl p-6 shadow-[6px_6px_0px_#242426] motion-safe:animate-pop-in">
        <div className="text-center mb-4">
          {/* inline-block: the trophy turns around its own center, not the middle of the line */}
          <div className={`inline-block text-4xl mb-1 ${iWon ? 'motion-safe:animate-wiggle' : ''}`}>
            {iWon ? '🏆' : '🎬'}
          </div>
          <h3 className="text-xl font-black text-[#242426]">{iWon ? 'ТЫ ПОБЕДИЛ!' : 'ИГРА ОКОНЧЕНА'}</h3>
          <p className="text-xs text-[#66625A] mt-1">{REASONS[results.reason]}</p>
        </div>

        <ol className="flex flex-col gap-2 mb-5">
          {rows.map(({ playerId, score, player }, index) => {
            const isWinner = results.winner_ids.includes(playerId);
            return (
              <li
                key={playerId}
                className={`flex items-center gap-3 rounded-2xl border-2 px-3 py-2 ${
                  isWinner ? 'border-[#242426] bg-[#F3EDC8]' : 'border-[#242426]/20 bg-[#F4F1EA]'
                }`}
              >
                <span className="w-5 text-center text-xs font-black text-[#55524B]">{index + 1}</span>
                {player ? <Avatar id={player.avatar_id} size="sm" /> : <div className="w-10 h-10" />}
                <span className="flex-1 font-extrabold text-sm text-[#242426] truncate">
                  {player?.username ?? 'Игрок ушёл'}
                  {playerId === myId && ' (Вы)'}
                </span>
                <span className="flex items-center gap-1 text-sm font-black text-[#8C6F36]">
                  {isWinner && <Trophy className="w-4 h-4" />}
                  {score}
                </span>
              </li>
            );
          })}
        </ol>

        {isOwner ? (
          <div className="flex flex-col gap-2">
            <button
              type="button"
              onClick={onPlayAgain}
              disabled={!canPlayAgain}
              className="w-full py-2.5 rounded-xl border-2 border-[#242426] bg-[#E4D976] font-black text-sm text-[#242426] shadow-[2px_2px_0px_#242426] hover:bg-[#DDD166] cursor-pointer flex items-center justify-center gap-2 disabled:bg-[#DDD9CE] disabled:text-[#868278] disabled:shadow-none disabled:cursor-not-allowed"
            >
              <Play className="w-4 h-4 fill-current" />
              СЫГРАТЬ ЕЩЁ →
            </button>
            {!canPlayAgain && (
              <p className="text-center text-xs text-[#66625A]">Нужно хотя бы {MIN_PLAYERS_TO_START} игрока</p>
            )}
            <button
              type="button"
              onClick={onClose}
              className="w-full py-2 rounded-xl border-2 border-[#242426] bg-[#FAF7F2] font-bold text-sm text-[#242426] hover:bg-[#ECE8DE] cursor-pointer"
            >
              В лобби
            </button>
          </div>
        ) : (
          <div className="flex flex-col gap-2">
            <p className="text-center text-xs text-[#66625A]">Владелец может начать новую игру</p>
            <button
              type="button"
              onClick={onClose}
              className="w-full py-2.5 rounded-xl border-2 border-[#242426] bg-[#E4D976] font-black text-sm text-[#242426] shadow-[2px_2px_0px_#242426] hover:bg-[#DDD166] cursor-pointer"
            >
              В ЛОББИ →
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
