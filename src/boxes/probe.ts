import { findIn } from '../lib/containers.js';
import { die } from '../lib/die.js';
import { hex, isKey } from './boxes.js';
import { PROBE_DELAY } from './config.js';

// Nothing about putting an item on the floor is settled: `moveItemOnGroundOffset` is the only call
// named for it and three ways of using it changed nothing on a live run. Rather than guess a
// fourth, this tries every plausible shape on ONE key and reports what each did - the same method
// the tinkering probe uses on the craft gump, for the same reason: the calls return an undocumented
// number and a refused move is silent, so the only honest signal is whether the item actually went.

// The container serial the UO drop packet uses to mean "the ground"
const GROUND = 0xffffffff;

const backpack = player.backpack ?? die('key-probe: no backpack');

const resolve = (serial: number): Item | undefined => {
  const found = client.findObject(serial);
  return found && found._tag !== 'Mobile' ? found : undefined;
};

const key = findIn(player.backpack?.contents, isKey);

if (!key) {
  log('key-probe: no key in the pack. Open a box first, or add its graphic to KEY_GRAPHICS.');
  die('key-probe: nothing to test with');
}

const serial = key.serial;
const graphic = key.graphic;
const startedIn = key.container;

log(`key-probe: testing with ${hex(serial)} (graphic ${hex(graphic)})`);
log(`key-probe: you are at ${player.x}, ${player.y}, ${player.z}`);

// The heart of it. An item's x/y are documented as world coordinates, but for something sitting in
// a container they are the slot it occupies in that container's window - which is why an "offset
// from where it is" lands nowhere. Printed so the two coordinate spaces can be compared by eye.
log(`key-probe: the key reports x ${key.x}, y ${key.y}, z ${key.z}, container ${hex(startedIn)}`);

interface Variant {
  name: string;
  note: string;
  run: () => void;
}

const VARIANTS: Variant[] = [
  {
    name: 'groundOffset 0/0/0',
    note: 'the documented call, at your feet',
    run: () => player.moveItemOnGroundOffset(serial, 0, 0, 0),
  },
  {
    name: 'groundOffset 1/0/0',
    note: 'the same call one tile east, in case 0/0/0 reads as "do not move"',
    run: () => player.moveItemOnGroundOffset(serial, 1, 0, 0),
  },
  {
    name: 'moveItem to GROUND with coordinates',
    note: 'addressed the way the drop packet does it',
    run: () => player.moveItem(serial, GROUND, player.x, player.y, player.z),
  },
  {
    name: 'moveItem to GROUND without coordinates',
    note: 'in case the client fills the position in itself',
    run: () => player.moveItem(serial, GROUND),
  },
  {
    name: 'moveItem to container 0 with coordinates',
    note: 'some clients spell "no container" as zero rather than -1',
    run: () => player.moveItem(serial, 0, player.x, player.y, player.z),
  },
  {
    name: 'moveTypeOnGroundOffset from the pack',
    note: 'the by-graphic twin of the first call, which names a source container',
    run: () => player.moveTypeOnGroundOffset(graphic, backpack.serial, 0, 0, 0),
  },
  {
    name: 'into the pack first, then groundOffset 0/0/0',
    note: 'tests whether the offset works once the item is somewhere the client tracks',
    run: () => {
      player.moveItem(serial, backpack.serial);
      sleep(PROBE_DELAY);
      player.moveItemOnGroundOffset(serial, 0, 0, 0);
    },
  },
  {
    name: 'into the pack first, then groundOffset 1/0/0',
    note: 'the same, one tile east',
    run: () => {
      player.moveItem(serial, backpack.serial);
      sleep(PROBE_DELAY);
      player.moveItemOnGroundOffset(serial, 1, 0, 0);
    },
  },
];

let winner: string | undefined;

for (const variant of VARIANTS) {
  log(`key-probe: trying ${variant.name} - ${variant.note}`);

  variant.run();
  sleep(PROBE_DELAY);

  const after = resolve(serial);

  // Gone from the client's world entirely is a drop on a shard that stops tracking it; a container
  // that is no longer the pack or the box it came from is a drop on one that keeps tracking it
  if (!after) {
    log(`key-probe:   the key no longer resolves - it is off you. ${variant.name} WORKS.`);
    winner = variant.name;
    break;
  }

  log(
    `key-probe:   still here: container ${hex(after.container)}, x ${after.x}, y ${after.y}, z ${after.z}`,
  );

  if (after.container !== startedIn && after.container !== backpack.serial) {
    log(`key-probe:   it left both the box and the pack. ${variant.name} WORKS.`);
    winner = variant.name;
    break;
  }
}

if (winner) {
  log(`key-probe: use '${winner}'. Tell Claude, or set DROP_METHOD in src/boxes/config.ts.`);
} else {
  log('key-probe: nothing moved the key off you. Paste this whole log back and we will read it.');
}

exit(`key-probe: ${winner ?? 'no variant worked'}`);
