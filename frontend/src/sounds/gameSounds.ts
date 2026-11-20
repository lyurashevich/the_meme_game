// Which sound a change in the game deserves. A pure function, like applyServerMessage:
// "old data + new data -> a sound or nothing", so it is tested without a browser or speakers.
import type { GameData } from '../store/gameStore';

export type SoundName =
  | 'round_started'
  | 'judge_now' // you lead this round and all the memes are on the table
  | 'you_won_round'
  | 'round_won' // someone else won the round
  | 'you_won_game'
  | 'game_over' // someone else won the game
  | 'chat_message';

// One change may fit several sounds (say, the last meme played and a chat message at once):
// the checks go from the most important down, and only the first one found is played.
export function soundFor(prev: GameData, next: GameData): SoundName | null {
  const myId = next.me?.player_id;
  // Coming back after a lost connection: the data jumps to "now", nothing has just happened
  if (!myId || prev.syncing) return null;

  if (next.gameEnded && next.gameEnded !== prev.gameEnded) {
    return next.gameEnded.winner_ids.includes(myId) ? 'you_won_game' : 'game_over';
  }
  if (next.roundWinner && next.roundWinner !== prev.roundWinner) {
    return next.roundWinner.winner_id === myId ? 'you_won_round' : 'round_won';
  }

  // Joining a room brings its whole state at once, with nothing new in it
  const prevRoom = prev.roomState;
  const nextRoom = next.roomState;
  if (!prevRoom || !nextRoom || prevRoom.room.id !== nextRoom.room.id) return null;

  const prevGame = prevRoom.game;
  const nextGame = nextRoom.game;
  if (nextGame) {
    const judgingStarted = nextGame.round_state === 'leader_choosing' && prevGame?.round_state !== 'leader_choosing';
    if (judgingStarted && nextGame.leader_id === myId) return 'judge_now';

    const roundStarted = nextGame.round_number !== null && nextGame.round_number !== prevGame?.round_number;
    if (roundStarted) return 'round_started';
  }

  const lastMessage = nextRoom.chat?.at(-1);
  if (lastMessage && lastMessage !== prevRoom.chat?.at(-1) && lastMessage.player_id !== myId) {
    return 'chat_message';
  }

  return null;
}
