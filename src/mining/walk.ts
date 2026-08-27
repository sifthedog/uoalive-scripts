import { createStepToward } from '../lib/walk.js';
import { MINE_RANGE, WALK_DELAY } from './config.js';
import { grid } from './grid.js';

// Returns whether the character actually moved, so the caller can notice a wall the grid did not
// know about and write the vein off rather than shuffling into it forever. No box: mining roams.
export const stepToward = /* @__PURE__ */ createStepToward({
  delayMs: WALK_DELAY,
  route: (spot) => grid.routeTo(spot, MINE_RANGE),
});
