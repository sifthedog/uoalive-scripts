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
  THROTTLE_BACKOFF,
  THROTTLE_BACKOFF_MAX,
} from '../lib/timings.js';

// The client's tenths - 1000 is 100.0
export const GOAL = 1000;

// A floor, not the cadence: nothing in the API reports the shard's skill timer, so pace.ts raises
// this until the refusals stop.
export const USE_DELAY = 1000;
export const PACE_STEP = 400;
export const PACE_MAX = 8000;

// Easing after a single landed read oscillates between a read and a refusal
export const PACE_EASE_AFTER = 5;

// Matched to USE_DELAY so a shard that words its results differently costs one delay, not several
export const EVAL_TIMEOUT = 1000;

// The skill list arrives asynchronously
export const SKILL_TIMEOUT = 5000;
export const SKILL_POLL = 250;

export const MAX_BLIND_READS = 20;

// Above the shared 60/300: at high skill a run legitimately reads for many minutes between tenths
export const STALL_WARN = 100;
export const STALL_STOP = 1000;

// RunUO-family guesses. A phrase that never matches shows up as an 'unknown' outcome, not as a
// silent wrong turn.
export const OUTCOME_TEXT = {
  // A failed check rolls the skill too, so these are half of what the training is made of
  missed: [
    'You cannot judge their mental abilities',
    'You have no idea of their mental abilities',
    'You cannot judge that creature',
  ],

  // Stems the whole ladder shares rather than its rungs. Not 'mental', which the misses carry.
  evaluated: ['intellect', 'mind'],

  unskilled: UNSKILLED_TEXT,
  saving: SAVING_TEXT,
  throttled: THROTTLED_TEXT,
};
