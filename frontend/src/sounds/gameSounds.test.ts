import { describe, expect, it } from 'vitest';
import type { ChatMessage, GameEnded, GameView, RoomState } from '../protocol';
import type { GameData } from '../store/gameStore';
import { soundFor } from './gameSounds';

const ME = 'p1';
const OTHER = 'p2';

const message = (player_id: string, text = 'лол'): ChatMessage => ({
  player_id,
  username: 'Someone',
  text,
  timestamp: '2026-11-18T12:00:00Z',
});

const game = (changes: Partial<GameView> = {}): GameView => ({
  state: 'active',
  round_number: 1,
  round_state: 'choosing_cards',
  leader_id: OTHER,
  situation: { id: 1, text: 'Когда...' },
  my_hand: [],
  my_selected_card_id: null,
  submitted_player_ids: [],
  table: [],
  winner: null,
  ends_at: null,
  ...changes,
});

const room = (gameView: GameView | null, chat: ChatMessage[] = [], roomId = 'r1'): RoomState => ({
  server_time: '2026-11-18T12:00:00Z',
  room: {
    id: roomId,
    name: 'Room',
    owner_id: ME,
    max_players: 10,
    settings: { round_time_limit: 60, max_rounds: null, score_to_win: null },
  },
  players: [],
  game: gameView,
  chat,
});

const data = (changes: Partial<GameData> = {}): GameData => ({
  connection: 'online',
  me: { player_id: ME, reconnect_token: 'token', username: 'Neo', avatar_id: 'cat' },
  rooms: [],
  roomState: room(game()),
  roundWinner: null,
  gameEnded: null,
  syncing: false,
  ...changes,
});

const gameEnded = (winner_ids: string[]): GameEnded => ({
  room_id: 'r1',
  reason: 'limit_reached',
  final_scores: {},
  winner_ids,
});

describe('soundFor', () => {
  it('a new round', () => {
    const next = data({ roomState: room(game({ round_number: 2 })) });

    expect(soundFor(data(), next)).toBe('round_started');
  });

  it('the first round, right after the lobby', () => {
    const next = data({ roomState: room(game()) });

    expect(soundFor(data({ roomState: room(null) }), next)).toBe('round_started');
  });

  it('the leader is called once the memes are on the table', () => {
    const prev = data({ roomState: room(game({ leader_id: ME })) });
    const next = data({ roomState: room(game({ leader_id: ME, round_state: 'leader_choosing' })) });

    expect(soundFor(prev, next)).toBe('judge_now');
  });

  it('the other players are not called to judge', () => {
    const next = data({ roomState: room(game({ round_state: 'leader_choosing' })) });

    expect(soundFor(data(), next)).toBeNull();
  });

  it('a won round sounds different for the winner and the others', () => {
    expect(soundFor(data(), data({ roundWinner: { winner_id: ME, card_id: 1 } }))).toBe('you_won_round');
    expect(soundFor(data(), data({ roundWinner: { winner_id: OTHER, card_id: 1 } }))).toBe('round_won');
  });

  it('the end of the game sounds different for the winner and the others', () => {
    expect(soundFor(data(), data({ gameEnded: gameEnded([ME]) }))).toBe('you_won_game');
    expect(soundFor(data(), data({ gameEnded: gameEnded([OTHER]) }))).toBe('game_over');
  });

  it('the end of the game wins over a chat message that came with it', () => {
    const next = data({ gameEnded: gameEnded([ME]), roomState: room(game(), [message(OTHER)]) });

    expect(soundFor(data(), next)).toBe('you_won_game');
  });

  it('a message from someone else', () => {
    const next = data({ roomState: room(game(), [message(OTHER)]) });

    expect(soundFor(data(), next)).toBe('chat_message');
  });

  it('no sound for my own message', () => {
    const next = data({ roomState: room(game(), [message(ME)]) });

    expect(soundFor(data(), next)).toBeNull();
  });

  it('no sound when nothing new has happened', () => {
    const state = data({ roomState: room(game(), [message(OTHER)]) });

    expect(soundFor(state, { ...state, connection: 'connecting' })).toBeNull();
  });

  it('no sound when joining a room with a game and a chat in it', () => {
    const next = data({ roomState: room(game({ round_number: 3 }), [message(OTHER)], 'r2') });

    expect(soundFor(data({ roomState: null }), next)).toBeNull();
  });

  it('no sound when coming back after a lost connection', () => {
    const prev = data({ syncing: true });
    const next = data({ roomState: room(game({ round_number: 5 }), [message(OTHER)]) });

    expect(soundFor(prev, next)).toBeNull();
  });
});
