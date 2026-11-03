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
