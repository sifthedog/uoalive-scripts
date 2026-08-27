import { beforeEach, describe, expect, it } from 'vitest';

import { Directions, installGlobals, type FakeWorld } from '../test-support/uo.js';
import { createStepToward } from './walk.js';

let world: FakeWorld;

const stepToward = createStepToward({ delayMs: 0 });

beforeEach(() => {
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

  for (const [name, spot, direction] of cases) {
    it(`runs ${name} toward a spot ${name} of the character`, () => {
      stepToward(spot);

      expect(world.player.run).toHaveBeenCalledWith(direction);
    });
  }

  // The first packet in a new direction only turns the character, so a single run() would leave it
  // facing the spot without having moved. The step has to land, or the sidestep below adds its own
  // calls to the tally.
  it('issues the direction twice, because the first one only turns', () => {
    world.player.run.mockImplementation(() => {
      world.player.x += 1;
    });

    stepToward({ x: 60, y: 50 });

    expect(world.player.run).toHaveBeenCalledTimes(2);
    expect(world.player.run.mock.calls).toEqual([[Directions.East], [Directions.East]]);
  });

  it('reports movement when the position changed', () => {
    world.player.run.mockImplementation(() => {
      world.player.x += 1;
    });

    expect(stepToward({ x: 60, y: 50 })).toBe(true);
  });

  // How the caller notices a wall and writes the tile off rather than shuffling into it forever
  it('reports no movement when the character did not budge', () => {
    expect(stepToward({ x: 60, y: 50 })).toBe(false);
  });

  it('does not move at all when standing on the spot', () => {
    expect(stepToward({ x: 50, y: 50 })).toBe(false);
    expect(world.player.run).not.toHaveBeenCalled();
  });

  describe('with a route', () => {
    it('takes the step the router hands back rather than the straight line', () => {
      const routed = createStepToward({ delayMs: 0, route: () => [0, 1] });

      routed({ x: 60, y: 50 });

      expect(world.player.run).toHaveBeenCalledWith(Directions.South);
    });

    // Undefined is 'nothing to say', not 'nowhere to go': the fire beetle stands further off than
    // the grid is flooded, and a walk that gave up there would never reach it
    it('falls back to the straight line when the router has nothing', () => {
      const routed = createStepToward({ delayMs: 0, route: () => undefined });

      routed({ x: 60, y: 50 });

      expect(world.player.run).toHaveBeenCalledWith(Directions.East);
    });
  });

  // A pet or another player parked in the gap is not in the terrain the router reads
  describe('a step that did not move the character', () => {
    it('tries either side of it before reporting a wall', () => {
      expect(stepToward({ x: 60, y: 50 })).toBe(false);
      expect(world.player.run.mock.calls.map(([direction]) => direction)).toEqual([
        Directions.East,
        Directions.East,
        Directions.Down,
        Directions.Down,
        Directions.Right,
        Directions.Right,
      ]);
    });

    it('stops at the first one that lands', () => {
      world.player.run.mockImplementation((direction: number) => {
        if (direction === Directions.Down) {
          world.player.y += 1;
        }
      });

      expect(stepToward({ x: 60, y: 50 })).toBe(true);
      expect(world.player.run).not.toHaveBeenCalledWith(Directions.Right);
    });
  });

  describe('with a constraint', () => {
    // The one place the character moves, so the one place a box has to be enforced
    it('takes the step the constraint hands back rather than the one asked for', () => {
      const sliding = createStepToward({ delayMs: 0, constrain: () => [1, 0] });

      sliding({ x: 60, y: 60 });

      expect(world.player.run).toHaveBeenCalledWith(Directions.East);
    });

    it('does not move when the constraint allows no step at all', () => {
      const penned = createStepToward({ delayMs: 0, constrain: () => undefined });

      expect(penned({ x: 60, y: 50 })).toBe(false);
      expect(world.player.run).not.toHaveBeenCalled();
    });
  });
});
