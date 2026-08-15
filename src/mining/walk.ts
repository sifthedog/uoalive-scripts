import { createStepToward } from '../lib/walk.js';
import { WALK_DELAY } from './config.js';

// Returns whether the character actually moved, so the caller can notice a wall and write the vein
// off rather than shuffling into it forever. No box: mining roams.
export const stepToward = /* @__PURE__ */ createStepToward({ delayMs: WALK_DELAY });
