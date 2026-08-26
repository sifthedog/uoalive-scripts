import { beforeEach, describe, expect, it, vi } from 'vitest';

import { installGlobals, item, type FakeWorld } from '../test-support/uo.js';
import { ORE_GRAPHICS, METAL_ASKS, METAL_MISSES } from './config.js';

const [MANY] = [...ORE_GRAPHICS];

let world: FakeWorld;

const ore = (serial: number, hue = 0) => item({ serial, graphic: MANY, hue, amount: 5 });

// The shard's tooltip as the screenshot shows it: a name, a weight, a divider, then the metal
const tooltip = (name: string, ...lines: string[]) => ({
  name,
  properties: [{ text: name }, ...lines.map((text) => ({ text }))],
});

// Every module here holds run-length state - the cache, the latch, the doubts and ORE_METALS itself
const fresh = async (opl: (serial: number) => unknown) => {
  vi.resetModules();
  world = installGlobals();
  world.client.queryItemOPL.mockImplementation(opl);

  return import('./metal.js');
};

beforeEach(() => {
  world = installGlobals();
});

describe('metalOf', () => {
  it('reads the metal off its own property line', async () => {
    const { metalOf } = await fresh(() => tooltip('Ore', 'Weight: 12', 'Verite'));

    expect(metalOf(ore(1))).toBe('verite');
  });

  it('reads a tooltip that names no metal as iron', async () => {
    const { metalOf } = await fresh(() => tooltip('Ore', 'Weight: 12'));

    expect(metalOf(ore(1))).toBe('iron');
  });

  // The distinction hue cannot make, and the one that has to collapse: 'Iron' and no line at all are
  // the same metal, and two keys for it would split a pack of plain ore for the whole run.
  it('gives a spelled-out Iron and a missing line the same key', async () => {
    const { metalOf } = await fresh((serial) =>
      serial === 1 ? tooltip('Ore', 'Weight: 12', 'Iron') : tooltip('Ore', 'Weight: 12'),
    );

    expect(metalOf(ore(1))).toBe(metalOf(ore(2)));
  });

  it('does not read the name line or the divider as the metal', async () => {
    const { metalOf } = await fresh(() => tooltip('Ore', '------------', 'Weight: 12'));

    expect(metalOf(ore(1))).toBe('iron');
  });

  it('learns a metal the seed has never heard of, and says so', async () => {
    const { metalOf } = await fresh(() => tooltip('Ore', 'Weight: 12', 'Doomium'));

    expect(metalOf(ore(1))).toBe('doomium');
    expect(world.log).toHaveBeenCalledWith(expect.stringContaining("'Doomium' is a metal too"));
  });

  it('does not learn a property that is not a metal', async () => {
    const { metalOf } = await fresh(() => tooltip('Ore', 'Blessed', 'Weight: 12'));

    expect(metalOf(ore(1))).toBe('iron');
  });

  it('asks once per serial', async () => {
    const { metalOf } = await fresh(() => tooltip('Ore', 'Weight: 12', 'Verite'));

    metalOf(ore(1));
    metalOf(ore(1));

    expect(world.client.queryItemOPL).toHaveBeenCalledTimes(1);
  });

  // The live run died here: the client threw out of queryItemOPL from inside nextPair, and the
  // exception took the whole script down rather than costing one pile its metal.
  it('survives a tooltip lookup that throws', async () => {
    const { metalOf } = await fresh(() => {
      throw new Error("Error in internal script function return");
    });

    expect(metalOf(ore(1))).toBeUndefined();
    expect(world.log).toHaveBeenCalledWith(expect.stringContaining('would not answer'));
  });

  it('gives up on a lookup that keeps throwing rather than asking every pile', async () => {
    const { metalOf } = await fresh(() => {
      throw new Error('nope');
    });

    for (let serial = 1; serial <= METAL_MISSES + 3; serial++) {
      metalOf(ore(serial));
    }

    expect(world.client.queryItemOPL).toHaveBeenCalledTimes(METAL_MISSES);
  });

  it('says nothing about a pile the tooltip did not answer for', async () => {
    const { metalOf } = await fresh(() => undefined);

    expect(metalOf(ore(1))).toBeUndefined();
  });

  it(`stops asking after ${METAL_MISSES} unanswered tooltips in a row`, async () => {
    const { metalOf } = await fresh(() => undefined);

    for (let serial = 1; serial <= METAL_MISSES + 3; serial++) {
      metalOf(ore(serial));
    }

    expect(world.client.queryItemOPL).toHaveBeenCalledTimes(METAL_MISSES);
    expect(world.log).toHaveBeenCalledWith(expect.stringContaining('tooltips are not naming'));
  });

  // A pack of plain iron answers every tooltip and names no metal in any of them, which must not
  // read as the shard not answering at all
  it('does not count a tooltip that named no metal against the latch', async () => {
    const { metalOf } = await fresh(() => tooltip('Ore', 'Weight: 12'));

    for (let serial = 1; serial <= METAL_MISSES + 3; serial++) {
      metalOf(ore(serial));
    }

    expect(world.client.queryItemOPL).toHaveBeenCalledTimes(METAL_MISSES + 3);
  });
  // The pile a swing has just delivered has usually not been sent its tooltip yet, and caching that
  // miss for the pile's life left it unnamed for good
  it('asks again on the next pass for a pile the tooltip had not reached', async () => {
    let arrived = false;
    const { metalOf, startMetalPass } = await fresh(() =>
      arrived ? tooltip('Ore', 'Weight: 12', 'Verite') : undefined,
    );

    expect(metalOf(ore(1))).toBeUndefined();

    arrived = true;
    startMetalPass();

    expect(metalOf(ore(1))).toBe('verite');
  });

  it('asks a missed serial once within the pass, however often it is read', async () => {
    const { metalOf } = await fresh(() => undefined);

    metalOf(ore(1));
    metalOf(ore(1));
    metalOf(ore(1));

    expect(world.client.queryItemOPL).toHaveBeenCalledTimes(1);
  });
});

// What keeps a pile out of nextPair's last-resort pairing while its tooltip is still in flight
describe('metalPending', () => {
  // Otherwise a shard with no OPL at all defers every pair until the miss latch trips
  it('holds nothing back on a shard that has never answered a tooltip', async () => {
    const { metalPending } = await fresh(() => undefined);

    expect(metalPending(ore(1))).toBe(false);
  });

  it('holds back the pile whose tooltip has not arrived, and not the one that answered', async () => {
    const { metalPending } = await fresh((serial) =>
      serial === 2 ? undefined : tooltip('Ore', 'Weight: 12', 'Verite'),
    );

    expect(metalPending(ore(1))).toBe(false);
    expect(metalPending(ore(2))).toBe(true);
  });

  // Deferring is a wait, never a stranding: a tooltip that never comes falls back to the refusal
  it(`lets it through after ${METAL_ASKS} lookups`, async () => {
    const { metalPending, startMetalPass } = await fresh((serial) =>
      serial === 2 ? undefined : tooltip('Ore', 'Weight: 12', 'Verite'),
    );

    // A fresh answering pile each pass, so it is METAL_ASKS being proven here and not the miss latch
    for (let ask = 1; ask < METAL_ASKS; ask++) {
      metalPending(ore(10 + ask));
      expect(metalPending(ore(2))).toBe(true);
      startMetalPass();
    }

    metalPending(ore(99));

    expect(metalPending(ore(2))).toBe(false);
  });
});

describe('forgetMissingMetals', () => {
  it('re-reads a serial the shard reissued after the pile it named was consumed', async () => {
    const { metalOf, forgetMissingMetals } = await fresh((serial) =>
      tooltip('Ore', 'Weight: 12', serial === 1 ? 'Verite' : 'Copper'),
    );

    expect(metalOf(ore(1))).toBe('verite');

    forgetMissingMetals([ore(2)]);
    world.client.queryItemOPL.mockImplementation(() => tooltip('Ore', 'Weight: 12', 'Copper'));

    expect(metalOf(ore(1))).toBe('copper');
  });

  it('keeps the piles still in the pack', async () => {
    const { metalOf, forgetMissingMetals } = await fresh(() => tooltip('Ore', 'Weight: 12', 'Gold'));

    metalOf(ore(1));
    forgetMissingMetals([ore(1)]);
    metalOf(ore(1));

    expect(world.client.queryItemOPL).toHaveBeenCalledTimes(1);
  });
});

describe('doubtMetal', () => {
  it('takes a metal the shard refused against itself back to unknown', async () => {
    const { metalOf, doubtMetal } = await fresh(() => tooltip('Ore', 'Weight: 12', 'Verite'));

    expect(metalOf(ore(1))).toBe('verite');

    doubtMetal('verite');

    expect(metalOf(ore(1))).toBeUndefined();
    expect(world.log).toHaveBeenCalledWith(expect.stringContaining("both read as 'verite'"));
  });

  it('says it once', async () => {
    const { doubtMetal } = await fresh(() => undefined);

    doubtMetal('verite');
    doubtMetal('verite');

    expect(world.log).toHaveBeenCalledTimes(1);
  });
});
