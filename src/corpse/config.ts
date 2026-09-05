export { CORPSE_GRAPHIC } from '../lib/arts.js';

// The shard's own reach. Nothing here walks, so a corpse further out is reported and left alone.
export const OPEN_RANGE = 2;

// Wider than reach on purpose: the point of looking past OPEN_RANGE is to be able to say 'yours is
// six tiles away' rather than nothing at all.
export const SCAN_RANGE = 18;

// A corpse you have never hovered has no tooltip at all, so every miss costs the full OPL_TIMEOUT
export const MAX_OPL_ASKS = 8;

export const OPL_TIMEOUT = 2000;

export const OPEN_DELAY = 800;

// Contents stay undefined until the shard answers the double-click
export const SETTLE_POLL = 100;
export const SETTLE_TIMEOUT = 2000;

// Stacks named in the log before it gives up and reports the totals
export const LOG_ITEMS = 40;

// RunUO's wording. Only what follows it is compared to your name, which is what keeps a guildmate
// whose name contains yours out of an exact match.
export const CORPSE_PREFIX = 'a corpse of ';
