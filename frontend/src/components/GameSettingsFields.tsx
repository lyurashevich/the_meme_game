import { Clock, Sparkles, Trophy } from 'lucide-react';
import type { ReactNode } from 'react';
import { ROUND_TIME_LIMITS, type GameSettings } from '../protocol';

const MAX_ROUNDS_OPTIONS = [null, 5, 10, 15, 20];
const SCORE_TO_WIN_OPTIONS = [null, 3, 5, 10];

interface GameSettingsFieldsProps {
  settings: GameSettings;
  disabled?: boolean; // everybody but the owner only sees them
  onChange: (settings: GameSettings) => void;
}

// Time per turn and the limits; used when creating a room and in the lobby's settings window
export default function GameSettingsFields({ settings, disabled = false, onChange }: GameSettingsFieldsProps) {
  // The server expects all the settings at once, so pass on the current ones with one value replaced
  const change = (changes: Partial<GameSettings>) => onChange({ ...settings, ...changes });

  return (
    <div className="flex flex-col gap-4 text-sm">
      <div className="flex items-center justify-between gap-3">
        <span className="flex items-center gap-1.5 font-bold text-[#55524B]">
          <Clock className="w-4 h-4" /> Время на ход
        </span>
        <div className="flex gap-1.5">
          {ROUND_TIME_LIMITS.map((seconds) => (
            <button
              key={seconds}
              type="button"
              disabled={disabled}
              aria-pressed={settings.round_time_limit === seconds}
              onClick={() => change({ round_time_limit: seconds })}
              className={`px-3 py-1.5 rounded-xl border-2 font-bold transition-all ${
                settings.round_time_limit === seconds
                  ? 'bg-[#E4D976] border-[#242426] text-[#242426]'
                  : 'bg-[#ECE8DE] border-[#242426]/30 text-[#55524B]'
              } ${disabled ? 'cursor-default' : 'cursor-pointer hover:border-[#242426]'}`}
            >
              {seconds}с
            </button>
          ))}
        </div>
      </div>

      <LimitSelect
        label="Раундов"
        icon={<Sparkles className="w-4 h-4" />}
        value={settings.max_rounds}
        options={MAX_ROUNDS_OPTIONS}
        disabled={disabled}
        onChange={(max_rounds) => change({ max_rounds })}
      />
      <LimitSelect
        label="Очков до победы"
        icon={<Trophy className="w-4 h-4" />}
        value={settings.score_to_win}
        options={SCORE_TO_WIN_OPTIONS}
        disabled={disabled}
        onChange={(score_to_win) => change({ score_to_win })}
      />
    </div>
  );
}

interface LimitSelectProps {
  label: string;
  icon: ReactNode;
  value: number | null;
  options: (number | null)[];
  disabled: boolean;
  onChange: (value: number | null) => void;
}

// A dropdown for an optional limit; "" in the <select> stands for "no limit" (null)
function LimitSelect({ label, icon, value, options, disabled, onChange }: LimitSelectProps) {
  // The server may hold a value that isn't in our list - still show it
  const values = options.includes(value) ? options : [...options, value];

  return (
    <label className="flex items-center justify-between gap-3">
      <span className="flex items-center gap-1.5 font-bold text-[#55524B]">
        {icon} {label}
      </span>
      <select
        value={value ?? ''}
        disabled={disabled}
        onChange={(event) => onChange(event.target.value === '' ? null : Number(event.target.value))}
        className="rounded-xl border-2 border-[#242426]/40 bg-[#ECE8DE] px-2.5 py-1.5 font-bold text-[#242426] disabled:opacity-100 disabled:appearance-none"
      >
        {values.map((option) => (
          <option key={option ?? 'none'} value={option ?? ''}>
            {option ?? 'без лимита'}
          </option>
        ))}
      </select>
    </label>
  );
}
