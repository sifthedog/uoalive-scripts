import { beforeEach, describe, expect, it, vi } from 'vitest';

import { Directions, installGlobals, terrainMap, type FakeWorld } from '../test-support/uo.js';

// The stepping itself is covered in src/lib/walk.test.ts. What is worth pinning here is the box:
// stepToward is the only thing that ever moves the character, so it is the only place BOUNDS can be
// enforced, and mining's binding deliberately has no constraint at all.
const BOX = { minX: 0, maxX: 100, minY: 0, maxY: 100 };

let world: FakeWorld;

const loadWalk = async (config: Record<string, unknown> = {}) => {
  vi.resetModules();
  vi.doMock('./config.js', async () => ({
    ...(await vi.importActual<object>('./config.js')),
    BOUNDS: BOX,
    WALK_DELAY: 0,
    ...config,
  }));
  return import('./walk.js');
};

beforeEach(() => {
  vi.resetModules();
  vi.doUnmock('./config.js');
  world = installGlobals({ player: { x: 50, y: 50 } });
});

describe('stepToward', () => {
  it('walks toward a tree inside the box', async () => {
    const { stepToward } = await loadWalk();

    stepToward({ x: 60, y: 50 });

    expect(world.player.run).toHaveBeenCalledWith(Directions.East);
  });

  // A box is mostly edge, so a diagonal that would leave it falls back to whichever cardinal half
  // stays inside - the character slides along the edge rather than giving up on the tree
  it('slides along the edge instead of stepping out of the box', async () => {
    world = installGlobals({ player: { x: 100, y: 50 } });
    const { stepToward } = await loadWalk();

    stepToward({ x: 110, y: 60 });

    expect(world.player.run).toHaveBeenCalledWith(Directions.South);
  });

  // The reported bug: trees are the impassable statics the walk has to cross to reach a tree, so a
  // straight line into one shuffled until MAX_TREE_STEPS wrote the tile off for five minutes.
  // ROUTE_RADIUS is narrowed to the picture, or the flood escapes through the unknown around it.
  it('routes around a thicket the straight line runs into', async () => {
    world.client.getTerrainList = terrainMap([46, 46], [
      '.........',
      '.....#...',
      '.....#...',
      '.....#...',
      '.....#...',
      '.....#...',
      '.....#...',
      '.....#...',
      '.........',
    ]);
    const { stepToward } = await loadWalk({ ROUTE_RADIUS: 4 });

    stepToward({ x: 54, y: 50 });

    expect(world.player.run).toHaveBeenCalledWith(Directions.North);
    expect(world.player.run).not.toHaveBeenCalledWith(Directions.East);
  });

  it('refuses a step that would leave the box on both axes', async () => {
    world = installGlobals({ player: { x: 100, y: 100 } });
    const { stepToward } = await loadWalk();

    expect(stepToward({ x: 110, y: 110 })).toBe(false);
    expect(world.player.run).not.toHaveBeenCalled();
  });
});
