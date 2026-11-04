// Shapes of the data the server sends (see "WS-протокол" in docs/mvp-plan.md).
// Field names are kept exactly as on the wire, so a message can be used as is.

export type RoundTimeLimit = 60 | 90 | 120;

export const ROUND_TIME_LIMITS: RoundTimeLimit[] = [60, 90, 120];

// `session` event: who this browser tab is
export interface Session {
  player_id: string;
  reconnect_token: string;
  username: string;
  avatar_id: string;
}

// One entry of the `rooms_list` event
export interface RoomSummary {
  id: string;
  name: string;
  owner_name: string | null;
  players_count: number;
  max_players: number;
  round_time_limit: RoundTimeLimit;
  max_rounds: number | null; // null: no limit
  status: 'waiting' | 'playing';
}

export interface GameSettings {
  round_time_limit: RoundTimeLimit;
  max_rounds: number | null;
  score_to_win: number | null;
}

export interface RoomPlayer {
  id: string;
  username: string;
  avatar_id: string;
  score: number;
  is_connected: boolean;
}

export interface MemeCard {
  id: number;
  image_url: string;
}

export interface Situation {
  id: number;
  text: string;
}

export type RoundState = 'choosing_cards' | 'leader_choosing' | 'round_ended';

export interface GameView {
  state: 'starting' | 'active';
  round_number: number | null;
  round_state: RoundState | null;
  leader_id: string | null;
  situation: Situation | null;
  my_hand: MemeCard[];
  my_selected_card_id: number | null;
  submitted_player_ids: string[];
  table: MemeCard[]; // anonymous; filled from the leader_choosing phase on
  winner: { player_id: string; card_id: number | null } | null;
  ends_at: string | null; // ISO deadline of the current phase
}

export interface ChatMessage {
  player_id: string;
  username: string;
  text: string;
  timestamp: string; // ISO
}

// `room_state` event: everything this player may see about their room
export interface RoomState {
  server_time: string; // ISO
  room: {
    id: string;
    name: string;
    owner_id: string | null;
    max_players: number;
    settings: GameSettings;
  };
  players: RoomPlayer[];
  game: GameView | null; // null: lobby
  chat?: ChatMessage[]; // only right after joining or reconnecting
}

// One-off events that a snapshot can't express
export interface RoundWinner {
  winner_id: string;
  card_id: number | null;
}

export interface GameEnded {
  room_id: string;
  reason: 'owner_ended' | 'limit_reached' | 'not_enough_players' | 'out_of_cards';
  final_scores: Record<string, number>; // player id -> score
  winner_ids: string[];
}

export interface ErrorPayload {
  code: string;
  message: string;
  details?: unknown[];
}

// Everything the server can send. `event` tells which one it is, and TypeScript
// narrows `payload` accordingly: after `if (message.event === 'session')` it knows it's a Session.
export type ServerMessage =
  | { event: 'session'; payload: Session }
  | { event: 'rooms_list'; payload: RoomSummary[] }
  | { event: 'room_state'; payload: RoomState }
  | { event: 'round_winner'; payload: RoundWinner }
  | { event: 'game_ended'; payload: GameEnded }
  | { event: 'chat_message'; payload: ChatMessage }
  | { event: 'you_left_room'; payload: { room_id: string } }
  | { event: 'ack'; request_id: string | null; payload: unknown }
  | { event: 'error'; request_id: string | null; payload: ErrorPayload };

type Empty = Record<string, never>;

// Client actions: what each one takes and what its ack carries
export interface Actions {
  update_profile: {
    payload: { username?: string; avatar_id?: string };
    result: { username: string; avatar_id: string };
  };
  create_room: { payload: { name?: string; max_players?: number }; result: { room_id: string } };
  join_room: { payload: { room_id: string }; result: { room_id: string } };
  leave_room: { payload: { confirm?: boolean }; result: { requires_confirmation: boolean } };
  update_settings: { payload: GameSettings; result: GameSettings };
  start_game: { payload: Empty; result: Empty };
  end_game: { payload: Empty; result: Empty };
  select_card: { payload: { card_id: number }; result: Empty };
  choose_winner: { payload: { card_id: number }; result: Empty };
  chat_message: { payload: { text: string }; result: Empty };
}

export type ActionName = keyof Actions;
