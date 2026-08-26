import { beforeEach, describe, expect, it } from 'vitest';

import { installGlobals, item, type FakeWorld } from '../test-support/uo.js';
import {
  collectIn,
  contentsOf,
  findIn,
  isContainer,
  openContainers,
  packContents,
} from './containers.js';

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

  // The live client answers `[]` for plain items, so an empty array is not evidence of anything -
  // taking it as proof made every item in the pack a container and the sell run clicked them all
  it('takes an empty contents array as no evidence, leaving it to the graphic', () => {
    expect(isContainer(item({ serial: 1, graphic: 0x1234, contents: [] }))).toBe(false);
  });

  it('still accepts an emptied bag, on its graphic', () => {
    expect(isContainer(item({ serial: 1, graphic: BAG, contents: [] }))).toBe(true);
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

// A live run died on "Exception executing 'itemGetContents': Unexpected end of JSON input" - the
// client failing the question rather than answering it. Nothing above these functions has a try in
// it, so an unreadable bag took the whole run with it.
describe('contentsOf', () => {
  // A bag whose contents getter throws on every read, counting how often it was asked
  const unreadableBag = (serial: number): Item & { reads: () => number } => {
    const bag = item({ serial, graphic: BAG }) as Item & { reads: () => number };
    let reads = 0;

    Object.defineProperty(bag, 'contents', {
      configurable: true,
      get: () => {
        reads += 1;
        throw new SyntaxError('Unexpected end of JSON input');
      },
    });

    bag.reads = () => reads;

    return bag;
  };

  it('reads an ordinary container normally', () => {
    const bag = item({ serial: 1, graphic: BAG, contents: [item({ serial: 2, graphic: POTION })] });

    expect(contentsOf(bag)).toHaveLength(1);
  });

  it('treats a bag that will not answer as one that has not been opened', () => {
    expect(contentsOf(unreadableBag(1))).toBeUndefined();
  });

  it('says so once rather than once per scan', () => {
    const bag = unreadableBag(2);

    contentsOf(bag);
    contentsOf(bag);
    contentsOf(bag);

    expect(world.log).toHaveBeenCalledTimes(1);
    expect(world.log).toHaveBeenCalledWith(expect.stringContaining('would not answer'));
  });

  // The crash was thrown out of a recursive walk, so the searches have to survive it too - and a
  // lower bound is what they already promise over containers nobody has opened
  it('lets a search step over an unreadable bag instead of dying in it', () => {
    const contents = [
      unreadableBag(3),
      item({ serial: 4, graphic: BAG, contents: [item({ serial: 5, graphic: POTION })] }),
    ];

    expect(collectIn(contents, (found) => found.graphic === POTION)).toHaveLength(1);
    expect(findIn(contents, (found) => found.graphic === POTION)?.serial).toBe(5);
  });

  // The read is a native round trip that fails rather than answers, and the pack is walked several
  // times per swing - re-asking cost a mining run hundreds of these between one dig and the next.
  it('asks a bag that will not answer once, not once per scan', () => {
    const bag = unreadableBag(6);

    contentsOf(bag);
    contentsOf(bag);
    contentsOf(bag);

    expect(bag.reads()).toBe(1);
  });

  it('asks again once the bag has been opened, which is what makes it readable', () => {
    const bag = unreadableBag(7);

    contentsOf(bag);
    openContainers(7);
    contentsOf(bag);

    expect(bag.reads()).toBe(2);
  });

  // Latching this one would leave every later pack read empty, and a run that believes its pack is
  // empty does nothing at all
  it('never gives up on the backpack, however it answered last time', () => {
    const loaded = [item({ serial: 9, graphic: POTION })];
    let answered = false;

    Object.defineProperty(world.player, 'backpack', {
      configurable: true,
      value: item({ serial: 8, graphic: BACKPACK }),
    });

    Object.defineProperty(world.player.backpack as object, 'contents', {
      configurable: true,
      get: () => {
        if (!answered) {
          answered = true;
          throw new SyntaxError('Unexpected end of JSON input');
        }

        return loaded;
      },
    });

    expect(packContents()).toBeUndefined();
    expect(packContents()).toHaveLength(1);
  });

  it('reads the pack as empty when the pack itself will not answer', () => {
    Object.defineProperty(world.player, 'backpack', {
      configurable: true,
      get: () => {
        throw new SyntaxError('Unexpected end of JSON input');
      },
    });

    expect(packContents()).toBeUndefined();
  });
});
