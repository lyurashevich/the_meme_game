<script setup lang="ts">
import { X, Palette, Type, Layout, ShieldCheck, Sparkles } from 'lucide-vue-next';

interface DesignSpecsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const props = defineProps<DesignSpecsModalProps>();
</script>

<template>
  <div
    v-if="props.isOpen"
    class="fixed inset-0 z-50 bg-[#242426]/60 backdrop-blur-sm flex items-center justify-center p-4"
  >
    <div
      class="w-full max-w-2xl bg-[#FAF7F2] border-[3px] border-[#242426] rounded-3xl p-6 sm:p-7 shadow-[6px_6px_0px_#242426] max-h-[90vh] overflow-y-auto"
    >
      <div class="flex items-center justify-between pb-3 border-b-2 border-[#242426]/15 mb-4">
        <div class="flex items-center gap-2">
          <div
            class="w-7 h-7 rounded-xl bg-[#E4D976] border-2 border-[#242426] flex items-center justify-center font-black text-xs"
          >
            ✦
          </div>
          <div>
            <h2 class="font-black text-lg text-[#242426] leading-tight">
              Концепция стиля «Что за мем»
            </h2>
            <p class="text-xs text-[#6E6A62]">
              Визуальный язык, типографика и архитектура 4-х экранов
            </p>
          </div>
        </div>
        <button
          @click="props.onClose"
          class="p-1.5 rounded-xl border-2 border-[#242426] bg-[#ECE8DE] hover:bg-[#E4D976] text-[#242426] transition-colors cursor-pointer"
        >
          <X class="w-4 h-4" />
        </button>
      </div>

      <div class="space-y-4 text-xs text-[#423F39] leading-relaxed">
        <!-- Section 1: Visual Identity -->
        <div class="p-3.5 rounded-2xl border-2 border-[#242426] bg-[#F4F1EA]">
          <h3 class="font-black text-sm text-[#242426] mb-1.5 flex items-center gap-1.5">
            <Sparkles class="w-4 h-4 text-[#8C7624]" />
            Вайб: «Ироничный постироничный интернет-юмор»
          </h3>
          <p>
            Интерфейс спроектирован с намеренно несерьезным, слегка наивным и обаятельно-нелепым характером. Мы отказались от агрессивного неонового гейминга и стерильного корпоративного SaaS в пользу теплого, крафтового инди-стиля с мемными стикерами, живыми деталями и ироничными подсказками.
          </p>
        </div>

        <!-- Section 2: Color Palette -->
        <div class="p-3.5 rounded-2xl border-2 border-[#242426] bg-[#F4F1EA]">
          <h3 class="font-black text-sm text-[#242426] mb-1.5 flex items-center gap-1.5">
            <Palette class="w-4 h-4 text-[#8C7624]" />
            Приглушенная палитра (без ядовитого неона)
          </h3>
          <div class="grid grid-cols-2 sm:grid-cols-4 gap-2 mt-2">
            <div class="p-2 rounded-xl border border-[#242426] bg-[#F4F1EA] text-center">
              <span class="font-extrabold text-[11px] block">Фон стола</span>
              <span class="text-[10px] text-[#69655D]">#F4F1EA (крафт)</span>
            </div>
            <div class="p-2 rounded-xl border border-[#242426] bg-[#E4D976] text-center">
              <span class="font-extrabold text-[11px] block">Горчичный</span>
              <span class="text-[10px] text-[#242426]">#E4D976 (акцент)</span>
            </div>
            <div class="p-2 rounded-xl border border-[#242426] bg-[#C8D7C5] text-center">
              <span class="font-extrabold text-[11px] block">Шалфей</span>
              <span class="text-[10px] text-[#304B2E]">#C8D7C5 (готовность)</span>
            </div>
            <div class="p-2 rounded-xl border border-[#242426] bg-[#E8BAA8] text-center">
              <span class="font-extrabold text-[11px] block">Терракота</span>
              <span class="text-[10px] text-[#552317]">#E8BAA8 (таймер)</span>
            </div>
          </div>
        </div>

        <!-- Section 3: Typography & Micro-UI -->
        <div class="p-3.5 rounded-2xl border-2 border-[#242426] bg-[#F4F1EA]">
          <h3 class="font-black text-sm text-[#242426] mb-1.5 flex items-center gap-1.5">
            <Type class="w-4 h-4 text-[#8C7624]" />
            Типографика и микро-детали
          </h3>
          <p>
            Шрифт <strong>Rubik</strong> с выразительными плотными начертаниями (600–900). Все плашки и кнопки имеют четкую обводку в 2px, легкий офсет теней (2–4px) и легкие микро-повороты карт (-2° до +2°), создающие ощущение настольной игры из реальных карточек.
          </p>
        </div>

        <!-- Section 4: 4-Screen Coherence -->
        <div class="p-3.5 rounded-2xl border-2 border-[#242426] bg-[#F4F1EA]">
          <h3 class="font-black text-sm text-[#242426] mb-1.5 flex items-center gap-1.5">
            <Layout class="w-4 h-4 text-[#8C7624]" />
            Единство всех 4-х экранов
          </h3>
          <ul class="list-disc pl-4 space-y-1">
            <li><strong>Экран 1:</strong> Минималистичный фокус на аватаре со стрелками переключения и вводе никнейма с кнопкой «ОК».</li>
            <li><strong>Экран 2:</strong> Сканируемый список комнат справа + панель создания комнаты и фильтров слева.</li>
            <li><strong>Экран 3:</strong> Игровой стол-плеймат с местами игроков, слотами под будущие карты, чатом и рукой карт.</li>
            <li><strong>Экран 4:</strong> Активная игра с крупной картой ситуации в центре, мемными картами игроков вокруг, таймером раунда и наглядным индикатором хода.</li>
          </ul>
        </div>
      </div>

      <div class="mt-5 pt-3 border-t border-[#242426]/15 flex justify-end">
        <button
          @click="props.onClose"
          class="px-5 py-2 rounded-xl border-2 border-[#242426] bg-[#E4D976] font-black text-xs text-[#242426] shadow-[2px_2px_0px_#242426] hover:bg-[#DDD166] cursor-pointer"
        >
          Понятно, закрыть
        </button>
      </div>
    </div>
  </div>
</template>
