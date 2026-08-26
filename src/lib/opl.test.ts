import { beforeEach, describe, expect, it, vi } from 'vitest';

import { installGlobals, type FakeWorld } from '../test-support/uo.js';

let world: FakeWorld;

// The `threw` latch lives for the length of a run, so each test takes a fresh module
const fresh = async (opl: () => unknown) => {
  vi.resetModules();
  world = installGlobals();
  world.client.queryItemOPL.mockImplementation(opl);

  return import('./opl.js');
};

beforeEach(() => {
  world = installGlobals();
});

describe('queryOPL', () => {
  it('hands back what the client answered', async () => {
    const { queryOPL } = await fresh(() => ({ name: 'Ring' }));

    expect(queryOPL(7, 2000, 'sell')?.name).toBe('Ring');
  });

  it('passes the serial and the timeout through', async () => {
    const { queryOPL } = await fresh(() => ({ name: 'Ring' }));

    queryOPL(7, 2000, 'sell');

    expect(world.client.queryItemOPL).toHaveBeenCalledWith(7, 2000);
  });

  // The live sell-watch died here: the client threw "Waiting for script RequestMegaCliloc timed
  // out" after the vendor had already taken the goods, and it ended the run rather than the lookup
  it('turns a throw into the empty answer callers already handle', async () => {
    const { queryOPL } = await fresh(() => {
      throw new Error('Waiting for script RequestMegaCliloc 1 timed out after 2000ms');
    });

    expect(queryOPL(7, 2000, 'sell')).toBeUndefined();
  });

  it('names the caller in what it logs, and quotes the client', async () => {
    const { queryOPL } = await fresh(() => {
      throw new Error('timed out after 2000ms');
    });

    queryOPL(7, 2000, 'boxes');

    expect(world.log).toHaveBeenCalledWith(
      expect.stringContaining('boxes: the tooltip lookup would not answer'),
    );
    expect(world.log).toHaveBeenCalledWith(expect.stringContaining('timed out after 2000ms'));
  });

  it('says it once however many items ask', async () => {
    const { queryOPL } = await fresh(() => {
      throw new Error('nope');
    });

    for (let serial = 1; serial <= 5; serial++) {
      queryOPL(serial, 2000, 'sell');
    }

    expect(world.log).toHaveBeenCalledTimes(1);
  });

  // It keeps asking: stopping is the caller's decision, taken on its own miss counter
  it('does not stop asking on its own account', async () => {
    const { queryOPL } = await fresh(() => {
      throw new Error('nope');
    });

    for (let serial = 1; serial <= 5; serial++) {
      queryOPL(serial, 2000, 'sell');
    }

    expect(world.client.queryItemOPL).toHaveBeenCalledTimes(5);
  });
});
