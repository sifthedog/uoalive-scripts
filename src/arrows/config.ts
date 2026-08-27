export {
  HEARTBEAT_EVERY,
  MAX_CYCLES,
  PACK_LIMIT,
  SAVE_DONE_TEXT,
  SAVE_POLL,
  SAVE_WAIT,
  SAVING_TEXT,
} from '../lib/timings.js';

export const AMMO_GRAPHICS = [
  0x0f3f, // arrow
  0x1bfb, // crossbow bolt
];

// The shard's own reach. Nothing in this script walks, so a stack further out is left alone.
export const GRAB_RANGE = 2;

// Between one move and the next. Low enough to keep a sweep brisk; a shard that throttles below it
// leaves stacks behind for the next cycle rather than failing, so erring fast is the cheap direction.
export const MOVE_DELAY = 250;

// A pure client-side scan, no packet, so this costs nothing to make brisk
export const WATCH_POLL = 100;

// How long a sweep waits for the stacks to actually leave the floor, and how often it looks
export const SETTLE_TIMEOUT = 2000;
export const SETTLE_POLL = 100;

// Sweeps in a row that issued moves and shifted nothing
export const MAX_QUIET_SWEEPS = 5;

export const SWEEP_BACKOFF = 1000;
export const SWEEP_BACKOFF_MAX = 8000;

// So the stop lands before the shard starts refusing to move the next stack
export const WEIGHT_BUFFER = 20;
