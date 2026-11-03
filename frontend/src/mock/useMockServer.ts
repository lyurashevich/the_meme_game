// A pretend server for the mockup: keeps the state the real server would send and
// changes it the way the real actions would. The WebSocket store that replaces it
// will offer the same fields and actions, so the screens stay as they are.
import { useState } from 'react';
import type { GameSettings, RoomPlayer, RoomState, RoundState, Session } from '../protocol';
import {
  MOCK_CHAT,
  MOCK_HAND,
  MOCK_OTHER_PLAYERS,
  MOCK_ROOMS,
  MOCK_SESSION,
  MOCK_SITUATION,
  MOCK_TABLE,
  MY_ID,
} from './data';

const LEADER_TIME_LIMIT = 30; // seconds, as on the server

const DEFAULT_SETTINGS: GameSettings = { round_time_limit: 60, max_rounds: 10, score_to_win: null };

const secondsFromNow = (seconds: number) => new Date(Date.now() + seconds * 1000).toISOString();

function asRoomPlayer(me: Session): RoomPlayer {
  return { id: me.player_id, username: me.username, avatar_id: me.avatar_id, score: 0, is_connected: true };
}

function lobbyState(me: Session, owner_id: string, name: string): RoomState {
  return {
    server_time: new Date().toISOString(),
    room: { id: 'room-1', name, owner_id, max_players: 8, settings: DEFAULT_SETTINGS },
    players: [asRoomPlayer(me), ...MOCK_OTHER_PLAYERS],
    game: null,
    chat: MOCK_CHAT,
  };
}

// Who played which card. On the real server this stays secret until the round ends.
function authorOf(cardId: number): string {
  return MOCK_TABLE.find((played) => played.card.id === cardId)?.player_id ?? MY_ID;
}

function gameState(lobby: RoomState, phase: RoundState, iAmLeader: boolean): RoomState {
  const leaderId = iAmLeader ? MY_ID : 'p2';
  const othersCards = MOCK_TABLE.filter((played) => played.player_id !== leaderId);
  const [myCard, ...restOfMyHand] = MOCK_HAND;
  const judging = phase !== 'choosing_cards';

  // While choosing, one of the others is still thinking; later everybody has played
  const submitted = othersCards.slice(0, judging ? undefined : 1).map((played) => played.player_id);
  const table = judging ? [...othersCards.map((played) => played.card), ...(iAmLeader ? [] : [myCard])] : [];
  const winnerCard = othersCards[0].card;

  return {
    ...lobby,
    server_time: new Date().toISOString(),
    game: {
      state: 'active',
      round_number: 2,
      round_state: phase,
      leader_id: leaderId,
      situation: MOCK_SITUATION,
      my_hand: judging && !iAmLeader ? restOfMyHand : MOCK_HAND,
      my_selected_card_id: judging && !iAmLeader ? myCard.id : null,
      submitted_player_ids: judging && !iAmLeader ? [...submitted, MY_ID] : submitted,
      table: table.sort((a, b) => a.id - b.id),
      winner: phase === 'round_ended' ? { player_id: authorOf(winnerCard.id), card_id: winnerCard.id } : null,
      ends_at:
        phase === 'choosing_cards'
          ? secondsFromNow(lobby.room.settings.round_time_limit)
          : phase === 'leader_choosing'
            ? secondsFromNow(LEADER_TIME_LIMIT)
            : null,
    },
  };
}

export function useMockServer() {
  const [me, setMe] = useState<Session>(MOCK_SESSION);
  const [roomState, setRoomState] = useState<RoomState | null>(null);

  // Each action takes the previous state and returns a new object instead of changing the old one:
  // React compares objects by reference to notice that something changed.
  const updateRoom = (change: (state: RoomState) => RoomState) => {
    setRoomState((current) => (current ? change(current) : current));
  };

  return {
    me,
    rooms: MOCK_ROOMS,
    roomState,

    updateProfile: (changes: Partial<Pick<Session, 'username' | 'avatar_id'>>) => {
      setMe((current) => ({ ...current, ...changes }));
    },

    createRoom: (options: { name?: string; max_players: number }) => {
      const room = lobbyState(me, MY_ID, options.name ?? 'Комната ' + me.username);
      setRoomState({
        ...room,
        room: { ...room.room, max_players: options.max_players },
        players: [asRoomPlayer(me)],
        chat: [],
      });
    },

    joinRoom: (roomId: string) => {
      const summary = MOCK_ROOMS.find((room) => room.id === roomId);
      setRoomState(lobbyState(me, 'p2', summary?.name ?? 'Комната'));
    },

    leaveRoom: () => setRoomState(null),

    updateSettings: (settings: GameSettings) => {
      updateRoom((state) => ({ ...state, room: { ...state.room, settings } }));
    },

    startGame: () => updateRoom((state) => gameState(state, 'choosing_cards', false)),

    endGame: () => updateRoom((state) => ({ ...state, game: null })),

    selectCard: (cardId: number) => {
      updateRoom((state) => {
        if (!state.game) return state;
        const game = state.game;
        return {
          ...state,
          game: {
            ...game,
            my_hand: game.my_hand.filter((card) => card.id !== cardId),
            my_selected_card_id: cardId,
            submitted_player_ids: [...game.submitted_player_ids, MY_ID],
          },
        };
      });
    },

    chooseWinner: (cardId: number) => {
      updateRoom((state) => {
        if (!state.game) return state;
        const winnerId = authorOf(cardId);
        return {
          ...state,
          players: state.players.map((p) => (p.id === winnerId ? { ...p, score: p.score + 1 } : p)),
          game: {
            ...state.game,
            round_state: 'round_ended',
            winner: { player_id: winnerId, card_id: cardId },
            ends_at: null,
          },
        };
      });
    },

    sendChat: (text: string) => {
      updateRoom((state) => ({
        ...state,
        chat: [
          ...(state.chat ?? []),
          { player_id: me.player_id, username: me.username, text, timestamp: new Date().toISOString() },
        ],
      }));
    },

    // Mockup only: jump straight to a given situation, keeping what was written in the chat
    mock: {
      showLobby: (asOwner: boolean) => {
        setRoomState((current) => ({
          ...lobbyState(me, asOwner ? MY_ID : 'p2', MOCK_ROOMS[0].name),
          chat: current?.chat ?? MOCK_CHAT,
        }));
      },
      showGame: (phase: RoundState, asLeader: boolean) => {
        setRoomState((current) => ({
          ...gameState(lobbyState(me, MY_ID, MOCK_ROOMS[0].name), phase, asLeader),
          chat: current?.chat ?? MOCK_CHAT,
        }));
      },
    },
  };
}

export type MockServer = ReturnType<typeof useMockServer>;
