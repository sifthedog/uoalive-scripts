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

// How far to look for a tree. The scan is a box, so this costs getTerrainList calls quadratically
export const SCAN_RADIUS = 12;

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

// A tile a walk never closed on. Shorter than REGROW_DELAY and deliberately not permanent: what
// blocked the path is usually another player or a pet, and this write-off now outlives the run.
export const UNREACHABLE_DELAY = 5 * 60 * 1000;

// How long to sleep at a time while waiting for a tile to regrow, and how often to say so. The wait
// is sliced rather than slept through in one go: a single blocking sleep of minutes leaves the
// client unresponsive for all of them, with no way to stop the script.
export const IDLE_POLL = 10_000;
export const IDLE_LOG_EVERY = 60_000;

// Pause between cycles of the main loop
export const STEP_DELAY = 300;

// How long to wait for the chop target cursor. Without an explicit value the client falls back
// to its own default, which is long enough to look like a hang.
export const TARGET_TIMEOUT = 2000;

// A swing plays its animation before the result arrives, so this has to outlast the animation
export const CHOP_TIMEOUT = 8000;

// Pause after each step, to stay under the server's movement throttle
export const WALK_DELAY = 300;

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

// Guesses, like OUTCOME_TEXT. Worth having: this is the shard saying outright that a wood cannot
// be worked, which is the one failure that no amount of retrying fixes.
export const UNSKILLED_TEXT = [
  'You are not skilled enough',
  'You lack the required skill',
  'You do not have enough skill',
];

// How long to wait for an equip to reach the hand layer, and how many times to reissue it
export const EQUIP_TIMEOUT = 2000;
export const EQUIP_POLL = 200;
export const EQUIP_ATTEMPTS = 3;

// Backstop on the main loop, so a misread outcome cannot swing forever
export const MAX_CYCLES = 5000;

// How often the loop says it is still alive, whatever it is doing. Every branch of the outcome
// switch used to be able to go quiet - one of them indefinitely - and a silent script standing
// still is indistinguishable from a hung one. This is the line that tells them apart.
export const HEARTBEAT_EVERY = 30_000;

// Cycles without a chop before the run complains, and before it gives up. Waiting for a tile to
// regrow does not count: that one is intended, and it reports itself.
export const STALL_WARN = 60;
export const STALL_STOP = 300;

// Consecutive "you must wait" refusals before giving up, and the backoff between them. The pause
// grows by BACKOFF each time so a real harvest delay is out-waited within a couple of swings,
// rather than being re-armed by a retry that comes back faster than the shard's own timer.
export const MAX_THROTTLED = 20;
export const THROTTLE_BACKOFF = 1000;
export const THROTTLE_BACKOFF_MAX = 8000;

// Consecutive unreadable outcomes before giving up. A wrong OUTCOME_TEXT trips this immediately,
// which is the point: better to stop and be told than to flail at a tree for an hour.
export const MAX_UNKNOWN = 5;

// Steps to spend walking to one tree before writing it off as unreachable
export const MAX_STEPS = 20;

// Buffer, so the stop lands before the shard starts refusing to move the new logs
export const WEIGHT_BUFFER = 40;
export const PACK_LIMIT = 120;

// Progress line every this many chops
export const LOG_EVERY = 25;

// How long to sit out a world save before carrying on regardless, and how often to look for the line
// that says it is over. Sliced rather than slept through, for the same reason the regrow wait is: a
// save that runs long must not leave the client unresponsive with no way to stop the script.
export const SAVE_WAIT = 60_000;
export const SAVE_POLL = 1000;

// What the shard says when it has finished writing its world file. Missing it costs SAVE_WAIT of
// standing still rather than anything worse, which is why the fallback is a plain timeout.
export const SAVE_DONE_TEXT = ['World save complete', 'Save complete', 'World save is complete'];

// Named separately from the OUTCOME_TEXT bucket below because three different things need it: the
// chop, which reads it as an outcome, and the board conversion and the haul, which have no outcomes
// at all and would otherwise read a frozen server as a wood that cannot be worked and an animal
// that will not take any more.
export const SAVING_TEXT = ['The world is saving', 'Saving world', 'World save started'];

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
