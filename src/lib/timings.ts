// Defaults the harvest scripts agreed on name-for-name, kept in one place so a value tuned against
// the shard is tuned once. A folder's config.ts re-exports what it takes unchanged and declares its
// own where it differs, so every consumer still imports from './config.js' and the folder is still
// the one place to look.
//
// Only put a constant here when the two scripts mean the same thing by it. CHOP_TIMEOUT and
// DIG_TIMEOUT are both 8000 and REGROW_DELAY and RESPAWN_DELAY are both 25 minutes, but those are
// independent facts about the shard that happen to share a number today - sharing them would tie
// two unrelated knobs together and hide it.

// How far to look. The scan is a box, so this costs getTerrainList calls quadratically
export const SCAN_RADIUS = 12;

// A tile a walk never closed on. Deliberately not permanent: what blocked the path is usually
// another player or a pet, and a write-off would outlive the run.
export const UNREACHABLE_DELAY = 5 * 60 * 1000;

// How long to sleep at a time while waiting for a resource to come back, and how often to say so.
// The wait is sliced rather than slept through in one go: a single blocking sleep of minutes leaves
// the client unresponsive for all of them, with no way to stop the script.
export const IDLE_POLL = 10_000;
export const IDLE_LOG_EVERY = 60_000;

// Pause between cycles of the main loop
export const STEP_DELAY = 300;

// Pause after each step, to stay under the server's movement throttle
export const WALK_DELAY = 300;

// How long to wait for a target cursor. Without an explicit value the client falls back to its own
// default, which is long enough to look like a hang.
export const TARGET_TIMEOUT = 2000;

// How long to wait for an equip to reach the hand layer, and how many times to reissue it
export const EQUIP_TIMEOUT = 2000;
export const EQUIP_POLL = 200;
export const EQUIP_ATTEMPTS = 3;

// Backstop on the main loop, so a misread outcome cannot swing forever
export const MAX_CYCLES = 5000;

// How often the loop says it is still alive, whatever it is doing. Every branch of an outcome switch
// can go quiet - one of them indefinitely - and a silent script standing still is indistinguishable
// from a hung one. This is the line that tells them apart.
export const HEARTBEAT_EVERY = 30_000;

// Cycles without progress before the run complains, and before it gives up. Waiting for a resource
// to come back does not count: that one is intended, and it reports itself.
export const STALL_WARN = 60;
export const STALL_STOP = 300;

// Consecutive "you must wait" refusals before giving up, and the backoff between them. The pause
// grows by THROTTLE_BACKOFF each time so a real harvest delay is out-waited within a couple of
// swings, rather than being re-armed by a retry that comes back faster than the shard's own timer.
export const MAX_THROTTLED = 20;
export const THROTTLE_BACKOFF = 1000;
export const THROTTLE_BACKOFF_MAX = 8000;

// Consecutive unreadable outcomes before giving up. A wrong OUTCOME_TEXT trips this immediately,
// which is the point: better to stop and be told than to flail at a tile for an hour.
export const MAX_UNKNOWN = 5;

// Steps to spend walking to one tile before writing it off as unreachable
export const MAX_STEPS = 20;

// The container's item cap
export const PACK_LIMIT = 120;

// Progress line every this many actions that landed
export const LOG_EVERY = 25;

// How long to sit out a world save before carrying on regardless, and how often to look for the line
// that says it is over. Sliced rather than slept through, for the same reason the idle wait is.
export const SAVE_WAIT = 60_000;
export const SAVE_POLL = 1000;

// What the shard says when it has finished writing its world file. Missing it costs SAVE_WAIT of
// standing still rather than anything worse, which is why the fallback is a plain timeout.
export const SAVE_DONE_TEXT = ['World save complete', 'Save complete', 'World save is complete'];

// Named separately from any OUTCOME_TEXT bucket, because the conversions have no outcomes at all and
// would otherwise read a frozen server as a resource that cannot be worked
export const SAVING_TEXT = ['The world is saving', 'Saving world', 'World save started'];

// The shard saying outright that you cannot work this material, which is the one failure no amount
// of retrying fixes. Guesses, like OUTCOME_TEXT; a folder with a wording of its own prepends it.
export const UNSKILLED_TEXT = [
  'You are not skilled enough',
  'You lack the required skill',
  'You do not have enough skill',
];
