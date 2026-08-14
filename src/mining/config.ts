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

// How far to look for a vein. The scan is a box, so this costs getTerrainList calls quadratically
export const SCAN_RADIUS = 12;

// How close to stand before swinging. The swing itself names no tile - it answers the cursor with
// yourself and lets the shard pick the ore - so this is not a range the shard enforces but the
// distance at which the scan stops walking and starts mining. Two tiles is the stock harvest range;
// drop it to 1 if swings from two tiles away come back empty while the vein clearly is not.
export const MINE_RANGE = 2;

// A vein comes back, so a tile that answers "there is no ore here" is worth returning to. This is
// the wait before it is, and the one knob to turn if the script comes back to a vein still empty.
export const RESPAWN_DELAY = 25 * 60 * 1000;

// A tile a walk never closed on. Shorter than RESPAWN_DELAY and deliberately not permanent: what
// blocked the path is usually another player or a pet, and this write-off now outlives the run.
export const UNREACHABLE_DELAY = 5 * 60 * 1000;

// How long to sleep at a time while waiting for a vein to come back, and how often to say so. The
// wait is sliced rather than slept through in one go: a single blocking sleep of minutes leaves the
// client unresponsive for all of them, with no way to stop the script.
export const IDLE_POLL = 10_000;
export const IDLE_LOG_EVERY = 60_000;

// Pause between cycles of the main loop
export const STEP_DELAY = 300;

// Pause after each step, to stay under the server's movement throttle
export const WALK_DELAY = 300;

// How long to wait for a target cursor. Without an explicit value the client falls back to its own
// default, which is long enough to look like a hang.
export const TARGET_TIMEOUT = 2000;

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

// A seed only, and the same shape as the ore set because ingots stack the same way. The real
// graphics are learned by diffing the pack across the first successful smelt, so a wrong guess
// here costs nothing.
export const INGOT_GRAPHICS = new Set([0x1bef, 0x1bf2, 0x1bee, 0x1bf1]);

// Pause after each ore combine, to stay under the server's action throttle
export const COMBINE_DELAY = 700;

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

// Guesses, like OUTCOME_TEXT. Worth having: this is the shard saying outright that an ore cannot be
// worked, which is the one failure that no amount of retrying fixes.
export const UNSKILLED_TEXT = [
  'You have no idea how to smelt this strange ore',
  'You are not skilled enough',
  'You lack the required skill',
  'You do not have enough skill',
];

// How long to wait for the mount layer to clear, and how many times to reissue the double-click
export const DISMOUNT_TIMEOUT = 2000;
export const DISMOUNT_POLL = 200;
export const DISMOUNT_ATTEMPTS = 3;

// How long to wait for an equip to reach the hand layer, and how many times to reissue it
export const EQUIP_TIMEOUT = 2000;
export const EQUIP_POLL = 200;
export const EQUIP_ATTEMPTS = 3;

// Backstop on the main loop, so a misread outcome cannot swing forever
export const MAX_CYCLES = 5000;

// How often the loop says it is still alive, whatever it is doing. Every branch of the outcome
// switch can go quiet - one of them indefinitely - and a silent script standing still is
// indistinguishable from a hung one. This is the line that tells them apart.
export const HEARTBEAT_EVERY = 30_000;

// Cycles without a swing landing before the run complains, and before it gives up. Waiting for a
// vein to come back does not count: that one is intended, and it reports itself.
export const STALL_WARN = 60;
export const STALL_STOP = 300;

// Consecutive "you must wait" refusals before giving up, and the backoff between them. The pause
// grows by BACKOFF each time so a real harvest delay is out-waited within a couple of swings,
// rather than being re-armed by a retry that comes back faster than the shard's own timer.
export const MAX_THROTTLED = 20;
export const THROTTLE_BACKOFF = 1000;
export const THROTTLE_BACKOFF_MAX = 8000;

// Spots in a row that had nothing to harvest before the run stops to point at the likely cause.
// Not a stop of its own: roaming past a few worked-out spots is ordinary, and the stall watchdog
// already bounds a run that never lands a swing. This is the hint, printed once.
export const NOTHING_NEARBY_HINT = 5;

// Consecutive unreadable outcomes before giving up. A wrong OUTCOME_TEXT trips this immediately,
// which is the point: better to stop and be told than to flail at a rock for an hour.
export const MAX_UNKNOWN = 5;

// Steps to spend walking to one vein before writing it off as unreachable
export const MAX_STEPS = 20;

// Smelting is the one thing that frees weight here, and it only happens once you are actually over
// the limit - the shard starts refusing to move things at that point, which is the signal. There is
// deliberately no buffer: a threshold below the limit would just be a second, earlier limit, and the
// guards have no weight check for the same reason. What ends an overweight run is a smelt that
// freed nothing, not the weight itself.
export const PACK_LIMIT = 120;

// Progress line every this many swings that landed
export const LOG_EVERY = 25;

// How long to sit out a world save before carrying on regardless, and how often to look for the
// line that says it is over. The wait is sliced rather than slept through, for the same reason the
// respawn wait is: a save that takes longer than expected must not leave the client unresponsive
// with no way to stop the script.
export const SAVE_WAIT = 60_000;
export const SAVE_POLL = 1000;

// What the shard says when it has finished writing its world file. Missing it costs SAVE_WAIT of
// standing still rather than anything worse, which is why the fallback is a plain timeout.
export const SAVE_DONE_TEXT = ['World save complete', 'Save complete', 'World save is complete'];

// Named separately from the OUTCOME_TEXT bucket below because two different things need it: the
// swing, which reads it as an outcome, and the smelt, which has no outcomes at all and would
// otherwise read a frozen server as three silent failures and write the ore off as unworkable.
export const SAVING_TEXT = ['The world is saving', 'Saving world', 'World save started'];

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
  // Full wordings first: the bare prefix also catches "You must wait N seconds" from systems that
  // have nothing to do with harvesting, and reading one of those as a mining throttle is how a
  // swing that was never refused ends up being retried forever. Kept last as a fallback all the
  // same - a phrase this list misses reads as an unreadable outcome, which is worse.
  throttled: ['You must wait to perform another action', 'You must wait a moment', 'You must wait'],
};

// How far around you dist/mine-probe.js looks. Larger than SCAN_RADIUS on purpose: the probe is
// read once by a human, so it may as well cover more ground than the loop does.
export const PROBE_RADIUS = 16;

// How many arts the main loop lists when it finds nothing to mine. Capped where the probe is not,
// because this one prints into the middle of a run: enough to recognise the mountain you are
// standing on, not so many that the reason for the stop scrolls away above it.
export const SURVEY_ARTS = 15;
