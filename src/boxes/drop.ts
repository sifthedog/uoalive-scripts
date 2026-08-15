import { DROP_METHOD, DROP_POLL, DROP_SPREAD, DROP_TIMEOUT } from './config.js';

interface Offset {
  x: number;
  y: number;
  z: number;
}

// One tile per key, walked round the ring, so a pile that a shard refuses to stack does not stall
// the whole run on the same square
let spread = 0;
const nextTile = (): Offset =>
  DROP_SPREAD[spread++ % DROP_SPREAD.length] ?? { x: 0, y: 0, z: 0 };

// `moveItemOnGroundOffset` at 0/0/0 is the answer on UOAlive, proven by dist/key-probe.js: the key
// landed on the tile the character was standing on, so the offset is from *you* and not from the
// item. The others are kept so a different shard needs no re-probing - DROP_METHOD = 'auto' tries
// each and keeps whichever demonstrably moves the item.
export type DropMethod = 'groundOffset' | 'groundOffsetStep' | 'worldSerial';

// The container serial the UO drop packet uses to mean "the ground"
const GROUND = 0xffffffff;

const ATTEMPTS: Record<DropMethod, (item: Item, tile: Offset) => void> = {
  // The documented call. The offset is from the character, which dist/key-probe.js proved.
  groundOffset: (item, tile) => player.moveItemOnGroundOffset(item.serial, tile.x, tile.y, tile.z),

  // The same call one tile east, in case an offset of 0/0/0 reads as "do not move"
  groundOffsetStep: (item) => player.moveItemOnGroundOffset(item.serial, 1, 0, 0),

  // A drop addressed the way the protocol does it: the ground's own container serial, and the
  // world coordinates to land on
  worldSerial: (item, tile) =>
    player.moveItem(item.serial, GROUND, player.x + tile.x, player.y + tile.y, player.z + tile.z),
};

const ORDER: DropMethod[] = ['groundOffset', 'groundOffsetStep', 'worldSerial'];

let proven: DropMethod | undefined = DROP_METHOD === 'auto' ? undefined : DROP_METHOD;
let exhausted = false;

// findObject answers with an Item or a Mobile, and only an Item has a container
const containerOf = (serial: number): number | undefined => {
  const found = client.findObject(serial);
  return found && found._tag !== 'Mobile' ? found.container : undefined;
};

// The item leaving the container is the only proof a drop landed: the calls return a number the
// client does not document, and a refused drop is silent.
//
// Polled rather than slept through, the expensive lesson of this file: read the container back too
// early and a drop that worked looks like one that did not, whereupon the recovery path moves the
// key "into the pack" - picking it back up off the floor.
const left = (serial: number, from: number): boolean => {
  for (let waited = 0; waited < DROP_TIMEOUT; waited += DROP_POLL) {
    sleep(DROP_POLL);

    if (containerOf(serial) !== from) {
      return true;
    }
  }

  return false;
};

export const dropMethod = (): DropMethod | undefined => proven;

// Returns whether the item is off the character. A false answer is the caller's cue to put it in
// the pack instead, which is why every failure here is recoverable rather than fatal.
export const dropToGround = (item: Item, from: number): boolean => {
  if (exhausted) {
    return false;
  }

  // One tile for this key, whichever call ends up delivering it
  const tile = nextTile();

  if (proven) {
    ATTEMPTS[proven](item, tile);
    return left(item.serial, from);
  }

  for (const candidate of ORDER) {
    ATTEMPTS[candidate](item, tile);

    if (left(item.serial, from)) {
      proven = candidate;
      log(`boxes: dropping works via '${candidate}' - pin it as DROP_METHOD to skip the retries`);
      return true;
    }
  }

  exhausted = true;
  log(
    `boxes: none of ${ORDER.join(', ')} would put a key on the floor. Keys are going into the ` +
      'pack instead - set DROP_KEYS = false to stop trying, and say so if you want another way in.',
  );

  return false;
};
