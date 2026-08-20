import { beforeEach, describe, expect, it, vi } from 'vitest';

import { installGlobals, item, type FakeWorld } from '../test-support/uo.js';
import { LOCKPICK_GRAPHICS } from './config.js';

const LOCKPICK = [...LOCKPICK_GRAPHICS][0];
const BAG = 0x0e76;

let world: FakeWorld;

// picks.ts remembers the graphic it learned and the bag it came from, so each test needs a fresh copy
const loadPicks = async () => import('./picks.js');

const inPack = (...contents: Item[]): void => {
  Object.defineProperty(world.player, 'backpack', {
    configurable: true,
    get: () => ({ serial: 0x40000000, contents }),
  });
};

beforeEach(() => {
  vi.resetModules();
  world = installGlobals();
});

describe('findLockpick', () => {
  it('matches by graphic', async () => {
    const { findLockpick } = await loadPicks();
    inPack(item({ serial: 1, graphic: 0x1bdd }), item({ serial: 2, graphic: LOCKPICK }));

    expect(findLockpick()?.serial).toBe(2);
  });

  it('matches by name when the shard draws them with another art', async () => {
    const { findLockpick } = await loadPicks();
    inPack(item({ serial: 3, graphic: 0x9999, name: 'a lockpick' }));

    expect(findLockpick()?.serial).toBe(3);
  });

  it('finds one inside a bag', async () => {
    const { findLockpick } = await loadPicks();
    inPack(item({ serial: 4, graphic: BAG, contents: [item({ serial: 5, graphic: LOCKPICK })] }));

    expect(findLockpick()?.serial).toBe(5);
  });

  it('answers nothing for an empty pack', async () => {
    const { findLockpick } = await loadPicks();
    inPack();

    expect(findLockpick()).toBeUndefined();
  });
});

describe('lockpickTotal', () => {
  it('sums the stacks rather than counting them', async () => {
    const { lockpickTotal } = await loadPicks();
    inPack(
      item({ serial: 6, graphic: LOCKPICK, amount: 40 }),
      item({ serial: 7, graphic: LOCKPICK, amount: 12 }),
    );

    expect(lockpickTotal()).toBe(52);
  });

  it('counts the ones in a bag', async () => {
    const { lockpickTotal } = await loadPicks();
    inPack(
      item({ serial: 8, graphic: LOCKPICK, amount: 3 }),
      item({
        serial: 9,
        graphic: BAG,
        contents: [item({ serial: 10, graphic: LOCKPICK, amount: 7 })],
      }),
    );

    expect(lockpickTotal()).toBe(10);
  });

  it('is zero when the pack holds none', async () => {
    const { lockpickTotal } = await loadPicks();
    inPack(item({ serial: 11, graphic: 0x1bdd, amount: 5 }));

    expect(lockpickTotal()).toBe(0);
  });
});
