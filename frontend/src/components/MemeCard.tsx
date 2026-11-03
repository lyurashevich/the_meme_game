import { useState } from 'react';
import type { MemeCard as MemeCardData } from '../protocol';

type CardSize = 'sm' | 'md';

const SIZE_CLASSES: Record<CardSize, string> = {
  sm: 'w-32 h-44',
  md: 'w-40 h-56 sm:w-44 sm:h-60',
};

interface MemeCardProps {
  card?: MemeCardData; // no card: face down (we only know that someone has played)
  size?: CardSize;
  isSelected?: boolean;
  isWinner?: boolean;
  caption?: string; // shown under the picture, e.g. who played the card
  onClick?: () => void; // no handler: the card can't be clicked
  className?: string;
}

export default function MemeCard({
  card,
  size = 'sm',
  isSelected = false,
  isWinner = false,
  caption,
  onClick,
  className = '',
}: MemeCardProps) {
  const base = `relative shrink-0 flex flex-col rounded-2xl border-2 border-[#242426] p-2 select-none transition-all duration-200 ${SIZE_CLASSES[size]} ${className}`;

  if (!card) {
    return (
      <div className={`${base} bg-[#D7D3C8] text-[#242426] shadow-[3px_3px_0px_#242426]`}>
        <div className="flex items-center justify-between text-[10px] font-bold tracking-wider uppercase opacity-70 px-0.5">
          <span>ЧТО ЗА МЕМ</span>
          <span>✦</span>
        </div>
        <div className="flex-1 mt-1.5 rounded-xl border border-dashed border-[#242426]/30 bg-[#C8C2B4] flex flex-col items-center justify-center p-2 text-center relative overflow-hidden">
          <div className="text-3xl mb-1 opacity-80">🤫</div>
          <span className="text-[12px] font-bold text-[#3B3A36]">Карта рубашкой</span>
          {/* Subtle diagonal lines */}
          <div className="absolute inset-0 opacity-5 pointer-events-none bg-[repeating-linear-gradient(45deg,#000,#000_2px,transparent_2px,transparent_8px)]" />
        </div>
      </div>
    );
  }

  const highlight = isWinner
    ? 'ring-4 ring-[#C8D7C5] shadow-[5px_5px_0px_#242426]'
    : isSelected
      ? 'ring-4 ring-[#E4D976] -translate-y-3 shadow-[5px_5px_0px_#242426]'
      : onClick
        ? 'shadow-[3px_3px_0px_#242426] hover:-translate-y-2 hover:shadow-[4px_4px_0px_#242426] cursor-pointer'
        : 'shadow-[3px_3px_0px_#242426]';

  return (
    // A real <button> can be reached with Tab and pressed with Enter; disabled when there's nothing to do
    <button
      type="button"
      onClick={onClick}
      disabled={!onClick}
      className={`${base} ${highlight} bg-[#FAF7F2] text-left disabled:cursor-default`}
    >
      <div className="flex items-center justify-between text-[10px] font-bold text-[#55524B] px-0.5">
        <span className="uppercase tracking-wider">РЕАКЦИЯ</span>
        <span className="px-1.5 py-0.5 rounded bg-[#EAE5D9] text-[#242426]">#МЕМ</span>
      </div>

      <div className="flex-1 mt-1.5 rounded-xl border border-[#242426] overflow-hidden bg-[#EBE7DF]">
        <MemeImage key={card.image_url} url={card.image_url} />
      </div>

      {caption && <div className="mt-1.5 text-center text-[11px] text-[#55524B] font-semibold truncate">{caption}</div>}

      {(isSelected || isWinner) && (
        <div className="absolute -top-2.5 -right-2.5 w-6 h-6 rounded-full bg-[#E4D976] border-2 border-[#242426] flex items-center justify-center text-xs font-black shadow-[1px_1px_0px_#242426]">
          {isWinner ? '★' : '✓'}
        </div>
      )}
    </button>
  );
}

// The picture comes from the media storage; if it can't be loaded, show a stub instead of a broken image
function MemeImage({ url }: { url: string }) {
  const [failed, setFailed] = useState(false);

  if (failed) {
    return (
      <div className="w-full h-full flex flex-col items-center justify-center text-center p-2 text-[#5E5B53]">
        <span className="text-2xl">🖼️</span>
        <span className="text-[10px] font-bold mt-1">Картинка не загрузилась</span>
      </div>
    );
  }

  return (
    <img src={url} alt="Мем" loading="lazy" onError={() => setFailed(true)} className="w-full h-full object-contain" />
  );
}
