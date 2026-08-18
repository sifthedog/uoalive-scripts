// 0x09aa is what UOAlive actually uses, identified by a live run off the name "Wooden Box" - which
// is why the name fallback earns its keep. The 0x0e7d/0x0e7e pair was the stock-art guess.
export const BOX_GRAPHICS = new Set([0x09aa, 0x0e7d, 0x0e7e]);

// As the sell gump labels them. Matched for equality, so 'wooden boxes' is not swept in.
export const BOX_NAME = 'wooden box';

// Anything not recognised as a key still goes into the pack, so an art missing from KEY_GRAPHICS
// costs a key you throw away by hand - never a possession on the floor.
export const DROP_KEYS = true;

// Offsets from where you stand, one per key. Spread across the ring because a shard that caps items
// per tile refuses the rest of the pile, at the full DROP_TIMEOUT each.
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

export const LOG_EVERY_KEY = 5;

// Without it a shard that has stopped accepting keys costs DROP_TIMEOUT per key for the whole pile.
export const MAX_STUCK = 3;

// Pinned from what a live run proved on UOAlive: the offset is from where *you* stand rather than
// from the item. 'auto' tries each in turn instead.
export const DROP_METHOD: 'auto' | 'groundOffset' | 'groundOffsetStep' | 'worldSerial' =
  'groundOffset';

// Polled, not slept through: reading the container back too early says the key is still in the box
// when it is on the floor, and the recovery for that picks it back up. 700ms flat did exactly that.
export const DROP_TIMEOUT = 3000;
export const DROP_POLL = 200;


// Matched alongside the name, and the first key found teaches the run the art for the rest
export const KEY_GRAPHICS = new Set([0x100e, 0x100f, 0x1010, 0x1011, 0x1012, 0x1013]);

// Off: the boxes are emptied and left in the pack. True offers them to whoever is in earshot.
export const SELL = false;

// 'perBox' looks the gump up under the container's serial, which is unverified - if it does not
// work nothing closes, the harmless direction. 'allGumps' works but shuts every gump you have open,
// paperdoll included, because the client has no per-container close.
export const CLOSE_BOXES: 'never' | 'perBox' | 'allGumps' = 'perBox';

export const CLOSE_TIMEOUT = 200;

// What puts the shard's real key graphic in the console. Turn it off for a pile of a hundred.
export const LOG_EVERY_BOX = true;

// Leave this many boxes behind
export const KEEP = 0;

// Skips the boxes the shard's tooltip says are empty, which a crafted pile is mostly made of. The
// tooltip costs a query rather than a double-click, an OPEN_DELAY and a window.
export const PEEK_CONTENTS = true;

export const OPL_TIMEOUT = 1000;

// A double-click has to reach the server and the contents have to come back
export const OPEN_DELAY = 800;

// Moves are asynchronous, so this is a pause between them rather than a wait for one to land
export const MOVE_DELAY = 600;

export const GUMP_TIMEOUT = 5000;

// Paid only when a pass is due: a round that sold everything listed does not ask twice
export const SELL_DELAY = 1500;

// sendSellRequest's boolean only says the packet went out, so the boxes leaving the pack is the
// only proof the vendor took them
export const SALE_TIMEOUT = 3000;
export const SALE_POLL = 200;

export const MAX_EMPTY_PASSES = 5;

// A sell gump lists a limited number of entries, so reopen it until nothing matches
export const MAX_SELL_PASSES = 10;

// A large pile hits the container cap before it is all emptied, and selling is what frees the room
export const MAX_ROUNDS = 20;

// Every key adds one item to the top level, so a big pile hits the 125-item cap before the weight one
export const WEIGHT_BUFFER = 40;
export const PACK_LIMIT = 120;
