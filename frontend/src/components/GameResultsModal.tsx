import { Trophy } from 'lucide-react';
import type { GameEnded, RoomPlayer } from '../protocol';
import Avatar from './Avatar';

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
  onClose: () => void;
}

export default function GameResultsModal({ results, players, myId, onClose }: GameResultsModalProps) {
  // Object.entries turns { id: score } into [[id, score], ...]; sort by score, best first
  const rows = Object.entries(results.final_scores)
    .map(([playerId, score]) => ({ playerId, score, player: players.find((p) => p.id === playerId) }))
    .sort((a, b) => b.score - a.score);
  const iWon = results.winner_ids.includes(myId);

  return (
    <div className="fixed inset-0 z-50 bg-[#242426]/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="w-full max-w-md bg-[#FAF7F2] border-2 border-[#242426] rounded-3xl p-6 shadow-[6px_6px_0px_#242426]">
        <div className="text-center mb-4">
          <div className="text-4xl mb-1">{iWon ? '🏆' : '🎬'}</div>
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

        <button
          type="button"
          onClick={onClose}
          className="w-full py-2.5 rounded-xl border-2 border-[#242426] bg-[#E4D976] font-black text-sm text-[#242426] shadow-[2px_2px_0px_#242426] hover:bg-[#DDD166] cursor-pointer"
        >
          В ЛОББИ →
        </button>
      </div>
    </div>
  );
}
