<script setup lang="ts">
import type { GameRoom, PlayerProfile, MemeCardData, ChatMessage } from '../types';
import AvatarGraphic from './Avatars.vue';
import MemeCard from './MemeCard.vue';
import {
  Crown,
  Play,
  Copy,
  Check,
  Send,
  MessageSquare,
  Users,
  Smile,
  Sparkles,
  Volume2,
  LogOut,
  HelpCircle,
} from 'lucide-vue-next';

import { ref } from 'vue';

interface Screen3Props {
  room: GameRoom;
  player: PlayerProfile;
  players: PlayerProfile[];
  handCards: MemeCardData[];
  chatMessages: ChatMessage[];
  onStartGame: () => void;
  onLeaveRoom: () => void;
  onSendMessage: (text: string) => void;
  onToggleReady: () => void;
}

const props = defineProps<Screen3Props>();

const chatInput = ref('');
const copiedCode = ref(false);
const selectedHandCard = ref<string | null>(null);

const isHost = props.player.isHost || props.player.nickname === props.room.hostName;

const handleSendChat = (e: Event) => {
  e.preventDefault();
  if (!chatInput.value.trim()) return;
  props.onSendMessage(chatInput.value.trim());
  chatInput.value = '';
};

const rotations = ['-rotate-1', 'rotate-0', 'rotate-1', '-rotate-2', 'rotate-2'];

const handleCopyCode = () => {
  navigator.clipboard?.writeText('MEM-742');
  setCopiedCode.value = true;
  setTimeout(() => setCopiedCode.value = false, 2000);
};

// Divide players into table positions (top, left, right)
const otherPlayers = props.players.filter((p) => p.id !== 'p-me');
const topPlayers = otherPlayers.slice(0, 2);
const leftPlayers = otherPlayers.slice(2, 3);
const rightPlayers = otherPlayers.slice(3, 4);
</script>

<template>
  <div class="max-w-7xl mx-auto px-3 sm:px-6 py-4 flex flex-col min-h-[calc(100vh-70px)]">
    <!-- Top Room Header Bar -->
    <div class="rounded-2xl border-2 border-[#242426] bg-[#FAF7F2] px-4 py-2.5 shadow-[3px_3px_0px_#242426] mb-4 flex flex-wrap items-center justify-between gap-3">
      <div class="flex items-center gap-2.5">
        <button
          @click="props.onLeaveRoom"
          title="Выйти в меню комнат"
          class="p-1.5 rounded-xl border border-[#242426]/30 hover:bg-[#ECE8DE] text-[#242426] transition-colors cursor-pointer"
        >
          <LogOut class="w-4 h-4" />
        </button>
        <div>
          <div class="flex items-center gap-2">
            <h2 class="font-black text-base sm:text-lg text-[#242426] tracking-tight">
              {{ props.room.name }}
            </h2>
            <span class="text-[10px] bg-[#E4D976] border border-[#242426] px-2 py-0.5 rounded-full font-bold">
              ЭКРАН 3: ЛОББИ
            </span>
          </div>
          <p class="text-[11px] text-[#6E6A61] font-medium">
            Хост: <strong>{{ props.room.hostName }}</strong> • Раунды: {{ props.room.roundsCount }} • Время хода: {{ props.room.timeLimit }}с
          </p>
        </div>
      </div>

      <!-- Room Code & Player Count -->
      <div class="flex items-center gap-2.5">
          <button
            @click="handleCopyCode"
            class="flex items-center gap-1.5 px-2.5 py-1 rounded-xl border border-[#242426] bg-[#ECE8DE] hover:bg-[#E4D976] text-xs font-bold text-[#242426] shadow-[1.5px_1.5px_0px_#242426] transition-all cursor-pointer"
            title="Скопировать код комнаты"
          >
          <Check
           v-if="copiedCode"
           class="w-3.5 h-3.5 text-green-700" />
            <Copy v-else class="w-3.5 h-3.5" />
            <span>Код: MEM-742</span>
          </button>

          <div class="flex items-center gap-1.5 px-2.5 py-1 rounded-xl border border-[#242426] bg-[#FAF7F2] text-xs font-extrabold text-[#242426]">
            <Users class="w-3.5 h-3.5" />
            <span>{{ props.players.length }}/{{ props.room.maxPlayers }}</span>
        </div>
      </div>
    </div>

    <!-- Main Play Area: Game Table (Center + Left/Top/Right Players) + Chat (Right Pane) -->
    <div class="grid grid-cols-1 lg:grid-cols-12 gap-4 flex-1 items-stretch mb-4">
      <!-- GAME TABLE AREA (9 columns on large screens) -->
      <div class="lg:col-span-8 xl:col-span-9 flex flex-col justify-between rounded-3xl border-2 border-[#242426] bg-[#E7E2D4] p-4 sm:p-6 shadow-[4px_4px_0px_#242426] relative overflow-hidden">
        <!-- Playmat stitched/dashed border -->
        <div class="absolute inset-2.5 rounded-2xl border-2 border-dashed border-[#242426]/20 pointer-events-none" />

        <!-- TOP PLAYERS ROW -->
        <div class="relative z-10 flex items-center justify-center gap-6 sm:gap-12 pt-1 pb-3">
          <div v-for="p in topPlayers" :key="p.id"
            class="flex flex-col items-center group bg-[#FAF7F2] border-2 border-[#242426] rounded-2xl p-2 sm:px-4 sm:py-2.5 shadow-[3px_3px_0px_#242426]"
          >
            <div class="relative">
              <AvatarGraphic :id="p.avatarId" size="md" />
                <span v-if="p.isHost"
                  title="Хост комнаты"
                  class="absolute -top-2.5 -right-2.5 w-6 h-6 rounded-full bg-[#E4D976] border-2 border-[#242426] flex items-center justify-center shadow-[1px_1px_0px_#242426]"
                >
                  <Crown class="w-3.5 h-3.5 text-[#242426]" />
                </span>
            </div>
            <span class="font-extrabold text-xs sm:text-sm text-[#242426] mt-1 truncate max-w-[110px]">
              {{ p.nickname }}
            </span>
            <span class="text-[10px] font-bold px-2 py-0.5 rounded-full mt-0.5 bg-[#C8D7C5] border border-[#242426]/30 text-[#2C442A]">
              {{ p.isReady ? 'ГОТОВ ✓' : 'ЖДЁМ ⏳' }}
            </span>
          </div>
        </div>

        <!-- MIDDLE ROW: Left Player, Central Table Slots, Right Player -->
        <div class="relative z-10 grid grid-cols-1 sm:grid-cols-12 items-center gap-4 my-auto py-2">
          <!-- Left Player Seat -->
          <div class="hidden sm:flex sm:col-span-2 justify-center">
            <div v-if="leftPlayers[0]" class="flex flex-col items-center bg-[#FAF7F2] border-2 border-[#242426] rounded-2xl p-2.5 shadow-[3px_3px_0px_#242426]">
              <AvatarGraphic :id="leftPlayers[0].avatarId" size="md" />
                <span class="font-extrabold text-xs text-[#242426] mt-1 truncate max-w-[90px]">
                  {{ leftPlayers[0].nickname }}
                </span>
                <span class="text-[10px] font-bold px-2 py-0.5 rounded-full mt-0.5 bg-[#C8D7C5] border border-[#242426]/30 text-[#2C442A]">
                  ГОТОВ ✓
                </span>
            </div>
          </div>

          <!-- CENTRAL TABLE FOCUS (Card Slots Preview) -->
          <div class="sm:col-span-8 flex flex-col items-center justify-center">
            <div class="w-full max-w-md rounded-2xl border-2 border-dashed border-[#242426]/40 bg-[#DCD6C5]/70 p-5 text-center flex flex-col items-center shadow-inner">
              <!-- Visual central slot representation for the future situation card -->
              <div class="w-48 h-28 rounded-xl border-2 border-dashed border-[#242426]/50 bg-[#F4F1EA]/80 flex flex-col items-center justify-center p-3 mb-3 relative -rotate-1 shadow-sm">
                <div class="text-xl mb-1">🃏</div>
                <span class="text-xs font-black uppercase tracking-wider text-[#35322D]">
                  Карта ситуации
                </span>
                <span class="text-[10px] text-[#69655C] leading-tight mt-0.5">
                  Будет выложена в центр после старта
                </span>
              </div>

              <!-- Sub-slots indicator for player meme responses -->
              <div class="flex items-center gap-2 mb-3">
                <div class="w-10 h-14 rounded-lg border border-dashed border-[#242426]/40 bg-[#FAF7F2]/50 rotate-3" />
                <div class="w-10 h-14 rounded-lg border border-dashed border-[#242426]/40 bg-[#FAF7F2]/50 -rotate-2" />
                <div class="w-10 h-14 rounded-lg border border-dashed border-[#242426]/40 bg-[#FAF7F2]/50 rotate-6" />
                <div class="w-10 h-14 rounded-lg border border-dashed border-[#242426]/40 bg-[#FAF7F2]/50 -rotate-4" />
              </div>

              <!-- Clear indication that game has NOT started yet -->
              <div class="bg-[#FAF7F2] border-2 border-[#242426] px-4 py-2 rounded-xl shadow-[2px_2px_0px_#242426] inline-block">
                <p class="text-xs font-bold text-[#242426] flex items-center justify-center gap-1.5">
                  <Sparkles class="w-4 h-4 text-[#B5A528]" />
                  <span>ИГРА ЕЩЁ НЕ НАЧАЛАСЬ</span>
                </p>
                <p class="text-[11px] text-[#69655D] mt-0.5">
                  Ждём команды хоста для раздачи карт ситуации
                </p>
              </div>

              <!-- Host Start Button or Player Ready Toggle -->
              <div class="mt-4 flex flex-wrap items-center justify-center gap-3">
                <button
                  type="button"
                  id="start-game-button"
                  @click="props.onStartGame"
                  class="rounded-2xl border-2 border-[#242426] bg-[#E4D976] hover:bg-[#DDD166] active:translate-y-0.5 px-6 py-2.5 font-black text-sm text-[#242426] shadow-[3px_3px_0px_#242426] flex items-center gap-2 cursor-pointer transition-all"
                >
                  <Play class="w-4 h-4 fill-[#242426]" />
                  <span>НАЧАТЬ ИГРУ (ХОСТ) →</span>
                </button>

                <button
                  type="button"
                  @click="props.onToggleReady"
                  class="rounded-2xl border-2 border-[#242426] bg-[#FAF7F2] hover:bg-[#EAE5D9] px-4 py-2.5 font-bold text-xs text-[#242426] shadow-[2px_2px_0px_#242426] cursor-pointer"
                >
                  {{ props.player.isReady ? 'Я готов ✓' : 'Нажать «Готов»' }}
                </button>
              </div>
            </div>
          </div>

          <!-- Right Player Seat -->
          <div class="hidden sm:flex sm:col-span-2 justify-center">
            <div v-if="rightPlayers[0]" class="flex flex-col items-center bg-[#FAF7F2] border-2 border-[#242426] rounded-2xl p-2.5 shadow-[3px_3px_0px_#242426]">
              <AvatarGraphic :id="rightPlayers[0].avatarId" size="md" />
                <span class="font-extrabold text-xs text-[#242426] mt-1 truncate max-w-[90px]">
                  {{ rightPlayers[0].nickname }}
                </span>
                <span class="text-[10px] font-bold px-2 py-0.5 rounded-full mt-0.5 bg-[#C8D7C5] border border-[#242426]/30 text-[#2C442A]">
                  ГОТОВ ✓
                </span>
            </div>
          </div>
        </div>

        <!-- TABLE BOTTOM: You (Current Player) status -->
        <div class="relative z-10 flex items-center justify-center pt-2">
          <div class="flex items-center gap-2.5 bg-[#FAF7F2] border-2 border-[#242426] px-4 py-1.5 rounded-2xl shadow-[2px_2px_0px_#242426]">
            <AvatarGraphic :id="player.avatarId" size="sm" />
            <div>
              <div class="flex items-center gap-1.5">
                <span class="font-black text-xs text-[#242426]">
                  {{ player.nickname }} (Вы)
                </span>
                <span class="text-[10px] bg-[#C8D7C5] px-1.5 py-0.2 rounded font-bold text-[#2A4428]">
                  ГОТОВ
                </span>
              </div>
              <span class="text-[10px] text-[#78746B]">
                Колода мемов загружена (5 карт)
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- CHAT AREA (Separate Functional Zone) (3 columns on large screens) -->
      <div class="lg:col-span-4 xl:col-span-3 rounded-3xl border-2 border-[#242426] bg-[#FAF7F2] p-4 shadow-[4px_4px_0px_#242426] flex flex-col justify-between h-[380px] lg:h-auto">
        <!-- Chat Header -->
        <div class="flex items-center justify-between pb-2.5 border-b-2 border-[#242426]/15">
          <div class="flex items-center gap-2">
            <MessageSquare class="w-4 h-4 text-[#242426]" />
            <span class="font-extrabold text-sm text-[#242426]">
              Чат комнаты
            </span>
          </div>
          <span class="text-[10px] bg-[#EAE5D9] px-2 py-0.5 rounded-full font-bold text-[#555148]">
            {{ players.length }} онлайн
          </span>
        </div>

        <!-- Messages Stream -->
        <div class="flex-1 overflow-y-auto my-2 space-y-2.5 pr-1 max-h-[300px] lg:max-h-none text-xs">
          <div v-for="msg in chatMessages" :key="msg.id"
            :class="[
                'p-2 rounded-xl border',
                msg.isSystem
                  ? 'bg-[#EAE5D9]/60 border-dashed border-[#242426]/30 text-center text-[11px] text-[#69645B] italic font-medium'
                  : 'bg-[#F4F1EA] border-[#242426]/20'
                ]"
          >
            <div v-if="!msg.isSystem" class="flex items-center justify-between mb-0.5">
              <span class="font-extrabold text-[#242426]">
                {{ msg.sender }}
              </span>
              <span class="text-[10px] text-[#88837A]">{{ msg.time }}</span>
            </div>
            <p class="text-[#35322E] font-medium leading-relaxed">
              {{ msg.text }}
            </p>
              </div>
        </div>

        <!-- Quick Reaction Emojis & Chat Input -->
        <div>
          <div class="flex items-center gap-1.5 mb-2 overflow-x-auto pb-1">
            <button v-for="emoji in ['🗿', '🤡', '💀', '🍿', '📉', '🔥']"
              :key="emoji"
              type="button"
              @click="props.onSendMessage(emoji)"
              class="px-2 py-1 rounded-lg border border-[#242426]/20 bg-[#ECE8DE] hover:bg-[#E4D976] text-xs transition-colors cursor-pointer"
            >
              {{ emoji }}
            </button>
          </div>

          <form @submit="handleSendChat" class="flex items-center gap-1.5">
            <input
              type="text"
              v-model="chatInput"
              placeholder="Сообщение в чат..."
              class="flex-1 rounded-xl border-2 border-[#242426] bg-[#F5F2EA] px-3 py-2 text-xs font-semibold text-[#242426] placeholder-[#9E988D] focus:outline-none focus:bg-[#FAF7F2]"
            />
            <button
              type="submit"
              class="p-2 rounded-xl border-2 border-[#242426] bg-[#E4D976] hover:bg-[#DDD166] text-[#242426] cursor-pointer shadow-[2px_2px_0px_#242426]"
            >
              <Send class="w-3.5 h-3.5" />
            </button>
          </form>
        </div>
      </div>
    </div>

    <!-- CARDS IN PLAYER'S HAND AT THE BOTTOM -->
    <div class="rounded-3xl border-2 border-[#242426] bg-[#FAF7F2] p-4 shadow-[4px_4px_0px_#242426]">
      <div class="flex items-center justify-between mb-3 px-1">
        <div class="flex items-center gap-2">
          <span class="font-black text-xs uppercase tracking-wider text-[#242426]">
            Твоя рука карт
          </span>
          <span class="text-[11px] bg-[#EAE5D9] px-2 py-0.5 rounded-full font-bold text-[#555148]">
            5 мемов готовы к бою
          </span>
        </div>
        <span class="text-xs text-[#7A756D] font-medium hidden sm:inline">
          Наведи на карту, чтобы рассмотреть детали
        </span>
      </div>

      <!-- Hand Cards Carousel / Row -->
      <div class="flex items-center gap-3 overflow-x-auto pb-2 pt-1 px-1">
        <MemeCard v-for="(card, idx) in handCards" :key="card.id"
          :card="card"
          size="sm"
          :is-playable="true"
          :is-selected="selectedHandCard === card.id"
          @click="selectedHandCard = selectedHandCard === card.id ? null : card.id"
          :rotation="rotations[idx % rotations.length]"
          class="shrink-0"
        />
      </div>
    </div>
  </div>
</template>