<script setup lang="ts">
import type { ScreenId } from '../types';
import { Sparkles, Layers, ChevronLeft, ChevronRight, Info } from 'lucide-vue-next';

interface MockupHeaderProps {
  currentScreen: ScreenId;
  onSelectScreen: (screen: ScreenId) => void;
  onToggleSpecs: () => void;
}

const props = defineProps<MockupHeaderProps>();

const screens: {
    id: ScreenId;
    number: number;
    title: string;
    subtitle: string;
}[] = [
  {
    id: 'screen1',
    number: 1,
    title: 'Создание игрока',
    subtitle: 'Аватар и никнейм',
 },
  {
    id: 'screen2',
    number: 2,
    title: 'Выбор комнаты',
    subtitle: 'Лобби-лист и создание',
  },
  {
    id: 'screen3',
    number: 3,
    title: 'Лобби до начала',
    subtitle: 'Игровой стол и чат',
  },
  {
    id: 'screen4',
    number: 4,
    title: 'Активная игра',
    subtitle: 'Ситуация, мемы, таймер',
  },
];

const currentIndex = screens.findIndex(
    (s) => s.id === props.currentScreen
);

const handlePrev = () => {
  if (currentIndex > 0) {
    props.onSelectScreen(screens[currentIndex - 1].id);
  }
};

const handleNext = () => {
  if (currentIndex < screens.length - 1) {
    props.onSelectScreen(screens[currentIndex + 1].id);
  }
};
</script>

<template>
  <header class="sticky top-0 z-50 border-b-2 border-[#242426] bg-[#ECE8DE] px-4 py-2.5 shadow-sm">
    <div class="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-3">
      <!-- Logo and Game identity -->
      <div class="flex items-center gap-3 w-full md:w-auto justify-between md:justify-start">
        <div class="flex items-center gap-2">
          <div class="w-8 h-8 rounded-xl border-2 border-[#242426] bg-[#E4D976] shadow-[2px_2px_0px_#242426] flex items-center justify-center font-black text-sm">
            <!--М?-->C?
          </div>

          <div>
            <div class="flex items-center gap-1.5">
              <span class="font-extrabold text-base tracking-tight text-[#242426]">
                <!--ЧТО ЗА МЕМ-->СИТУАЦИИ
              </span>
              <span class="text-[10px] px-1.5 py-0.2 rounded font-bold uppercase tracking-wider bg-[#242426] text-[#FAF7F2]">
                <!--UI Mockups-->online
              </span>
            </div>
            <p class="text-[11px] text-[#636058] font-medium hidden sm:block">
              <!--Мультиплеерная карточная игра • 4 экрана-->
              Мультиплеерная карточная игра
            </p>
          </div>
        </div>

        <button
          @click="props.onToggleSpecs"
          class="md:hidden flex items-center gap-1 text-xs font-semibold px-2.5 py-1.5 rounded-lg border border-[#242426] bg-[#FAF7F2] hover:bg-[#EAE5D9] transition-colors"
        >
          <Info class="w-3.5 h-3.5" />
          <span>Стиль</span>
        </button>
      </div>

      <!-- 4 Screens Switcher Navigation -->
      <nav class="flex items-center gap-1.5 bg-[#DFD9CD] p-1 rounded-xl border border-[#242426]/30 overflow-x-auto max-w-full">
        <button v-for="s in screens"
          :key="s.id"
          @click="props.onSelectScreen(s.id)"
          :class="`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition-all whitespace-nowrap cursor-pointer ${
            props.currentScreen === s.id
              ? 'bg-[#FAF7F2] text-[#242426] border border-[#242426] shadow-[2px_2px_0px_#242426]'
              : 'text-[#58554E] hover:text-[#242426] hover:bg-[#ECE8DE]'
          }`"
          >
          <span
            :class="`w-4 h-4 rounded-full text-[10px] flex items-center justify-center font-black ${
              props.currentScreen === s.id
                ? 'bg-[#E4D976] text-[#242426]'
                : 'bg-[#CAC3B4] text-[#4F4C45]'
              }`"
            >
              {{ s.number }}
          </span>

          <span>{{ s.title }}</span>
        </button>
      </nav>

      <!-- Quick Stepper + Specs button -->
      <div class="hidden md:flex items-center gap-2">
        <div class="flex items-center gap-1 border border-[#242426]/20 bg-[#FAF7F2] rounded-lg p-0.5">
          <button
            @click="handlePrev"
            :disabled="currentIndex === 0"
            title="Предыдущий экран"
            class="p-1 rounded hover:bg-[#EAE5D9] disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
          >
            <ChevronLeft class="w-4 h-4 text-[#242426]" />
          </button>
          <span class="text-[11px] font-bold px-1.5 text-[#55524B]">
            {{ currentIndex + 1 }} / {{ screens.length }}
          </span>
          <button
            @click="handleNext"
            :disabled="currentIndex === screens.length - 1"
            title="Следующий экран"
            class="p-1 rounded hover:bg-[#EAE5D9] disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
          >
            <ChevronRight class="w-4 h-4 text-[#242426]" />
          </button>
        </div>

        <button
          @click="props.onToggleSpecs"
          class="flex items-center gap-1.5 text-xs font-bold px-3 py-1.5 rounded-xl border-2 border-[#242426] bg-[#FAF7F2] shadow-[2px_2px_0px_#242426] hover:bg-[#E4D976] hover:shadow-[3px_3px_0px_#242426] transition-all cursor-pointer"
        >
          <Sparkles class="w-3.5 h-3.5 text-[#242426]" />
          <span>Концепт стиля</span>
        </button>
      </div>
    </div>
  </header>
</template>