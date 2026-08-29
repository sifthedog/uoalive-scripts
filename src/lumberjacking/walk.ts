import { createStepToward } from '../lib/walk.js';
import { allowedStep } from './bounds.js';
import { CHOP_RANGE, WALK_DELAY } from './config.js';
import { grid } from './grid.js';

// Returns whether the character actually moved, so the caller can notice a fence the grid did not
// know about and write the tree off rather than shuffling into it forever.
export const stepToward = /* @__PURE__ */ createStepToward({
  delayMs: WALK_DELAY,
  route: (spot) => grid.routeTo(spot, CHOP_RANGE),

  // Kept behind the route as a backstop: grid's passable already keeps the plan inside the box
  constrain: allowedStep,
});
