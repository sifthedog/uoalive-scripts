// Re-exported rather than imported directly so this file stays the only one consumers import.
export {
  ATTACK_TEXT,
  CALL_ON_SIGHT_NOTORIETY,
  EQUIP_ATTEMPTS,
  EQUIP_POLL,
  EQUIP_TIMEOUT,
  GUARD_CALL,
  GUARD_CALLS,
  GUARD_CALL_DELAY,
  GUARD_REPLY_WAIT,
  GUARD_ZONE_TEXT,
  HEARTBEAT_EVERY,
  HOSTILE_NOTORIETY,
  IDLE_LOG_EVERY,
  IDLE_POLL,
  LOG_EVERY,
  MAX_CYCLES,
  MAX_NO_CURSOR,
  MAX_STEPS,
  MAX_THROTTLED,
  MAX_UNKNOWN,
  NO_CURSOR_READ,
  NO_GUARDS_TEXT,
  PACK_LIMIT,
  SAVE_DONE_TEXT,
  SAVE_POLL,
  SAVE_WAIT,
  SAVING_TEXT,
  SCAN_RADIUS,
  STALL_STOP,
  STALL_WARN,
  STEP_DELAY,
  TARGET_TIMEOUT,
  THREAT_RANGE,
  THROTTLED_TEXT,
  THROTTLE_BACKOFF,
  THROTTLE_BACKOFF_MAX,
  UNGUARDED_TEXT,
  UNREACHABLE_DELAY,
  UNSKILLED_TEXT,
  WALK_DELAY,
  WATCH_FOR_TROUBLE,
} from '../lib/timings.js';

// Imported as well as re-exported: OUTCOME_TEXT aliases it into its own `saving` bucket, while the
// conversion and the haul have no outcomes at all and check the same wordings directly.
import { SAVING_TEXT } from '../lib/timings.js';

export const AXE_NAME = 'axe';

// Optional: pin the spare bag instead of discovering it
export const SPARE_BAG_SERIAL: number | undefined = undefined;

// Trees are found by their tiledata name, so these stay empty until this shard proves the name match
// wrong. Both are seeds only - a refusal learned on the shard goes into the run's memory.
export const TREE_GRAPHICS = new Set<number>();
export const NOT_TREE_GRAPHICS = new Set<number>();

export type Bounds = { minX: number; maxX: number; minY: number; maxY: number };

// The character never steps outside this box, corners included. Set it to undefined to roam. Trees
// outside it are still fair game as long as one can be reached from a tile inside it.
export const BOUNDS: Bounds | undefined = { minX: 2400, maxX: 2580, minY: 400, maxY: 600 };

export const CHOP_RANGE = 2;

// A stack's graphic changes with its size, so match a set rather than one graphic. Hue is
// deliberately not part of the match: a shard with special woods hues its logs, and those still
// count, still convert and still need hauling.
export const LOG_GRAPHICS = new Set([0x1bdd, 0x1be0, 0x1bde, 0x1bdf]);

// A seed only: the real board graphic is learned by diffing the pack across the first conversion.
export const BOARD_GRAPHICS = new Set([0x1bd7, 0x1bd9, 0x1bda, 0x1bdb]);

// How long before a tile that answered "not enough wood" is worth coming back to
export const REGROW_DELAY = 25 * 60 * 1000;

// A swing plays its animation before the result arrives, so this has to outlast the animation
export const CHOP_TIMEOUT = 8000;

// Longer than the shared TARGET_TIMEOUT, because the cursor is waited for by polling two signals
export const CHOP_TARGET_TIMEOUT = 4000;
export const CHOP_TARGET_POLL = 100;

// The cursor the shard opens for a swing, read only to tell a shard that refused the action apart
// from one whose cursor target.open missed. Unverified here - correct it against the real journal.
export const CHOP_PROMPT_TEXT = [
  'What do you want to use this on',
  'Select a tree',
  'Where do you wish to chop',
];

// Optional: pin the animals instead of discovering them. Order does not matter - the haul walks to
// whichever is nearest first either way.
export const PACK_ANIMAL_SERIALS: number[] = [];

// Pack horse, pack llama, giant beetle. Unverified on this shard; the search logs the body it finds.
export const PACK_ANIMAL_GRAPHICS = new Set([0x123, 0x124, 0x317]);

// A cursor at startup to click the animals, ESC to fall back to PACK_ANIMAL_SERIALS or the search
export const PICK_PACK_ANIMALS = true;

// A backstop only - the selection ends when you press ESC
export const MAX_PICKS = 8;

export const OPL_TIMEOUT = 2000;

export const UNLOAD_RANGE = 2;

// Deliberately larger than the guards' WEIGHT_BUFFER, so hauling always gets its turn before the
// overweight stop fires.
export const HAUL_BUFFER = 120;

// Pauses after each conversion and each move, to stay under the server's action throttle
export const CONVERT_DELAY = 700;
export const MOVE_DELAY = 700;

// Polled rather than slept through: the throttle can delay a conversion well past a fixed pause, and
// reading too early looks like a failure.
export const CONVERT_TIMEOUT = 4000;
export const CONVERT_POLL = 200;

// More than one, because a throttled or stale attempt also looks silent, and giving up on hue 0
// means hauling ordinary logs.
export const CONVERT_ATTEMPTS = 3;

// One pass converts one stack, so this bounds a haul.
export const MAX_CONVERT_PASSES = 60;

// Buffer, so the stop lands before the shard starts refusing to move the new logs
export const WEIGHT_BUFFER = 40;

// Guesses for a RunUO-family shard. Correct these against the real journal after the first run - a
// phrase that never matches shows up as 'unknown' outcomes, not as a silent wrong turn.
export const OUTCOME_TEXT = {
  chopped: ['You put', 'You hack at the tree', 'You chop some'],
  empty: ["There's not enough wood here to harvest", 'There are no logs left'],
  // "You can't use an axe on that" is UOAlive's wording, seen on a live run against an 'o'hii tree'
  // static (0xc9e) - the tiledata calls it a tree, the shard will not harvest it
  notTree: [
    "You can't use an axe on that",
    "You can't chop that",
    "You can't use a bladed item on that",
    'You cannot chop',
  ],
  tooFar: ['That is too far away', 'You cannot reach that'],
  // Confirmed from a live run. Line of sight, not range: the tile is inside CHOP_RANGE and no amount
  // of walking closer or waiting fixes it.
  notSeen: ['Target cannot be seen'],
  wornOut: ['You have worn out your tool'],
  // Without a bucket of its own a world save reads as five unreadable outcomes in a row, which ended
  // a live mining run.
  saving: SAVING_TEXT,
  // Full wordings first: the bare prefix also catches "You must wait N seconds" from systems that
  // have nothing to do with harvesting. Kept last as a fallback all the same - a phrase this list
  // misses reads as an unreadable outcome, which is worse.
  throttled: ['You must wait to perform another action', 'You must wait a moment', 'You must wait'],
};
