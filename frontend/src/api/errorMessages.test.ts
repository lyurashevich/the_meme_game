import { readFileSync } from 'node:fs';
import { describe, expect, it, vi } from 'vitest';
import { describeError } from './errorMessages';
import { ActionError } from './GameSocket';

const serverError = (code: string) => new ActionError({ code, message: 'English text for developers' });

describe('describeError', () => {
  it('picks the sentence by the code, not the server message', () => {
    expect(describeError(serverError('room_is_full'))).toBe('В комнате нет свободных мест');
  });

  it('has a sentence for every error the client makes itself', () => {
    for (const code of ['not_connected', 'connection_lost', 'timeout']) {
      expect(describeError(serverError(code))).not.toContain('Что-то пошло не так');
    }
  });

  it('falls back to a general sentence for a code it does not know', () => {
    const warn = vi.spyOn(console, 'warn').mockImplementation(() => {});

    expect(describeError(serverError('brand_new_code'))).toBe('Что-то пошло не так. Попробуйте ещё раз');
    expect(warn).toHaveBeenCalled();
    warn.mockRestore();
  });

  it('does not show the text of an unexpected exception to the player', () => {
    const log = vi.spyOn(console, 'error').mockImplementation(() => {});

    expect(describeError(new TypeError('x is undefined'))).toBe('Что-то пошло не так. Попробуйте ещё раз');
    log.mockRestore();
  });
});

describe('the server errors', () => {
  // Never the answer to a game action: the base class, the REST card editing, and a stale token,
  // which the server handles on connecting by simply making a new player
  const NOT_FROM_THE_GAME = [
    'custom_exception',
    'admin_api_disabled',
    'invalid_admin_token',
    'invalid_reconnect_token',
  ];

  it('every error code of the backend has a sentence', () => {
    const source = readFileSync(new URL('../../../app/exceptions.py', import.meta.url), 'utf-8');
    const codes = [...source.matchAll(/code: str = "(\w+)"/g)].map((match) => match[1]);
    const warn = vi.spyOn(console, 'warn').mockImplementation(() => {});

    const missing = codes
      .filter((code) => !NOT_FROM_THE_GAME.includes(code))
      .filter((code) => describeError(serverError(code)).startsWith('Что-то пошло не так'));

    expect(codes.length).toBeGreaterThan(10); // the file was really read
    expect(missing).toEqual([]);
    warn.mockRestore();
  });
});
