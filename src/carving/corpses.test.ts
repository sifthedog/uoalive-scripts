import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { type FakeWorld, installGlobals, item } from '../test-support/uo.js';
import { BLOCKED_DELAY, CARVE_RANGE, CORPSE_GRAPHIC } from './config.js';
import { describeGround, inReach, isBlocked, nearest, nextToCarve, onGround, prune } from './corpses.js';
import { forget, memory } from './memory.js';

const START = 1_700_000_000_000;

let world: FakeWorld;

const corpse = (serial: number, at: { x: number; y: number } = { x: 100, y: 100 }) =>
  item({ serial, graphic: CORPSE_GRAPHIC, ...at });

const lying = (...corpses: Item[]) => vi.fn(() => corpses);

afterEach(() => {
  vi.useRealTimers();
});

beforeEach(() => {
  vi.useFakeTimers();
  vi.setSystemTime(START);
  forget();
  world = installGlobals({ player: { x: 100, y: 100 } });
});

describe('onGround', () => {
  it('takes every corpse the client is tracking, container or not', () => {
    world.client.findAllItemsOfType = lying(
      corpse(1),
      item({ serial: 2, graphic: CORPSE_GRAPHIC, container: 0x40000000 }),
    );

    expect(onGround().map((found) => found.serial)).toEqual([1, 2]);
  });

  // graphic reads 0 for an entity the client has stopped tracking
  it('drops one the client no longer knows the art of', () => {
    world.client.findAllItemsOfType = lying(corpse(1), item({ serial: 2, graphic: 0 }));

    expect(onGround().map((found) => found.serial)).toEqual([1]);
  });
});

describe('inReach', () => {
  it('keeps what is within range and leaves the rest', () => {
    const close = corpse(1, { x: 102, y: 100 });
    const far = corpse(2, { x: 105, y: 100 });

    expect(inReach([close, far], CARVE_RANGE).map((found) => found.serial)).toEqual([1]);
  });

  // Chebyshev: a diagonal step covers a tile of x and a tile of y at once
  it('measures a diagonal as one step per tile', () => {
    expect(inReach([corpse(1, { x: 102, y: 102 })], CARVE_RANGE)).toHaveLength(1);
    expect(inReach([corpse(1, { x: 103, y: 103 })], CARVE_RANGE)).toHaveLength(0);
  });
});

describe('nearest', () => {
  it('answers with nothing for an empty field', () => {
    expect(nearest([])).toBeUndefined();
  });

  it('answers with the closest distance', () => {
    expect(nearest([corpse(1, { x: 107, y: 100 }), corpse(2, { x: 103, y: 100 })])).toBe(3);
  });
});

describe('nextToCarve', () => {
  it('takes the closest one', () => {
    const found = nextToCarve([corpse(1, { x: 102, y: 100 }), corpse(2, { x: 101, y: 100 })]);

    expect(found?.serial).toBe(2);
  });

  it('skips one already dealt with', () => {
    memory().done.add(2);

    const found = nextToCarve([corpse(1, { x: 102, y: 100 }), corpse(2, { x: 101, y: 100 })]);

    expect(found?.serial).toBe(1);
  });

  it('skips one still blocked, and comes back to it once the block expires', () => {
    memory().blocked.set(1, START + BLOCKED_DELAY);

    expect(nextToCarve([corpse(1)])).toBeUndefined();

    vi.setSystemTime(START + BLOCKED_DELAY);

    expect(nextToCarve([corpse(1)])?.serial).toBe(1);
  });
});

describe('isBlocked', () => {
  it('is false for a serial nothing was ever said about', () => {
    expect(isBlocked(1)).toBe(false);
  });
});

// The sets outlive the run, and corpses decay
describe('prune', () => {
  it('forgets a corpse the client can no longer resolve', () => {
    memory().done.add(1);
    memory().emptied.add(1);
    memory().done.add(2);
    world.client.findObject = vi.fn((serial: number) => (serial === 2 ? corpse(2) : undefined));

    prune();

    expect([...memory().done]).toEqual([2]);
    expect([...memory().emptied]).toEqual([]);
  });

  it('drops a block that has expired even though the corpse is still there', () => {
    memory().blocked.set(1, START + BLOCKED_DELAY);
    world.client.findObject = vi.fn(() => corpse(1));

    prune();
    expect(memory().blocked.size).toBe(1);

    vi.setSystemTime(START + BLOCKED_DELAY);
    prune();
    expect(memory().blocked.size).toBe(0);
  });
});

describe('describeGround', () => {
  it('counts what the client can see, so a wrong graphic shows up at startup', () => {
    world.client.findAllItemsOfType = lying(corpse(1), corpse(2));

    expect(describeGround()).toBe('0x2006 x2');
  });
});
