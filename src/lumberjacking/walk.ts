import { allowedStep } from './bounds.js';
import { WALK_DELAY } from './config.js';

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

// One naive step toward the tree. Returns whether the character actually moved, so the caller can
// notice a fence and write the tree off rather than shuffling into it forever.
export const stepToward = (tree: { x: number; y: number }): boolean => {
  // The one place the character moves, so the one place the box has to be enforced
  const step = allowedStep(Math.sign(tree.x - player.x), Math.sign(tree.y - player.y));

  if (step === undefined) {
    return false;
  }

  const direction = DIRECTION_BY_STEP.get(`${step[0]},${step[1]}`);

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
