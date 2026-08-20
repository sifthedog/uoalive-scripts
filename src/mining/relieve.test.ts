import { beforeEach, describe, expect, it, vi } from 'vitest';

import { installGlobals, type FakeWorld } from '../test-support/uo.js';

// The weight backstop both mining runs share, and the only thing in either that ends a run on
// weight. A world save freezes the smelt exactly the way an ore that cannot be worked does, and
// reading one as the other ended a live run at 467/453 with 83 ore and a working beetle beside it.

let world: FakeWorld;

interface Doubles {
  ore: number[];
  saving: boolean[];
  retry: boolean;
}

const load = async (doubles: Partial<Doubles> = {}) => {
  const ore = doubles.ore ?? [90, 90, 90];
  const saving = doubles.saving ?? [];

  let read = 0;
  let looks = 0;

  const groupOres = vi.fn();
  const oreTotal = vi.fn(() => ore[Math.min(read++, ore.length - 1)]);
  const isSaving = vi.fn(() => saving[Math.min(looks++, saving.length - 1)] ?? false);
  const waitOutSave = vi.fn();
  const retryUnsmeltable = vi.fn(() => doubles.retry ?? false);
  const smelt = vi.fn(() => false);

  vi.doMock('./ore.js', () => ({ groupOres, oreTotal }));
  vi.doMock('./save.js', () => ({ isSaving, waitOutSave }));
  vi.doMock('./smelt.js', () => ({ retryUnsmeltable }));

  const { createSmeltForRoom } = await import('./relieve.js');

  return {
    smeltForRoom: createSmeltForRoom({ smelt }),
    groupOres,
    waitOutSave,
    retryUnsmeltable,
    smelt,
  };
};

beforeEach(() => {
  vi.resetModules();
  world = installGlobals();
});

describe('createSmeltForRoom', () => {
  it('does nothing at all while there is room to work in', async () => {
    world.player.weight = 100;

    const { smeltForRoom, smelt } = await load();

    expect(smeltForRoom()).toBeUndefined();
    expect(smelt).not.toHaveBeenCalled();
  });

  // Ore leaving the pack is the proof, not the weight going down: the client can still be reporting
  // its pre-smelt figure when the pack diff has confirmed the conversion
  it('spends the cycle smelting when ore left the pack', async () => {
    world.player.weight = 467;

    const { smeltForRoom } = await load({ ore: [90, 40] });

    expect(smeltForRoom()).toEqual({ phase: 'smelting' });
  });

  it('ends the run when a live shard freed nothing', async () => {
    world.player.weight = 467;

    const { smeltForRoom } = await load({ ore: [83, 83, 83, 83] });

    expect(smeltForRoom()).toEqual({
      stop: 'overweight (467/400) with 83 ore left, and smelting freed nothing',
    });
  });

  describe('a world save', () => {
    // The run's one retry, spent against a frozen shard, is what left the next cycle with nothing to
    // try and ended the run
    it('waits it out rather than spending the retry', async () => {
      world.player.weight = 467;

      const { smeltForRoom, waitOutSave, retryUnsmeltable } = await load({
        ore: [83, 83],
        saving: [true],
        retry: true,
      });

      expect(smeltForRoom()).toEqual({ phase: 'smelting' });
      expect(waitOutSave).toHaveBeenCalledTimes(1);
      expect(retryUnsmeltable).not.toHaveBeenCalled();
    });

    // Arriving only after the retry has reopened the hues, where the verdict would otherwise be drawn
    it('waits out one that starts during the second pass', async () => {
      world.player.weight = 467;

      const { smeltForRoom, waitOutSave, retryUnsmeltable } = await load({
        ore: [83, 83, 83, 83],
        saving: [false, true],
        retry: false,
      });

      expect(smeltForRoom()).toEqual({ phase: 'smelting' });
      expect(retryUnsmeltable).toHaveBeenCalledTimes(1);
      expect(waitOutSave).toHaveBeenCalledTimes(1);
    });

    it('never ends the run on it', async () => {
      world.player.weight = 467;

      const { smeltForRoom } = await load({ ore: [83, 83, 83, 83], saving: [true] });

      expect(smeltForRoom()).not.toHaveProperty('stop');
    });
  });

  // The stationary run has advice to give that the roaming one has not
  it('carries the hint into the ending when it is given one', async () => {
    world.player.weight = 467;
    vi.doMock('./ore.js', () => ({ groupOres: vi.fn(), oreTotal: () => 83 }));
    vi.doMock('./save.js', () => ({ isSaving: () => false, waitOutSave: vi.fn() }));
    vi.doMock('./smelt.js', () => ({ retryUnsmeltable: () => false }));

    const { createSmeltForRoom } = await import('./relieve.js');
    const smeltForRoom = createSmeltForRoom({
      smelt: () => false,
      hint: 'the beetle has to be standing next to you',
    });

    expect(smeltForRoom()).toEqual({
      stop:
        'overweight (467/400) with 83 ore left, and smelting freed nothing - ' +
        'the beetle has to be standing next to you',
    });
  });
});
