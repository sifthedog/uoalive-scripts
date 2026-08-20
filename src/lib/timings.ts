// Defaults the scripts agreed on name-for-name. A folder's config.ts re-exports what it takes and
// declares its own where it differs.
//
// Only put a constant here when two scripts mean the same thing by it. CHOP_TIMEOUT and DIG_TIMEOUT
// are both 8000 and REGROW_DELAY and RESPAWN_DELAY are both 25 minutes, but those are independent
// facts about the shard that happen to share a number today.

// The scan is a box, so this costs getTerrainList calls quadratically
export const SCAN_RADIUS = 12;

// A tile a walk never closed on. Deliberately not permanent: what blocked the path is usually
// another player or a pet.
export const UNREACHABLE_DELAY = 5 * 60 * 1000;

// Sliced rather than slept through: a single blocking sleep of minutes leaves the client
// unresponsive for all of them, with no way to stop the script.
export const IDLE_POLL = 10_000;
export const IDLE_LOG_EVERY = 60_000;

export const STEP_DELAY = 300;

// Pause after each step, to stay under the server's movement throttle
export const WALK_DELAY = 300;

// Without an explicit value the client falls back to its own default, which is long enough to look
// like a hang.
export const TARGET_TIMEOUT = 2000;

export const EQUIP_TIMEOUT = 2000;
export const EQUIP_POLL = 200;
export const EQUIP_ATTEMPTS = 3;

// Backstop on the main loop, so a misread outcome cannot swing forever
export const MAX_CYCLES = 5000;

// Every branch of an outcome switch can go quiet - one of them indefinitely - and a silent script
// standing still is indistinguishable from a hung one. This is the line that tells them apart.
export const HEARTBEAT_EVERY = 30_000;

// Cycles without progress before the run complains, and before it gives up. Waiting for a resource
// to come back does not count: that one is intended, and it reports itself.
export const STALL_WARN = 60;
export const STALL_STOP = 300;

// The pause grows by THROTTLE_BACKOFF each time so a real harvest delay is out-waited within a
// couple of swings, rather than being re-armed by a retry that comes back faster than the shard's
// own timer.
export const MAX_THROTTLED = 20;
export const THROTTLE_BACKOFF = 1000;
export const THROTTLE_BACKOFF_MAX = 8000;

// A wrong OUTCOME_TEXT trips this immediately, which is the point: better to stop and be told than
// to flail at a tile for an hour.
export const MAX_UNKNOWN = 5;

// Generous like MAX_THROTTLED rather than tight like MAX_UNKNOWN, because this is a shard declining
// to start an action and not a script that cannot read one: a run once ended on five of these in
// fifteen seconds with a pickaxe plainly in hand.
export const MAX_NO_CURSOR = 20;

// The refusal that explains a missing cursor has usually arrived already - the journal was cleared
// immediately before the swing - so this is a short window for wording that lands a moment late.
export const NO_CURSOR_READ = 500;

export const MAX_STEPS = 20;

// The container's item cap
export const PACK_LIMIT = 120;

// Progress line every this many actions that landed
export const LOG_EVERY = 25;

// Sliced rather than slept through, for the same reason the idle wait is
export const SAVE_WAIT = 60_000;
export const SAVE_POLL = 1000;

// Missing it costs SAVE_WAIT of standing still rather than anything worse, which is why the fallback
// is a plain timeout.
export const SAVE_DONE_TEXT = ['World save complete', 'Save complete', 'World save is complete'];

// Named separately from any OUTCOME_TEXT bucket, because the conversions have no outcomes at all and
// would otherwise read a frozen server as a resource that cannot be worked
export const SAVING_TEXT = ['The world is saving', 'Saving world', 'World save started'];

// Full wordings first, with the bare prefix last as a fallback: 'You must wait N seconds' is said by
// systems that have nothing to do with harvesting, and reading one of those as a refusal here is
// harmless (a pass is skipped) where missing a real one is not (a hue is written off).
export const THROTTLED_TEXT = [
  'You must wait to perform another action',
  'You must wait a moment',
  'You must wait',
];

// The one failure no amount of retrying fixes. Guesses, like OUTCOME_TEXT; a folder with a wording
// of its own prepends it.
export const UNSKILLED_TEXT = [
  'You are not skilled enough',
  'You lack the required skill',
  'You do not have enough skill',
];

// SearchEntityOptions Gray|Criminal|Enemy|Murderer, as numbers so a bundle with nothing to do with
// combat does not read a client enum at startup. Innocent is out: every blue NPC would be trouble.
export const HOSTILE_NOTORIETY = 16 | 8 | 2 | 4;

// Criminal, Enemy and Murderer - the notorieties worth saying 'guards' at on sight alone. Gray is
// deliberately out of it: every wild cat and crow on this shard is gray, and one wandering past is
// not evidence of anything. A gray that actually draws blood still gets the call.
export const CALL_ON_SIGHT_NOTORIETY = 8 | 2 | 4;

// selectEntity takes no range at all - it answers with whatever the client is tracking - so this is
// the filter that makes 'the nearest hostile' mean anything.
export const THREAT_RANGE = 12;

export const WATCH_FOR_TROUBLE = true;

export const GUARD_CALL = 'guards';

// Calls per episode, 0 for no cap. More than one because a guard that arrives late, or kills one of
// two, leaves the run in the trouble it started in.
export const GUARD_CALLS = 3;
export const GUARD_CALL_DELAY = 10_000;

// Long enough for the shard to refuse, short enough that the next swing does not notice
export const GUARD_REPLY_WAIT = 800;

// The one answer worth acting on: a wording found here stops the run calling for the rest of it.
export const NO_GUARDS_TEXT = [
  'The guards can not be called here',
  'The guards cannot be called here',
  'Guards can not be called here',
  'Guards cannot be called here',
  'There are no guards here',
];

// Empty on purpose: nothing in stock RunUO announces being attacked, and a wrong guess here calls
// the guards at every cycle of a quiet run. Add what this shard actually says.
export const ATTACK_TEXT: string[] = [];

// Said only on crossing the boundary, so a run that started inside a town never sees either
export const GUARD_ZONE_TEXT = ['under the protection of the town guards', 'now under guard'];
export const UNGUARDED_TEXT = ['left the protection of the town guards', 'no longer under guard'];
