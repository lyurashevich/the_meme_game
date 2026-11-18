import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';
import MemeCard from './MemeCard';

describe('MemeCard face down', () => {
  it('has no caption on the back, only a label for screen readers', () => {
    const html = renderToStaticMarkup(<MemeCard />);
    const visibleText = html.replace(/<[^>]*>/g, ''); // what is left without the tags and their attributes

    expect(visibleText).toBe('?');
    expect(html).toContain('role="img"');
    expect(html).toContain('aria-label="Карта рубашкой вверх"');
  });
});
