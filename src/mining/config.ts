// Tuned once, in src/lib/timings.ts, and re-exported here so this file stays the only one any
// consumer imports. To give mining its own value for one of these, delete it from this list and
// declare it below.
export {
  EQUIP_ATTEMPTS,
  EQUIP_POLL,
  EQUIP_TIMEOUT,
  HEARTBEAT_EVERY,
  IDLE_LOG_EVERY,
  IDLE_POLL,
  LOG_EVERY,
  MAX_CYCLES,
  MAX_NO_CURSOR,
  MAX_STEPS,
  MAX_THROTTLED,
  MAX_UNKNOWN,
  NO_CURSOR_READ,
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
  THROTTLED_TEXT,
  THROTTLE_BACKOFF,
  THROTTLE_BACKOFF_MAX,
  UNREACHABLE_DELAY,
  WALK_DELAY,
} from '../lib/timings.js';

// Imported as well as re-exported, because OUTCOME_TEXT below aliases SAVING_TEXT into its own
// `saving` bucket: the swing reads a save as an outcome, while the smelt has no outcomes at all and
// checks the same wordings directly.
import {
  SAVING_TEXT,
  THROTTLED_TEXT as SHARED_THROTTLED_TEXT,
  UNSKILLED_TEXT as SHARED_UNSKILLED_TEXT,
} from '../lib/timings.js';

export const PICKAXE_NAME = 'pickaxe';

// Optional: pin the bag the spare pickaxes live in instead of discovering it. Worth setting if the
// spares are inside a bag inside another bag - openContainers only opens the top level of the pack,
// so a nested bag is never reached, and pinning it here skips the search entirely.
export const SPARE_BAG_SERIAL: number | undefined = undefined;

// The land tiles the shard calls a mountain or a cave floor. Unlike lumberjacking's trees, these
// cannot be identified by name: getStatic reads the *static* tiledata, and a mountainside is a land
// tile, which getTile answers for with flags and no name at all. So a table it is.
//
// These are the stock RunUO bands and a hypothesis about this shard, nothing more. Stand on a
// mountainside and run dist/mine-probe.js: it lists every distinct graphic around you with its
// isLand flag, which is what settles the real numbers.
const range = (from: number, to: number): number[] =>
  Array.from({ length: to - from + 1 }, (_, offset) => from + offset);

export const ORE_TILE_GRAPHICS = new Set([
  ...range(220, 251),
  ...range(1339, 1359),
  ...range(1361, 1383),
  ...range(1386, 1394),
]);

// The override, and a seed only - a refusal learned on the shard goes into the run's memory rather
// than back into here. Put a graphic in ORE_TILE_GRAPHICS above if a mineable tile is skipped, and
// in here if the script keeps swinging at something that is not a vein. Unlike the runtime bans
// this one is not split by land and static: it is hand-written, so whoever writes it knows which
// they meant, and banning both directions is the harmless way to be wrong.
export const NOT_ORE_GRAPHICS = new Set<number>();

// Cave floors are statics rather than land, and those the client *can* name, so they go through the
// same tiledata match lumberjacking uses for trees. Wider than it looks: 'rock' also names the
// pebbles scattered over half the world, so this will pick up scenery. That is the cheap direction
// to be wrong in - the first swing at one answers "you can't mine that", markNotMineable bans the
// art, and the rest of its copies stop being walked to. Narrow it here if the run spends its first
// minutes learning the same lesson over and over.
export const ORE_STATIC_NAME = /cave|rock|mountain|ore/i;

// How close to stand before swinging. The swing itself names no tile - it answers the cursor with
// yourself and lets the shard pick the ore - so this is not a range the shard enforces but the
// distance at which the scan stops walking and starts mining. Two tiles is the stock harvest range;
// drop it to 1 if swings from two tiles away come back empty while the vein clearly is not.
export const MINE_RANGE = 2;

// A vein comes back, so a tile that answers "there is no ore here" is worth returning to. This is
// the wait before it is, and the one knob to turn if the script comes back to a vein still empty.
export const RESPAWN_DELAY = 25 * 60 * 1000;

// A swing plays its animation before the result arrives, so this has to outlast the animation
export const DIG_TIMEOUT = 8000;

// The arts an ore pile is drawn with. The stock tables call these the 1, 2, 3 and 4+ sizes, and on
// this shard they are not that: a pile of 33 arrives wearing the one the tables call a single. So
// this is a set to be matched against and nothing more - never a way to read a stack's size, which
// is what item.amount is for.
export const ORE_GRAPHICS = new Set([0x19b7, 0x19ba, 0x19b9, 0x19b8]);

// The fallback for a shard whose ore wears an art this set has never heard of, and the reason the
// pack in the screenshot reads '33 Ore' at all. A whole word, on the precedent of the key search in
// src/boxes: 'ore' inside 'more' or 'sycamore' would put something in the smelter that was never
// meant to go there. A graphic learned through this route is added to the set above, so the match
// costs one tooltip and then goes back to being a graphic lookup.
export const ORE_NAME = /\bore\b/i;

// A seed only: the real graphics are learned by diffing the pack across the first successful smelt,
// so a wrong guess here costs nothing.
export { INGOT_GRAPHICS } from '../lib/arts.js';

// Pause after each ore combine, to stay under the server's action throttle
export const COMBINE_DELAY = 700;

// A swing's ore arrives after the sentence that announced it, so grouping the instant the journal
// reads 'dug' can consolidate a pack the new pile has not turned up in yet. Polled rather than
// slept through, on the reasoning in convert.ts's waitForChange - the common case is that it has
// already landed and costs nothing, and the wait only shows up on the swings that need it.
export const ORE_SETTLE_TIMEOUT = 1500;
export const ORE_SETTLE_POLL = 150;

// The fire beetle is the whole reason this script does not need a forge. Stock body is 0xa9; the
// search logs the name and body of whatever it actually finds, so a wrong guess here is visible
// rather than silent. FIRE_BEETLE_SERIAL pins one exactly and skips the search.
export const FIRE_BEETLE_GRAPHICS = new Set([0xa9]);
export const FIRE_BEETLE_SERIAL: number | undefined = undefined;

// How far to look for the beetle, and how close you have to be to smelt against it
export const BEETLE_SCAN_RADIUS = 18;
export const SMELT_RANGE = 2;

// Steps to spend walking to the beetle before giving up on this smelt. The ore keeps, so a walk
// that does not close costs a pass rather than the run.
export const MAX_BEETLE_STEPS = 24;

// Pause after each smelt, to stay under the server's action throttle
export const SMELT_DELAY = 700;

// How long to watch the pack for a smelt landing. Polled rather than slept through: the throttle
// can delay it well past a fixed pause, and reading too early looks like a failure.
export const SMELT_TIMEOUT = 4000;
export const SMELT_POLL = 200;

// Two ore make an ingot, so a stack of one cannot be smelted at all - the shard simply refuses it.
// That refusal is silent in the pack diff and indistinguishable from a throttled attempt, so an
// unsmeltable single would burn SMELT_ATTEMPTS and then write off the whole hue, taking every
// future stack of it with it. Skipped by size instead, and skipped only for as long as it is that
// size: groupOres piles a hue together first, so what is still at one afterwards is genuinely the
// odd ore out, and the next swing that lands on it makes it two.
export const MIN_SMELT_AMOUNT = 2;

// Silent failures in a row before giving up on an ore. More than one, because a throttled or stale
// attempt also looks silent, and giving up on hue 0 means carrying plain iron ore around.
export const SMELT_ATTEMPTS = 3;

// Backstop on the smelting loop. One pass smelts one stack, so this bounds a smelt.
export const MAX_SMELT_PASSES = 60;

// The shared wordings plus mining's own, which is about a coloured ore needing the skill to work it
// and has no counterpart anywhere else
export const UNSKILLED_TEXT = [
  'You have no idea how to smelt this strange ore',
  ...SHARED_UNSKILLED_TEXT,
];

// How long to wait for the mount layer to clear, and how many times to reissue the double-click
export const DISMOUNT_TIMEOUT = 2000;
export const DISMOUNT_POLL = 200;
export const DISMOUNT_ATTEMPTS = 3;

// Spots in a row that had nothing to harvest before the run stops to point at the likely cause.
// Not a stop of its own: roaming past a few worked-out spots is ordinary, and the stall watchdog
// already bounds a run that never lands a swing. This is the hint, printed once.
export const NOTHING_NEARBY_HINT = 5;

// Guesses for a RunUO-family shard. Correct these against the real journal after the first run -
// a phrase that never matches shows up as 'unknown' outcomes, not as a silent wrong turn.
export const OUTCOME_TEXT = {
  dug: ['You dig some', 'You put', 'You loosen some rocks'],
  // What parks a vein for RESPAWN_DELAY. Both wordings are in the wild: RunUO says metal, some
  // shards say ore, and reading either one as unknown would stop the run on a worked-out vein.
  empty: [
    'There is no metal here to mine',
    'There is no ore here to mine',
    'You cannot mine there',
  ],
  // Confirmed from a live run on this shard. Distinct from `empty` because of that last word: this
  // one is the shard answering about everything within reach of where you are standing, which is
  // the only kind of answer a swing that names no tile can really get. It parks the whole area
  // rather than a tile, and that is what makes the character walk away - reading it as `empty`
  // would park one tile, swing again from the same spot, and get the same sentence back.
  nothingNearby: [
    'There are no harvestable resources nearby',
    'There is nothing here to harvest',
  ],
  // About the art rather than the tile, so the whole graphic is banned - the same lesson
  // lumberjacking learned when the tiledata called a whole family of statics a tree
  notOre: ["You can't mine that", 'Try mining in rock', 'You can only mine'],
  tooFar: ['That is too far away', 'You cannot reach that'],
  // Line of sight, not range - the tile is inside MINE_RANGE and the shard still will not have it,
  // so no amount of walking closer or waiting fixes it
  notSeen: ['Target cannot be seen'],
  // The ore is destroyed when this fires, not dropped, so it has to trigger a smelt rather than
  // another swing. Lumberjacking has no equivalent: it stops on weight long before the item cap.
  packFull: ['Your backpack is full', 'That container cannot hold more'],
  wornOut: ['You have worn out your tool'],
  // The shard freezing to write its world file. Nothing works while it does: the swing is refused,
  // the journal answers with none of the wordings above, and every cycle of it reads as an
  // unreadable outcome - five in a row and the run is over, which is what a save did to a live one.
  // It is not a failure of anything and nothing about the vein is learned from it; it is a pause.
  saving: SAVING_TEXT,
  // Shared with the smelt, which reads the same refusal with no outcomes to read it as: to the
  // conversion a throttle is silence, and silence is what writes a hue off. One list, so a wording
  // corrected against this shard's journal fixes both.
  throttled: SHARED_THROTTLED_TEXT,
};

// How far around you dist/mine-probe.js looks. Larger than SCAN_RADIUS on purpose: the probe is
// read once by a human, so it may as well cover more ground than the loop does.
export const PROBE_RADIUS = 16;

// How many arts the main loop lists when it finds nothing to mine. Capped where the probe is not,
// because this one prints into the middle of a run: enough to recognise the mountain you are
// standing on, not so many that the reason for the stop scrolls away above it.
export const SURVEY_ARTS = 15;
