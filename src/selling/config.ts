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

// A vendor only offers what is at the top level of your pack, so matching items sitting in a bag
// inside it are moved out before the sale. Set false to sell only what is already loose.
export const HOIST_FROM_BAGS = true;

// Moves are asynchronous, so this is a pause between them rather than a wait for one to land
export const MOVE_DELAY = 600;

// A double-click has to reach the server and the contents have to come back
export const OPEN_DELAY = 800;

// How many times the pack may be rescanned while items are still shifting out of bags
export const MAX_HOIST_PASSES = 5;
