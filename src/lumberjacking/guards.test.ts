import { beforeEach, describe, expect, it, vi } from 'vitest';

import { installGlobals, item } from '../test-support/uo.js';

const BOX = { minX: 0, maxX: 100, minY: 0, maxY: 100 };

const loadGuards = async (config: Record<string, unknown> = {}) => {
  vi.doMock('./config.js', async () => ({
    ...(await vi.importActual<object>('./config.js')),
    BOUNDS: BOX,
    ...config,
  }));
  return import('./guards.js');
};

beforeEach(() => {
  vi.resetModules();
  vi.doUnmock('./config.js');
  installGlobals({ player: { x: 50, y: 50 } });
});

describe('stopReason', () => {
  it('finds no reason to stop in the ordinary case', async () => {
    const { stopReason } = await loadGuards();

    expect(stopReason()).toBeUndefined();
  });

  it('stops when the character is dead', async () => {
    installGlobals({ player: { x: 50, y: 50, isDead: true } });
    const { stopReason } = await loadGuards();

    expect(stopReason()).toBe('you are dead');
  });

  // Every step is checked before it is taken, so this only trips if something else moved the
  // character - a teleporter, a boat, a GM - or if the run started outside the box
  it('stops when something has moved the character out of the box', async () => {
    installGlobals({ player: { x: 500, y: 50 } });
    const { stopReason } = await loadGuards();

    expect(stopReason()).toBe('at 500,50, outside (0,0)-(100,100)');
  });

  it('does not mind being anywhere when no box is set', async () => {
    installGlobals({ player: { x: 500, y: 50 } });
    const { stopReason } = await loadGuards({ BOUNDS: undefined });

    expect(stopReason()).toBeUndefined();
  });

  // The buffer means the stop lands before the shard starts refusing to move the new logs
  it('stops a buffer short of the real weight cap', async () => {
    installGlobals({ player: { x: 50, y: 50, weight: 370, weightMax: 400 } });
    const { stopReason } = await loadGuards({ WEIGHT_BUFFER: 40 });

    expect(stopReason()).toBe('overweight (370/400)');
  });

  it('keeps going while still inside the buffer', async () => {
    installGlobals({ player: { x: 50, y: 50, weight: 359, weightMax: 400 } });
    const { stopReason } = await loadGuards({ WEIGHT_BUFFER: 40 });

    expect(stopReason()).toBeUndefined();
  });

  // The client refreshes weight and weightMax independently and reports a max of 0 in between,
  // against which `weight > weightMax - 40` is true for every character in the game. This stopped
  // a live mining run on its first cycle, at a weight comfortably inside the limit it claimed to
  // have exceeded; lumberjacking carried the same unguarded expression.
  it('does not read a stat refresh as an overloaded character', async () => {
    installGlobals({ player: { x: 50, y: 50, weight: 436, weightMax: 0 } });
    const { stopReason } = await loadGuards({ WEIGHT_BUFFER: 40 });

    expect(stopReason()).toBeUndefined();
  });

  it('stops when the top level of the pack is full', async () => {
    const contents = Array.from({ length: 5 }, (_, i) => item({ serial: i, graphic: 0x1bdd }));
    installGlobals({ player: { x: 50, y: 50 }, backpack: contents });
    const { stopReason } = await loadGuards({ PACK_LIMIT: 5 });

    expect(stopReason()).toBe('pack is full (5 items at the top level)');
  });

  // Death first, so a corpse is never reported as merely overweight
  it('reports death ahead of every other reason', async () => {
    installGlobals({ player: { x: 500, y: 50, isDead: true, weight: 999, weightMax: 400 } });
    const { stopReason } = await loadGuards();

    expect(stopReason()).toBe('you are dead');
  });
});
