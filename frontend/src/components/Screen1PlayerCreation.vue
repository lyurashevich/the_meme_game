<script setup lang="ts">
import { AVATAR_OPTIONS } from '../avatars';
import AvatarGraphic from './Avatars.vue';
import type { PlayerProfile } from './types';
import { ChevronLeft, ChevronRight, Dices, Sparkles, Check, Smile } from 'lucide-vue-next';
import { ref } from 'vue';

interface Screen1Props {
  player: PlayerProfile;
  onUpdatePlayer: (profile: Partial<PlayerProfile>) => void;
  onConfirm: () => void;
}

const FUN_NICKNAMES = [
  'Дед_Инсайд',
  'Кринж_Мастер',
  'Кот_В_Шоке',
  'Капибара_Босс',
  'Пятничный_Баг',
  'Толян_Мемолог',
  'Чайный_Пакет',
  'Главный_Клоун',
  'Постиронист',
];

const props = defineProps<Screen1Props>();

const currentAvatarIndex = Math.max(0, AVATAR_OPTIONS.findIndex((a) => a.id === props.player.avatarId));

const inputNick = ref(props.player.nickname || 'Мемный чел');
const isConfirmedAnim = ref(false);

const handlePrevAvatar = () => {
    const prevIndex =
      currentAvatarIndex === 0 ? AVATAR_OPTIONS.length - 1 : currentAvatarIndex - 1;
    props.onUpdatePlayer({ avatarId: AVATAR_OPTIONS[prevIndex].id });
};

const handleNextAvatar = () => {
    const nextIndex =
      currentAvatarIndex === AVATAR_OPTIONS.length - 1 ? 0 : currentAvatarIndex + 1;
    props.onUpdatePlayer({ avatarId: AVATAR_OPTIONS[nextIndex].id });
};

const handleRandomNick = () => {
    const random = FUN_NICKNAMES[Math.floor(Math.random() * FUN_NICKNAMES.length)];
    inputNick.value = random;
    props.onUpdatePlayer({ nickname: random });
};

const handleConfirmClick = (e: Event) => {
    e.preventDefault();
    const finalNick = inputNick.value.trim() || 'Анонимный_Мем';
    props.onUpdatePlayer({ nickname: finalNick });
    isConfirmedAnim.value = true;
    setTimeout(() => {
      props.onConfirm();
    }, 300);};

const currentAvatar = AVATAR_OPTIONS[currentAvatarIndex] || AVATAR_OPTIONS[0];
</script>

<template>
  <div class="relative min-h-[calc(100vh-65px)] flex flex-col items-center justify-center p-4 sm:p-6 bg-[#F4F1EA]">
    <!-- Decorative subtle background doodles/quirky stickers -->
    <div class="absolute top-8 left-8 hidden lg:block opacity-40 select-none pointer-events-none -rotate-6">
      <div class="border-2 border-dashed border-[#242426]/40 rounded-xl px-3 py-1.5 text-xs font-bold text-[#55524B] bg-[#ECE8DE]">
        «Мемы спасут мир (но это не точно)»
      </div>
    </div>
    <div class="absolute bottom-8 right-8 hidden lg:block opacity-40 select-none pointer-events-none rotate-3">
      <div class="border-2 border-dashed border-[#242426]/40 rounded-xl px-3 py-1.5 text-xs font-bold text-[#55524B] bg-[#ECE8DE]">
        Экран 1: Профиль игрока
      </div>
    </div>

    <!-- Main Centered Container -->
    <div class="w-full max-w-md mx-auto flex flex-col items-center">
      <!-- Game Title & Slogan -->
      <div class="text-center mb-6 select-none">
        <div class="inline-block bg-[#E4D976] border-2 border-[#242426] px-3.5 py-1 rounded-full text-xs font-extrabold uppercase tracking-widest text-[#242426] shadow-[2px_2px_0px_#242426] mb-3 -rotate-1">
          Карточная веб-игра
        </div>
        <h1 class="text-4xl sm:text-5xl font-black tracking-tight text-[#242426] leading-none">
          <!--ЧТО ЗА МЕМ?-->
          СИТУАЦИИ
        </h1>
        <p class="mt-2 text-sm text-[#66635C] font-medium">
          Создай своего персонажа перед входом в комнату
        </p>
      </div>

      <!-- Profile Creation Card -->
      <div class="w-full rounded-3xl border-2 border-[#242426] bg-[#FAF7F2] p-6 sm:p-8 shadow-[5px_5px_0px_#242426] flex flex-col items-center relative">
        <!-- Subtle top badge -->
        <div class="absolute -top-3.5 bg-[#FAF7F2] border-2 border-[#242426] px-3 py-0.5 rounded-full text-[11px] font-bold text-[#44423E] shadow-[2px_2px_0px_#242426]">
          ШАГ 1 ИЗ 4 • ВЫБОР АВАТАРА
        </div>

        <!-- Central Avatar Selector with Left & Right Arrows -->
        <div class="flex items-center justify-center gap-4 sm:gap-6 my-4 w-full">
          <!-- Left Arrow Button -->
          <button
            type="button"
            @click="handlePrevAvatar"
            aria-label="Предыдущий аватар"
            class="w-12 h-12 rounded-2xl border-2 border-[#242426] bg-[#ECE8DE] hover:bg-[#E4D976] active:translate-y-0.5 shadow-[3px_3px_0px_#242426] flex items-center justify-center transition-all cursor-pointer group"
          >
            <ChevronLeft class="w-6 h-6 text-[#242426] group-hover:-translate-x-0.5 transition-transform" />
          </button>

          <!-- Avatar Display Container -->
          <div class="flex flex-col items-center">
            <div class="relative group cursor-pointer" @click="handleNextAvatar" title="Нажмите, чтобы сменить">
              <AvatarGraphic
                :id="currentAvatar.id"
                size="xl"
                class="hover:scale-[1.02] transition-transform"
              />
              <span class="absolute -bottom-2 -right-2 bg-[#242426] text-[#FAF7F2] text-[10px] font-bold px-2 py-0.5 rounded-md border border-[#FAF7F2]">
                {{ currentAvatarIndex + 1 }}/{{ AVATAR_OPTIONS.length }}
              </span>
            </div>
          </div>

           <!-- Right Arrow Button -->
           <button
             type="button"
             @click="handleNextAvatar"
             aria-label="Следующий аватар"
             class="w-12 h-12 rounded-2xl border-2 border-[#242426] bg-[#ECE8DE] hover:bg-[#E4D976] active:translate-y-0.5 shadow-[3px_3px_0px_#242426] flex items-center justify-center transition-all cursor-pointer group"
           >
           <ChevronRight class="w-6 h-6 text-[#242426] group-hover:translate-x-0.5 transition-transform" />
         </button>
        </div>

        <!-- Avatar Name & Humor Mood Pill -->
        <div class="text-center mt-1 mb-5">
          <h3 class="font-extrabold text-lg text-[#242426]">
            {{ currentAvatar.name }}
          </h3>
          <p class="text-xs text-[#5D5950] italic mt-0.5 px-4 font-medium">
            {{ currentAvatar.mood }}
          </p>
        </div>

        <!-- Nickname Input Form -->
        <form @submit="handleConfirmClick" class="w-full flex flex-col gap-4">
          <div>
            <div class="flex items-center justify-between mb-1.5 px-1">
              <label
                for="nickname-input"
                class="text-xs font-bold uppercase tracking-wider text-[#4E4B44]"
              >
                Твой никнейм в игре:
              </label>
              <button
                type="button"
                @click="handleRandomNick"
                class="text-xs font-bold text-[#6D685E] hover:text-[#242426] flex items-center gap-1 cursor-pointer transition-colors"
                title="Случайный никнейм"
              >
                <Dices class="w-3.5 h-3.5" />
                <span>Случайный</span>
              </button>
            </div>

            <div class="relative">
              <input
                id="nickname-input"
                type="text"
                maxLength="18"
                v-model="inputNick"
                @input="props.onUpdatePlayer({ nickname: inputNick })"
                placeholder="Введи никнейм..."
                class="w-full rounded-2xl border-2 border-[#242426] bg-[#F5F2EA] px-4 py-3 text-base font-bold text-[#242426] placeholder-[#9E988D] focus:outline-none focus:bg-[#FAF7F2] focus:ring-2 focus:ring-[#242426] shadow-[2px_2px_0px_#242426] transition-all"
              />
            </div>
          </div>

          <!-- OK Confirmation Button -->
          <button
            type="submit"
            id="confirm-player-button"
                :class="[
                  'w-full mt-2 rounded-2xl border-2 border-[#242426] py-3.5 px-6 font-black text-base text-[#242426] shadow-[4px_4px_0px_#242426] transition-all cursor-pointer flex items-center justify-center gap-2',
                  isConfirmedAnim
                    ? 'bg-[#C8D7C5] translate-y-1 shadow-[1px_1px_0px_#242426]'
                    : 'bg-[#E4D976] hover:bg-[#DDD166] active:translate-y-1 active:shadow-[1px_1px_0px_#242426]'
                ]"
          >
            <template v-if="isConfirmedAnim">
              <Check class="w-5 h-5" />
              <span>ГОТОВО! ПЕРЕХОДИМ...</span>
            </template>

            <template v-else>
              <span>ОК</span>
              <span class="text-sm font-semibold opacity-75">-> к комнатам</span>
            </template>
          </button>
        </form>

        <!-- Micro-humor footer detail -->
        <div class="mt-5 pt-3 border-t border-[#242426]/15 w-full flex items-center justify-between text-[11px] text-[#78746B]">
          <span class="flex items-center gap-1">
            <Smile class="w-3.5 h-3.5" />
            Без регистрации и смс
          </span>
          <span>Статус: готов шутить</span>
        </div>
      </div>

      <!-- Small hint for mockups -->
      <p class="mt-4 text-xs text-[#7A766E] text-center max-w-xs">
        Нажми <strong>«ОК»</strong>, чтобы подтвердить профиль и перейти к выбору комнаты (Экран 2).
      </p>
    </div>
  </div>
</template>
