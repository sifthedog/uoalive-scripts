import { beforeEach, describe, expect, it, vi } from 'vitest';

import { installGlobals, item, type FakeWorld } from '../test-support/uo.js';

let world: FakeWorld;

// hoist.ts remembers tooltip answers and latches whether the shard answers them at all, so every
// test takes a fresh module rather than inheriting what the last one asked - the same reason
// peek.test.ts does it
const fresh = () => {
  vi.resetModules();
  return import('./hoist.js');
};

const BAG = 0x0e76;
const INGOT = 0x1bf2;
const SCIMITAR = 0x13b6;
const POTION = 0x0f0e;

const bag = (serial: number, contents: Item[]): Item =>
  item({ serial, graphic: BAG, name: 'bag', contents });

const ingot = (serial: number, amount: number): Item =>
  item({ serial, graphic: INGOT, name: 'iron ingot', amount });

beforeEach(() => {
  vi.resetModules();
  world = installGlobals();
});

const packOf = (...contents: Item[]) => {
  world = installGlobals({ backpack: contents });
  return world;
};

describe('sellableMatches', () => {
  // What a reopened gump would list, which on this shard is everything in the pack at any depth
  it('finds a match loose in the pack', async () => {
    packOf(ingot(0x11, 30));
    const { sellableMatches } = await fresh();

    expect(sellableMatches('iron ingot').map((found) => found.serial)).toEqual([0x11]);
  });

  // The vendor sells out of a bag here, so a match inside one is still on offer. Counting the top
  // level alone stopped the sale with the bags still full.
  it('finds a match inside a bag', async () => {
    packOf(bag(0x10, [ingot(0x11, 30)]));
    const { sellableMatches } = await fresh();

    expect(sellableMatches('iron ingot').map((found) => found.serial)).toEqual([0x11]);
  });

  it('reaches a bag inside a bag', async () => {
    packOf(bag(0x10, [bag(0x20, [ingot(0x21, 5)])]));
    const { sellableMatches } = await fresh();

    expect(sellableMatches('iron ingot').map((found) => found.serial)).toEqual([0x21]);
  });

  it('finds nothing in an empty pack', async () => {
    packOf();
    const { sellableMatches } = await fresh();

    expect(sellableMatches('iron ingot')).toEqual([]);
  });

  // Same rule as everywhere else the name is matched: equality, not a substring
  it('rejects a name that merely contains the wanted one', async () => {
    packOf(item({ serial: 0x11, graphic: INGOT, name: 'dull copper iron ingot' }));
    const { sellableMatches } = await fresh();

    expect(sellableMatches('iron ingot')).toEqual([]);
  });

  // A pack that will not answer is a pack with nothing in it, not the end of the run
  it('reads an unreadable pack as empty', async () => {
    packOf(ingot(0x11, 30));
    Object.defineProperty(world.player, 'backpack', {
      configurable: true,
      get: () => {
        throw new SyntaxError('Unexpected end of JSON input');
      },
    });
    const { sellableMatches } = await fresh();

    expect(sellableMatches('iron ingot')).toEqual([]);
  });
});

describe('nestedMatches', () => {
  it('finds a match inside a bag', async () => {
    packOf(bag(0x10, [ingot(0x11, 30)]));
    const { nestedMatches } = await fresh();

    expect(nestedMatches('iron ingot').map((found) => found.serial)).toEqual([0x11]);
  });

  // The top level is what the vendor already offers, so moving those would be pure round trips
  it('ignores matches already loose in the pack', async () => {
    packOf(ingot(0x11, 30), bag(0x10, []));
    const { nestedMatches } = await fresh();

    expect(nestedMatches('iron ingot')).toEqual([]);
  });

  it('reaches a bag inside a bag', async () => {
    packOf(bag(0x10, [bag(0x20, [ingot(0x21, 5)])]));
    const { nestedMatches } = await fresh();

    expect(nestedMatches('iron ingot').map((found) => found.serial)).toEqual([0x21]);
  });

  it('matches on name regardless of case', async () => {
    packOf(bag(0x10, [item({ serial: 0x11, graphic: INGOT, name: 'IRON INGOT' })]));
    const { nestedMatches } = await fresh();

    expect(nestedMatches('iron ingot')).toHaveLength(1);
  });

  // Same rule as the sell gump: equality, so 'dull copper iron ingot' is a different item
  it('rejects a name that merely contains the wanted one', async () => {
    packOf(bag(0x10, [item({ serial: 0x11, graphic: INGOT, name: 'dull copper iron ingot' })]));
    const { nestedMatches } = await fresh();

    expect(nestedMatches('iron ingot')).toEqual([]);
  });

  // Names are empty until tooltip data arrives, which is the normal state for an unhovered item
  it('falls back to the tooltip for a nameless item', async () => {
    packOf(bag(0x10, [item({ serial: 0x11, graphic: INGOT })]));
    world.client.queryItemOPL = vi.fn(() => ({ serial: 0x11, name: 'iron ingot' }));
    const { nestedMatches } = await fresh();

    expect(nestedMatches('iron ingot').map((found) => found.serial)).toEqual([0x11]);
  });

  it('does not spend a tooltip query on a top-level item', async () => {
    packOf(ingot(0x11, 30));
    world.client.queryItemOPL = vi.fn(() => ({ serial: 0x11, name: 'iron ingot' }));
    const { nestedMatches } = await fresh();

    nestedMatches('iron ingot');

    expect(world.client.queryItemOPL).not.toHaveBeenCalled();
  });

  // The pack is walked several times a run, and an item's name does not change between walks
  it('asks the tooltip once per serial and remembers the answer', async () => {
    packOf(bag(0x10, [item({ serial: 0x11, graphic: INGOT })]));
    world.client.queryItemOPL = vi.fn(() => ({ serial: 0x11, name: 'iron ingot' }));
    const { nestedMatches } = await fresh();

    nestedMatches('iron ingot');
    nestedMatches('iron ingot');
    nestedMatches('iron ingot');

    expect(world.client.queryItemOPL).toHaveBeenCalledTimes(1);
  });

  // Three unanswered in a row is the shard, not the items. Without this a pack of nameless items
  // costs OPL_TIMEOUT each, every walk, for an answer that is never coming.
  it('stops asking once the shard has ignored three in a row', async () => {
    packOf(
      bag(0x10, [
        item({ serial: 0x11, graphic: INGOT }),
        item({ serial: 0x12, graphic: INGOT }),
        item({ serial: 0x13, graphic: INGOT }),
        item({ serial: 0x14, graphic: INGOT }),
        item({ serial: 0x15, graphic: INGOT }),
      ]),
    );
    world.client.queryItemOPL = vi.fn(() => undefined);
    const { nestedMatches } = await fresh();

    nestedMatches('iron ingot');
    nestedMatches('iron ingot');

    expect(world.client.queryItemOPL).toHaveBeenCalledTimes(3);
    expect(world.log).toHaveBeenCalledWith(expect.stringContaining('tooltips are not answering'));
  });
});

describe('hoistToPack', () => {
  it('moves every nested match into the pack', async () => {
    const world = packOf(bag(0x10, [ingot(0x11, 30), ingot(0x12, 5)]));
    const { hoistToPack } = await fresh();

    expect(hoistToPack('iron ingot')).toBe(2);
    expect(world.player.moveItem.mock.calls).toEqual([
      [0x11, 0x40000000],
      [0x12, 0x40000000],
    ]);
  });

  // An unopened bag has undefined contents, so the double-click pass is what makes it visible
  it('opens containers before deciding the pack is clean', async () => {
    const world = packOf(item({ serial: 0x10, graphic: BAG, name: 'bag' }));
    const { hoistToPack } = await fresh();

    hoistToPack('iron ingot');

    expect(world.player.use).toHaveBeenCalledWith(0x10);
  });

  // Opening a bag reveals the bag inside it, which only the next pass can double-click
  it('reaches a bag that only appears once its parent is opened', async () => {
    const world = packOf(bag(0x10, [item({ serial: 0x20, graphic: BAG, name: 'bag' })]));
    const { hoistToPack } = await fresh();

    hoistToPack('iron ingot');

    expect(world.player.use.mock.calls).toEqual([[0x10], [0x20]]);
  });

  // Re-opening the same bag every pass would cost OPEN_DELAY a pass and find nothing new
  it('opens each container only once', async () => {
    const world = packOf(bag(0x10, [ingot(0x11, 30)]));
    const { hoistToPack } = await fresh();

    hoistToPack('iron ingot');

    expect(world.player.use.mock.calls).toEqual([[0x10]]);
  });

  it('moves nothing when everything is already loose', async () => {
    const world = packOf(ingot(0x11, 30));
    const { hoistToPack } = await fresh();

    expect(hoistToPack('iron ingot')).toBe(0);
    expect(world.player.moveItem).not.toHaveBeenCalled();
  });

  // The fake never mutates the pack, so a second pass sees the same items. Without the stall guard
  // this would move them MAX_HOIST_PASSES times over.
  it('stops instead of moving the same item every pass', async () => {
    packOf(bag(0x10, [ingot(0x11, 30)]));
    const { hoistToPack } = await fresh();

    expect(hoistToPack('iron ingot')).toBe(1);
  });

  it('gives up when there is no backpack', async () => {
    world = installGlobals({ player: { backpack: undefined } });
    const { hoistToPack } = await fresh();

    expect(hoistToPack('iron ingot')).toBe(0);
    expect(world.log).toHaveBeenCalledWith(expect.stringContaining('no backpack'));
  });

  // The live client answers `contents` with `[]` for plain items rather than the `undefined` the
  // type promises, so treating any array as proof of a container made every item in the pack one -
  // and player.use() went down the whole list, equipping a weapon and drinking a potion.
  it('opens nothing but the bag when every item reports empty contents', async () => {
    const world = packOf(
      item({ serial: 0x11, graphic: SCIMITAR, name: 'Scimitar', contents: [] }),
      item({ serial: 0x12, graphic: POTION, name: 'greater heal potion', contents: [] }),
      item({ serial: 0x13, graphic: BAG, name: 'bag', contents: [] }),
    );
    const { hoistToPack } = await fresh();

    hoistToPack('Scimitar');

    expect(world.player.use.mock.calls).toEqual([[0x13]]);
  });

  // Recognising containers by graphic means a shard's own container art would hide what is in it,
  // so anything that reads like a bag and is not on the list says so - once, not once per pass
  it('names a probable container whose graphic is not on the list', async () => {
    const world = packOf(bag(0x10, []), item({ serial: 0x30, graphic: 0x9999, name: 'leather bag' }));
    const { hoistToPack } = await fresh();

    hoistToPack('iron ingot');

    const warnings = world.log.mock.calls.filter((call) =>
      String(call[0]).includes('not in CONTAINER_GRAPHICS'),
    );

    expect(warnings).toHaveLength(1);
    expect(warnings[0][0]).toContain('leather bag');
    expect(world.player.use.mock.calls).toEqual([[0x10]]);
  });

  it('says nothing about an ordinary item that is not a container', async () => {
    const world = packOf(item({ serial: 0x11, graphic: SCIMITAR, name: 'Scimitar' }));
    const { hoistToPack } = await fresh();

    hoistToPack('Scimitar');

    expect(world.log).not.toHaveBeenCalledWith(expect.stringContaining('CONTAINER_GRAPHICS'));
  });
});
