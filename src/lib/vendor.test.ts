import { beforeEach, describe, expect, it, vi } from 'vitest';

import { installGlobals, item, type FakeWorld } from '../test-support/uo.js';
import {
  namedExactly,
  openSellGump,
  totalOf,
  waitForSale,
  withKeepBack,
  type VendorEntry,
} from './vendor.js';

const ingots = (...amounts: number[]): VendorEntry[] =>
  amounts.map((amount, index) => ({ serial: index + 1, name: 'iron ingot', amount }));

describe('namedExactly', () => {
  it('matches the given name', () => {
    expect(namedExactly('iron ingot')({ serial: 1, name: 'iron ingot' })).toBe(true);
  });

  it('ignores case on both sides', () => {
    expect(namedExactly('Iron Ingot')({ serial: 1, name: 'IRON INGOT' })).toBe(true);
  });

  // Equality, not a substring test - selling 'iron ingots' when asked for 'iron ingot' would be a
  // different item, and a substring match would also hit 'dull copper iron ingot'
  it('rejects a name that merely contains the given one', () => {
    const matches = namedExactly('iron ingot');

    expect(matches({ serial: 1, name: 'dull copper iron ingot' })).toBe(false);
    expect(matches({ serial: 1, name: 'iron ingots' })).toBe(false);
  });

  it('rejects an entry with no name at all', () => {
    expect(namedExactly('iron ingot')({ serial: 1 } as VendorEntry)).toBe(false);
  });
});

describe('withKeepBack', () => {
  it('offers everything when nothing is kept back', () => {
    expect(withKeepBack(ingots(10, 5), 0)).toEqual([
      { serial: 1, amount: 10 },
      { serial: 2, amount: 5 },
    ]);
  });

  it('drops whole stacks that fit inside the keep-back', () => {
    expect(withKeepBack(ingots(4, 6, 20), 10)).toEqual([{ serial: 3, amount: 20 }]);
  });

  // The interesting case: the keep-back runs out part way through a stack, so that stack is split
  it('splits the stack the keep-back runs out in', () => {
    expect(withKeepBack(ingots(4, 20), 10)).toEqual([{ serial: 2, amount: 14 }]);
  });

  it('offers nothing when the keep-back covers everything', () => {
    expect(withKeepBack(ingots(10, 20), 100)).toEqual([]);
  });

  // Exactly KEEP on offer means exactly KEEP kept, so nothing is sold and the caller stops
  it('offers nothing when the total is exactly the keep-back', () => {
    expect(withKeepBack(ingots(10, 20), 30)).toEqual([]);
  });

  it('offers a single unit when the total is one over the keep-back', () => {
    expect(withKeepBack(ingots(10, 21), 30)).toEqual([{ serial: 2, amount: 1 }]);
  });

  it('counts an entry with no amount as one', () => {
    expect(
      withKeepBack(
        [
          { serial: 1, name: 'iron ingot' },
          { serial: 2, name: 'iron ingot', amount: 5 },
        ],
        1,
      ),
    ).toEqual([{ serial: 2, amount: 5 }]);
  });

  it('keeps nothing back from an empty offer', () => {
    expect(withKeepBack([], 10)).toEqual([]);
  });

  // Once the keep-back is spent it stays spent, so a later stack is never re-trimmed
  it('spends the keep-back only once across many stacks', () => {
    expect(withKeepBack(ingots(8, 8, 8), 5)).toEqual([
      { serial: 1, amount: 3 },
      { serial: 2, amount: 8 },
      { serial: 3, amount: 8 },
    ]);
  });
});

describe('totalOf', () => {
  it('adds the amounts up', () => {
    expect(totalOf(ingots(10, 5))).toBe(15);
  });

  // A box has no amount, and one box is one box
  it('counts an entry with no amount as one', () => {
    expect(totalOf([{ serial: 1, name: 'wooden box' }])).toBe(1);
  });
});

describe('waitForSale', () => {
  const stack = (serial: number, amount: number): Item =>
    item({ serial, graphic: 0x1bf2, amount });

  it('reports the whole offer when the stack leaves the pack', () => {
    installGlobals({ backpack: [] });

    expect(waitForSale([{ serial: 1, amount: 20 }], 1000, 200)).toBe(20);
  });

  // The request went out and the goods are still there, which is what a vendor refusing looks like
  it('reports nothing when the stack stays put', () => {
    installGlobals({ backpack: [stack(1, 20)] });

    expect(waitForSale([{ serial: 1, amount: 20 }], 1000, 200)).toBe(0);
  });

  // A stack the vendor only partly took keeps its serial and comes back smaller
  it('reports the part of a stack that went', () => {
    installGlobals({ backpack: [stack(1, 8)] });

    expect(waitForSale([{ serial: 1, amount: 20 }], 1000, 200)).toBe(12);
  });

  // Only the offered serials count - the rest of the pack is nobody's business here
  it('ignores everything that was not offered', () => {
    installGlobals({ backpack: [stack(1, 20), stack(2, 5)] });

    expect(waitForSale([{ serial: 2, amount: 5 }], 1000, 200)).toBe(0);
  });

  // Polled rather than read once: the pack updates when the server says so, not when the request
  // is sent, and a sale read too early looks like a sale that never happened
  it('keeps looking until the goods go', () => {
    const world = installGlobals({ backpack: [stack(1, 20)] });
    let polls = 0;

    world.sleep.mockImplementation(() => {
      if (++polls === 3 && world.player.backpack) {
        world.player.backpack.contents = [];
      }
    });

    expect(waitForSale([{ serial: 1, amount: 20 }], 1000, 200)).toBe(20);
    expect(polls).toBe(3);
  });

  it('stops looking once the timeout is spent', () => {
    const world = installGlobals({ backpack: [stack(1, 20)] });

    expect(waitForSale([{ serial: 1, amount: 20 }], 1000, 200)).toBe(0);
    expect(world.sleep).toHaveBeenCalledTimes(5);
  });
});

describe('openSellGump', () => {
  let world: FakeWorld;

  beforeEach(() => {
    world = installGlobals();
  });

  const vendor = { serial: 0x99 } as unknown as Mobile;

  it('says the trigger phrase and returns the entries', () => {
    world.gump.waitForVendorGumpData = vi.fn(() => ({
      type: 'sell',
      vendor,
      items: [{ serial: 1, name: 'iron ingot', amount: 3 }],
    }));

    const data = openSellGump('sell', 5000);

    expect(world.player.say).toHaveBeenCalledWith('vendor sell');
    expect(data?.vendor).toBe(vendor);
    expect(data?.items).toEqual([{ serial: 1, name: 'iron ingot', amount: 3 }]);
  });

  it('gives up when no gump arrives', () => {
    expect(openSellGump('sell', 5000)).toBeUndefined();
    expect(world.log).toHaveBeenCalledWith(expect.stringContaining('no vendor gump'));
  });

  // Saying 'vendor sell' next to a vendor already showing a buy gump answers with the buy one, and
  // sending a sell request against that would be selling into the wrong list
  it('refuses a buy gump', () => {
    world.gump.waitForVendorGumpData = vi.fn(() => ({ type: 'buy', vendor, items: [] }));

    expect(openSellGump('sell', 5000)).toBeUndefined();
    expect(world.log).toHaveBeenCalledWith(expect.stringContaining("'buy' gump"));
  });

  // The client's typings leave items as any, and an absent list has to read as no entries rather
  // than throwing on the caller's filter
  it('reads a missing item list as no entries', () => {
    world.gump.waitForVendorGumpData = vi.fn(() => ({ type: 'sell', vendor }));

    expect(openSellGump('sell', 5000)?.items).toEqual([]);
  });
});
