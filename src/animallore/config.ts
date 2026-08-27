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

// Text off the lore gump itself, so it is recognised without knowing its serial. Its own wording,
// not 'Attributes', which half the gumps in the game carry.
export const LORE_GUMP_TEXT = 'Loyalty Rating';

// The gump on this shard draws its own close button, which means the server may have sent it
// non-closable - a right-click and the client-side close both do nothing to one of those. Set this
// to the button id the X answers to if close() turns out not to shut it; the run says so once.
export const LORE_GUMP_BUTTON: number | undefined = undefined;

// How long a read is given to produce either a gump or a sentence, and how often both are checked.
// Polled rather than waited on: a read that works says nothing at all, so a plain journal wait would
// cost the whole timeout on every success.
export const LORE_TIMEOUT = 2000;
export const LORE_POLL = 150;

// The pause between reads. Only a floor: the shard's own skill timer is not something the client can
// be asked for, so pace.ts raises this until the refusals stop.
export const READ_DELAY = 1000;
export const PACE_STEP = 400;
export const PACE_MAX = 8000;

// Reads that have to land before the pace eases back down. More than one, because easing after a
// single success oscillates between a read and a refusal and spends half the run waiting.
export const PACE_EASE_AFTER = 5;

// The skill list arrives asynchronously, so the opening read is polled for
export const SKILL_TIMEOUT = 5000;
export const SKILL_POLL = 250;

// A client that has gone quiet about the skill is a blip, not an ending, so it has a budget of its own
export const MAX_BLIND_READS = 20;

// A pet wanders, so being out of range is a wait rather than a stop - until it is plainly not coming back
export const MAX_AWAY = 20;

export const OPL_TIMEOUT = 1000;

// Well above the shared figures: at high skill a run legitimately reads for many minutes between
// tenths, and the only thing this counts is cycles where neither the journal nor the skill moved.
export const STALL_WARN = 100;
export const STALL_STOP = 1000;

// Guesses for a RunUO-family shard. Correct them against the real journal after the first run - a
// phrase that never matches shows up as an 'unknown' outcome, not as a silent wrong turn.
//
// There is no bucket for a read that worked, because the shard says nothing when one does. The gump
// is the whole of the proof, which is why lore.ts polls for it rather than for a sentence.
export const OUTCOME_TEXT = {
  // A failed skill check, and still the other half of the training: the roll happened either way
  missed: ["You can't think of anything you know offhand", 'You cannot think of anything'],
  notAnimal: ["That's not an animal", 'That is not an animal', 'You have no idea what that is'],
  notYours: ['You can only lore tamed creatures'],
  tooFar: ['That is too far away', 'You cannot see that', 'Target cannot be seen'],
  unskilled: UNSKILLED_TEXT,
  saving: SAVING_TEXT,
  throttled: THROTTLED_TEXT,
};
