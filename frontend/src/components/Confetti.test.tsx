import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';
import Confetti from './Confetti';

const PIECE = 'animate-confetti-fall';

describe('Confetti', () => {
  it('has as many pieces as asked for', () => {
    const html = renderToStaticMarkup(<Confetti count={25} spreadSeconds={1} />);

    expect(html.split(PIECE).length - 1).toBe(25);
  });

  it('is hidden from screen readers and lets clicks through', () => {
    const html = renderToStaticMarkup(<Confetti count={1} spreadSeconds={0} />);

    expect(html).toContain('aria-hidden="true"');
    expect(html).toContain('pointer-events-none');
  });
});
