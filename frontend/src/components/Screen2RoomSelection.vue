<script setup lang="ts">
import type { GameRoom, PlayerProfile } from '../types';
import AvatarGraphic from './Avatars.vue';
import {
  Plus,
  Users,
  Search,
  Lock,
  ArrowRight,
  Sparkles,
  RefreshCw,
  Clock,
  Filter,
  Flame,
} from 'lucide-vue-next';

import { computed, ref } from 'vue';

interface Screen2Props {
  player: PlayerProfile;
  rooms: GameRoom[];
  onJoinRoom: (room: GameRoom) => void;
  onCreateRoom: (newRoom: GameRoom) => void;
  onEditProfile: () => void;
}

const props = defineProps<Screen2Props>();

const searchTerm = ref('');
const activeFilter = ref('Все');
const showCreateModal = ref(false);

// New room modal state
const newRoomName = ref('Только свежие мемы 🔥');
const newRoomMaxPlayers = ref(6);
const newRoomTime = ref(60);
const newRoomTag = ref('Классика');

const filterTags = ['Все', 'Жизненно', 'Работа', 'Котики', '16+'];

const filteredRooms = computed(() => {
  return props.rooms.filter((r) => {
    const matchesSearch =
      r.name.toLowerCase().includes(searchTerm.value.toLowerCase()) ||
      r.hostName.toLowerCase().includes(searchTerm.value.toLowerCase());

    const matchesFilter = 
      activeFilter.value === 'Все' ? true : r.tag === activeFilter.value;

    return matchesSearch && matchesFilter;
  });
});

const handleCreateSubmit = (e: Event) => {
  e.preventDefault();
  const createdRoom: GameRoom = {
    // id: `room-${Date.now()}`,
    name: newRoomName.value.trim() || 'Новая комната с мемами',
    playerId: props.player.id,
    isPrivate: false,
    // hostName: props.player.nickname,
    // playersCount: 1,
    maxPlayers: newRoomMaxPlayers.value,
    // roundsCount: 5,
    // timeLimit: newRoomTime.value,
    // tag: newRoomTag.value,
    // status: 'waiting',
  };
  showCreateModal.value = false;
  props.onCreateRoom(createdRoom);
};
</script>

<template>
  <div class="max-w-7xl mx-auto px-4 py-6 sm:px-6 sm:py-8">
    <!-- Top Welcome & Subtitle -->
    <div class="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
      <div>
        <div class="flex items-center gap-2">
          <h1 class="text-2xl sm:text-3xl font-black tracking-tight text-[#242426]">
            ВЫБОР КОМНАТЫ
          </h1>
          <span class="bg-[#E4D976] border-2 border-[#242426] px-2.5 py-0.5 rounded-full text-xs font-bold text-[#242426] shadow-[2px_2px_0px_#242426]">
            ЭКРАН 2
          </span>
        </div>
        <p class="text-sm text-[#666259] font-medium mt-1">
          Выбери подходящую тусовку или создай свою комнату с блэкджеком и котами
        </p>
      </div>

      <!-- Player Profile Quick Pill -->
      <div class="flex items-center gap-3 bg-[#FAF7F2] border-2 border-[#242426] p-2 pr-4 rounded-2xl shadow-[3px_3px_0px_#242426] self-start md:self-auto">
        <AvatarGraphic :id="props.player.avatarId" size="sm" />
        <div>
          <div class="flex items-center gap-1.5">
            <span class="font-extrabold text-sm text-[#242426]">
              {{ props.player.nickname }}
            </span>
            <span class="text-[10px] bg-[#EAE5D9] px-1.5 py-0.5 rounded text-[#57534A] font-bold">
              В сети
            </span>
          </div>
          <p class="text-[11px] text-[#78746B] flex items-center gap-1">
            <span>Готов деградировать</span>
          </p>
        </div>
        <button
          @click="props.onEditProfile"
          title="Изменить аватар или ник"
          class="ml-1 text-xs font-bold text-[#555148] hover:text-[#242426] underline cursor-pointer"
        >
          Изменить
        </button>
      </div>
    </div>

    <!-- Main Grid: Left side controls + Right side rooms list -->
    <div class="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
      <!-- Left Column: Action Card & Filters -->
      <div class="lg:col-span-4 flex flex-col gap-5">
        <!-- Create Room Primary Button Card -->
        <div class="rounded-3xl border-2 border-[#242426] bg-[#FAF7F2] p-5 shadow-[4px_4px_0px_#242426]">
          <div class="flex items-center gap-2 mb-2">
            <Sparkles class="w-5 h-5 text-[#242426]" />
            <h2 class="font-extrabold text-base text-[#242426]">
              Своя компания?
            </h2>
          </div>
          <p class="text-xs text-[#66625A] mb-4">
            Создай приватную или открытую комнату, настрой количество раундов и позови друзей по коду.
          </p>

          <button
            type="button"
            id="create-room-button"
            @click="showCreateModal = true"
            class="w-full rounded-2xl border-2 border-[#242426] bg-[#E4D976] hover:bg-[#DDD166] active:translate-y-0.5 p-3.5 font-black text-sm text-[#242426] shadow-[3px_3px_0px_#242426] flex items-center justify-center gap-2 cursor-pointer transition-all"
          >
            <Plus class="w-5 h-5 stroke-[2.5]" />
            <span>СОЗДАТЬ КОМНАТУ</span>
          </button>
        </div>

        <!-- Quick Filter Pill List -->
        <div class="rounded-3xl border-2 border-[#242426] bg-[#FAF7F2] p-5 shadow-[4px_4px_0px_#242426]">
          <div class="flex items-center justify-between mb-3">
            <span class="text-xs font-bold uppercase tracking-wider text-[#4E4B44] flex items-center gap-1.5">
              <Filter class="w-3.5 h-3.5" />
              Категории
            </span>
            <span class="text-[11px] text-[#7A766D] font-medium">
              {{ filteredRooms.length }} доступно
            </span>
          </div>

          <div class="flex flex-wrap gap-2">
            <button
              v-for="tag in filterTags"
              :key="tag"
              @click="activeFilter = tag"
              :class="[
                'px-3 py-1.5 rounded-xl text-xs font-bold border transition-all cursor-pointer',
                activeFilter === tag
                  ? 'bg-[#242426] text-[#FAF7F2] border-[#242426] shadow-[2px_2px_0px_#242426]'
                  : 'bg-[#ECE8DE] text-[#4E4A42] border-[#242426]/30 hover:bg-[#E2DDD2]'
              ]"
            >
              {{ tag }}
            </button>
          </div>

        <!--
          <!-- Humorous Tip Card -->
          <div class="mt-5 pt-4 border-t border-[#242426]/15 text-xs text-[#5D5950] bg-[#F2EEE4] p-3 rounded-2xl border border-[#242426]/20">
            <p class="font-bold text-[#242426] mb-0.5 flex items-center gap-1">
              <span>💡 Мемный этикет:</span>
            </p>
            <p class="italic text-[11px]">
              «Если шутка не зашла, сделай вид, что это был сарказм над зумерами».
            </p>
          </div>
        </div>
      </div>
      -->

      <!-- Right Column: Room List -->
      <div class="lg:col-span-8 flex flex-col gap-4">
        <!-- Search bar & Refresh -->
        <div class="flex items-center gap-3">
          <div class="relative flex-1">
            <Search class="w-4 h-4 text-[#7A766D] absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
            <input
              type="text"
              v-model="searchTerm"
              placeholder="Поиск по названию или хосту..."
              class="w-full rounded-2xl border-2 border-[#242426] bg-[#FAF7F2] pl-10 pr-4 py-2.5 text-sm font-semibold text-[#242426] placeholder-[#9B958A] focus:outline-none focus:ring-2 focus:ring-[#242426] shadow-[2px_2px_0px_#242426]"
            />
          </div>

          <button
            @click="searchTerm = ''; activeFilter = 'Все'"
            title="Сбросить фильтры"
            class="p-2.5 rounded-2xl border-2 border-[#242426] bg-[#FAF7F2] hover:bg-[#EAE5D9] shadow-[2px_2px_0px_#242426] text-[#242426] cursor-pointer"
          >
            <RefreshCw class="w-4 h-4" />
          </button>
        </div>

        <!-- Rooms List -->
        <template v-if="filteredRooms.length === 0">
          <div class="flex flex-col gap-3">
            <div class="rounded-3xl border-2 border-dashed border-[#242426]/40 p-10 text-center bg-[#FAF7F2]/60">
              <p class="font-bold text-base text-[#4E4B43]">
                Комнаты не найдены :(
              </p>
              <p class="text-xs text-[#7A766E] mt-1 mb-4">
                Попробуйте изменить поисковый запрос или создайте свою!
              </p>
              <button
                @click="showCreateModal = true"
                class="px-4 py-2 rounded-xl border-2 border-[#242426] bg-[#E4D976] text-xs font-black shadow-[2px_2px_0px_#242426]"
              >
                Создать новую
              </button>
            </div>
          </div>
        </template>

        <template v-else>
          <div
            v-for="room in filteredRooms"
            :key="room.id"
            class="group rounded-3xl border-2 border-[#242426] bg-[#FAF7F2] p-4 sm:p-5 shadow-[4px_4px_0px_#242426] hover:shadow-[5px_5px_0px_#242426] transition-all flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4"
            :class="{
              'room-full': room.playersCount >= room.maxPlayers,
              'room-almost-full': room.playersCount === room.maxPlayers - 1
            }"
          >
            <!-- Left: Info -->
            <div class="flex-1">
              <div class="flex items-center gap-2 flex-wrap mb-1.5">
                <span class="font-extrabold text-base text-[#242426] group-hover:text-[#5A5128] transition-colors">
                  {{ room.name }}
                </span>

                <span class="text-[10px] font-extrabold px-2 py-0.5 rounded-full bg-[#EAE5D9] text-[#4A473E] border border-[#242426]/20">
                  {{ room.tag }}
                </span>

                <span
                  v-if="room.playersCount === room.maxPlayers - 1"
                  class="text-[10px] font-black px-2 py-0.5 rounded-full bg-[#E8BAA8] text-[#52291E] border border-[#242426]/30 flex items-center gap-1"
                >
                  <Flame class="w-3 h-3" />
                  Осталось 1 место!
                </span>
              </div>

              <!-- Subtitle Details -->
              <div class="flex items-center gap-4 text-xs text-[#636058] font-medium flex-wrap">
                <span class="flex items-center gap-1">
                  <span class="text-[#88847A]">Хост:</span>
                  <strong class="text-[#242426]">{{ room.hostName }}</strong>
                </span>
                <span class="flex items-center gap-1">
                  <Clock class="w-3.5 h-3.5 text-[#88847A]" />
                  <span>{{ room.timeLimit }} сек/ход</span>
                </span>
                <span>• {{ room.roundsCount }} раундов</span>
              </div>
            </div>

            <!-- Right: Player count and Join button -->
            <div class="flex items-center gap-3 w-full sm:w-auto justify-between sm:justify-end pt-2 sm:pt-0 border-t sm:border-t-0 border-[#242426]/10">
              <!-- Players Counter Chip -->
              <div class="flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-[#242426]/30 bg-[#ECE8DE]">
                <Users class="w-4 h-4 text-[#44413A]" />
                <span class="text-xs font-black text-[#242426]">
                  {{ room.playersCount }}
                </span>
                <span class="text-xs text-[#6D695F]">/ {{ room.maxPlayers }}</span>
              </div>

              <!-- Join Button -->
              <button
                type="button"
                :disabled="room.playersCount >= room.maxPlayers"
                @click="props.onJoinRoom(room)"
                :class="[
                  'px-4 py-2 rounded-xl border-2 border-[#242426] text-xs font-black transition-all flex items-center gap-1.5 cursor-pointer',
                  room.playersCount >= room.maxPlayers
                    ? 'bg-[#DDD9CE] text-[#868278] cursor-not-allowed shadow-none'
                    : 'bg-[#C8D7C5] hover:bg-[#B5C8B1] active:translate-y-0.5 text-[#242426] shadow-[3px_3px_0px_#242426]'
                ]"
              >
                <span>{{ room.playersCount >= room.maxPlayers ? 'Заполнено' : 'Залететь' }}</span>
                <ArrowRight v-if="room.playersCount < room.maxPlayers" class="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        </template>
      </div>
    </div>
  </div>

  <!-- Create Room Modal -->
  <div v-if="showCreateModal" class="fixed inset-0 z-50 bg-[#242426]/60 backdrop-blur-sm flex items-center justify-center p-4">
    <div class="w-full max-w-md bg-[#FAF7F2] border-2 border-[#242426] rounded-3xl p-6 shadow-[6px_6px_0px_#242426] relative animate-in fade-in zoom-in-95 duration-150">
      <h3 class="text-xl font-black text-[#242426] mb-1">
        Создать новую комнату
      </h3>
      <p class="text-xs text-[#66625A] mb-4">
        Задайте правила игры и количество мест для вашей пати
      </p>

      <form @submit.prevent="handleCreateSubmit" class="flex flex-col gap-4">
        <div>
          <label class="text-xs font-bold text-[#44413A] uppercase tracking-wide block mb-1">
            Название комнаты:
          </label>
          <input
            type="text"
            maxlength="36"
            v-model="newRoomName"
            class="w-full rounded-xl border-2 border-[#242426] bg-[#F5F2EA] px-3.5 py-2 text-sm font-bold text-[#242426] focus:outline-none focus:bg-[#FAF7F2]"
            required
          />
        </div>

        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="text-xs font-bold text-[#44413A] block mb-1">
              Макс. игроков:
            </label>
            <select
              v-model="newRoomMaxPlayers"
              class="w-full rounded-xl border-2 border-[#242426] bg-[#F5F2EA] px-3 py-2 text-sm font-bold text-[#242426]"
            >
              <option :value="4">4 игрока</option>
              <option :value="6">6 игроков</option>
              <option :value="8">8 игроков</option>
            </select>
          </div>

          <div>
            <label class="text-xs font-bold text-[#44413A] block mb-1">
              Время на ход:
            </label>
            <select
              v-model="newRoomTime"
              class="w-full rounded-xl border-2 border-[#242426] bg-[#F5F2EA] px-3 py-2 text-sm font-bold text-[#242426]"
            >
              <option :value="30">30 секунд</option>
              <option :value="45">45 секунд</option>
              <option :value="60">60 секунд</option>
            </select>
          </div>
        </div>

        <div>
          <label class="text-xs font-bold text-[#44413A] block mb-1">
            Тематика колоды:
          </label>
          <div class="grid grid-cols-3 gap-2">
            <button
              v-for="t in ['Классика', 'Офис', 'Котики']"
              :key="t"
              type="button"
              @click="newRoomTag = t"
              :class="[
                'py-1.5 text-xs font-bold rounded-xl border transition-all',
                newRoomTag === t
                  ? 'bg-[#E4D976] text-[#242426] border-[#242426] shadow-[2px_2px_0px_#242426]'
                  : 'bg-[#ECE8DE] text-[#55524B] border-[#242426]/30'
              ]"
            >
              {{ t }}
            </button>
          </div>
        </div>

        <div class="flex items-center gap-3 mt-4 pt-3 border-t border-[#242426]/15">
          <button
            type="button"
            @click="showCreateModal = false"
            class="flex-1 py-2.5 rounded-xl border-2 border-[#242426] bg-[#ECE8DE] font-bold text-xs text-[#44413A] hover:bg-[#E2DDD2]"
          >
            Отмена
          </button>
          <button
            type="submit"
            class="flex-1 py-2.5 rounded-xl border-2 border-[#242426] bg-[#E4D976] font-black text-xs text-[#242426] shadow-[2px_2px_0px_#242426] hover:bg-[#DDD166]"
          >
            Создать и войти →
          </button>
        </div>
      </form>
    </div>
  </div>
</template>