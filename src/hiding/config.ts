import { SAVING_TEXT, THROTTLED_TEXT, UNSKILLED_TEXT } from '../lib/timings.js';

export {
  HEARTBEAT_EVERY,
  LOG_EVERY,
  SAVE_DONE_TEXT,
  SAVE_POLL,
  SAVE_WAIT,
  SAVING_TEXT,
  STALL_STOP,
  STALL_WARN,
} from '../lib/timings.js';

// The client's tenths - 1000 is 100.0
export const HIDING_GOAL = 1000;
export const STEALTH_GOAL = 1000;

// The shard's own timer refuses most attempts at this cadence, which is expected and costs a journal
// read and nothing else.
export const ATTEMPT_DELAY = 500;

// Matched to ATTEMPT_DELAY so a shard that says nothing costs the delay rather than several of them
export const HIDE_TIMEOUT = 500;
export const STEALTH_TIMEOUT = 500;

// Far above the shared figure: most cycles are refusals, not attempts
export const MAX_CYCLES = 50_000;

// The skill list arrives asynchronously, so the opening read is polled for
export const SKILL_TIMEOUT = 5000;
export const SKILL_POLL = 250;

// A client gone quiet about a skill is a blip, not an ending, so it has a budget of its own
export const MAX_BLIND_READS = 20;

// Only 'You have hidden yourself well' is confirmed on this shard. The rest are RunUO-family
// guesses; a phrase that never matches shows up as an 'unknown' outcome, not as a silent wrong turn.
export const HIDE_TEXT = {
  hidden: ['You have hidden yourself well'],

  // Most of what training is made of: a refused hide rolls the skill exactly as a successful one does
  failed: ["You can't seem to hide here", 'You cannot seem to hide here'],

  busy: ['You are busy doing something else and cannot hide'],
  saving: SAVING_TEXT,
  throttled: THROTTLED_TEXT,
};

export const STEALTH_TEXT = {
  quietly: ['You begin to move quietly'],

  // Rolls the skill and reveals you, which is the signal to hide again
  failed: ['You fail in your attempt to move unnoticed'],

  notHidden: ['You must hide first'],

  // Before the bare wordings UNSKILLED_TEXT ends with, since outcomeFor takes the first bucket that matches
  notHiddenWell: ['You are not hidden well enough', ...UNSKILLED_TEXT],

  armour: ['You could not hide unless you were wearing lighter armor'],
  saving: SAVING_TEXT,
  throttled: THROTTLED_TEXT,
};
