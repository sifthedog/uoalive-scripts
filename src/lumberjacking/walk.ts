import { createStepToward } from '../lib/walk.js';
import { allowedStep } from './bounds.js';
import { WALK_DELAY } from './config.js';

// Returns whether the character actually moved, so the caller can notice a fence and write the tree
// off rather than shuffling into it forever.
export const stepToward = /* @__PURE__ */ createStepToward({ delayMs: WALK_DELAY, constrain: allowedStep });
