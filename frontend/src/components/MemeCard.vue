<script setup lang="ts">
import type { MemeCardData } from '../types';
import AvatarGraphic from './Avatars.vue';

interface MemeCardProps {
  card: MemeCardData;
  isSelected?: boolean;
  isPlayable?: boolean;
  isRevealed?: boolean;
  playerName?: string;
  votesCount?: number;
  onClick?: () => void;
  size?: 'sm' | 'md' | 'lg';
  rotation?: string;
  className?: string;
}

const props = defineProps<MemeCardProps>();

// Face up card
const sizeStyles = {
  sm: 'w-32 h-44 text-xs p-2.5',
  md: 'w-44 sm:w-48 h-64 sm:h-68 text-sm p-3.5',
  lg: 'w-56 h-76 p-4 text-base',
};
</script>

<template>
  <div v-if="!props.isRevealed"
    @click="props.onClick"
      :class="`relative flex flex-col justify-between items-center rounded-2xl border-2 border-[#242426] bg-[#D7D3C8] text-[#242426] p-3 shadow-[3px_3px_0px_#242426] transition-all duration-200 select-none ${
          props.size === 'sm' ? 'w-32 h-44' : 'w-40 h-56'
        } ${props.rotation} ${props.className}`"
    >
    <div class="w-full flex items-center justify-between text-[11px] font-bold tracking-wider uppercase opacity-70">
      <span>ЧТО ЗА МЕМ</span>
      <span class="text-xs">✦</span>
    </div>

    <!-- Patterned card back -->
    <div class="w-full flex-1 my-2 rounded-xl border border-dashed border-[#242426]/30 bg-[#C8C2B4] flex flex-col items-center justify-center p-2 text-center relative overflow-hidden">
      <div class="text-3xl select-none mb-1 opacity-80">🤫</div>
      <span class="text-[12px] font-bold text-[#3B3A36]">Карта рубашкой</span>
      <span class="text-[10px] text-[#5E5B53] mt-0.5">Ждёт вскрытия ведущим</span>
    <!-- Subtle diagonal lines -->
    <div class="absolute inset-0 opacity-5 pointer-events-none bg-[repeating-linear-gradient(45deg,#000,#000_2px,transparent_2px,transparent_8px)]" />      </div>

    <div v-if="props.playerName" class="w-full py-1 px-2 rounded-lg bg-[#242426] text-[#FAF7F2] text-[11px] font-semibold truncate text-center">
      {{ props.playerName }}
    </div>
  </div>

  <div v-else
    @click="props.onClick"
    :class="`group relative flex flex-col justify-between rounded-2xl border-2 border-[#242426] shadow-[3px_3px_0px_#242426] transition-all duration-200 select-none bg-[#FAF7F2] ${
      sizeStyles[props.size]
      } ${
      props.isSelected
        ? 'ring-4 ring-[#E4D976] -translate-y-3 shadow-[5px_5px_0px_#242426]'
        : props.isPlayable
        ? 'hover:-translate-y-2 hover:shadow-[4px_4px_0px_#242426] cursor-pointer'
        : ''
    } ${props.rotation} ${props.className}`"
  >
      <!-- Top Card Bar -->
    <div class="flex items-center justify-between gap-1 text-[11px] font-bold text-[#55524B]">
      <span class="truncate uppercase tracking-wider">РЕАКЦИЯ</span>
        <span v-if="props.votesCount !== undefined && props.votesCount > 0" class="bg-[#E4D976] text-[#242426] px-1.5 py-0.5 rounded-full border border-[#242426] text-[10px] font-bold flex items-center gap-0.5">
          ★ {{ props.votesCount }}
        </span>
      <span class="text-[10px] px-1.5 py-0.5 rounded bg-[#EAE5D9] text-[#242426]">
        #МЕМ
      </span>
    </div>

    <!-- Card Artwork Illustration (Subtle indie funny meme) -->
    <div
      class="my-2 flex-1 rounded-xl border border-[#242426] flex flex-col items-center justify-center p-2 relative overflow-hidden"
      :style="{ backgroundColor: props.card.colorTheme || '#EBE7DF' }"
    >
      <AvatarGraphic :id="props.card.memeType" size="md" class="border-none shadow-none" />
      <p class="mt-1 text-center font-extrabold text-[12px] leading-tight text-[#242426] line-clamp-2 px-1">
        {{ props.card.title }}
      </p>
    </div>

    <!-- Card Caption / Punchline -->
    <div class="bg-[#F0ECE2] rounded-lg p-2 border border-[#242426]/20">
      <p class="text-[11px] sm:text-[12px] font-medium leading-snug text-[#343230] text-center">
        {{ props.card.caption }}
      </p>
    </div>

    <div v-if="props.playerName" class="mt-1 flex items-center justify-center gap-1 text-[11px] text-[#55524B] font-semibold truncate">
      <span>от</span> <span class="text-[#242426] font-bold">{{ props.playerName }}</span>
    </div>

    <!-- Selection check indicator -->
    <div v-if="props.isSelected" class="absolute -top-2.5 -right-2.5 w-6 h-6 rounded-full bg-[#E4D976] border-2 border-[#242426] flex items-center justify-center text-xs font-black shadow-[1px_1px_0px_#242426]">
      ✓
    </div>
  </div>
</template>
