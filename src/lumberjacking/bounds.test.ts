import { beforeEach, describe, expect, it, vi } from 'vitest';

import { installGlobals } from '../test-support/uo.js';

// bounds.ts reads BOUNDS from config at module scope, so the box has to be mocked before the import
// rather than assigned afterwards. A small square keeps the arithmetic checkable by hand.
const BOX = { minX: 10, maxX: 20, minY: 10, maxY: 20 };

const withBounds = async (bounds: typeof BOX | undefined) => {
  vi.resetModules();
  vi.doMock('./config.js', () => ({ BOUNDS: bounds }));
  return import('./bounds.js');
};

beforeEach(() => {
  vi.resetModules();
  vi.doUnmock('./config.js');
  installGlobals();
});

describe('inBounds', () => {
  it('accepts anywhere when no box is set', async () => {
    const { inBounds } = await withBounds(undefined);

    expect(inBounds(-9999, 9999)).toBe(true);
  });

  it('accepts the interior', async () => {
    const { inBounds } = await withBounds(BOX);

    expect(inBounds(15, 15)).toBe(true);
  });

  // "corners included" - the config comment says the box is inclusive, so all four edges are
  it('includes every edge and corner', async () => {
    const { inBounds } = await withBounds(BOX);

    expect(inBounds(10, 15)).toBe(true);
    expect(inBounds(20, 15)).toBe(true);
    expect(inBounds(15, 10)).toBe(true);
    expect(inBounds(15, 20)).toBe(true);
    expect(inBounds(10, 10)).toBe(true);
    expect(inBounds(20, 20)).toBe(true);
  });

  it('rejects one tile past any edge', async () => {
    const { inBounds } = await withBounds(BOX);

    expect(inBounds(9, 15)).toBe(false);
    expect(inBounds(21, 15)).toBe(false);
    expect(inBounds(15, 9)).toBe(false);
    expect(inBounds(15, 21)).toBe(false);
  });
});

describe('describeBounds', () => {
  it('says anywhere when no box is set', async () => {
    const { describeBounds } = await withBounds(undefined);

    expect(describeBounds()).toBe('anywhere');
  });

  it('prints the corners', async () => {
    const { describeBounds } = await withBounds(BOX);

    expect(describeBounds()).toBe('(10,10)-(20,20)');
  });
});

describe('reachableFromBounds', () => {
  it('reaches anything when no box is set', async () => {
    const { reachableFromBounds } = await withBounds(undefined);

    expect(reachableFromBounds(9999, 9999, 2)).toBe(true);
  });

  it('reaches a tile inside the box', async () => {
    const { reachableFromBounds } = await withBounds(BOX);

    expect(reachableFromBounds(15, 15, 2)).toBe(true);
  });

  // The clamp gives the closest legal standing spot, so range is measured from the edge, not from
  // wherever the character happens to be
  it('reaches a tile just outside, from the edge', async () => {
    const { reachableFromBounds } = await withBounds(BOX);

    expect(reachableFromBounds(22, 15, 2)).toBe(true);
  });

  it('does not reach a tile beyond range of the edge', async () => {
    const { reachableFromBounds } = await withBounds(BOX);

    expect(reachableFromBounds(23, 15, 2)).toBe(false);
  });

  // Chebyshev, not Euclidean: a diagonal step covers both axes, so (22,22) is 2 away from (20,20)
  it('measures the diagonal the way the shard does', async () => {
    const { reachableFromBounds } = await withBounds(BOX);

    expect(reachableFromBounds(22, 22, 2)).toBe(true);
    expect(reachableFromBounds(23, 23, 2)).toBe(false);
  });
});

describe('allowedStep', () => {
  it('takes the diagonal when it stays inside', async () => {
    installGlobals({ player: { x: 15, y: 15 } });
    const { allowedStep } = await withBounds(BOX);

    expect(allowedStep(1, 1)).toEqual([1, 1]);
  });

  // The point of the fallback: a box has a lot of edge, and giving up at it would strand the
  // character rather than sliding it along
  it('slides along the edge when the diagonal would leave the box', async () => {
    installGlobals({ player: { x: 20, y: 15 } });
    const { allowedStep } = await withBounds(BOX);

    expect(allowedStep(1, 1)).toEqual([0, 1]);
  });

  it('keeps the horizontal half when the vertical one would leave', async () => {
    installGlobals({ player: { x: 15, y: 20 } });
    const { allowedStep } = await withBounds(BOX);

    expect(allowedStep(1, 1)).toEqual([1, 0]);
  });

  it('gives up in a corner where every option leaves the box', async () => {
    installGlobals({ player: { x: 20, y: 20 } });
    const { allowedStep } = await withBounds(BOX);

    expect(allowedStep(1, 1)).toBeUndefined();
  });

  it('never answers with a step that goes nowhere', async () => {
    installGlobals({ player: { x: 15, y: 15 } });
    const { allowedStep } = await withBounds(BOX);

    expect(allowedStep(0, 0)).toBeUndefined();
  });

  it('passes a cardinal step straight through', async () => {
    installGlobals({ player: { x: 15, y: 15 } });
    const { allowedStep } = await withBounds(BOX);

    expect(allowedStep(0, -1)).toEqual([0, -1]);
    expect(allowedStep(-1, 0)).toEqual([-1, 0]);
  });
});
