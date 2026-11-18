import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';
import type { GameEnded, RoomPlayer } from '../protocol';
import GameResultsModal from './GameResultsModal';

const PLAY_AGAIN = 'СЫГРАТЬ ЕЩЁ';

const player = (id: string): RoomPlayer => ({ id, username: id, avatar_id: 'cat', score: 0, is_connected: true });

const RESULTS: GameEnded = {
  room_id: 'r1',
  reason: 'limit_reached',
  final_scores: { p1: 5, p2: 3 },
  winner_ids: ['p1'],
};

// The window as HTML: enough to check what it shows, with no browser emulation
const render = ({ isOwner, playersCount }: { isOwner: boolean; playersCount: number }): string =>
  renderToStaticMarkup(
    <GameResultsModal
      results={RESULTS}
      players={Array.from({ length: playersCount }, (_, index) => player(`p${index + 1}`))}
      myId="p1"
      isOwner={isOwner}
      onPlayAgain={() => {}}
      onClose={() => {}}
    />,
  );

// The opening tag of the button with this text, e.g. '<button type="button" disabled="" class="...">'
const buttonTag = (html: string, text: string): string | undefined => {
  const button = html.split('<button').find((part) => part.split('</button>')[0].includes(text));
  return button && `<button${button.split('>')[0]}>`;
};

describe('GameResultsModal', () => {
  it('lets the owner play again when there are enough players', () => {
    const html = render({ isOwner: true, playersCount: 3 });

    expect(buttonTag(html, PLAY_AGAIN)).not.toContain('disabled');
    expect(html).toContain('В лобби');
  });

  it('turns "play again" off for the owner when there are too few players, and says why', () => {
    const html = render({ isOwner: true, playersCount: 2 });

    expect(buttonTag(html, PLAY_AGAIN)).toContain('disabled');
    expect(html).toContain('Нужно хотя бы 3 игрока');
  });

  it('shows the other players no "play again", only the way back to the lobby', () => {
    const html = render({ isOwner: false, playersCount: 3 });

    expect(html).not.toContain(PLAY_AGAIN);
    expect(html).toContain('В ЛОББИ');
    expect(html).toContain('Владелец может начать новую игру');
  });
});
