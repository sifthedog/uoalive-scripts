import { WALK_DELAY } from './config.js';

// A copy of src/lumberjacking/walk.ts, minus the box. There is no pathfinding call in this API -
// player.run takes one direction at a time - so this steps naively and watches whether it actually
// moved. Mining roams: the veins run out and come back on their own timers, so what keeps the run
// somewhere sensible is where the ore is, not a rectangle.

// RunUO's offsets. Directions.Right/Down/Left/Up are the diagonals NE/SE/SW/NW.
const DIRECTION_BY_STEP = new Map([
  ['0,-1', Directions.North],
  ['1,-1', Directions.Right],
  ['1,0', Directions.East],
  ['1,1', Directions.Down],
  ['0,1', Directions.South],
  ['-1,1', Directions.Left],
  ['-1,0', Directions.West],
  ['-1,-1', Directions.Up],
]);

// One naive step toward the spot. Returns whether the character actually moved, so the caller can
// notice a wall and write the vein off rather than shuffling into it forever. Named `spot` rather
// than `target` because `target` is the ambient cursor global, and shadowing it here would be a
// trap for whoever next adds a target.cancel() to this file.
export const stepToward = (spot: { x: number; y: number }): boolean => {
  const stepX = Math.sign(spot.x - player.x);
  const stepY = Math.sign(spot.y - player.y);

  if (stepX === 0 && stepY === 0) {
    return false;
  }

  const direction = DIRECTION_BY_STEP.get(`${stepX},${stepY}`);

  if (direction === undefined) {
    return false;
  }

  const beforeX = player.x;
  const beforeY = player.y;

  // Issued twice on purpose: a step in a direction you are not already facing only turns you
  player.run(direction);
  sleep(WALK_DELAY);
  player.run(direction);
  sleep(WALK_DELAY);

  return player.x !== beforeX || player.y !== beforeY;
};
