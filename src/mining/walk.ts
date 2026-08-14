import { createStepToward } from '../lib/walk.js';
import { WALK_DELAY } from './config.js';

// One naive step toward the spot. Returns whether the character actually moved, so the caller can
// notice a wall and write the vein off rather than shuffling into it forever. No box: mining roams,
// and the veins run out and come back on their own timers.
export const stepToward = createStepToward({ delayMs: WALK_DELAY });
