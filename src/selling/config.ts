// Tuned once, in src/lib/timings.ts, and re-exported here so this file stays the only one any
// consumer imports. To give selling its own value for one of these, delete it from this list and
// declare it below.
export { HEARTBEAT_EVERY, MAX_CYCLES } from '../lib/timings.js';

// Leave this many behind in your pack
export const KEEP = 0;

// A sell gump lists a limited number of entries, so reopen it until nothing matches
export const MAX_PASSES = 10;

// How long the vendor gump may take to arrive
export const GUMP_TIMEOUT = 5000;

// The pause before reopening the gump, which is paid only when a pass is actually due - a run that
// sold everything the vendor listed stops without saying 'vendor sell' a second time
export const SELL_DELAY = 1500;

// A sale is polled for, not slept through: sendSellRequest's boolean only says the packet went out,
// so the goods leaving the pack is the only proof the vendor took them.
export const SALE_TIMEOUT = 3000;
export const SALE_POLL = 200;

// How long to wait for tooltip data on the targeted item
export const OPL_TIMEOUT = 2000;

// Whether this shard's vendors are blind to sub-containers. They are not: the sell gump lists what
// is inside a bag in your pack and sells it from there, which is what stock RunUO does - its
// GenericSellInfo walks the backpack recursively. So nothing needs moving before a sale, and the
// hoist is left off: it is a pile of double-clicks and moves for an answer the vendor already has.
//
// Set true only on a shard whose vendors offer the top level of the pack and nothing below it.
export const HOIST_FROM_BAGS = false;

// Moves are asynchronous, so this is a pause between them rather than a wait for one to land
export const MOVE_DELAY = 600;

// A double-click has to reach the server and the contents have to come back
export const OPEN_DELAY = 800;

// How many times the pack may be rescanned while items are still shifting out of bags
export const MAX_HOIST_PASSES = 5;

// --- sell-watch only ---

// How many of the watched item have to pile up before it is worth saying 'vendor sell'. The whole
// point of the watch is to batch: a sale costs speech, a gump and a round trip whether it moves one
// item or forty, so this is how much work each of those is made to do.
export const SELL_AT = 30;

// The other way a sale becomes due. A container holds 125 items and the shard starts refusing what
// will not fit, so a pack filling with something *other* than the watched item still needs the room
// the watched item is taking up. Under the cap rather than at it, so the sale happens while there
// is still space to work in - the same reasoning as PACK_LIMIT in the harvest scripts.
export const SELL_AT_SLOTS = 110;

// How often the pack is counted. Counting is silent - it reads the pack, it does not open a gump -
// so this can be brisk without the character standing there talking to itself.
export const WATCH_POLL = 5000;

// A sale that took nothing means the vendor is out of earshot, out of gold, refusing in silence, or
// counting something whose name does not match what the gump lists. They are indistinguishable from
// here and none of them is fixed by asking again immediately, so back off further each time rather
// than shouting 'vendor sell' every WATCH_POLL. Same helper the harvest scripts use on a throttle.
export const WATCH_BACKOFF = 10_000;
export const WATCH_BACKOFF_MAX = 120_000;

// Fruitless sales in a row before the run gives up. Without it a watch left next to a vendor that
// has stopped buying stands there all afternoon, saying so every couple of minutes.
export const MAX_QUIET_SALES = 5;
