import type { CSSProperties, ReactElement } from 'react';
import { AVATAR_OPTIONS } from '../avatars';

type AvatarSize = 'sm' | 'md' | 'lg' | 'xl';

const SIZE_CLASSES: Record<AvatarSize, string> = {
  sm: 'w-10 h-10',
  md: 'w-14 h-14',
  lg: 'w-24 h-24',
  xl: 'w-40 h-40 sm:w-48 sm:h-48',
};

// One drawing per avatar id (see AVATAR_OPTIONS for names and colors)
const DRAWINGS: Record<string, ReactElement> = {
  cat: (
    <svg viewBox="0 0 100 100" className="w-full h-full p-1.5" fill="none" xmlns="http://www.w3.org/2000/svg">
      {/* Cat ears */}
      <polygon points="22,35 15,10 40,25" fill="#D5CEC2" stroke="#242426" strokeWidth="3" strokeLinejoin="round" />
      <polygon points="26,30 20,15 36,24" fill="#E6A8A8" />
      <polygon points="78,35 85,10 60,25" fill="#D5CEC2" stroke="#242426" strokeWidth="3" strokeLinejoin="round" />
      <polygon points="74,30 80,15 64,24" fill="#E6A8A8" />
      {/* Cat face */}
      <ellipse cx="50" cy="56" rx="36" ry="32" fill="#FAF7F2" stroke="#242426" strokeWidth="3" />
      {/* Suspicious tiny eyes with slanting brows */}
      <line x1="28" y1="44" x2="42" y2="47" stroke="#242426" strokeWidth="3.5" strokeLinecap="round" />
      <ellipse cx="35" cy="50" rx="4" ry="2.5" fill="#242426" />
      <line x1="72" y1="44" x2="58" y2="47" stroke="#242426" strokeWidth="3.5" strokeLinecap="round" />
      <ellipse cx="65" cy="50" rx="4" ry="2.5" fill="#242426" />
      {/* Pink triangle nose */}
      <polygon points="50,60 46,56 54,56" fill="#D98E8E" stroke="#242426" strokeWidth="2" strokeLinejoin="round" />
      {/* Straight unimpressed mouth */}
      <path d="M 44 67 Q 50 65 56 67" stroke="#242426" strokeWidth="3" strokeLinecap="round" fill="none" />
      {/* Whiskers */}
      <line x1="16" y1="58" x2="34" y2="60" stroke="#242426" strokeWidth="2.5" strokeLinecap="round" />
      <line x1="14" y1="65" x2="33" y2="64" stroke="#242426" strokeWidth="2.5" strokeLinecap="round" />
      <line x1="84" y1="58" x2="66" y2="60" stroke="#242426" strokeWidth="2.5" strokeLinecap="round" />
      <line x1="86" y1="65" x2="67" y2="64" stroke="#242426" strokeWidth="2.5" strokeLinecap="round" />
    </svg>
  ),
  frog: (
    <svg viewBox="0 0 100 100" className="w-full h-full p-1.5" fill="none" xmlns="http://www.w3.org/2000/svg">
      {/* Frog eyes */}
      <circle cx="32" cy="30" r="16" fill="#A4C2A5" stroke="#242426" strokeWidth="3" />
      <circle cx="68" cy="30" r="16" fill="#A4C2A5" stroke="#242426" strokeWidth="3" />
      {/* Dark exhausted eye bags */}
      <path d="M 20 38 Q 32 46 44 38" stroke="#6F8870" strokeWidth="2.5" fill="none" />
      <path d="M 56 38 Q 68 46 80 38" stroke="#6F8870" strokeWidth="2.5" fill="none" />
      {/* Heavy pupils */}
      <ellipse cx="32" cy="30" rx="6" ry="7" fill="#242426" />
      <circle cx="30" cy="28" r="2" fill="#FAF7F2" />
      <ellipse cx="68" cy="30" rx="6" ry="7" fill="#242426" />
      <circle cx="66" cy="28" r="2" fill="#FAF7F2" />
      {/* Frog face */}
      <path
        d="M 16 48 C 16 35, 84 35, 84 48 C 88 74, 80 84, 50 84 C 20 84, 12 74, 16 48 Z"
        fill="#B3CFB4"
        stroke="#242426"
        strokeWidth="3"
      />
      {/* Melancholic wavy mouth */}
      <path
        d="M 28 66 Q 38 61 50 66 Q 62 71 72 65"
        stroke="#242426"
        strokeWidth="3.5"
        strokeLinecap="round"
        fill="none"
      />
      {/* Cheeks subtle blush */}
      <circle cx="24" cy="58" r="4" fill="#8FA890" opacity="0.6" />
      <circle cx="76" cy="58" r="4" fill="#8FA890" opacity="0.6" />
      {/* Nostrils */}
      <circle cx="46" cy="54" r="1.5" fill="#242426" />
      <circle cx="54" cy="54" r="1.5" fill="#242426" />
    </svg>
  ),
  capybara: (
    <svg viewBox="0 0 100 100" className="w-full h-full p-1.5" fill="none" xmlns="http://www.w3.org/2000/svg">
      {/* Capybara Head shape (boxy snout) */}
      <path
        d="M 26 36 C 26 26, 74 26, 74 36 L 76 68 C 76 80, 24 80, 24 68 Z"
        fill="#BC9F7D"
        stroke="#242426"
        strokeWidth="3"
      />
      {/* Tiny ears */}
      <circle cx="22" cy="36" r="6" fill="#A58766" stroke="#242426" strokeWidth="2.5" />
      <circle cx="78" cy="36" r="6" fill="#A58766" stroke="#242426" strokeWidth="2.5" />
      {/* Orange on head */}
      <circle cx="50" cy="22" r="11" fill="#E89B48" stroke="#242426" strokeWidth="2.5" />
      <path d="M 50 11 Q 54 8 56 6" stroke="#242426" strokeWidth="2" strokeLinecap="round" />
      <ellipse cx="55" cy="8" rx="3" ry="1.5" fill="#6B8E5E" />
      {/* Zen closed slit eyes */}
      <path d="M 32 46 Q 38 49 44 46" stroke="#242426" strokeWidth="3.5" strokeLinecap="round" fill="none" />
      <path d="M 56 46 Q 62 49 68 46" stroke="#242426" strokeWidth="3.5" strokeLinecap="round" fill="none" />
      {/* Wide snout */}
      <ellipse cx="50" cy="65" rx="16" ry="10" fill="#A78869" stroke="#242426" strokeWidth="2" />
      {/* Nostrils & chill mouth */}
      <ellipse cx="44" cy="63" rx="2.5" ry="1.5" fill="#242426" />
      <ellipse cx="56" cy="63" rx="2.5" ry="1.5" fill="#242426" />
      <path d="M 44 71 Q 50 73 56 71" stroke="#242426" strokeWidth="3" strokeLinecap="round" fill="none" />
    </svg>
  ),
  doge: (
    <svg viewBox="0 0 100 100" className="w-full h-full p-1.5" fill="none" xmlns="http://www.w3.org/2000/svg">
      {/* Doge ears */}
      <polygon points="18,36 12,12 36,22" fill="#DAB778" stroke="#242426" strokeWidth="3" strokeLinejoin="round" />
      <polygon points="82,36 88,12 64,22" fill="#DAB778" stroke="#242426" strokeWidth="3" strokeLinejoin="round" />
      {/* Doge face */}
      <ellipse cx="50" cy="54" rx="35" ry="32" fill="#E4C88E" stroke="#242426" strokeWidth="3" />
      <ellipse cx="50" cy="64" rx="22" ry="18" fill="#F8EED7" stroke="#242426" strokeWidth="2" />
      {/* Side eye eyebrow */}
      <path d="M 28 38 Q 36 34 42 40" stroke="#242426" strokeWidth="3" strokeLinecap="round" fill="none" />
      <path d="M 58 40 Q 64 34 72 38" stroke="#242426" strokeWidth="3" strokeLinecap="round" fill="none" />
      {/* Side eye pupils looking right */}
      <ellipse cx="36" cy="46" rx="6" ry="7" fill="#FAF7F2" stroke="#242426" strokeWidth="2.5" />
      <circle cx="39" cy="46" r="3.5" fill="#242426" />
      <ellipse cx="64" cy="46" rx="6" ry="7" fill="#FAF7F2" stroke="#242426" strokeWidth="2.5" />
      <circle cx="67" cy="46" r="3.5" fill="#242426" />
      {/* Nose */}
      <polygon points="50,60 45,55 55,55" fill="#242426" stroke="#242426" strokeWidth="2" strokeLinejoin="round" />
      {/* W-mouth */}
      <path
        d="M 42 66 Q 46 70 50 67 Q 54 70 58 66"
        stroke="#242426"
        strokeWidth="3"
        strokeLinecap="round"
        fill="none"
      />
    </svg>
  ),
  hamster: (
    <svg viewBox="0 0 100 100" className="w-full h-full p-1.5" fill="none" xmlns="http://www.w3.org/2000/svg">
      {/* Huge round cheeks */}
      <circle cx="28" cy="30" r="11" fill="#E0B69F" stroke="#242426" strokeWidth="2.5" />
      <circle cx="72" cy="30" r="11" fill="#E0B69F" stroke="#242426" strokeWidth="2.5" />
      <circle cx="50" cy="56" r="34" fill="#E8C7B4" stroke="#242426" strokeWidth="3" />
      {/* Puffy chubby cheeks */}
      <circle cx="28" cy="65" r="16" fill="#F4DDD2" stroke="#242426" strokeWidth="2" />
      <circle cx="72" cy="65" r="16" fill="#F4DDD2" stroke="#242426" strokeWidth="2" />
      {/* Massive round stressed eyes */}
      <circle cx="34" cy="48" r="10" fill="#242426" />
      <circle cx="32" cy="45" r="3.5" fill="#FFFFFF" />
      <circle cx="37" cy="50" r="1.5" fill="#FFFFFF" />
      <circle cx="66" cy="48" r="10" fill="#242426" />
      <circle cx="64" cy="45" r="3.5" fill="#FFFFFF" />
      <circle cx="69" cy="50" r="1.5" fill="#FFFFFF" />
      {/* Tiny shock mouth :O */}
      <ellipse cx="50" cy="66" rx="4" ry="5.5" fill="#B95C5C" stroke="#242426" strokeWidth="2" />
      {/* Little hands clasped in existential angst */}
      <ellipse cx="44" cy="80" rx="5" ry="4" fill="#F4DDD2" stroke="#242426" strokeWidth="2" />
      <ellipse cx="56" cy="80" rx="5" ry="4" fill="#F4DDD2" stroke="#242426" strokeWidth="2" />
    </svg>
  ),
  pigeon: (
    <svg viewBox="0 0 100 100" className="w-full h-full p-1.5" fill="none" xmlns="http://www.w3.org/2000/svg">
      {/* Pigeon Head */}
      <ellipse cx="50" cy="48" rx="28" ry="32" fill="#9BA6B2" stroke="#242426" strokeWidth="3" />
      {/* Green iridescent neck feather patch */}
      <path d="M 28 62 C 34 76, 66 76, 72 62 Z" fill="#889F8F" stroke="#242426" strokeWidth="2" />
      {/* Absolutely blank orange eyes */}
      <circle cx="33" cy="44" r="8" fill="#E67E48" stroke="#242426" strokeWidth="2.5" />
      <circle cx="33" cy="44" r="3" fill="#242426" />
      <circle cx="67" cy="44" r="8" fill="#E67E48" stroke="#242426" strokeWidth="2.5" />
      <circle cx="67" cy="44" r="3" fill="#242426" />
      {/* Tiny sharp yellow beak */}
      <polygon points="50,56 42,50 58,50" fill="#DEB14B" stroke="#242426" strokeWidth="2.5" strokeLinejoin="round" />
      {/* A tiny crumb / question mark above */}
      <circle cx="50" cy="18" r="2.5" fill="#B38F60" />
    </svg>
  ),
};

interface AvatarProps {
  id: string;
  size?: AvatarSize;
  className?: string;
  style?: CSSProperties;
}

export default function Avatar({ id, size = 'md', className = '', style }: AvatarProps) {
  const option = AVATAR_OPTIONS.find((avatar) => avatar.id === id) ?? AVATAR_OPTIONS[0];

  return (
    <div
      className={`relative inline-flex items-center justify-center rounded-2xl border-2 border-[#242426] shadow-[2px_2px_0px_#242426] overflow-hidden select-none transition-transform ${SIZE_CLASSES[size]} ${className}`}
      style={{ backgroundColor: option.bgColor, ...style }}
    >
      {DRAWINGS[option.id]}
    </div>
  );
}
