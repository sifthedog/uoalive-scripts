import { approach, distanceTo, isMobile } from '../lib/entity.js';
import { createStepToward } from '../lib/walk.js';
import { TAME_APPROACH, TAME_MAX_STEPS, TAME_RANGE, WALK_DELAY } from './config.js';
import { isSaving } from './save.js';

// No grid and no route, unlike mining and lumberjacking: the animal moves every step, so a scanned
// route would be recomputed and thrown away each time.
export const stepToward = /* @__PURE__ */ createStepToward({ delayMs: WALK_DELAY });

// 'gained' is ground made up on something that is still walking away, which is worth another cycle;
// 'stuck' is the only one that counts against MAX_AWAY.
export type Chase = 'closed' | 'gained' | 'stuck';

const distanceOf = (serial: number): number | undefined => {
  const found = client.findObject(serial);

  return found && isMobile(found) ? distanceTo(found) : undefined;
};

export const walkTo = (serial: number): Chase => {
  const before = distanceOf(serial);

  const reached = approach(serial, {
    label: 'tame',
    range: TAME_APPROACH,
    maxSteps: TAME_MAX_STEPS,
    step: stepToward,
    isSaving,
  });

  if (reached) {
    return 'closed';
  }

  const after = distanceOf(serial);

  return before !== undefined && after !== undefined && after < before ? 'gained' : 'stuck';
};

// One step, and only when it has drifted: called between the slices of a taming wait, so the animal
// is followed while the attempt resolves rather than only between attempts
export const keepUp = (serial: number): void => {
  const found = client.findObject(serial);

  if (found && isMobile(found) && distanceTo(found) > TAME_RANGE) {
    stepToward(found);
  }
};
