import { useState, type CSSProperties } from 'react';

// The game's own colors, so the confetti looks like part of it
const COLORS = ['#E4D976', '#C8D7C5', '#E8BAA8', '#242426', '#FAF7F2'];

const MIN_SIZE_PX = 6;
const MAX_SIZE_PX = 12;
const MIN_FALL_SECONDS = 1.8;
const MAX_FALL_SECONDS = 3;
const MAX_DRIFT_PX = 120; // sideways, either way
const MAX_SPIN_DEGREES = 720; // either way

interface Piece {
  left: number; // % of the screen width
  size: number;
  color: string;
  delay: number;
  duration: number;
  drift: number;
  spin: number;
}

const between = (min: number, max: number) => min + Math.random() * (max - min);

function makePieces(count: number, spreadSeconds: number): Piece[] {
  return Array.from({ length: count }, (_, index) => ({
    left: between(0, 100),
    size: between(MIN_SIZE_PX, MAX_SIZE_PX),
    color: COLORS[index % COLORS.length],
    delay: between(0, spreadSeconds),
    duration: between(MIN_FALL_SECONDS, MAX_FALL_SECONDS),
    drift: between(-MAX_DRIFT_PX, MAX_DRIFT_PX),
    spin: between(-MAX_SPIN_DEGREES, MAX_SPIN_DEGREES),
  }));
}

interface ConfettiProps {
  count: number;
  spreadSeconds: number; // the pieces start one by one over this time: 0 is a burst, more is a rain
}

// Falls once over the whole screen, then stays out of sight until it's removed. Clicks go through it;
// with "reduce motion" switched on in the system it isn't shown at all.
export default function Confetti({ count, spreadSeconds }: ConfettiProps) {
  // Made once, when it appears: Math.random() in every render would scatter the pieces anew each time
  const [pieces] = useState(() => makePieces(count, spreadSeconds));

  return (
    <div aria-hidden="true" className="pointer-events-none fixed inset-0 z-[60] overflow-hidden motion-reduce:hidden">
      {pieces.map((piece, index) => (
        <span
          key={index}
          className="absolute top-0 rounded-[2px] animate-confetti-fall"
          style={
            {
              left: `${piece.left}%`,
              width: piece.size,
              height: piece.size / 2,
              backgroundColor: piece.color,
              animationDelay: `${piece.delay}s`,
              animationDuration: `${piece.duration}s`,
              '--drift': `${piece.drift}px`,
              '--spin': `${piece.spin}deg`,
            } as CSSProperties // CSSProperties doesn't know custom properties like --drift
          }
        />
      ))}
    </div>
  );
}
