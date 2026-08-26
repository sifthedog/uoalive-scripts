import { beforeEach, describe, expect, it, vi } from 'vitest';

import { installGlobals, type FakeWorld } from '../test-support/uo.js';

let world: FakeWorld;

// peek.ts latches the shard's answer about whether the property exists at all, so each test takes
// a fresh module
const fresh = async (PEEK_CONTENTS = true) => {
  vi.resetModules();
  vi.doMock('./config.js', () => ({ PEEK_CONTENTS, OPL_TIMEOUT: 1000 }));
  return import('./peek.js');
};

const opl = (...lines: string[]) => vi.fn(() => ({ properties: lines.map((text) => ({ text })) }));

beforeEach(() => {
  vi.resetModules();
  vi.doUnmock('./config.js');
  world = installGlobals();
});

describe('peekContents', () => {

  // Guessing 'empty' on a box that is not would hand a key to a vendor, so a throw has to read as
  // 'open it and see' rather than as a count
  it('says nothing when the tooltip lookup throws', async () => {
    world.client.queryItemOPL = vi.fn(() => {
      throw new Error('Waiting for script RequestMegaCliloc 1 timed out after 2000ms');
    });

    const { peekContents } = await fresh();

    expect(peekContents(7)).toBeUndefined();
    expect(world.log).toHaveBeenCalledWith(expect.stringContaining('would not answer'));
  });
  it('reads the count out of a RunUO contents line', async () => {
    world.client.queryItemOPL = opl('Wooden Box', 'Contents: 3/125, 4 stones');

    const { peekContents } = await fresh();

    expect(peekContents(7)).toBe(3);
  });

  // The answer the whole thing is for: an empty box never has to be opened
  it('reports an empty box as zero', async () => {
    world.client.queryItemOPL = opl('Contents: 0/125, 0 stones');

    const { peekContents } = await fresh();

    expect(peekContents(7)).toBe(0);
  });

  it('reads the count out of a property value rather than its text', async () => {
    world.client.queryItemOPL = vi.fn(() => ({
      properties: [{ text: 'Contents', values: [{ text: '2/125, 2 stones' }] }],
    }));

    const { peekContents } = await fresh();

    expect(peekContents(7)).toBe(2);
  });

  // undefined is "open it and see", never "empty": guessing empty on a box that is not would hand
  // a key to a vendor
  it('gives no answer when the tooltip says nothing about contents', async () => {
    world.client.queryItemOPL = opl('Wooden Box', 'Weight: 3 stones');

    const { peekContents } = await fresh();

    expect(peekContents(7)).toBeUndefined();
  });

  it('gives no answer when there is no tooltip at all', async () => {
    const { peekContents } = await fresh();

    expect(peekContents(7)).toBeUndefined();
  });

  // Asked once and then left alone, the way tool.ts stops asking for "uses remaining" - otherwise
  // every box in the pile pays the OPL timeout for an answer that never comes
  it('stops asking once the shard has shown it does not send the property', async () => {
    world.client.queryItemOPL = opl('Weight: 3 stones');

    const { peekContents } = await fresh();
    peekContents(7);
    peekContents(8);

    expect(world.client.queryItemOPL).toHaveBeenCalledTimes(1);
  });

  it('asks nothing at all when peeking is turned off', async () => {
    world.client.queryItemOPL = opl('Contents: 0/125, 0 stones');

    const { peekContents } = await fresh(false);

    expect(peekContents(7)).toBeUndefined();
    expect(world.client.queryItemOPL).not.toHaveBeenCalled();
  });
});
