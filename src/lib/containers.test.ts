import { beforeEach, describe, expect, it } from 'vitest';

import { installGlobals, item, type FakeWorld } from '../test-support/uo.js';
import { collectIn, findIn, isContainer, openContainers } from './containers.js';

const BACKPACK = 0x0e75;
const BAG = 0x0e76;
const POTION = 0x0f0e;

let world: FakeWorld;

beforeEach(() => {
  world = installGlobals();
});

describe('isContainer', () => {
  it('trusts a known contents array over the graphic list', () => {
    expect(isContainer(item({ serial: 1, graphic: 0x1234, contents: [item({ serial: 2, graphic: POTION })] }))).toBe(
      true,
    );
  });

  it('accepts an empty contents array - an opened container is still a container', () => {
    expect(isContainer(item({ serial: 1, graphic: 0x1234, contents: [] }))).toBe(true);
  });

  it('falls back to the graphic list when contents are unknown', () => {
    expect(isContainer(item({ serial: 1, graphic: BAG }))).toBe(true);
  });

  it('rejects anything that is neither', () => {
    expect(isContainer(item({ serial: 1, graphic: POTION }))).toBe(false);
  });
});

describe('findIn', () => {
  it('finds a match at the top level', () => {
    const found = findIn([item({ serial: 7, graphic: 0x0f3f, name: 'pickaxe' })], (i) =>
      (i.name ?? '').includes('pickaxe'),
    );

    expect(found?.serial).toBe(7);
  });

  it('finds a match inside a sub-container', () => {
    const found = findIn(
      [item({ serial: 1, graphic: BAG, contents: [item({ serial: 7, graphic: 0x0f3f })] })],
      (i) => i.graphic === 0x0f3f,
    );

    expect(found?.serial).toBe(7);
  });

  it('descends before moving on, so the deepest branch of the first bag wins', () => {
    const found = findIn(
      [
        item({ serial: 1, graphic: BAG, contents: [item({ serial: 7, graphic: 0x0f3f })] }),
        item({ serial: 2, graphic: 0x0f3f }),
      ],
      (i) => i.graphic === 0x0f3f,
    );

    expect(found?.serial).toBe(7);
  });

  it('returns null when nothing matches', () => {
    expect(findIn([item({ serial: 1, graphic: BAG })], () => false)).toBeNull();
  });

  // Contents stay undefined until a container has been opened, which is not an error
  it('returns null for an unopened container', () => {
    expect(findIn(undefined, () => true)).toBeNull();
  });
});

describe('collectIn', () => {
  it('returns every match, nested ones included', () => {
    const found = collectIn(
      [
        item({ serial: 1, graphic: 0x1bdd }),
        item({
          serial: 2,
          graphic: BAG,
          contents: [
            item({ serial: 3, graphic: 0x1bdd }),
            item({ serial: 4, graphic: BAG, contents: [item({ serial: 5, graphic: 0x1bdd })] }),
          ],
        }),
      ],
      (i) => i.graphic === 0x1bdd,
    );

    expect(found.map((i) => i.serial)).toEqual([1, 3, 5]);
  });

  it('returns an empty list when nothing matches', () => {
    expect(collectIn([item({ serial: 1, graphic: BAG })], () => false)).toEqual([]);
  });

  it('returns an empty list for an unopened container', () => {
    expect(collectIn(undefined, () => true)).toEqual([]);
  });
});

describe('openContainers', () => {
  it('opens only the pinned bag when one is given', () => {
    world = installGlobals({ backpack: [item({ serial: 2, graphic: BAG })] });

    expect(openContainers(0x999)).toBe(true);
    expect(world.player.use).toHaveBeenCalledTimes(1);
    expect(world.player.use).toHaveBeenCalledWith(0x999);
  });

  it('opens every container in the pack when none is pinned', () => {
    world = installGlobals({
      backpack: [item({ serial: 2, graphic: BAG }), item({ serial: 3, graphic: BACKPACK })],
    });

    expect(openContainers()).toBe(true);
    expect(world.player.use.mock.calls).toEqual([[2], [3]]);
  });

  // player.use() on a non-container *uses* it, so a potion in the pack would be drunk
  it('never uses an item that is not a container', () => {
    world = installGlobals({
      backpack: [item({ serial: 2, graphic: POTION }), item({ serial: 3, graphic: BAG })],
    });

    openContainers();

    expect(world.player.use).toHaveBeenCalledTimes(1);
    expect(world.player.use).toHaveBeenCalledWith(3);
  });

  it('reports that it opened nothing when the pack holds no containers', () => {
    world = installGlobals({ backpack: [item({ serial: 2, graphic: POTION })] });

    expect(openContainers()).toBe(false);
    expect(world.player.use).not.toHaveBeenCalled();
  });
});
