// Wooden boxes. The graphic is the reliable matcher; an item's name is empty until the client has
// tooltip data for it. 0x0e7d is already in CONTAINER_GRAPHICS in src/lib/containers.ts, which is
// what confirms it; 0x0e7e is the same item's second art.
// 0x09aa is what UOAlive actually uses - identified by a live run off the name "Wooden Box", which
// is why the name fallback earns its keep. The 0x0e7d/0x0e7e pair was the stock-art guess and is
// kept in case another shard uses it.
export const BOX_GRAPHICS = new Set([0x09aa, 0x0e7d, 0x0e7e]);

// How the vendor's sell gump labels them. Matched case-insensitively and for equality, never as a
// substring, so 'small wooden box' and 'wooden boxes' do not get swept in.
export const BOX_NAME = 'wooden box';

// Keys go on the floor instead of into the pack. Anything a box holds that is *not* recognised as
// a key still goes into the pack, so an art missing from KEY_GRAPHICS costs a key you have to
// throw away by hand - never a possession on the floor.
export const DROP_KEYS = true;

// Where the keys land, as offsets from where you are standing, cycled through one per key. 0/0/0
// is your own tile. Spread across the ring rather than piled on one square because a shard that
// caps items per tile refuses the rest of the pile, and a refused drop costs the full DROP_TIMEOUT
// each - forty keys against one tile is a minute of nothing happening. Cut this to a single
// { x: 0, y: 0, z: 0 } to have everything land underfoot.
export const DROP_SPREAD = [
  { x: 0, y: 0, z: 0 },
  { x: 1, y: 0, z: 0 },
  { x: 0, y: 1, z: 0 },
  { x: 1, y: 1, z: 0 },
  { x: -1, y: 0, z: 0 },
  { x: 0, y: -1, z: 0 },
  { x: -1, y: -1, z: 0 },
  { x: 1, y: -1, z: 0 },
  { x: -1, y: 1, z: 0 },
];

// Say something every this many keys, so a long run is visibly working rather than apparently hung
export const LOG_EVERY_KEY = 5;

// Consecutive keys that will not drop before giving up. Without it a shard that has stopped
// accepting them costs DROP_TIMEOUT per key for the whole pile.
export const MAX_STUCK = 3;

// Which call actually drops an item on this shard. Pinned from what dist/key-probe.js proved on
// UOAlive: moveItemOnGroundOffset at 0/0/0 puts the key at your feet, and the offset turns out to
// be from where *you* are standing rather than from the item. 'auto' tries each in turn instead.
export const DROP_METHOD: 'auto' | 'groundOffset' | 'groundOffsetStep' | 'worldSerial' =
  'groundOffset';

// A drop is polled for, not slept through. Reading the container back too early says the key is
// still in the box when it is already on the floor, and the recovery for that - putting the key in
// the pack - then picks the key back *up* off the floor. 700ms flat was enough to do exactly that;
// the probe needed 1200ms to see it land.
export const DROP_TIMEOUT = 3000;
export const DROP_POLL = 200;

// Probe only: long enough to watch each attempt resolve on screen, since which one worked is read
// off the world rather than out of a return value
export const PROBE_DELAY = 1200;

// Which arts are keys. Matched alongside the name, so a key the client has tooltip data for is
// recognised whatever its graphic, and the first one found teaches the run the art for the rest.
export const KEY_GRAPHICS = new Set([0x100e, 0x100f, 0x1010, 0x1011, 0x1012, 0x1013]);

// Off: the run empties the boxes and stops, leaving them in the pack for you to do what you like
// with. Set true to have it say 'vendor sell' and offer the emptied boxes to whoever is in earshot.
export const SELL = false;

// Opening a pile of boxes leaves a pile of windows on screen.
//
// 'perBox' shuts each box's own window as soon as it has been emptied, by looking the gump up under
// the container's serial. Whether a container window is addressable that way is unverified - if it
// is not, the lookup answers nothing and no window closes, which is the harmless direction.
//
// 'allGumps' is the blunt one: `client.closeAllGumps()` at the end of the run. It works, but it
// closes *every* gump you have open - paperdoll, character, journal, backpack - because the client
// has no per-container close. That is why it is no longer the default.
export const CLOSE_BOXES: 'never' | 'perBox' | 'allGumps' = 'perBox';

// How long to wait for a box's window when closing it one at a time
export const CLOSE_TIMEOUT = 200;

// A line per box naming what came out of it and its graphic. Worth having on the first run - it is
// what puts the shard's real key graphic in the console. Turn it off for a pile of a hundred.
export const LOG_EVERY_BOX = true;

// Leave this many boxes behind
export const KEEP = 0;

// Read each box's tooltip before opening it and skip the ones the shard says are empty. A crafted
// pile is mostly boxes whose keys are already out, and the tooltip costs a query rather than a
// double-click, an OPEN_DELAY and a window. Set false to open everything the old way.
export const PEEK_CONTENTS = true;

// How long to wait for tooltip data on a box
export const OPL_TIMEOUT = 1000;

// A double-click has to reach the server and the contents have to come back
export const OPEN_DELAY = 800;

// Moves are asynchronous, so this is a pause between them rather than a wait for one to land
export const MOVE_DELAY = 600;

export const GUMP_TIMEOUT = 5000;

// The pause before reopening the sell gump, paid only when a pass is actually due - a round that
// sold every box the vendor listed stops without saying 'vendor sell' a second time
export const SELL_DELAY = 1500;

// A sale is polled for, not slept through, the same way a drop is: sendSellRequest's boolean only
// says the packet went out, so the boxes leaving the pack is the only proof the vendor took them.
export const SALE_TIMEOUT = 3000;
export const SALE_POLL = 200;

// How many times a box may be rescanned while it is still shifting items
export const MAX_EMPTY_PASSES = 5;

// A sell gump lists a limited number of entries, so reopen it until nothing matches
export const MAX_SELL_PASSES = 10;

// Empty, sell, and go round again - a large pile hits the container cap before it is all emptied,
// and selling is what frees the room
export const MAX_ROUNDS = 20;

// Stop this far short of the weight cap, and this far short of the 125-item container limit. Every
// key taken out of a box adds one item to the top level of the pack, so a big pile walks into the
// item cap long before the weight one.
export const WEIGHT_BUFFER = 40;
export const PACK_LIMIT = 120;
