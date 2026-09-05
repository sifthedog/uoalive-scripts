import { SAVING_TEXT, THROTTLED_TEXT, UNSKILLED_TEXT } from '../lib/timings.js';

export {
  HEARTBEAT_EVERY,
  LOG_EVERY,
  MAX_CYCLES,
  MAX_THROTTLED,
  SAVE_DONE_TEXT,
  SAVE_POLL,
  SAVE_WAIT,
  SAVING_TEXT,
  STALL_STOP,
  STALL_WARN,
  THROTTLE_BACKOFF,
  THROTTLE_BACKOFF_MAX,
  WALK_DELAY,
} from '../lib/timings.js';

// The shard accepts an attempt and answers seconds later, so the wait is in two stages: the first is
// how long it has to say it started or refuse outright, the second how long the started one has.
export const TAME_START_TIMEOUT = 3000;
export const TAME_RESOLVE_TIMEOUT = 15_000;

// Both waits are taken in slices this long rather than in one go, because the animal walks while the
// attempt resolves and a script sat in one long wait cannot follow it
export const TAME_WAIT_SLICE = 500;

// Walked into before every attempt rather than waited for, since the tooFar wordings are guesses and
// distanceTo is not
export const TAME_RANGE = 2;

// How far the run looks for the next animal of the type you picked, in Chebyshev tiles. 0 turns the
// hunt off and asks for every animal.
export const HUNT_RADIUS = 12;

// Closed to nearer than the range that triggers the walk, or one step by the animal puts it back out
// of reach and every cycle is a walk
export const TAME_APPROACH = 1;

// Higher than the shared MAX_STEPS: an ore vein stays where it was scanned and an animal does not
export const TAME_MAX_STEPS = 40;

// A floor, not the cadence: the shard's skill timer is not something the client can be asked for, so
// lib/pace.ts raises this until the refusals stop.
export const TAME_DELAY = 1500;
export const PACE_STEP = 400;
export const PACE_MAX = 8000;

// Easing after a single success oscillates between an attempt and a refusal
export const PACE_EASE_AFTER = 5;

// The creature has to cool off, which is a fixed wait rather than something the pace should learn
export const ANGRY_DELAY = 10_000;

export const MAX_AWAY = 10;
export const MAX_CONTESTED = 20;
export const MAX_ANGRY = 10;
export const MAX_PENDING = 10;

// A failed tame turns the animal on you, so this run has a health floor where animal-lore has none
export const HEALTH_FLOOR = 0.5;

export const SKILL_TIMEOUT = 5000;
export const SKILL_POLL = 250;

export const OPL_TIMEOUT = 1000;

// The client API has no rename call and nothing for releasing, so both go through the creature's
// context menu. Every wording below is a guess; a miss is a log line, not a wrong button.
export const PET_NAME: string = 'sifinha';

// What becomes of the animal once it is yours. 'kill' keeps it and puts it to work, 'release' hands
// the follower slot back, 'keep' does neither.
export const AFTER_TAME: 'kill' | 'release' | 'keep' = 'kill';

export const KILL_MENU_TEXT = ['Kill', 'Attack'];
export const KILL_CURSOR_TIMEOUT = 2000;

// Long, because this one is waiting on a person rather than on the shard
export const KILL_PICK_TIMEOUT = 60_000;
export const KILL_PICK_POLL = 250;

export const MENU_TIMEOUT = 2000;
export const PROMPT_TIMEOUT = 2000;

// Matched as case-insensitive fragments, so 'Command: Release' lands on the bare word
export const RENAME_MENU_TEXT = ['Rename'];
export const RELEASE_MENU_TEXT = ['Release'];

// The shard asks before it lets a pet go. Which button is 'yes' is not something the client reports,
// so the release is retried with each of these until the animal is actually let go.
export const RELEASE_CONFIRM_BUTTONS = [1, 2, 0];

// Fallback for a client that does not move Gump.lastSerial for this gump: fragments, because
// containsText is a case-insensitive substring match and the wording is a guess
export const RELEASE_CONFIRM_TEXT = ['release this creature', 'release this', 'Are you sure'];
export const RELEASE_CONFIRM_TIMEOUT = 1500;
export const RELEASE_CONFIRM_POLL = 150;

// isRenamable back to false is the proof that does not go through the journal
export const RELEASE_TIMEOUT = 3000;
export const RELEASE_POLL = 250;

// Guesses for a RunUO-family shard, apart from `tamed` and `failed` which are read off this one. A
// phrase that never matches shows up as an 'unknown' outcome, not as a silent wrong turn.
//
// Stored without the asterisks RunUO wraps its overhead lines in, so containsText still matches, and
// `angry` as a fragment because the shard prefixes the creature's name.
export const OUTCOME_TEXT = {
  tamed: ['It seems to accept you as master'],

  failed: ['You fail to tame the creature'],

  // Not a result: the attempt has been accepted and will answer in a few seconds
  starting: [
    'You start to tame the creature',
    'You continue to tame the creature',
    'You are already taming this creature',
  ],

  angry: ['is too angry to continue taming', 'You have been interrupted'],

  contested: ['Someone else is already taming this creature'],

  alreadyTame: ['That animal looks tame already'],

  hopeless: ['You have no chance of taming this creature'],

  notAnimal: ['That creature cannot be tamed', "You can't tame that", "That wasn't a valid target"],

  tooFar: [
    'You must be closer to attempt to tame this creature',
    'You are too far away to continue taming',
    'That is too far away',
    'You cannot see that',
  ],

  // Below the specific refusals: UNSKILLED_TEXT ends in bare prefixes, and the first bucket holding
  // a match is the one that wins
  unskilled: UNSKILLED_TEXT,

  saving: SAVING_TEXT,
  throttled: THROTTLED_TEXT,
};

