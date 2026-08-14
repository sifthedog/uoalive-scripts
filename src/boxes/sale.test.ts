import { beforeEach, describe, expect, it, vi } from 'vitest';

import type { VendorEntry } from '../lib/vendor.js';
import { installGlobals, item, type FakeWorld } from '../test-support/uo.js';
import { pickOffer, sellBoxes } from './sale.js';

const box = (serial: number): VendorEntry => ({ serial, name: 'wooden box' });

// UOAlive's wooden box, so isBox recognises it without needing tooltip data
const inPack = (serial: number): Item => item({ serial, graphic: 0x09aa, name: 'wooden box' });

let world: FakeWorld;
const vendor = { serial: 0x99 } as unknown as Mobile;

beforeEach(() => {
  world = installGlobals();
});

describe('pickOffer', () => {
  it('offers every box by name when nothing was skipped', () => {
    const offer = pickOffer([box(1), box(2)], new Set([1, 2]), 0);

    expect(offer).toEqual({ kind: 'offer', entries: [box(1), box(2)] });
  });

  // With nothing skipped a name match is enough, so a box the run never touched - one bought, say -
  // still goes, because every box in the pack has been proved empty
  it('does not need the serials to line up when nothing was skipped', () => {
    const offer = pickOffer([box(1)], new Set(), 0);

    expect(offer).toEqual({ kind: 'offer', entries: [box(1)] });
  });

  it('ignores everything the vendor lists that is not a box', () => {
    const offer = pickOffer([{ serial: 1, name: 'iron ingot' }, box(2)], new Set([2]), 0);

    expect(offer).toEqual({ kind: 'offer', entries: [box(2)] });
  });

  it('reports what the vendor listed when no box is on offer', () => {
    const offer = pickOffer([{ serial: 1, name: 'iron ingot' }], new Set(), 0);

    expect(offer).toEqual({ kind: 'none', listed: ['iron ingot'] });
  });

  // The point of the whole script: a box that would not open still has its key in it, so once one
  // has been skipped only the boxes watched going empty may be handed over
  it('offers only the boxes proved empty once one was skipped', () => {
    const offer = pickOffer([box(1), box(2), box(3)], new Set([1, 3]), 1);

    expect(offer).toEqual({ kind: 'offer', entries: [box(1), box(3)] });
  });

  // If the gump numbers its entries some other way there is no telling which box is which, and
  // selling by name would include the one that never opened. That stops rather than guessing.
  it('refuses to sell by name when a skipped box exists and no serial matches', () => {
    const offer = pickOffer([box(1), box(2)], new Set([98, 99]), 1);

    expect(offer).toEqual({ kind: 'mismatch', named: 2 });
  });
});

describe('sellBoxes', () => {
  const gumpShowing = (...rounds: VendorEntry[][]) => {
    let round = 0;

    return vi.fn(() => ({
      type: 'sell',
      vendor,
      items: rounds[Math.min(round++, rounds.length - 1)],
    }));
  };

  // A sale is watched for in the pack, because sendSellRequest's return only says the packet went
  // out. So a vendor that takes the boxes is one that empties them out of the backpack, and a
  // vendor that refuses is the default fixture: the request goes, nothing moves.
  const vendorTaking = () =>
    vi.fn((_vendor: Mobile, items: { serial: number }[]) => {
      const gone = new Set(items.map((entry) => entry.serial));
      const pack = world.player.backpack;

      if (pack) {
        pack.contents = (pack.contents ?? []).filter((held) => !gone.has(held.serial));
      }

      return true;
    });

  const packHolding = (...serials: number[]) => {
    world = installGlobals({ backpack: serials.map(inPack) });
    world.client.sendSellRequest = vendorTaking();
  };

  it('sends the boxes and reports how many went', () => {
    packHolding(1, 2);
    world.gump.waitForVendorGumpData = gumpShowing([box(1), box(2)]);

    expect(sellBoxes(new Set([1, 2]), 0)).toBe(2);
    expect(world.client.sendSellRequest).toHaveBeenCalledWith(vendor, [
      { serial: 1, amount: 1 },
      { serial: 2, amount: 1 },
    ]);
  });

  // The whole point of watching the pack: with the boxes gone there is nothing a reopened gump
  // could list, so the round stops rather than saying 'vendor sell' a second time to find that out
  it('says vendor sell once when the pack is cleared in one pass', () => {
    packHolding(1, 2);
    world.gump.waitForVendorGumpData = gumpShowing([box(1), box(2)]);

    sellBoxes(new Set([1, 2]), 0);

    expect(world.player.say).toHaveBeenCalledTimes(1);
  });

  // A sell gump lists a limited number of entries, so a box the gump did not list is left in the
  // pack - and that, and only that, is what earns a second 'vendor sell'
  it('reopens the gump while boxes are still in the pack', () => {
    packHolding(1, 2, 3);
    world.gump.waitForVendorGumpData = gumpShowing([box(1), box(2)], [box(3)]);

    expect(sellBoxes(new Set([1, 2, 3]), 0)).toBe(3);
    expect(world.client.sendSellRequest).toHaveBeenCalledTimes(2);
    expect(world.player.say).toHaveBeenCalledTimes(2);
  });

  // A box that would not open is never going to be sold, so it is not a reason to ask again
  it('does not reopen for boxes that were never emptied', () => {
    packHolding(1, 2);
    world.gump.waitForVendorGumpData = gumpShowing([box(1), box(2)]);

    expect(sellBoxes(new Set([1]), 1)).toBe(1);
    expect(world.player.say).toHaveBeenCalledTimes(1);
  });

  // The request went out and the boxes are still in the pack, which is a vendor refusing in silence
  it('stops when nothing leaves the pack', () => {
    world = installGlobals({ backpack: [inPack(1)] });
    world.gump.waitForVendorGumpData = gumpShowing([box(1)]);

    expect(sellBoxes(new Set([1]), 0)).toBe(0);
    expect(world.client.sendSellRequest).toHaveBeenCalledTimes(1);
    expect(world.log).toHaveBeenCalledWith(expect.stringContaining('stalled'));
  });

  it('sells nothing when a box was skipped and the serials do not match', () => {
    world.gump.waitForVendorGumpData = gumpShowing([box(1), box(2)]);

    expect(sellBoxes(new Set([98]), 1)).toBe(0);
    expect(world.client.sendSellRequest).not.toHaveBeenCalled();
  });

  it('sells nothing when no vendor gump appears', () => {
    expect(sellBoxes(new Set([1]), 0)).toBe(0);
    expect(world.client.sendSellRequest).not.toHaveBeenCalled();
  });
});
