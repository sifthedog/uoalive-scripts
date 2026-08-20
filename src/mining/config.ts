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
  WALK_DELAY,
  WATCH_FOR_TROUBLE,
} from '../lib/timings.js';

// Imported as well as re-exported: OUTCOME_TEXT aliases SAVING_TEXT into its own `saving` bucket,
// while the smelt has no outcomes at all and checks the same wordings directly.
import {
  SAVING_TEXT,
  THROTTLED_TEXT as SHARED_THROTTLED_TEXT,
  UNSKILLED_TEXT as SHARED_UNSKILLED_TEXT,
} from '../lib/timings.js';

export const PICKAXE_NAME = 'pickaxe';

// Worth setting if the spares are inside a bag inside another bag: openContainers only opens the top
// level of the pack, so a nested bag is never reached.
export const SPARE_BAG_SERIAL: number | undefined = undefined;

// A table because these cannot be identified by name: getStatic reads the *static* tiledata, and a
// mountainside is a land tile, which getTile answers for with flags and no name at all.
//
// These are the stock RunUO bands and a hypothesis about this shard. A dead-end run prints the arts
// it actually saw, which is what settles the real numbers.
const range = (from: number, to: number): number[] =>
  Array.from({ length: to - from + 1 }, (_, offset) => from + offset);

export const ORE_TILE_GRAPHICS = new Set([
  ...range(220, 251),
  ...range(1339, 1359),
  ...range(1361, 1383),
  ...range(1386, 1394),
]);

// A seed only - a refusal learned on the shard goes into the run's memory rather than back in here.
// Unlike the runtime bans this one is not split by land and static: it is hand-written, so banning
// both directions is the harmless way to be wrong.
export const NOT_ORE_GRAPHICS = new Set<number>();

// Cave floors are statics rather than land, and those the client can name. Wider than it looks:
// 'rock' also names the pebbles scattered over half the world. That is the cheap direction to be
// wrong in - the first swing answers "you can't mine that" and markNotMineable bans the art.
export const ORE_STATIC_NAME = /cave|rock|mountain|ore/i;

// Not a range the shard enforces - the swing answers the cursor with yourself and lets the shard
// pick the ore - but the distance at which the scan stops walking and starts mining.
export const MINE_RANGE = 2;

// How long before a tile that answered "there is no ore here" is worth returning to
export const RESPAWN_DELAY = 25 * 60 * 1000;

// A swing plays its animation before the result arrives, so this has to outlast the animation
export const DIG_TIMEOUT = 8000;

// Longer than the shared TARGET_TIMEOUT, because the cursor is waited for by polling two signals
export const DIG_TARGET_TIMEOUT = 4000;
export const DIG_TARGET_POLL = 100;

// The cursor the shard opens for a swing. Read only to tell a shard that refused the action apart
// from one that asked and had its cursor missed - the two are the same 'no cursor' without it.
export const DIG_PROMPT_TEXT = ['Where do you wish to dig'];

// A set to be matched against and nothing more. The stock tables call these the 1, 2, 3 and 4+
// sizes; on this shard they are not that - a pile of 33 arrives wearing the one called a single. Use
// item.amount to read a stack's size.
export const ORE_GRAPHICS = new Set([0x19b7, 0x19ba, 0x19b9, 0x19b8]);

// The fallback for a shard whose ore wears an art this set has never heard of. A whole word: 'ore'
// inside 'more' or 'sycamore' would put something in the smelter that was never meant to go there.
export const ORE_NAME = /\bore\b/i;

// A seed only: the real graphics are learned by diffing the pack across the first successful smelt.
export { INGOT_GRAPHICS } from '../lib/arts.js';

// Pause after each ore combine, to stay under the server's action throttle
export const COMBINE_DELAY = 700;

// A combine is silent whether it lands or not, so the pack is polled for the proof rather than slept
// through: the throttle can hold one well past a fixed pause.
export const COMBINE_TIMEOUT = 2000;
export const COMBINE_POLL = 200;

// Attempts per groupOres call. A pack holding several metals can spend one refusal per metal on every
// new pile, and this is what keeps that off the swing loop.
export const MAX_COMBINE_ATTEMPTS = 12;

// The shard refusing two piles as different metals, which is what tells the metals apart here - hue
// reads 0 for a pile the client has not been sent the properties of. Stock RunUO wording, a guess.
export const DIFFERENT_ORE_TEXT = ['You cannot combine ores of different metals'];

// A swing's ore arrives after the sentence that announced it, so grouping the instant the journal
// reads 'dug' can consolidate a pack the new pile has not turned up in yet.
export const ORE_SETTLE_TIMEOUT = 1500;
export const ORE_SETTLE_POLL = 150;

// The fire beetle is the whole reason this script does not need a forge. The search logs the name
// and body of whatever it finds, so a wrong guess here is visible rather than silent.
export const FIRE_BEETLE_GRAPHICS = new Set([0xa9]);
export const FIRE_BEETLE_SERIAL: number | undefined = undefined;

// A cursor at startup, so the beetle is chosen rather than guessed at by body and renamability -
// which picks a stranger's pet if theirs is the nearer one. ESC falls back to that search.
export const PICK_BEETLE = true;

export const BEETLE_SCAN_RADIUS = 18;
export const SMELT_RANGE = 2;

// The ore keeps, so a walk that does not close costs a pass rather than the run.
export const MAX_BEETLE_STEPS = 24;

// Pause after each smelt, to stay under the server's action throttle
export const SMELT_DELAY = 700;

// Polled rather than slept through: the throttle can delay a smelt well past a fixed pause, and
// reading too early looks like a failure.
export const SMELT_TIMEOUT = 4000;
export const SMELT_POLL = 200;

// Two ore make an ingot, so a stack of one is refused - silently, in a way the pack diff cannot tell
// from a throttled attempt. Left alone it would burn SMELT_ATTEMPTS and write off the whole hue.
// groupOres piles a hue together first, so what is still at one afterwards is the odd ore out.
export const MIN_SMELT_AMOUNT = 2;

// More than one, because a throttled or stale attempt also looks silent, and giving up on hue 0
// means carrying plain iron ore around.
export const SMELT_ATTEMPTS = 3;

// One pass smelts one stack, so this bounds a smelt.
export const MAX_SMELT_PASSES = 60;

// The shared wordings plus mining's own, about a coloured ore needing the skill to work it
export const UNSKILLED_TEXT = [
  'You have no idea how to smelt this strange ore',
  ...SHARED_UNSKILLED_TEXT,
];

export const DISMOUNT_TIMEOUT = 2000;
export const DISMOUNT_POLL = 200;
export const DISMOUNT_ATTEMPTS = 3;

// Spots in a row with nothing to harvest before the run points at the likely cause. Not a stop of
// its own - roaming past a few worked-out spots is ordinary, and the stall watchdog already bounds a
// run that never lands a swing.
export const NOTHING_NEARBY_HINT = 5;

// Guesses for a RunUO-family shard. Correct these against the real journal after the first run - a
// phrase that never matches shows up as 'unknown' outcomes, not as a silent wrong turn.
export const OUTCOME_TEXT = {
  dug: ['You dig some', 'You put', 'You loosen some rocks'],
  // Both wordings are in the wild: RunUO says metal, some shards say ore.
  empty: [
    'There is no metal here to mine',
    'There is no ore here to mine',
    'You cannot mine there',
  ],
  // Confirmed from a live run. Distinct from `empty` because of that last word: this is the shard
  // answering about everything within reach, so it parks the whole area and walks the character
  // away. Read as `empty` it would park one tile and get the same sentence back from the same spot.
  nothingNearby: [
    'There are no harvestable resources nearby',
    'There is nothing here to harvest',
  ],
  // About the art rather than the tile, so the whole graphic is banned
  notOre: ["You can't mine that", 'Try mining in rock', 'You can only mine'],
  tooFar: ['That is too far away', 'You cannot reach that'],
  // Line of sight, not range: the tile is inside MINE_RANGE and no amount of walking closer or
  // waiting fixes it
  notSeen: ['Target cannot be seen'],
  // The ore is destroyed when this fires, not dropped, so it has to trigger a smelt rather than
  // another swing.
  packFull: ['Your backpack is full', 'That container cannot hold more'],
  wornOut: ['You have worn out your tool'],
  // Without a bucket of its own a world save reads as five unreadable outcomes in a row, which ended
  // a live run.
  saving: SAVING_TEXT,
  // Shared with the smelt, which has no outcomes to read a refusal as: to the conversion a throttle
  // is silence, and silence is what writes a hue off. One list, so a correction fixes both.
  throttled: SHARED_THROTTLED_TEXT,
};

// Capped because this prints into the middle of a run: enough to recognise the mountain you are
// standing on, not so many that the reason for the stop scrolls away.
export const SURVEY_ARTS = 15;
