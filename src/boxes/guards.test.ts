import { beforeEach, describe, expect, it, vi } from 'vitest';

import { installGlobals, item } from '../test-support/uo.js';

const withKeys = async (DROP_KEYS: boolean) => {
  vi.resetModules();
  vi.doMock('./config.js', () => ({ DROP_KEYS, PACK_LIMIT: 120, WEIGHT_BUFFER: 40 }));
  return import('./guards.js');
};

beforeEach(() => {
  vi.resetModules();
  vi.doUnmock('./config.js');
  installGlobals();
});

describe('stopReason', () => {
  it('stops a dead character either way', async () => {
    installGlobals({ player: { isDead: true } });

    const { stopReason } = await withKeys(true);

    expect(stopReason()).toBe('you are dead');
  });

  // The bug behind "15 wooden boxes, emptied 0": these checks come from the crafting scripts, where
  // every cycle adds to the pack. Emptying a box onto the floor only ever frees weight and slots,
  // so an overloaded character is precisely who the run should be working for, not stopping on.
  it('ignores weight while the keys are going on the floor', async () => {
    installGlobals({ player: { weight: 400, weightMax: 400 } });

    const { stopReason } = await withKeys(true);

    expect(stopReason()).toBeUndefined();
  });

  it('ignores a full pack while the keys are going on the floor', async () => {
    installGlobals({ backpack: Array.from({ length: 130 }, (_, index) => item({ serial: index, graphic: 0x1bef })) });

    const { stopReason } = await withKeys(true);

    expect(stopReason()).toBeUndefined();
  });

  // With DROP_KEYS off the keys do land in the pack, so both limits are real again
  it('stops on weight once the keys are being kept', async () => {
    installGlobals({ player: { weight: 400, weightMax: 400 } });

    const { stopReason } = await withKeys(false);

    expect(stopReason()).toContain('overweight');
  });

  it('stops on a full pack once the keys are being kept', async () => {
    installGlobals({ backpack: Array.from({ length: 130 }, (_, index) => item({ serial: index, graphic: 0x1bef })) });

    const { stopReason } = await withKeys(false);

    expect(stopReason()).toContain('pack is full');
  });

  it('passes an ordinary character', async () => {
    const { stopReason } = await withKeys(false);

    expect(stopReason()).toBeUndefined();
  });

  // A max of 0 is the client refreshing stats, not a character who can carry nothing
  it('does not read a stat refresh as an overloaded character', async () => {
    installGlobals({ player: { weight: 436, weightMax: 0 } });

    const { stopReason } = await withKeys(false);

    expect(stopReason()).toBeUndefined();
  });
});
