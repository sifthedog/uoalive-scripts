// Re-exported rather than imported directly so this file stays the only one consumers import.
export { HEARTBEAT_EVERY, MAX_CYCLES } from '../lib/timings.js';

export const KEEP = 0;

// A sell gump lists a limited number of entries, so reopen it until nothing matches
export const MAX_PASSES = 10;

// A backstop only - the selection ends when you press ESC
export const MAX_PICKS = 20;

export const GUMP_TIMEOUT = 5000;

// Paid only when a pass is due: a run that sold everything listed does not ask twice
export const SELL_DELAY = 1500;

// sendSellRequest's boolean only says the packet went out, so the goods leaving the pack is the
// only proof the vendor took them
export const SALE_TIMEOUT = 3000;
export const SALE_POLL = 200;

export const OPL_TIMEOUT = 2000;

// Off, because this shard's vendors sell out of a bag in your pack, as stock RunUO does. Set true
// only where vendors offer the top level of the pack and nothing below it.
export const HOIST_FROM_BAGS = false;

// Moves are asynchronous, so this is a pause between them rather than a wait for one to land
export const MOVE_DELAY = 600;

// A double-click has to reach the server and the contents have to come back
export const OPEN_DELAY = 800;

export const MAX_HOIST_PASSES = 5;

// sell-watch only. A sale costs the same whether it moves one item or forty, so this is the batch.
// Counted by stack amount, not by slot, so for something that stacks this is the only trigger that
// fires - a non-stacking pile reaches SELL_AT_SLOTS first and sells on that instead.
export const SELL_AT = 30;

// The other way a sale becomes due. Under the 125-item cap rather than at it, so the sale happens
// while there is still space to work in.
export const SELL_AT_SLOTS = 110;

// Counting is silent - it reads the pack, it does not open a gump - so this can be brisk.
export const WATCH_POLL = 5000;

// A sale that took nothing means a vendor out of earshot, out of gold, or refusing in silence -
// indistinguishable from here, and none of them fixed by asking again immediately.
export const WATCH_BACKOFF = 10_000;
export const WATCH_BACKOFF_MAX = 120_000;

// Without it a watch left next to a vendor that has stopped buying stands there all afternoon.
export const MAX_QUIET_SALES = 5;
