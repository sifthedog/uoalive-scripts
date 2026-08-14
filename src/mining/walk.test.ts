import { beforeEach, describe, expect, it, vi } from 'vitest';

import { Directions, installGlobals, type FakeWorld } from '../test-support/uo.js';

// The stepping itself is covered in src/lib/walk.test.ts. What is worth pinning here is the absence
// of a box: mining roams, and the forest rectangle this folder was seeded with stopped every run on
// cycle zero before it had scanned, equipped or swung at anything.
let world: FakeWorld;

const loadWalk = async () => {
  vi.resetModules();
  vi.doMock('./config.js', () => ({ WALK_DELAY: 0 }));
  return import('./walk.js');
};

beforeEach(() => {
  vi.resetModules();
  vi.doUnmock('./config.js');
  world = installGlobals({ player: { x: 2400, y: 900 } });
});

describe('stepToward', () => {
  it('walks toward a vein wherever the character happens to be', async () => {
    const { stepToward } = await loadWalk();

    stepToward({ x: 2410, y: 900 });

    expect(world.player.run).toHaveBeenCalledWith(Directions.East);
  });

  it('takes the diagonal rather than sliding off it', async () => {
    const { stepToward } = await loadWalk();

    stepToward({ x: 2410, y: 910 });

    expect(world.player.run).toHaveBeenCalledWith(Directions.Down);
  });
});
