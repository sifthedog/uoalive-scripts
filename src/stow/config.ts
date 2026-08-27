export {
  HEARTBEAT_EVERY,
  SAVE_DONE_TEXT,
  SAVE_POLL,
  SAVE_WAIT,
  SAVING_TEXT,
} from '../lib/timings.js';

// Local rather than the shared 5000, which is under three hours at WATCH_POLL - this one is meant
// to be left running
export const MAX_CYCLES = 20_000;

// A pack read is client-side, but it walks the whole tree and this loop runs all afternoon
export const WATCH_POLL = 2000;

// A double-click has to reach the server and the contents have to come back
export const OPEN_DELAY = 800;

// Between one move and the next. A throttled pass comes back partial rather than failing, so the
// stragglers go next cycle and erring fast is the cheap direction.
export const MOVE_DELAY = 250;

// How long a pass waits for the stacks to leave the pack, and how often it looks
export const SETTLE_TIMEOUT = 2000;
export const SETTLE_POLL = 100;

// Gates the double-clicking only, never the walking. Off leaves a bag dropped in mid-run invisible,
// since contents stay undefined until something opens it.
export const OPEN_NESTED = true;

// A bag that answers nothing however often it is opened is left alone rather than clicked all day
export const MAX_REOPENS = 3;

// Passes that issued moves and shifted nothing - a full destination, or one out of reach
export const MAX_QUIET_STOWS = 5;

export const STOW_BACKOFF = 2000;
export const STOW_BACKOFF_MAX = 60_000;

// Polls the client could not see the destination for. A minute, because riding two screens away and
// back is normal on a run this long.
export const MAX_LOST_DEST = 30;

// A backstop only - the selection ends when you press ESC
export const MAX_PICKS = 20;

export const OPL_TIMEOUT = 2000;

// A line per stack over an afternoon is a lot of log; the batch line carries the totals
export const LOG_EVERY_ITEM = false;
