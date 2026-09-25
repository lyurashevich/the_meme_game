<script setup lang="ts">
import type {
  GameRoom,
  PlayerProfile,
  MemeCardData,
  SituationCardData,
  ChatMessage,
} from '../types';
import AvatarGraphic from './Avatars.vue';
import MemeCard from './MemeCard.vue';
import {
  Clock,
  Crown,
  Trophy,
  CheckCircle,
  Hourglass,
  Send,
  MessageSquare,
  Sparkles,
  ArrowUpCircle,
  ThumbsUp,
  Flame,
  AlertCircle,
} from 'lucide-vue-next';

import { ref, onMounted, onUnmounted } from 'vue';

interface Screen4Props {
  room: GameRoom;
  player: PlayerProfile;
  players: PlayerProfile[];
  situation: SituationCardData;
  handCards: MemeCardData[];
  tableCards: {
    id: string;
    playerId: string;
    playerName: string;
    avatarId: string;
    isRevealed: boolean;
    card: MemeCardData;
    position: 'top-left' | 'top-right' | 'bottom-left' | 'bottom-right';
    votesCount?: number;
  }[];
  chatMessages: ChatMessage[];
  onSendMessage: (text: string) => void;
  onPlayCard: (card: MemeCardData) => void;
}

let timer: ReturnType<typeof setInterval>;

const props = defineProps<Screen4Props>();

const rotations = ['-rotate-2', 'rotate-1', '-rotate-1', 'rotate-2'];

const timeLeft = ref(38);
const selectedHandCard = ref<MemeCardData | null>(null);
const hasSubmitted = ref(true); // Default to submitted so all cards show on mockup
const chatInput = ref('');
const votedCardId = ref<string | null>('play-1');

// Gentle timer countdown tick simulation for interactive mockup
onMounted(() => {
  timer = setInterval(() => {
    timeLeft.value = timeLeft.value > 1 ? timeLeft.value - 1 : 60;
  }, 1000);
});

onUnmounted(() => {
    clearInterval(timer);
})

const handleSendChat = (e: Event) => {
  e.preventDefault();
  if (!chatInput.value.trim()) return;
  props.onSendMessage(chatInput.value.trim());
  chatInput.value = '';
};

const handleSelectCard = (card: MemeCardData) => {
  selectedHandCard.value = card;
};

const handlePlaySelectedCard = () => {
  if (selectedHandCard.value) {
    props.onPlayCard(selectedHandCard.value);
    hasSubmitted.value = true;
  }
};
</script>

<template>
  <div class="max-w-7xl mx-auto px-3 sm:px-6 py-4 flex flex-col min-h-[calc(100vh-70px)]">
    <!-- Active Game HUD Header Bar -->
    <div class="rounded-2xl border-2 border-[#242426] bg-[#FAF7F2] px-4 py-2.5 shadow-[3px_3px_0px_#242426] mb-4 flex flex-wrap items-center justify-between gap-3">
      <!-- Left: Round & Room Info -->
      <div class="flex items-center gap-3">
        <div class="flex items-center gap-2">
          <span class="font-black text-base sm:text-lg text-[#242426] tracking-tight">
            РАУНД {{ situation.roundNumber }} ИЗ {{ room.roundsCount }}
          </span>
          <span class="text-[10px] bg-[#E8BAA8] border border-[#242426] px-2 py-0.5 rounded-full font-extrabold text-[#471E14]">
            ЭКРАН 4: ИГРА
          </span>
        </div>
        <span class="text-xs text-[#6B675E] font-medium hidden sm:inline">
          Тема: <strong class="text-[#242426]">{{ situation.category }}</strong>
        </span>
      </div>

      <!-- Center: Action Status Banner -->
      <div class="flex items-center gap-2 bg-[#E4D976] border-2 border-[#242426] px-3.5 py-1 rounded-xl shadow-[2px_2px_0px_#242426]">
        <div v-if="hasSubmitted" class="flex items-center gap-1.5 text-xs font-black text-[#242426]">
          <CheckCircle class="w-4 h-4 text-[#242426]" />
          <span>ТВОЙ МЕМ СДАН! Ожидаем вскрытия ведущим</span>
        </div>
          <div v-else class="flex items-center gap-1.5 text-xs font-black text-[#242426] animate-pulse">
            <Sparkles class="w-4 h-4 text-[#242426]" />
            <span>ТВОЙ ХОД: Выбери мем из руки внизу!</span>
          </div>
      </div>

      <!-- Right: Round Timer -->
      <div class="flex items-center gap-2">
        <div
          :class="[
            'flex items-center gap-1.5 px-3 py-1 rounded-xl border-2 border-[#242426] font-black text-xs shadow-[2px_2px_0px_#242426]',
              timeLeft < 15
                ? 'bg-[#E8BAA8] text-[#551E14] animate-bounce'
                : 'bg-[#FAF7F2] text-[#242426]'
            ]"
        >
          <Clock class="w-3.5 h-3.5" />
          <span>0:{{ timeLeft < 10 ? `0${timeLeft}` : timeLeft }}</span>
        </div>

        <div class="text-[11px] font-bold text-[#6D6960] hidden md:block">
          Осталось времени
        </div>
      </div>
    </div>

    <!-- Main Game Layout: Table Area + Chat Area -->
    <div class="grid grid-cols-1 lg:grid-cols-12 gap-4 flex-1 items-stretch mb-4">
      <!-- CENTRAL GAME TABLE (9 columns on large screens) -->
      <div class="lg:col-span-8 xl:col-span-9 flex flex-col justify-between rounded-3xl border-2 border-[#242426] bg-[#DDD7C7] p-4 sm:p-6 shadow-[4px_4px_0px_#242426] relative overflow-hidden">
        <!-- Subtle playmat texture and dashed border -->
        <div class="absolute inset-2.5 rounded-2xl border-2 border-dashed border-[#242426]/20 pointer-events-none" />

        <!-- PLAYERS AROUND THE TABLE (Top row with scores & turn statuses) -->
        <div class="relative z-10 flex items-center justify-around gap-2 pt-1 pb-3 flex-wrap">
          <div
            v-for="p in players"
            :key="p.id"
            :class="[
                'flex items-center gap-2 bg-[#FAF7F2] border-2 border-[#242426] rounded-2xl p-1.5 sm:px-3 sm:py-2 shadow-[2px_2px_0px_#242426] transition-all',
                p.id === 'p-me' ? 'ring-2 ring-[#E4D976]' : ''
              ]"
          >
            <div class="relative">
              <AvatarGraphic :id="p.avatarId" size="sm" />
                <span
                  v-if="p.isHost"
                  title="Ведущий раунда"
                  class="absolute -top-1.5 -right-1.5 w-4 h-4 rounded-full bg-[#E4D976] border border-[#242426] flex items-center justify-center"
                >
                  <Crown class="w-2.5 h-2.5 text-[#242426]" />
                </span>
            </div>

            <div class="text-left">
              <div class="flex items-center gap-1">
                <span class="font-extrabold text-xs text-[#242426] truncate max-w-[85px] sm:max-w-[110px]">
                  {{ p.nickname }}
                </span>
                <span class="text-[10px] font-bold text-[#8C6F36] flex items-center">
                  🏆 {{ p.score || 0 }}
                </span>
              </div>

              <div class="text-[9px] sm:text-[10px] font-bold flex items-center gap-1">
                <span v-if="p.isHost" class="text-[#8C6F36]">Судит раунд</span>
                <span v-else-if="p.hasPlayedCard" class="text-[#2E5429]">Выбрал мем ✓</span>
                <span v-else class="text-[#885A2B] flex items-center gap-0.5">
                  <Hourglass class="w-2.5 h-2.5 animate-spin" />
                  Думает...
                </span>
              </div>
            </div>
          </div>
        </div>

        <!-- TABLE CENTER: Central Situation Card + Surrounding Player Cards -->
        <div class="relative z-10 my-auto py-4 flex flex-col items-center">
          <!-- The Large Central Situation Card (Main Visual Focus) -->
          <div class="w-full max-w-xl rounded-3xl border-3 border-[#242426] bg-[#FAF7F2] p-5 sm:p-6 shadow-[5px_5px_0px_#242426] relative mb-6">
            <!-- Card Header -->
            <div class="flex items-center justify-between gap-2 mb-2.5 pb-2 border-b-2 border-[#242426]/15">
              <div class="flex items-center gap-2">
                <span class="w-3 h-3 rounded-full bg-[#E8BAA8] border border-[#242426]" />
                <span class="text-xs font-black uppercase tracking-widest text-[#59554E]">
                  КАРТА СИТУАЦИИ
                </span>
              </div>
            </div>

            <!-- Situation Prompt Text -->
            <div class="my-2">
              <p class="text-base sm:text-lg font-black leading-snug text-[#242426] text-center px-2 sm:px-4">
                «{{ props.situation.prompt }}»
              </p>
            </div>

            <!-- Sub-bar / Instructions -->
            <div class="mt-3 pt-2 border-t border-[#242426]/10 flex items-center justify-between text-[11px] text-[#716D64]">
              <span>Сыграно карт: 4 из 4</span>
              <span class="font-bold text-[#242426]">
                Ведущий оценивает совпадение юмора
              </span>
            </div>
          </div>

          <!-- CARDS PLAYED BY PARTICIPANTS PLACED AROUND THE SITUATION -->
          <div class="w-full">
            <div class="text-center mb-2">
              <span class="text-[11px] font-black uppercase tracking-widest bg-[#FAF7F2] border border-[#242426] px-3 py-1 rounded-full text-[#38352F] shadow-[1.5px_1.5px_0px_#242426]">
                МЕМЫ ИГРОКОВ НА СТОЛЕ
              </span>
            </div>

            <!-- Cards Grid surrounding the table -->
            <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-4 justify-items-center">
              <div
                v-for="(played, idx) in tableCards"
                :key="played.id"
                class="flex flex-col items-center"
              >
                <MemeCard
                  :card="played.card"
                  :is-revealed="played.isRevealed"
                  :player-name="played.playerName"
                  :votes-count="played.votesCount"
                  :is-selected="isVoted"
                  size="sm"
                  :rotation="rotations[idx % rotations.length]"
                  @click="votedCardId = played.id"
                  class="cursor-pointer hover:scale-105 transition-transform"
                />
                <button
                  v-if="played.isRevealed"
                  type="button"
                  @click="votedCardId = played.id"
                  :class="[
                      'mt-2 flex items-center gap-1 text-[11px] font-bold px-2 py-0.5 rounded-lg border transition-all cursor-pointer',
                      votedCardId = played.id
                        ? 'bg-[#E4D976] text-[#242426] border-[#242426] shadow-[1.5px_1.5px_0px_#242426]'
                        : 'bg-[#FAF7F2] text-[#555147] border-[#242426]/30 hover:bg-[#EAE5D9]'
                      ]"
                >
                  <ThumbsUp class="w-3 h-3" />
                  <span>{isVoted ? 'Твой голос!' : 'Голосовать'}</span>
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- TABLE BOTTOM: Quick action bar -->
        <div class="relative z-10 flex items-center justify-between pt-2 border-t border-[#242426]/15 text-xs">
          <span class="font-bold text-[#4F4B43]">
            Раунд ведёт: <strong>Саня_Деплой 👑</strong>
          </span>
          <span class="text-[#6B665E] italic hidden sm:inline">
            «Победитель раунда получает +1 мемный балл»
          </span>
        </div>

        <!-- CHAT AREA (3 columns on large screens) -->
        <div class="lg:col-span-4 xl:col-span-3 rounded-3xl border-2 border-[#242426] bg-[#FAF7F2] p-4 shadow-[4px_4px_0px_#242426] flex flex-col justify-between h-[380px] lg:h-auto">
          <!-- Chat Header -->
          <div class="flex items-center justify-between pb-2.5 border-b-2 border-[#242426]/15">
            <div class="flex items-center gap-2">
              <MessageSquare class="w-4 h-4 text-[#242426]" />
              <span class="font-extrabold text-sm text-[#242426]">
                Чат игры
              </span>
            </div>
            <span class="text-[10px] bg-[#C8D7C5] px-2 py-0.5 rounded-full font-bold text-[#274624]">
              Живое обсуждение
            </span>
          </div>

          <!-- Messages Stream -->
          <div class="flex-1 overflow-y-auto my-2 space-y-2.5 pr-1 max-h-[300px] lg:max-h-none text-xs">
            <div v-for="msg in chatMessages" :key="msg.id"
              :class="[
                'p-2 rounded-xl border',
                msg.isSystem
                  ? 'bg-[#EAE5D9]/70 border-dashed border-[#242426]/30 text-center text-[11px] text-[#69645B] italic font-medium'
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
              <button v-for="react in ['💀 Ору', '🗿 База', '🤡 Кринж', '🔥 В яблочко', '📉']"
                :key="react"
                type="button"
                @click="onSendMessage(react)"
                class="px-2 py-1 rounded-lg border border-[#242426]/20 bg-[#ECE8DE] hover:bg-[#E4D976] text-xs font-bold text-[#3B3831] whitespace-nowrap transition-colors cursor-pointer"
              >
                {{ react }}
              </button>
            </div>

            <form @submit="handleSendChat" class="flex items-center gap-1.5">
              <input
                type="text"
                v-model="chatInput"
                placeholder="Написать реакцию..."
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
    </div>

    <!-- CARDS IN PLAYER'S HAND AT THE BOTTOM -->
    <div class="rounded-3xl border-2 border-[#242426] bg-[#FAF7F2] p-4 shadow-[4px_4px_0px_#242426]">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-3 px-1">
        <div class="flex items-center gap-2">
          <span class="font-black text-xs uppercase tracking-wider text-[#242426]">
            Твоя рука карт
          </span>
          <span class="text-[11px] bg-[#EAE5D9] px-2 py-0.5 rounded-full font-bold text-[#555148]">
            {{ handCards.length }} карт в запасе
          </span>
          <span class="text-[10px] text-[#706B62] font-semibold hidden md:inline">
            (Выбери мем и нажми «Сыграть»)
          </span>
        </div>

        <div v-if="selectedHandCard" class="flex items-center gap-2 self-end sm:self-auto">
          <span class="text-xs font-bold text-[#242426] truncate max-w-[160px]">
            Выбрано: {{ selectedHandCard.title }}
          </span>
            <button
              type="button"
              @click="handlePlaySelectedCard"
              class="px-3.5 py-1.5 rounded-xl border-2 border-[#242426] bg-[#E4D976] hover:bg-[#DDD166] font-black text-xs text-[#242426] shadow-[2px_2px_0px_#242426] flex items-center gap-1 cursor-pointer transition-all active:translate-y-0.5"
            >
              <ArrowUpCircle class="w-3.5 h-3.5" />
              <span>СЫГРАТЬ ЭТОТ МЕМ</span>
            </button>
        </div>
      </div>

      <!-- Hand Cards Carousel -->
      <div class="flex items-center gap-3 overflow-x-auto pb-2 pt-1 px-1">
        <div
          v-for="(card, idx) in handCards"
          :key="card.id"
          class="relative group shrink-0"
        >
          <MemeCard
            :card="card"
            size="sm"
            :is-playable="true"
            :is-selected="isSelected"
            @click="handleSelectCard(card)"
            :rotation="rotations[idx % rotations.length]"
          />
        </div>
      </div>
    </div>
  </div>
</template>
