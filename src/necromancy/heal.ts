import { createBandager } from '../lib/heal.js';
import {
  BANDAGE,
  BANDAGE_ATTEMPTS,
  BANDAGE_GRAPHIC,
  BANDAGE_TIMEOUT,
  HEAL_OUTCOME_TEXT,
  TARGET_TIMEOUT,
} from './config.js';
import { belowFloor } from './guards.js';
import { waitOutSave } from './save.js';

// Runs at the top of every cycle, *before* the guards: the guard that would end the run for a hurt
// character is the same floor this heals to, so the order is the whole point.

const bandager = /* @__PURE__ */ createBandager({
  prefix: 'necro',
  graphic: BANDAGE_GRAPHIC,
  outcomeText: HEAL_OUTCOME_TEXT,
  timeoutMs: BANDAGE_TIMEOUT,
  cursorTimeoutMs: TARGET_TIMEOUT,
  attempts: BANDAGE_ATTEMPTS,
  recovered: () => !belowFloor(),
  waitOutSave,
});

// No-op when the character is fine, so the loop may call it blindly. With BANDAGE off it is always a
// no-op and the floor goes back to being only a stop.
export const mend = (): void => {
  if (!BANDAGE) {
    return;
  }

  bandager.mend();
};

export const outOfBandages = bandager.empty;
