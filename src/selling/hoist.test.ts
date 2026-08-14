import { beforeEach, describe, expect, it, vi } from 'vitest';

import { installGlobals, item, type FakeWorld } from '../test-support/uo.js';
import { hoistToPack, looseMatches, nestedMatches } from './hoist.js';

let world: FakeWorld;

const bag = (serial: number, contents: Item[]): Item =>
  item({ serial, graphic: 0x0e76, name: 'bag', contents });

const ingot = (serial: number, amount: number): Item =>
  item({ serial, graphic: 0x1bf2, name: 'iron ingot', amount });

beforeEach(() => {
  world = installGlobals();
});

const packOf = (...contents: Item[]) => {
  world = installGlobals({ backpack: contents });
  return world;
};

describe('looseMatches', () => {
  // The mirror of nestedMatches: what the vendor can see, which is what a reopened gump would list
  it('finds a match loose in the pack', () => {
    packOf(ingot(0x11, 30));

    expect(looseMatches('iron ingot').map((found) => found.serial)).toEqual([0x11]);
  });

  it('ignores a match still inside a bag', () => {
    packOf(bag(0x10, [ingot(0x11, 30)]));

    expect(looseMatches('iron ingot')).toEqual([]);
  });

  it('finds nothing in an empty pack', () => {
    packOf();

    expect(looseMatches('iron ingot')).toEqual([]);
  });

  // Same rule as everywhere else the name is matched: equality, not a substring
  it('rejects a name that merely contains the wanted one', () => {
    packOf(item({ serial: 0x11, graphic: 0x1bf2, name: 'dull copper iron ingot' }));

    expect(looseMatches('iron ingot')).toEqual([]);
  });
});

describe('nestedMatches', () => {
  it('finds a match inside a bag', () => {
    packOf(bag(0x10, [ingot(0x11, 30)]));

    expect(nestedMatches('iron ingot').map((found) => found.serial)).toEqual([0x11]);
  });

  // The top level is what the vendor already offers, so moving those would be pure round trips
  it('ignores matches already loose in the pack', () => {
    packOf(ingot(0x11, 30), bag(0x10, []));

    expect(nestedMatches('iron ingot')).toEqual([]);
  });

  it('reaches a bag inside a bag', () => {
    packOf(bag(0x10, [bag(0x20, [ingot(0x21, 5)])]));

    expect(nestedMatches('iron ingot').map((found) => found.serial)).toEqual([0x21]);
  });

  it('matches on name regardless of case', () => {
    packOf(bag(0x10, [item({ serial: 0x11, graphic: 0x1bf2, name: 'IRON INGOT' })]));

    expect(nestedMatches('iron ingot')).toHaveLength(1);
  });

  // Same rule as the sell gump: equality, so 'dull copper iron ingot' is a different item
  it('rejects a name that merely contains the wanted one', () => {
    packOf(bag(0x10, [item({ serial: 0x11, graphic: 0x1bf2, name: 'dull copper iron ingot' })]));

    expect(nestedMatches('iron ingot')).toEqual([]);
  });

  // Names are empty until tooltip data arrives, which is the normal state for an unhovered item
  it('falls back to the tooltip for a nameless item', () => {
    packOf(bag(0x10, [item({ serial: 0x11, graphic: 0x1bf2 })]));
    world.client.queryItemOPL = vi.fn(() => ({ serial: 0x11, name: 'iron ingot' }));

    expect(nestedMatches('iron ingot').map((found) => found.serial)).toEqual([0x11]);
  });

  it('does not spend a tooltip query on a top-level item', () => {
    packOf(ingot(0x11, 30));
    world.client.queryItemOPL = vi.fn(() => ({ serial: 0x11, name: 'iron ingot' }));

    nestedMatches('iron ingot');

    expect(world.client.queryItemOPL).not.toHaveBeenCalled();
  });
});

describe('hoistToPack', () => {
  it('moves every nested match into the pack', () => {
    const world = packOf(bag(0x10, [ingot(0x11, 30), ingot(0x12, 5)]));

    expect(hoistToPack('iron ingot')).toBe(2);
    expect(world.player.moveItem.mock.calls).toEqual([
      [0x11, 0x40000000],
      [0x12, 0x40000000],
    ]);
  });

  // An unopened bag has undefined contents, so the double-click pass is what makes it visible
  it('opens containers before deciding the pack is clean', () => {
    const world = packOf(item({ serial: 0x10, graphic: 0x0e76, name: 'bag' }));

    hoistToPack('iron ingot');

    expect(world.player.use).toHaveBeenCalledWith(0x10);
  });

  // Opening a bag reveals the bag inside it, which only the next pass can double-click
  it('reaches a bag that only appears once its parent is opened', () => {
    const world = packOf(bag(0x10, [item({ serial: 0x20, graphic: 0x0e76, name: 'bag' })]));

    hoistToPack('iron ingot');

    expect(world.player.use.mock.calls).toEqual([[0x10], [0x20]]);
  });

  // Re-opening the same bag every pass would cost OPEN_DELAY a pass and find nothing new
  it('opens each container only once', () => {
    const world = packOf(bag(0x10, [ingot(0x11, 30)]));

    hoistToPack('iron ingot');

    expect(world.player.use.mock.calls).toEqual([[0x10]]);
  });

  it('moves nothing when everything is already loose', () => {
    const world = packOf(ingot(0x11, 30));

    expect(hoistToPack('iron ingot')).toBe(0);
    expect(world.player.moveItem).not.toHaveBeenCalled();
  });

  // The fake never mutates the pack, so a second pass sees the same items. Without the stall guard
  // this would move them MAX_HOIST_PASSES times over.
  it('stops instead of moving the same item every pass', () => {
    packOf(bag(0x10, [ingot(0x11, 30)]));

    expect(hoistToPack('iron ingot')).toBe(1);
  });

  it('gives up when there is no backpack', () => {
    world = installGlobals({ player: { backpack: undefined } });

    expect(hoistToPack('iron ingot')).toBe(0);
    expect(world.log).toHaveBeenCalledWith(expect.stringContaining('no backpack'));
  });
});
