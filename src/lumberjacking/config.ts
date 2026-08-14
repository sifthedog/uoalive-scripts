// Tuned once, in src/lib/timings.ts, and re-exported here so this file stays the only one any
// consumer imports. To give lumberjacking its own value for one of these, delete it from this list
// and declare it below.
export {
  EQUIP_ATTEMPTS,
  EQUIP_POLL,
  EQUIP_TIMEOUT,
  HEARTBEAT_EVERY,
  IDLE_LOG_EVERY,
  IDLE_POLL,
  LOG_EVERY,
  MAX_CYCLES,
  MAX_STEPS,
  MAX_THROTTLED,
  MAX_UNKNOWN,
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
  THROTTLE_BACKOFF,
  THROTTLE_BACKOFF_MAX,
  UNSKILLED_TEXT,
  UNREACHABLE_DELAY,
  WALK_DELAY,
} from '../lib/timings.js';

// Imported as well as re-exported, because OUTCOME_TEXT below aliases it into its own `saving`
// bucket: the chop reads a save as an outcome, while the conversion and the haul have no outcomes
// at all and check the same wordings directly.
import { SAVING_TEXT } from '../lib/timings.js';

export const AXE_NAME = 'axe';

// Optional: pin the spare bag instead of discovering it
export const SPARE_BAG_SERIAL: number | undefined = undefined;

// Trees are found by their tiledata name, so these stay empty until this shard proves the name
// match wrong. Put a graphic in TREE_GRAPHICS if a harvestable tree is skipped, and in
// NOT_TREE_GRAPHICS if a decorative static keeps being chopped at. Both are seeds only - a refusal
// learned on the shard goes into the run's memory, not back into here.
export const TREE_GRAPHICS = new Set<number>();
export const NOT_TREE_GRAPHICS = new Set<number>();

export type Bounds = { minX: number; maxX: number; minY: number; maxY: number };

// The character never steps outside this box, corners included. Set it to undefined to roam.
// Trees outside it are still fair game as long as one can be reached from a tile inside it.
export const BOUNDS: Bounds | undefined = { minX: 2400, maxX: 2580, minY: 400, maxY: 600 };

// How close you have to be to hit one. Two tiles is the stock harvest range
export const CHOP_RANGE = 2;

// Logs stack, and a stack's graphic changes with its size like ore does, so match a set of
// graphics rather than one graphic. Hue is deliberately not part of the match: a shard with
// special woods hues its logs, and those still count, still convert and still need hauling.
export const LOG_GRAPHICS = new Set([0x1bdd, 0x1be0, 0x1bde, 0x1bdf]);

// A seed only. The real board graphic is learned by diffing the pack across the first successful
// conversion, so a wrong guess here costs nothing.
export const BOARD_GRAPHICS = new Set([0x1bd7, 0x1bd9, 0x1bda, 0x1bdb]);

// A stump regrows, so a tile that answers "not enough wood" is worth coming back to. This is the
// wait before it is, and the one knob to turn if the script returns to a tree that is still bare.
export const REGROW_DELAY = 25 * 60 * 1000;

// A swing plays its animation before the result arrives, so this has to outlast the animation
export const CHOP_TIMEOUT = 8000;

// Optional: pin the animals instead of discovering them. Order does not matter - the haul walks
// to whichever is nearest first either way.
export const PACK_ANIMAL_SERIALS: number[] = [];

// Pack horse, pack llama, giant beetle. Unverified on this shard; the search logs the body it
// finds, so an unusual pack animal can be added here or pinned above.
export const PACK_ANIMAL_GRAPHICS = new Set([0x123, 0x124, 0x317]);

// How close you have to be to move items onto the animal
export const UNLOAD_RANGE = 2;

// Weight at which to stop chopping and go make boards. Deliberately larger than the guards'
// WEIGHT_BUFFER, so hauling always gets its turn before the overweight stop fires.
export const HAUL_BUFFER = 120;

// Pauses after each conversion and each move, to stay under the server's action throttle
export const CONVERT_DELAY = 700;
export const MOVE_DELAY = 700;

// How long to watch the pack for a conversion landing. Polled rather than slept through: the
// throttle can delay it well past a fixed pause, and reading too early looks like a failure.
export const CONVERT_TIMEOUT = 4000;
export const CONVERT_POLL = 200;

// Silent failures in a row before giving up on a hue. More than one, because a throttled or
// stale attempt also looks silent, and giving up on hue 0 means hauling ordinary logs.
export const CONVERT_ATTEMPTS = 3;

// Backstop on the conversion loop. One pass converts one stack, so this bounds a haul.
export const MAX_CONVERT_PASSES = 60;

// Buffer, so the stop lands before the shard starts refusing to move the new logs
export const WEIGHT_BUFFER = 40;

// Guesses for a RunUO-family shard. Correct these against the real journal after the first run -
// a phrase that never matches shows up as 'unknown' outcomes, not as a silent wrong turn.
export const OUTCOME_TEXT = {
  chopped: ['You put', 'You hack at the tree', 'You chop some'],
  empty: ["There's not enough wood here to harvest", 'There are no logs left'],
  // "You can't use an axe on that" is UOAlive's wording, seen on a live run against an
  // 'o'hii tree' static (0xc9e) - the tiledata calls it a tree, the shard will not harvest it
  notTree: [
    "You can't use an axe on that",
    "You can't chop that",
    "You can't use a bladed item on that",
    'You cannot chop',
  ],
  tooFar: ['That is too far away', 'You cannot reach that'],
  // Confirmed from a live run. Line of sight, not range - the tile is inside CHOP_RANGE and the
  // shard still will not have it, so no amount of walking closer or waiting fixes it.
  notSeen: ['Target cannot be seen'],
  wornOut: ['You have worn out your tool'],
  // The shard freezing to write its world file. Nothing works while it does: the swing is refused,
  // the journal answers with none of the wordings above, and every cycle of it reads as an
  // unreadable outcome - five in a row and the run is over. It is not a failure of anything and
  // nothing about the tree is learned from it; it is a pause. Found on a live mining run.
  saving: SAVING_TEXT,
  // Full wordings first: the bare prefix also catches "You must wait N seconds" from systems that
  // have nothing to do with harvesting, and reading one of those as a chop throttle is how a swing
  // that was never refused ends up being retried forever. Kept last as a fallback all the same -
  // a phrase this list misses reads as an unreadable outcome, which is worse.
  throttled: ['You must wait to perform another action', 'You must wait a moment', 'You must wait'],
};
