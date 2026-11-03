// What the app knows about the game, kept outside of React components:
// the socket fills it with what the server sends, the screens read it and call the actions.
import { create } from 'zustand';
import { GameSocket, type ConnectionStatus } from '../api/GameSocket';
import { createTokenStorage, type TokenStorage } from '../api/tokenStorage';
import type {
  Actions,
  GameEnded,
  GameSettings,
  RoomState,
  RoomSummary,
  RoundWinner,
  ServerMessage,
  Session,
} from '../protocol';

const CHAT_LIMIT = 100;

export interface GameData {
  connection: ConnectionStatus;
  me: Session | null;
  rooms: RoomSummary[];
  roomState: RoomState | null; // null: not in a room
  roundWinner: RoundWinner | null; // the latest one, for the animation
  gameEnded: GameEnded | null; // results of the last game, until the player closes them
  // From `session` until the server says where we are (room_state or rooms_list).
  // Lets a reconnect drop a room that was removed while we were away.
  syncing: boolean;
}

const INITIAL_DATA: GameData = {
  connection: 'offline',
  me: null,
  rooms: [],
  roomState: null,
  roundWinner: null,
  gameEnded: null,
  syncing: false,
};

// How a server message changes the data. A pure function: no socket, no storage,
// just "old data + message -> what changes". That makes it easy to test.
export function applyServerMessage(data: GameData, message: ServerMessage): Partial<GameData> {
  switch (message.event) {
    case 'session':
      // A different player id means the old session expired and the server made a new player
      return message.payload.player_id === data.me?.player_id
        ? { me: message.payload, syncing: true }
        : { ...INITIAL_DATA, connection: data.connection, me: message.payload, syncing: true };
    case 'rooms_list':
      // Right after connecting, the list (instead of a room) means we aren't in a room any more
      return data.syncing ? { rooms: message.payload, roomState: null, syncing: false } : { rooms: message.payload };
    case 'room_state': {
      // The history comes only with the first snapshot; later snapshots keep the chat we have
      const sameRoom = data.roomState?.room.id === message.payload.room.id;
      const chat = message.payload.chat ?? (sameRoom ? data.roomState?.chat : undefined) ?? [];
      return { roomState: { ...message.payload, chat }, syncing: false };
    }
    case 'chat_message': {
      if (!data.roomState) return {};
      const chat = [...(data.roomState.chat ?? []), message.payload].slice(-CHAT_LIMIT);
      return { roomState: { ...data.roomState, chat } };
    }
    case 'round_winner':
      return { roundWinner: message.payload };
    case 'game_ended':
      return { gameEnded: message.payload };
    case 'you_left_room':
      // Results are about the room just left; coming back later must not bring them up again
      return { roomState: null, roundWinner: null, gameEnded: null };
    default:
      return {};
  }
}

interface GameActions {
  connect: () => void;
  simulateConnectionLoss: () => void;
  dismissGameResults: () => void;
  updateProfile: (changes: Actions['update_profile']['payload']) => Promise<Actions['update_profile']['result']>;
  createRoom: (options: Actions['create_room']['payload']) => Promise<Actions['create_room']['result']>;
  joinRoom: (roomId: string) => Promise<Actions['join_room']['result']>;
  leaveRoom: (confirm?: boolean) => Promise<Actions['leave_room']['result']>;
  updateSettings: (settings: GameSettings) => Promise<GameSettings>;
  startGame: () => Promise<unknown>;
  endGame: () => Promise<unknown>;
  selectCard: (cardId: number) => Promise<unknown>;
  chooseWinner: (cardId: number) => Promise<unknown>;
  sendChat: (text: string) => Promise<unknown>;
}

export type GameStore = GameData & GameActions;

export const useGameStore = create<GameStore>()((set, get) => {
  // One player per tab; see tokenStorage.ts. Created on first use, not on import,
  // so the tests (no browser there) can import this module.
  let tokenStorage: TokenStorage | null = null;
  const tokens = () => (tokenStorage ??= createTokenStorage(sessionStorage, window));
  const socket = new GameSocket({
    url: () => {
      // Same host as the page: in development Vite passes /ws on to the backend
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const token = tokens().get();
      const query = token ? `?reconnect_token=${encodeURIComponent(token)}` : '';
      return `${protocol}//${window.location.host}/ws${query}`;
    },
    onStatus: (connection) => set({ connection }),
    onMessage: (message) => {
      if (message.event === 'session') tokens().set(message.payload.reconnect_token);
      set(applyServerMessage(get(), message));
    },
  });

  return {
    ...INITIAL_DATA,

    connect: () => socket.connect(),
    simulateConnectionLoss: () => socket.simulateDrop(),
    dismissGameResults: () => set({ gameEnded: null }),

    updateProfile: async (changes) => {
      const profile = await socket.send('update_profile', changes);
      // The server answers with the saved profile but sends no new `session`, so update `me` here
      set((state) => ({ me: state.me && { ...state.me, ...profile } }));
      return profile;
    },
    createRoom: (options) => socket.send('create_room', options),
    joinRoom: (roomId) => socket.send('join_room', { room_id: roomId }),
    leaveRoom: (confirm = false) => socket.send('leave_room', { confirm }),
    updateSettings: (settings) => socket.send('update_settings', settings),
    startGame: () => socket.send('start_game', {}),
    endGame: () => socket.send('end_game', {}),
    selectCard: (cardId) => socket.send('select_card', { card_id: cardId }),
    chooseWinner: (cardId) => socket.send('choose_winner', { card_id: cardId }),
    sendChat: (text) => socket.send('chat_message', { text }),
  };
});
