import { FlaskConical } from 'lucide-react';
import type { RoomState, RoundState } from '../protocol';
import type { MockServer } from '../mock/useMockServer';

const PHASES: { id: RoundState; title: string }[] = [
  { id: 'choosing_cards', title: 'Игроки сдают мемы' },
  { id: 'leader_choosing', title: 'Ведущий выбирает' },
  { id: 'round_ended', title: 'Итог раунда' },
];

interface MockControlsProps {
  myId: string;
  roomState: RoomState;
  mock: MockServer['mock'];
}

// Mockup tool: shows the lobby and the game from different points of view.
// Goes away together with the mock server.
export default function MockControls({ myId, roomState, mock }: MockControlsProps) {
  const game = roomState.game;
  const chip = (isActive: boolean) =>
    `px-2.5 py-1 rounded-lg border text-[11px] font-bold cursor-pointer transition-colors ${
      isActive ? 'bg-[#242426] text-[#FAF7F2] border-[#242426]' : 'bg-[#FAF7F2] text-[#4E4A42] border-[#242426]/30'
    }`;

  return (
    <div className="border-b border-dashed border-[#242426]/30 bg-[#F0ECE2] px-4 py-2">
      <div className="max-w-7xl mx-auto flex flex-wrap items-center gap-2 text-xs">
        <span className="flex items-center gap-1 font-black text-[#55524B] mr-1">
          <FlaskConical className="w-3.5 h-3.5" /> МАКЕТ:
        </span>

        {game ? (
          <>
            {PHASES.map((phase) => (
              <button
                key={phase.id}
                className={chip(game.round_state === phase.id)}
                onClick={() => mock.showGame(phase.id, game.leader_id === myId)}
              >
                {phase.title}
              </button>
            ))}
            <span className="mx-1 text-[#242426]/30">|</span>
            <button
              className={chip(game.leader_id !== myId)}
              onClick={() => mock.showGame(game.round_state ?? 'choosing_cards', false)}
            >
              Я игрок
            </button>
            <button
              className={chip(game.leader_id === myId)}
              onClick={() => mock.showGame(game.round_state ?? 'choosing_cards', true)}
            >
              Я ведущий
            </button>
          </>
        ) : (
          <>
            <button className={chip(roomState.room.owner_id === myId)} onClick={() => mock.showLobby(true)}>
              Я владелец
            </button>
            <button className={chip(roomState.room.owner_id !== myId)} onClick={() => mock.showLobby(false)}>
              Я гость
            </button>
          </>
        )}
      </div>
    </div>
  );
}
