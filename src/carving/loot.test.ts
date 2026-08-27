import { beforeEach, describe, expect, it, vi } from 'vitest';

import { type FakeWorld, installGlobals, item } from '../test-support/uo.js';
import { CORPSE_GRAPHIC, TAKE_GRAPHICS } from './config.js';
import { pending, take } from './loot.js';
import { forget, memory } from './memory.js';

const PACK = 0x40000000;
const CORPSE = 0x40000001;
const [FEATHER] = [...TAKE_GRAPHICS];
const MEAT = 0x09f1;

let world: FakeWorld;

const corpse = (serial: number, contents?: Item[]) =>
  item({ serial, graphic: CORPSE_GRAPHIC, contents });

// The client answers with the corpse as it stands now, so a test that moves things restates it
const holding = (contents?: Item[]) => {
  world.client.findObject = vi.fn(() => corpse(CORPSE, contents));
};

beforeEach(() => {
  forget();
  world = installGlobals();
});

describe('pending', () => {
  it('is nothing for a corpse that has not been carved', () => {
    expect(pending([corpse(CORPSE)])).toBeUndefined();
  });

  it('is the carved corpse nothing has been taken out of yet', () => {
    memory().done.add(CORPSE);

    expect(pending([corpse(CORPSE)])?.serial).toBe(CORPSE);
  });

  it('is nothing once it has been emptied', () => {
    memory().done.add(CORPSE);
    memory().emptied.add(CORPSE);

    expect(pending([corpse(CORPSE)])).toBeUndefined();
  });
});

describe('take', () => {
  it('opens the corpse before reading it', () => {
    holding([]);

    take(corpse(CORPSE), PACK);

    expect(world.player.use).toHaveBeenCalledWith(CORPSE);
  });

  it('moves only what is on the list', () => {
    holding([
      item({ serial: 2, graphic: FEATHER, amount: 12 }),
      item({ serial: 3, graphic: MEAT, amount: 4 }),
    ]);

    take(corpse(CORPSE), PACK);

    expect(world.player.moveItem.mock.calls).toEqual([[2, PACK]]);
  });

  it('counts what actually left the corpse, not what was asked to', () => {
    let contents = [item({ serial: 2, graphic: FEATHER, amount: 12 })];
    world.client.findObject = vi.fn(() => corpse(CORPSE, contents));
    world.player.moveItem = vi.fn(() => {
      contents = [];

      return 1;
    });

    expect(take(corpse(CORPSE), PACK)).toEqual({ stacks: 1, items: 12 });
    expect(memory().emptied.has(CORPSE)).toBe(true);
  });

  it('leaves a stack the shard refused off the tally, and comes back for it', () => {
    holding([item({ serial: 2, graphic: FEATHER, amount: 12 })]);

    expect(take(corpse(CORPSE), PACK)).toEqual({ stacks: 0, items: 0 });
    expect(memory().emptied.has(CORPSE)).toBe(false);
  });

  it('writes off a corpse holding nothing worth taking', () => {
    holding([item({ serial: 3, graphic: MEAT })]);

    expect(take(corpse(CORPSE), PACK)).toEqual({ stacks: 0, items: 0 });
    expect(world.player.moveItem).not.toHaveBeenCalled();
    expect(memory().emptied.has(CORPSE)).toBe(true);
  });

  // Reading contents can throw rather than answer, which containers.ts turns into undefined
  it('writes off one that will not say what it holds rather than asking forever', () => {
    world.client.findObject = vi.fn(() =>
      item({
        serial: CORPSE,
        graphic: CORPSE_GRAPHIC,
        get contents(): Item[] {
          throw new Error('Unexpected end of JSON input');
        },
      }),
    );

    expect(take(corpse(CORPSE), PACK)).toEqual({ stacks: 0, items: 0 });
    expect(memory().emptied.has(CORPSE)).toBe(true);
  });
});
