import { BOUNDS } from './config.js';

export const describeBounds = (): string =>
  BOUNDS ? `(${BOUNDS.minX},${BOUNDS.minY})-(${BOUNDS.maxX},${BOUNDS.maxY})` : 'anywhere';

export const inBounds = (x: number, y: number): boolean =>
  !BOUNDS || (x >= BOUNDS.minX && x <= BOUNDS.maxX && y >= BOUNDS.minY && y <= BOUNDS.maxY);

const clamp = (value: number, low: number, high: number): number =>
  Math.min(Math.max(value, low), high);

// Clamping the tile into the box gives the closest legal standing spot, so this asks the shard's own
// Chebyshev range question from there rather than from where the character is.
export const reachableFromBounds = (x: number, y: number, range: number): boolean => {
  if (!BOUNDS) {
    return true;
  }

  const standX = clamp(x, BOUNDS.minX, BOUNDS.maxX);
  const standY = clamp(y, BOUNDS.minY, BOUNDS.maxY);

  return Math.max(Math.abs(x - standX), Math.abs(y - standY)) <= range;
};

// A diagonal that would leave the box often has a cardinal half that stays inside, and taking that
// slides along the edge rather than giving up - which matters, because a box has a lot of edge.
export const allowedStep = (dx: number, dy: number): [number, number] | undefined => {
  const options: [number, number][] = [
    [dx, dy],
    [dx, 0],
    [0, dy],
  ];

  for (const [stepX, stepY] of options) {
    if (stepX === 0 && stepY === 0) {
      continue;
    }

    if (inBounds(player.x + stepX, player.y + stepY)) {
      return [stepX, stepY];
    }
  }

  return undefined;
};
