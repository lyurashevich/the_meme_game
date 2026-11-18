// The sounds are made right in the browser (Web Audio API): a few short notes each, no audio files.
import type { SoundName } from './gameSounds';

// Quiet: the sounds are hints, not music
const VOLUME = 0.15;
// Gain can't fade to exactly 0 exponentially; this is already silence
const SILENCE = 0.0001;

// Frequencies in Hz
const NOTE = {
  G4: 392.0,
  C5: 523.25,
  E5: 659.25,
  G5: 783.99,
  A5: 880.0,
  C6: 1046.5,
} as const;

interface Note {
  frequency: number;
  at: number; // seconds from the start of the sound
  length: number; // seconds
}

interface Sound {
  wave: OscillatorType;
  notes: Note[];
}

const SOUNDS: Record<SoundName, Sound> = {
  round_started: {
    wave: 'sine',
    notes: [
      { frequency: NOTE.G5, at: 0, length: 0.12 },
      { frequency: NOTE.C6, at: 0.1, length: 0.35 },
    ],
  },
  judge_now: {
    wave: 'triangle',
    notes: [
      { frequency: NOTE.A5, at: 0, length: 0.1 },
      { frequency: NOTE.A5, at: 0.15, length: 0.1 },
      { frequency: NOTE.C6, at: 0.3, length: 0.2 },
    ],
  },
  you_won_round: {
    wave: 'triangle',
    notes: [
      { frequency: NOTE.C5, at: 0, length: 0.12 },
      { frequency: NOTE.E5, at: 0.12, length: 0.12 },
      { frequency: NOTE.G5, at: 0.24, length: 0.12 },
      { frequency: NOTE.C6, at: 0.36, length: 0.4 },
    ],
  },
  round_won: {
    wave: 'sine',
    notes: [
      { frequency: NOTE.G4, at: 0, length: 0.12 },
      { frequency: NOTE.C5, at: 0.12, length: 0.3 },
    ],
  },
  you_won_game: {
    wave: 'triangle',
    notes: [
      { frequency: NOTE.C5, at: 0, length: 0.15 },
      { frequency: NOTE.E5, at: 0.15, length: 0.15 },
      { frequency: NOTE.G5, at: 0.3, length: 0.15 },
      { frequency: NOTE.C6, at: 0.45, length: 0.2 },
      { frequency: NOTE.G5, at: 0.65, length: 0.12 },
      { frequency: NOTE.C6, at: 0.77, length: 0.6 },
    ],
  },
  game_over: {
    wave: 'sine',
    // a chord: three notes at once
    notes: [
      { frequency: NOTE.C5, at: 0, length: 0.8 },
      { frequency: NOTE.E5, at: 0, length: 0.8 },
      { frequency: NOTE.G5, at: 0, length: 0.8 },
    ],
  },
  chat_message: {
    wave: 'sine',
    notes: [{ frequency: NOTE.A5, at: 0, length: 0.06 }],
  },
};

let context: AudioContext | null = null;

// Browsers keep a page silent until the user clicks or presses a key on it (the autoplay policy),
// so the audio is switched on by the first such gesture.
export function unlockAudioOnFirstGesture(page: EventTarget): void {
  const unlock = () => {
    context ??= new AudioContext();
    void context.resume();
  };
  page.addEventListener('pointerdown', unlock, { once: true });
  page.addEventListener('keydown', unlock, { once: true });
}

export function playSound(name: SoundName): void {
  // Not allowed yet: skip the sound. Queued on a stopped context, it would play out of place on the first click.
  if (context?.state !== 'running') return;

  const { wave, notes } = SOUNDS[name];
  const start = context.currentTime;
  for (const note of notes) {
    const oscillator = context.createOscillator();
    const gain = context.createGain();
    const from = start + note.at;
    const to = from + note.length;

    oscillator.type = wave;
    oscillator.frequency.value = note.frequency;
    gain.gain.setValueAtTime(VOLUME, from);
    gain.gain.exponentialRampToValueAtTime(SILENCE, to); // a fade, since a sudden stop clicks
    oscillator.connect(gain).connect(context.destination);
    oscillator.start(from);
    oscillator.stop(to);
  }
}
