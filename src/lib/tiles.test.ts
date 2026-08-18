import { beforeEach, describe, expect, it, vi } from 'vitest';

import { installGlobals, type FakeWorld } from '../test-support/uo.js';
import { createApproach, type Found, type Tile } from './tiles.js';

// The scan-and-walk both roaming harvesters do between cycles. createScan and createTileStore are
// covered through the folders that configure them, in vein.test.ts and tree.test.ts.

let world: FakeWorld;

type Target = Tile & { distance: number };

const at = (x: number, distance: number): Target => ({ x, y: 0, z: 0, graphic: 231, distance });

const approaching = (
  overrides: Partial<Parameters<typeof createApproach<Tile>>[0]> & { scan: () => Found<Tile> },
) =>
  createApproach<Tile>({
    range: 2,
    maxSteps: 3,
    step: () => true,
    markUnreachable: vi.fn(),
    idleUntil: vi.fn(),
    nothingFound: () => 'no ore in range',
    ...overrides,
  });

beforeEach(() => {
  world = installGlobals({ player: { x: 0, y: 0 } });
});

describe('createApproach', () => {
  it('hands back a target already within range', () => {
    const found = at(2, 2);

    expect(approaching({ scan: () => ({ found }) })()).toEqual({ target: found });
  });

  it('takes a step toward one that is further off', () => {
    const step = vi.fn(() => true);

    expect(approaching({ scan: () => ({ found: at(5, 5) }), step })()).toEqual({ walked: true });
    expect(step).toHaveBeenCalled();
  });

  it('waits for the soonest one coming back rather than stopping', () => {
    const idleUntil = vi.fn();

    expect(approaching({ scan: () => ({ readyAt: 1234 }), idleUntil })()).toEqual({ waited: true });
    expect(idleUntil).toHaveBeenCalledWith(1234);
  });

  // Nothing found and nothing coming back is the end of the run, and the one chance to say what was
  // on the ground instead
  it('ends the run when nothing is left and nothing is regrowing', () => {
    expect(approaching({ scan: () => ({}) })()).toEqual({ stop: 'no ore in range' });
  });

  describe('a target it cannot get to', () => {
    it('sets it aside once the walk is out of patience', () => {
      const markUnreachable = vi.fn();
      const approach = approaching({
        scan: () => ({ found: at(5, 5) }),
        maxSteps: 2,
        markUnreachable,
      });

      approach();
      approach();
      expect(markUnreachable).not.toHaveBeenCalled();

      approach();
      expect(markUnreachable).toHaveBeenCalled();
    });

    it('sets it aside the moment a step is blocked', () => {
      const markUnreachable = vi.fn();

      approaching({ scan: () => ({ found: at(5, 5) }), step: () => false, markUnreachable })();

      expect(markUnreachable).toHaveBeenCalled();
    });

    // Two different targets taking turns as nearest still reset it - the stall watchdog is what
    // bounds that, not this counter
    it('starts the count again when the walk changes target', () => {
      const markUnreachable = vi.fn();
      let x = 5;
      const approach = approaching({
        scan: () => ({ found: at(x, 5) }),
        maxSteps: 2,
        markUnreachable,
      });

      approach();
      approach();
      x = 6;
      approach();
      approach();

      expect(markUnreachable).not.toHaveBeenCalled();
    });

    it('forgets the walk once a target comes into range', () => {
      const markUnreachable = vi.fn();
      let distance = 5;
      const approach = approaching({
        scan: () => ({ found: at(5, distance) }),
        maxSteps: 2,
        markUnreachable,
      });

      approach();
      approach();
      distance = 1;
      approach();
      distance = 5;
      approach();
      approach();

      expect(markUnreachable).not.toHaveBeenCalled();
    });
  });
});
