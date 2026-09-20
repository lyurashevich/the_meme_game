/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

<script setup lang="ts">

import { apiFetch } from './api'

import type {
  ScreenId,
  PlayerProfile,
  GameRoom,
  MemeCardData,
  ChatMessage,
} from './types';

import {
  INITIAL_ROOMS,
  CURRENT_SITUATION,
  MOCK_HAND_CARDS,
  PLAYED_TABLE_CARDS,
  MOCK_PLAYERS_IN_ROOM,
  MOCK_CHAT_MESSAGES,
} from './data/mockData';

import { ref } from 'vue';

import MockupHeader from './components/MockupHeader.vue';
import Screen1PlayerCreation from './components/Screen1PlayerCreation.vue';
import Screen2RoomSelection from './components/Screen2RoomSelection.vue';
import Screen3RoomLobby from './components/Screen3RoomLobby.vue';
import Screen4ActiveGame from './components/Screen4ActiveGame.vue';
import DesignSpecsModal from './components/DesignSpecsModal.vue';

// Screen state
const currentScreen = ref<ScreenId>('screen1');
const showSpecs = ref(false);

// Player state
const player = ref<PlayerProfile>({
  id: 'p-me',
  nickname: 'Кот_В_Шоке',
  avatarId: 'cat',
  isHost: false,
  score: 2,
  status: 'Готов шутить',
  isReady: true,
  hasPlayedCard: true,
});

// Rooms & active game data
// const rooms = ref<GameRoom[]>(INITIAL_ROOMS);
const rooms = ref<GameRoom[]>([]);
const currentRoom = ref<GameRoom>(INITIAL_ROOMS[0]);
const playersInRoom = ref<PlayerProfile[]>(MOCK_PLAYERS_IN_ROOM);
const handCards = ref<MemeCardData[]>(MOCK_HAND_CARDS);
const chatMessages = ref<ChatMessage[]>(MOCK_CHAT_MESSAGES);
const tableCards = ref(PLAYED_TABLE_CARDS);

// Profile update handler
const handleUpdatePlayer = (updated: Partial<PlayerProfile>) => {
  player.value = {
    ...player.value,
    ...updated,
  };

  playersInRoom.value = playersInRoom.value.map((p) =>
    p.id === 'p-me' ? { ...p, ...updated } : p
  );
};

// Screen transitions
const handleConfirmProfile = async () => {
  try {
    const saved = await apiFetch<PlayerProfile>('/player/', {
      method: 'POST',
      body: JSON.stringify(player.value),
    })
    console.log('saved', saved)
    player.value = saved
    await loadRooms()
    currentScreen.value = 'screen2'
  } catch (e) {
    console.error('Ошибка сохранения профиля:', e)
  }
}

const handleJoinRoom = async (room: GameRoom) => {
  console.log(room)
  try {
    const res = await apiFetch<GameRoom>(`/room/${room.id}`, {
      method: 'PATCH',
      body: JSON.stringify({
        player_id: player.value.id,
        room_id: room.id,
        confirm: false,
      })
    })
    currentRoom.value = res;
    currentScreen.value = 'screen3';
  } catch (e) {
    console.error('Ошибка присоединения к комнате:', e)
  }
};

const handleCreateRoom = async (newRoom: GameRoom) => {
  console.log(newRoom);
  try {
    const saved = await apiFetch<RoomData>('/room/', {
      method: 'POST',
      body: JSON.stringify(newRoom)
    })
    rooms.value = [newRoom, ...rooms.value];
    currentRoom.value = saved;
    player.value = {
      ...player.value,
      isHost: true,
    };
    currentScreen.value = 'screen3';
  } catch (e) {
    console.error('Ошибка создания комнаты:', e)
  }
};

const handleStartGame = () => {
  setCurrentScreen.value = 'screen4';
};

const handleLeaveRoom = () => {
  currentScreen.value = 'screen2';
};

const handleEditProfile = () => {
  currentScreen.value = 'screen1';
};

const handleSendMessage = (text: string) => {
  const newMsg: ChatMessage = {
    id: `m-${Date.now()}`,
    sender: player.value.nickname || 'Вы',
    avatarId: player.value.avatarId,
    text,
    time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
  };
  chatMessages.value = [...chatMessages.value, newMsg];
};

const handleToggleReady = () => {
  const nextReady = !player.value.isReady;
  handleUpdatePlayer({ isReady: nextReady });
};

const handlePlayCard = (card: MemeCardData) => {
  // Add card to table if not present
  tableCards.value = [
    ...tableCards.value.filter((c) => c.playerId !== 'p-me'),
    {
      id: `play-me-${Date.now()}`,
      playerId: 'p-me',
      playerName: `${player.value.nickname} (Вы)`,
      avatarId: player.value.avatarId,
      isRevealed: true,
      card: card,
      position: 'bottom-right',
      votesCount: 0,
    },
  ];
};

const loadRooms = async () => {
  try {
    const data = await apiFetch<GameRoom[]>('/room/all')
    console.log(data)
    rooms.value = data
  } catch (e) {
    console.error('Ошибка загрузки комнат:', e)
  }
}
</script>

<template>
  <div class="min-h-screen bg-[#F4F1EA] text-[#242426] flex flex-col font-['Rubik',sans-serif]">
    <!-- Top Header with screen tabs and quick switcher -->
    <MockupHeader
      :current-screen="currentScreen"
      @select-screen="currentScreen = $event"
      @toggle-specs="showSpecs = true"
    />

    <!-- Main Screen Content -->
    <main class="flex-1">
      <Screen1PlayerCreation
        v-if="currentScreen === 'screen1'"
        :player="player"
        @update-player="handleUpdatePlayer"
        @confirm="handleConfirmProfile"
      />

      <Screen2RoomSelection
        v-if="currentScreen === 'screen2'"
        :player="player"
        :rooms="rooms"
        @join-room="handleJoinRoom"
        @create-room="handleCreateRoom"
        @edit-profile="handleEditProfile"
      />

      <Screen3RoomLobby
        v-if="currentScreen === 'screen3'"
        :room="currentRoom"
        :player="player"
        :players="playersInRoom"
        :hand-cards="handCards"
        :chat-messages="chatMessages"
        @start-game="handleStartGame"
        @leave-room="handleLeaveRoom"
        @send-message="handleSendMessage"
        @toggle-ready="handleToggleReady"
      />

      <Screen4ActiveGame
        v-if="currentScreen === 'screen4'"
        :room="currentRoom"
        :player="player"
        :players="playersInRoom"
        :situation="CURRENT_SITUATION"
        :hand-cards="handCards"
        :table-cards="tableCards"
        :chat-messages="chatMessages"
        @send-message="handleSendMessage"
        @play-card="handlePlayCard"
      />
    </main>

      <!-- Style Concept & Rationale Modal -->
    <DesignSpecsModal :is-open="showSpecs" @close = "false" />
  </div>
</template>
