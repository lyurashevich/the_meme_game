import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';
import MemeCard from './MemeCard';

const CARD = { id: 1, image_url: '/media/memes/1.jpg' };

describe('MemeCard face down', () => {
  it('has no caption on the back, only a label for screen readers', () => {
    const html = renderToStaticMarkup(<MemeCard />);
    const visibleText = html.replace(/<[^>]*>/g, ''); // what is left without the tags and their attributes

    expect(visibleText).toBe('?');
    expect(html).toContain('role="img"');
    expect(html).toContain('aria-label="Карта рубашкой вверх"');
  });
});

describe('MemeCard confirm button', () => {
  const render = (isSelected: boolean) =>
    renderToStaticMarkup(
      <MemeCard card={CARD} isSelected={isSelected} onClick={() => {}} confirmLabel="Сыграть" onConfirm={() => {}} />,
    );

  it('is on the card once it is picked', () => {
    expect(render(true)).toContain('>Сыграть</button>');
  });

  it('is not there before the card is picked', () => {
    expect(render(false)).not.toContain('Сыграть');
  });

  it('never appears on a card that can only be looked at', () => {
    const html = renderToStaticMarkup(<MemeCard card={CARD} isSelected confirmLabel="Сыграть" />);

    expect(html).not.toContain('Сыграть');
    expect(html).not.toContain('<button');
  });
});
