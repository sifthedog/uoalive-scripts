export {
  EQUIP_ATTEMPTS,
  EQUIP_POLL,
  EQUIP_TIMEOUT,
  HEARTBEAT_EVERY,
  LOG_EVERY,
  MAX_NO_CURSOR,
  MAX_NO_TOOL,
  MAX_THROTTLED,
  MAX_UNKNOWN,
  NO_CURSOR_READ,
  PACK_LIMIT,
  SAVE_DONE_TEXT,
  SAVE_POLL,
  SAVE_WAIT,
  STALL_STOP,
  STALL_WARN,
  STEP_DELAY,
  TARGET_TIMEOUT,
  THROTTLE_BACKOFF,
  THROTTLE_BACKOFF_MAX,
} from '../lib/timings.js';

import { SAVING_TEXT, THROTTLED_TEXT } from '../lib/timings.js';

export { SAVING_TEXT };

// Bounds carves and loots, not the idle polls between them, so a quiet field costs nothing
export const MAX_CYCLES = 100_000;

// Every corpse in the game is this art; what died is carried in the hue and the name.
export const CORPSE_GRAPHIC = 0x2006;

export const KNIFE_NAME = 'knife';

// Optional: pin the spare bag instead of discovering it
export const SPARE_BAG_SERIAL: number | undefined = undefined;

// Seeds only - createTool learns the real graphic off the first one it finds, and falls back to the
// name where the client has tooltip data.
export const KNIFE_GRAPHICS = new Set([
  0x13f6, // butcher knife
  0x13f7, // butcher knife
  0x0ec4, // cleaver
  0x0ec5, // cleaver
  0x0f51, // dagger
  0x0f52, // dagger
  0x10e4, // skinning knife
  0x10e5, // skinning knife
]);

// What gets moved out of a carved corpse. Hides (0x1078), raw ribs (0x09f1) and raw bird (0x09b9)
// are a line each if you want them too.
export const TAKE_GRAPHICS = new Set([
  0x1bd1, // feather
]);

// Off if this shard puts the feathers straight into the pack: nothing is then ever worth opening a
// corpse for, and each open costs a cycle.
export const LOOT_CORPSES = true;

// The shard's own reach. Nothing in this script walks, so a corpse further out is left alone.
export const CARVE_RANGE = 2;

// No animation to outlast, unlike a chop
export const CARVE_TIMEOUT = 3000;

// A pure client-side scan, so this costs nothing to make brisk
export const WATCH_POLL = 400;

export const OPEN_DELAY = 800;
export const MOVE_DELAY = 250;

// How long a haul waits for the stacks to leave the corpse, and how often it looks
export const SETTLE_TIMEOUT = 2000;
export const SETTLE_POLL = 100;

// Idle passes between sweeps of the memory sets for corpses that have decayed
export const PRUNE_EVERY = 50;

// tooFar and notSeen, which is usually something standing between you and the body
export const BLOCKED_DELAY = 60_000;

// So the stop lands before the shard starts refusing to move the feathers
export const WEIGHT_BUFFER = 20;

// Guesses for a RunUO-family shard. Correct these against the real journal after the first run - a
// phrase that never matches shows up as 'unknown' outcomes, not as a silent wrong turn.
export const OUTCOME_TEXT = {
  carved: [
    'You pluck the bird',
    'Feathers now go into your pack',
    'You carve away',
    'You carve some',
    'You skin the',
  ],
  nothingLeft: [
    'You see nothing useful to carve from the corpse',
    'There is nothing left to carve',
  ],
  notCarvable: [
    "You can't use a bladed item on that",
    'You cannot carve that',
    'That is not a corpse',
  ],
  tooFar: ['That is too far away', 'You cannot reach that'],
  notSeen: ['Target cannot be seen'],
  saving: SAVING_TEXT,
  throttled: THROTTLED_TEXT,
};
