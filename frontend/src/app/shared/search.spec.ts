import { isDue, daysSince } from '../core/review';
import { score } from './search';

describe('search ranking', () => {
  it('needs every word to appear in the title or group', () => {
    expect(score('LRU Cache', 'Design', ['lru', 'cache'])).toBeGreaterThan(0);
    expect(score('LRU Cache', 'Design', ['lru', 'heap'])).toBe(-1);
    expect(score('Two Sum', 'Arrays & Hashing', ['hashing'])).toBeGreaterThan(0);
  });

  it('ranks a title that starts with the word above one that only contains it', () => {
    const words = ['hashmap'];
    expect(score('HashMap internals', 'Core Java notes', words))
      .toBeGreaterThan(score('How ConcurrentHashMap differs', 'Core Java Q&A', words));
  });
});

describe('review schedule', () => {
  const day = 86400000;
  const now = Date.parse('2026-10-28T12:00:00Z');

  it('brings a starred item back after three days', () => {
    expect(isDue(new Date(now - 2 * day).toISOString(), now)).toBeFalse();
    expect(isDue(new Date(now - 3 * day).toISOString(), now)).toBeTrue();
    expect(isDue(undefined, now)).toBeTrue();
  });

  it('counts whole days since a time', () => {
    expect(daysSince(new Date(now - 4.5 * day).toISOString(), now)).toBe(4);
    expect(daysSince(undefined, now)).toBeUndefined();
  });
});
