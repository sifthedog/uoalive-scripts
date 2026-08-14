import { beforeEach, describe, expect, it, vi } from 'vitest';

import { installGlobals, item } from '../test-support/uo.js';

// The checks themselves are covered in src/lib/guards.test.ts. What is worth pinning here is which
// of them mining composes - both absences are load-bearing and both were learned the hard way.
const loadGuards = async (config: Record<string, unknown> = {}) => {
  vi.doMock('./config.js', () => ({ PACK_LIMIT: 5, ...config }));
  return import('./guards.js');
};

beforeEach(() => {
  vi.resetModules();
  vi.doUnmock('./config.js');
  installGlobals();
});

describe('stopReason', () => {
  it('finds no reason to stop in the ordinary case', async () => {
    const { stopReason } = await loadGuards();

    expect(stopReason()).toBeUndefined();
  });

  it('stops when the character is dead', async () => {
    installGlobals({ player: { isDead: true } });
    const { stopReason } = await loadGuards();

    expect(stopReason()).toBe('you are dead');
  });

  it('stops when the top level of the pack is full', async () => {
    installGlobals({
      backpack: Array.from({ length: 5 }, (_, index) => item({ serial: index, graphic: 0x19b7 })),
    });
    const { stopReason } = await loadGuards();

    expect(stopReason()).toBe('pack is full (5 items at the top level)');
  });

  // Being over the limit is what triggers the smelt, so a guard at a buffer below it would fire
  // first, every time, and the smelt would never happen at all. What ends an overweight run is a
  // smelt that freed nothing - decided in the loop, not here.
  it('leaves an overweight character to the smelt', async () => {
    installGlobals({ player: { weight: 999, weightMax: 400 } });
    const { stopReason } = await loadGuards();

    expect(stopReason()).toBeUndefined();
  });

  // Mining roams. The box this folder was seeded with was lumberjacking's forest, and it stopped
  // every run on cycle zero - before it had scanned, equipped or swung at anything.
  it('does not mind where in the world the character is standing', async () => {
    installGlobals({ player: { x: 300, y: 4000 } });
    const { stopReason } = await loadGuards();

    expect(stopReason()).toBeUndefined();
  });
});
