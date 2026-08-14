import { beforeEach, describe, expect, it, vi } from 'vitest';

import { Directions, installGlobals, type FakeWorld } from '../test-support/uo.js';

const BOX = { minX: 0, maxX: 100, minY: 0, maxY: 100 };

let world: FakeWorld;

const loadWalk = async () => {
  vi.resetModules();
  vi.doMock('./config.js', () => ({ BOUNDS: BOX, WALK_DELAY: 0 }));
  return import('./walk.js');
};

beforeEach(() => {
  vi.resetModules();
  vi.doUnmock('./config.js');
  world = installGlobals({ player: { x: 50, y: 50 } });
});

describe('stepToward', () => {
  // RunUO's numbering, where Right/Down/Left/Up are the diagonals NE/SE/SW/NW rather than the
  // cardinals their names suggest. Getting one wrong walks the character the wrong way.
  const cases: [string, { x: number; y: number }, number][] = [
    ['north', { x: 50, y: 40 }, Directions.North],
    ['north-east', { x: 60, y: 40 }, Directions.Right],
    ['east', { x: 60, y: 50 }, Directions.East],
    ['south-east', { x: 60, y: 60 }, Directions.Down],
    ['south', { x: 50, y: 60 }, Directions.South],
    ['south-west', { x: 40, y: 60 }, Directions.Left],
    ['west', { x: 40, y: 50 }, Directions.West],
    ['north-west', { x: 40, y: 40 }, Directions.Up],
  ];

  for (const [name, tree, direction] of cases) {
    it(`runs ${name} toward a tree ${name} of the character`, async () => {
      const { stepToward } = await loadWalk();

      stepToward(tree);

      expect(world.player.run).toHaveBeenCalledWith(direction);
    });
  }

  // The first packet in a new direction only turns the character, so a single run() would leave it
  // facing the tree without having moved
  it('issues the direction twice, because the first one only turns', async () => {
    const { stepToward } = await loadWalk();

    stepToward({ x: 60, y: 50 });

    expect(world.player.run).toHaveBeenCalledTimes(2);
    expect(world.player.run.mock.calls).toEqual([[Directions.East], [Directions.East]]);
  });

  it('reports movement when the position changed', async () => {
    const { stepToward } = await loadWalk();
    world.player.run.mockImplementation(() => {
      world.player.x += 1;
    });

    expect(stepToward({ x: 60, y: 50 })).toBe(true);
  });

  // How the caller notices a fence and writes the tree off rather than shuffling into it forever
  it('reports no movement when the character did not budge', async () => {
    const { stepToward } = await loadWalk();

    expect(stepToward({ x: 60, y: 50 })).toBe(false);
  });

  it('does not move at all when standing on the tree', async () => {
    const { stepToward } = await loadWalk();

    expect(stepToward({ x: 50, y: 50 })).toBe(false);
    expect(world.player.run).not.toHaveBeenCalled();
  });
});
