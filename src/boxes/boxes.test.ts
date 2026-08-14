import { beforeEach, describe, expect, it, vi } from 'vitest';

import { installGlobals, item, type FakeWorld } from '../test-support/uo.js';
import { dumpPack, emptyBox, findBoxes, isBox, isKey } from './boxes.js';

const BOX = 0x0e7d;
const KEY = 0x100e;
const BAG = 0x0e76;
const PACK = 0x40000000;

let world: FakeWorld;

// The box is re-resolved through findObject between passes, so a test describes what each
// successive look inside it finds. The last entry is repeated once the script runs past the end.
const boxThatShows = (serial: number, passes: (Item[] | undefined)[]) => {
  let pass = 0;

  return vi.fn((asked: number) => {
    if (asked !== serial) {
      return undefined;
    }

    const contents = passes[Math.min(pass, passes.length - 1)];
    pass++;
    return item({ serial, graphic: BOX, contents });
  });
};

beforeEach(() => {
  world = installGlobals();
});

describe('isBox / isKey', () => {
  it('knows a wooden box by graphic', () => {
    expect(isBox(item({ serial: 1, graphic: BOX }))).toBe(true);
    expect(isBox(item({ serial: 2, graphic: 0x0e7e }))).toBe(true);
    expect(isBox(item({ serial: 3, graphic: BAG }))).toBe(false);
  });

  it('knows a key by graphic', () => {
    expect(isKey(item({ serial: 1, graphic: KEY }))).toBe(true);
    expect(isKey(item({ serial: 2, graphic: BOX }))).toBe(false);
  });
});

// findBoxes latches the graphic it learns, so each of these takes a fresh module
const fresh = async () => {
  vi.resetModules();
  return import('./boxes.js');
};

describe('findBoxes', () => {
  it('finds boxes at the top of the pack', async () => {
    installGlobals({
      backpack: [item({ serial: 1, graphic: BOX }), item({ serial: 2, graphic: 0x1bef })],
    });

    const { findBoxes: find } = await fresh();

    expect(find().map((box) => box.serial)).toEqual([1]);
  });

  // collectIn recurses, which is what makes a box inside a bag reachable
  it('finds a box nested inside another container', async () => {
    installGlobals({
      backpack: [
        item({ serial: 1, graphic: BAG, contents: [item({ serial: 2, graphic: BOX })] }),
      ],
    });

    const { findBoxes: find } = await fresh();

    expect(find().map((box) => box.serial)).toEqual([2]);
  });

  // The case that put '0 wooden boxes' on the screen next to a pack full of them: the shard's art
  // is not in BOX_GRAPHICS, so the name has to carry the match
  it('falls back to the name when the graphic is unknown', async () => {
    installGlobals({
      backpack: [item({ serial: 1, graphic: 0x9999, name: 'a wooden box' })],
    });

    const { findBoxes: find } = await fresh();

    expect(find().map((box) => box.serial)).toEqual([1]);
  });

  it('names the unknown graphic so it can go in the config', async () => {
    const world = installGlobals({
      backpack: [item({ serial: 1, graphic: 0x9999, name: 'a wooden box' })],
    });

    const { findBoxes: find } = await fresh();
    find();

    expect(world.log).toHaveBeenCalledWith(expect.stringContaining('0x9999'));
  });

  // A name arrives only with tooltip data, so once one box has been identified the rest are
  // matched on the graphic it taught rather than waiting for each of them to be described
  it('matches the rest of the pile on the graphic it learned', async () => {
    installGlobals({
      backpack: [
        item({ serial: 1, graphic: 0x9999, name: 'a wooden box' }),
        item({ serial: 2, graphic: 0x9999 }),
      ],
    });

    const { findBoxes: find } = await fresh();

    expect(find().map((box) => box.serial)).toEqual([1, 2]);
  });

  // Contents stay undefined until a container has been opened, so a bag nobody opened hides
  // everything in it - worth one pass of double-clicks before concluding the pack is empty
  it('opens the pack containers before giving up', async () => {
    const bag = item({ serial: 1, graphic: BAG, contents: undefined });
    const world = installGlobals({ backpack: [bag] });

    const { findBoxes: find } = await fresh();

    world.player.use = vi.fn(() => {
      bag.contents = [item({ serial: 2, graphic: BOX })];
    });

    expect(find().map((box) => box.serial)).toEqual([2]);
    expect(world.player.use).toHaveBeenCalledWith(1);
  });
});

describe('closing', () => {
  // The checked-in config is 'perBox', so the blunt close is never reached. Closing the character
  // window along with the boxes is what took it off the default.
  it('never closes every gump under the checked-in config', async () => {
    const { closeEverything } = await fresh();

    closeEverything();

    expect(world.client.closeAllGumps).not.toHaveBeenCalled();
  });

  it('closes one box window by the container serial', async () => {
    const close = vi.fn();
    world.gump.exists = vi.fn(() => true);
    world.gump.findOrWait = vi.fn(() => ({ close }));

    const { closeBox } = await fresh();
    closeBox(0x40000007);

    expect(world.gump.findOrWait).toHaveBeenCalledWith(0x40000007, 200);
    expect(close).toHaveBeenCalled();
  });

  // Container windows may not be gumps in that sense at all, and answering nothing has to be a
  // no-op rather than a crash
  it('does nothing when the container has no gump', async () => {
    world.gump.exists = vi.fn(() => false);

    const { closeBox } = await fresh();

    expect(() => closeBox(0x40000007)).not.toThrow();
    expect(world.gump.findOrWait).not.toHaveBeenCalled();
  });
});

describe('dumpPack', () => {
  it('names every graphic at the top of the pack', () => {
    const world = installGlobals({
      backpack: [item({ serial: 1, graphic: 0x9999, hue: 0, amount: 1, name: 'a wooden box' })],
    });

    dumpPack();

    expect(world.log).toHaveBeenCalledWith(expect.stringContaining('0x9999'));
    expect(world.log).toHaveBeenCalledWith(expect.stringContaining('a wooden box'));
  });
});

describe('emptyBox', () => {
  it('opens the box before looking inside it', () => {
    world.client.findObject = boxThatShows(7, [[]]);

    emptyBox(7, PACK);

    expect(world.player.use).toHaveBeenCalledWith(7);
  });

  it('throws the key on the floor and reports the box emptied', () => {
    world.client.findObject = boxThatShows(7, [[item({ serial: 8, graphic: KEY })], []]);

    const result = emptyBox(7, PACK);

    expect(world.player.moveItemOnGroundOffset).toHaveBeenCalledWith(
      8,
      expect.any(Number),
      expect.any(Number),
      expect.any(Number),
    );
    expect(world.player.moveItem).not.toHaveBeenCalled();
    expect(result.outcome).toBe('emptied');
    expect(result.dropped.map((key) => key.serial)).toEqual([8]);
  });

  // Whatever is in there comes out, but only keys hit the floor. That way round on purpose: an art
  // this does not recognise ends up somewhere safe rather than on the ground.
  it('keeps anything that is not a key, and only drops the keys', () => {
    world.client.findObject = boxThatShows(7, [
      [item({ serial: 8, graphic: KEY }), item({ serial: 9, graphic: 0x0eed })],
      [],
    ]);

    const result = emptyBox(7, PACK);

    expect(world.player.moveItemOnGroundOffset).toHaveBeenCalledWith(
      8,
      expect.any(Number),
      expect.any(Number),
      expect.any(Number),
    );
    expect(world.player.moveItem).toHaveBeenCalledWith(9, PACK);
    expect(result.moved.map((moved) => moved.serial)).toEqual([8, 9]);
    expect(result.dropped.map((key) => key.serial)).toEqual([8]);
  });

  // These two latch the key graphic they learn, so each takes a fresh module or the first one's
  // 0x9999 makes the second one's turkey a key
  it('recognises a key by name when the graphic is unknown', async () => {
    world.client.findObject = boxThatShows(7, [
      [item({ serial: 8, graphic: 0x9999, name: 'a rusty iron key' })],
      [],
    ]);

    const { emptyBox: empty } = await fresh();

    expect(empty(7, PACK).dropped.map((key) => key.serial)).toEqual([8]);
  });

  // A whole word, so the name test cannot put a turkey or a monkey on the floor
  it('does not read key inside another word as a key', async () => {
    world.client.findObject = boxThatShows(7, [
      [item({ serial: 8, graphic: 0x9999, name: 'a roasted turkey' })],
      [],
    ]);

    const { emptyBox: empty } = await fresh();

    expect(empty(7, PACK).dropped).toEqual([]);
    expect(world.player.moveItem).toHaveBeenCalledWith(8, PACK);
  });

  it('keeps going while the box is still shifting items', () => {
    world.client.findObject = boxThatShows(7, [
      [item({ serial: 8, graphic: KEY }), item({ serial: 9, graphic: KEY })],
      [item({ serial: 9, graphic: KEY })],
      [],
    ]);

    const result = emptyBox(7, PACK);

    expect(result.outcome).toBe('emptied');
    expect(result.moved.map((moved) => moved.serial)).toEqual([8, 9]);
  });

  // Contents stay undefined until a container has been opened, so a box still undefined after the
  // double-click never opened - locked, most likely - and must not be treated as empty
  it('reports a box that never opened rather than calling it empty', () => {
    world.client.findObject = boxThatShows(7, [undefined]);

    expect(emptyBox(7, PACK).outcome).toBe('unopened');
    expect(world.player.moveItem).not.toHaveBeenCalled();
  });

  it('reports a box whose contents stop moving', () => {
    world.client.findObject = boxThatShows(7, [
      [item({ serial: 8, graphic: KEY })],
      [item({ serial: 8, graphic: KEY })],
    ]);

    expect(emptyBox(7, PACK).outcome).toBe('stalled');
  });

  // A failed move leaves the same item in the box for the next pass, and it is one item either way
  it('counts an item that had to be moved twice only once', () => {
    world.client.findObject = boxThatShows(7, [
      [item({ serial: 8, graphic: KEY }), item({ serial: 9, graphic: KEY })],
      [item({ serial: 8, graphic: KEY })],
      [],
    ]);

    expect(emptyBox(7, PACK).moved.map((moved) => moved.serial)).toEqual([8, 9]);
  });

  // Contents that are not keys, so the box is the only thing findObject is asked about and the
  // shrinking count is not confused by the drop checking where a key ended up
  it('gives up on a box that never runs out', () => {
    let size = 20;
    world.client.findObject = vi.fn((asked: number) =>
      asked !== 7
        ? undefined
        : item({
            serial: 7,
            graphic: BOX,
            contents: Array.from({ length: size-- }, (_, index) =>
              item({ serial: 100 + index, graphic: 0x0eed }),
            ),
          }),
    );

    expect(emptyBox(7, PACK).outcome).toBe('stalled');
  });
});
