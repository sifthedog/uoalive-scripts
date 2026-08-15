import { beforeEach, describe, expect, it, vi } from 'vitest';

import type { VendorEntry } from '../lib/vendor.js';
import { installGlobals, item, type FakeWorld } from '../test-support/uo.js';
import { sellAll } from './sell.js';

let world: FakeWorld;
const vendor = { serial: 0x99 } as unknown as Mobile;

const listed = (serial: number, amount: number, name = 'iron ingot'): VendorEntry => ({
  serial,
  name,
  amount,
});

const ingot = (serial: number, amount: number): Item =>
  item({ serial, graphic: 0x1bf2, name: 'iron ingot', amount });

const blade = (serial: number, amount: number): Item =>
  item({ serial, graphic: 0x13b6, name: 'scimitar', amount });

const gumpShowing = (...rounds: VendorEntry[][]) => {
  let round = 0;

  return vi.fn(() => ({
    type: 'sell',
    vendor,
    items: rounds[Math.min(round++, rounds.length - 1)],
  }));
};

// A sale is watched for in the pack, because sendSellRequest's return only says the packet went
// out. So a vendor that takes the ingots is one that takes them out of the backpack; the default
// fixture, which moves nothing, is a vendor refusing in silence.
const vendorTaking = () =>
  vi.fn((_vendor: Mobile, items: { serial: number; amount: number }[]) => {
    const sold = new Map(items.map((entry) => [entry.serial, entry.amount]));

    // Down every bag, because this shard's vendors sell out of one
    const taken = (contents: Item[] | undefined): Item[] =>
      (contents ?? [])
        .map((held) => {
          const gone = sold.get(held.serial) ?? 0;

          if (gone) {
            return item({
              serial: held.serial,
              graphic: held.graphic,
              name: held.name,
              amount: (held.amount ?? 1) - gone,
            });
          }

          if (Array.isArray(held.contents)) {
            (held as { contents: Item[] }).contents = taken(held.contents);
          }

          return held;
        })
        .filter((held) => (held.amount ?? 1) > 0);

    const pack = world.player.backpack;

    if (pack) {
      pack.contents = taken(pack.contents);
    }

    return true;
  });

const packHolding = (...contents: Item[]) => {
  world = installGlobals({ backpack: contents });
  world.client.sendSellRequest = vendorTaking();
};

beforeEach(() => {
  world = installGlobals();
});

describe('sellAll', () => {
  it('offers what the vendor listed and reports what went', () => {
    packHolding(ingot(1, 20), ingot(2, 5));
    world.gump.waitForVendorGumpData = gumpShowing([listed(1, 20), listed(2, 5)]);

    expect(sellAll(['iron ingot']).total).toBe(25);
    expect(world.client.sendSellRequest).toHaveBeenCalledWith(vendor, [
      { serial: 1, amount: 20 },
      { serial: 2, amount: 5 },
    ]);
  });

  // The gump the vendor already has open lists every name, so selling three items costs one
  // 'vendor sell' rather than three
  it('sells several names through one gump', () => {
    packHolding(ingot(1, 20), blade(2, 3));
    world.gump.waitForVendorGumpData = gumpShowing([listed(1, 20), listed(2, 3, 'scimitar')]);

    const sold = sellAll(['iron ingot', 'scimitar']);

    expect(sold.total).toBe(23);
    expect(sold.byName).toEqual(
      new Map([
        ['iron ingot', 20],
        ['scimitar', 3],
      ]),
    );
    expect(world.player.say).toHaveBeenCalledTimes(1);
    expect(world.client.sendSellRequest).toHaveBeenCalledWith(vendor, [
      { serial: 1, amount: 20 },
      { serial: 2, amount: 3 },
    ]);
  });

  // The report is keyed by the name that was picked, and a vendor gump need not spell it the same
  it('reports under the name it was asked for', () => {
    packHolding(ingot(1, 20));
    world.gump.waitForVendorGumpData = gumpShowing([listed(1, 20, 'IRON INGOT')]);

    expect(sellAll(['Iron Ingot']).byName).toEqual(new Map([['Iron Ingot', 20]]));
  });

  // A vendor that buys one of the two still gets sold that one
  it('sells the names on offer and says which were not', () => {
    packHolding(ingot(1, 20), blade(2, 3));
    world.gump.waitForVendorGumpData = gumpShowing([listed(1, 20)], []);

    const sold = sellAll(['iron ingot', 'scimitar']);

    expect(sold.total).toBe(20);
    expect(sold.byName.get('scimitar')).toBe(0);
    expect(world.log).toHaveBeenCalledWith(expect.stringContaining('nothing of iron ingot, scimitar'));
  });

  // The whole point of watching the pack rather than reopening the gump: with the ingots gone there
  // is nothing another pass could list, so the run stops instead of saying 'vendor sell' to find out
  it('says vendor sell once when the pack is cleared in one pass', () => {
    packHolding(ingot(1, 20));
    world.gump.waitForVendorGumpData = gumpShowing([listed(1, 20)]);

    sellAll(['iron ingot']);

    expect(world.player.say).toHaveBeenCalledTimes(1);
    expect(world.player.say).toHaveBeenCalledWith('vendor sell');
  });

  // A sell gump lists a limited number of entries, so a stack it did not list is left in the pack -
  // and that, and only that, is what earns a second 'vendor sell'
  it('reopens the gump while matches are still loose in the pack', () => {
    packHolding(ingot(1, 20), ingot(2, 5));
    world.gump.waitForVendorGumpData = gumpShowing([listed(1, 20)], [listed(2, 5)]);

    expect(sellAll(['iron ingot']).total).toBe(25);
    expect(world.player.say).toHaveBeenCalledTimes(2);
  });

  // This shard's vendors sell out of a bag, so ingots the gump did not list are still on offer and
  // still worth another pass. Counting the top level alone stopped the run with the bag full.
  it('reopens for matches sitting in a bag', () => {
    packHolding(ingot(1, 20), item({ serial: 0x10, graphic: 0x0e76, contents: [ingot(2, 5)] }));
    world.gump.waitForVendorGumpData = gumpShowing([listed(1, 20)], [listed(2, 5)]);

    expect(sellAll(['iron ingot']).total).toBe(25);
    expect(world.player.say).toHaveBeenCalledTimes(2);
  });

  // The request went out and the ingots are still there, which is what a refusal looks like
  it('stops when nothing leaves the pack', () => {
    world = installGlobals({ backpack: [ingot(1, 20)] });
    world.gump.waitForVendorGumpData = gumpShowing([listed(1, 20)]);

    expect(sellAll(['iron ingot']).total).toBe(0);
    expect(world.client.sendSellRequest).toHaveBeenCalledTimes(1);
    expect(world.log).toHaveBeenCalledWith(expect.stringContaining('stalled'));
  });

  // A vendor out of gold takes part of what it was offered. The next pass offers the rest, gets
  // nothing, and stops there.
  it('goes round once more after a partial take, then stops', () => {
    packHolding(ingot(1, 20));
    world.gump.waitForVendorGumpData = gumpShowing([listed(1, 20)], [listed(1, 12)]);
    world.client.sendSellRequest = vi.fn((_vendor: Mobile) => {
      const pack = world.player.backpack;

      if (pack?.contents?.length) {
        pack.contents = [ingot(1, 12)];
      }

      return true;
    });

    expect(sellAll(['iron ingot']).total).toBe(8);
    expect(world.client.sendSellRequest).toHaveBeenCalledTimes(2);
  });

  it('says what the vendor listed when nothing matches', () => {
    world.gump.waitForVendorGumpData = gumpShowing([{ serial: 1, name: 'dull copper ingot' }]);

    expect(sellAll(['iron ingot']).total).toBe(0);
    expect(world.client.sendSellRequest).not.toHaveBeenCalled();
    expect(world.log).toHaveBeenCalledWith(expect.stringContaining('dull copper ingot'));
  });

  it('sells nothing when no vendor gump appears', () => {
    expect(sellAll(['iron ingot']).total).toBe(0);
    expect(world.client.sendSellRequest).not.toHaveBeenCalled();
  });
});
