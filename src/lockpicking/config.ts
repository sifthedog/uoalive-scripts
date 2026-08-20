import { SAVING_TEXT, THROTTLED_TEXT, UNSKILLED_TEXT } from '../lib/timings.js';

export {
  EQUIP_ATTEMPTS,
  EQUIP_POLL,
  EQUIP_TIMEOUT,
  HEARTBEAT_EVERY,
  LOG_EVERY,
  MAX_CYCLES,
  MAX_NO_CURSOR,
  MAX_THROTTLED,
  NO_CURSOR_READ,
  SAVE_DONE_TEXT,
  SAVE_POLL,
  SAVE_WAIT,
  SAVING_TEXT,
  TARGET_TIMEOUT,
  THROTTLE_BACKOFF,
  THROTTLE_BACKOFF_MAX,
} from '../lib/timings.js';

// The client's tenths - 1000 is 100.0
export const GOAL = 1000;

// 0x14fb is the stock art. A lockpick found by name teaches the run whatever this shard uses.
export const LOCKPICK_GRAPHICS = new Set([0x14fb]);

export const LOCKPICK_NAME = 'lockpick';

// The double-click on the container before the one on the lockpick. Some shards will not open a
// lockpicking cursor for a container the client has never asked about.
export const POKE_BOX = true;
export const POKE_DELAY = 600;

export const ATTEMPT_DELAY = 1200;
export const PICK_TIMEOUT = 5000;

// The skill list arrives asynchronously, so the opening read is polled for
export const SKILL_TIMEOUT = 5000;
export const SKILL_POLL = 250;

// A client that has gone quiet about the skill is a blip, not an ending, so it has a budget of its own
export const MAX_BLIND_READS = 20;

// Well above the shared figures: at high skill a run legitimately picks for many minutes between
// tenths, and the only thing this counts is cycles where neither the journal nor the skill moved.
export const STALL_WARN = 100;
export const STALL_STOP = 1000;

export const OPL_TIMEOUT = 1000;

// Guesses for a RunUO-family shard. Correct them against the real journal after the first run - a
// phrase that never matches shows up as an 'unknown' outcome, not as a silent wrong turn.
export const OUTCOME_TEXT = {
  // What training is made of: a lock that will not open still rolls the skill
  failed: ['You are unable to pick the lock'],
  broke: ['You broke the lockpick', 'You have broken your lockpick', 'You broke your lockpick'],
  picked: ['You successfully pick the lock', 'You pick the lock'],
  // Before the bare wordings UNSKILLED_TEXT ends with, since outcomeFor takes the first bucket that matches
  tooHard: ['This lock cannot be picked by you', 'The lock is too complex', ...UNSKILLED_TEXT],
  notLocked: ['This does not appear to be locked', 'That does not appear to be locked'],
  tooFar: ['That is too far away', 'You cannot reach that'],
  noPicks: ['You do not have any lockpicks'],
  saving: SAVING_TEXT,
  throttled: THROTTLED_TEXT,
};
