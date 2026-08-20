import { beforeEach, describe, expect, it, vi } from 'vitest';

import { Layers, installGlobals, item, mobile, type FakeWorld } from '../test-support/uo.js';

const BOARD = 0x1bd7;
const LOG = 0x1bdd;
const BEETLE = 0x317;
const ANIMAL_PACK = 0x50000000;

let world: FakeWorld;

// haul.ts latches "already reported the animals" after the first search, and it reads the
// unconvertible hues out of boards.ts, so both modules start clean each test.
const loadHaul = async (config: Record<string, unknown> = {}) => {
  vi.doMock('./config.js', async () => ({
    ...(await vi.importActual<object>('./config.js')),
    BOUNDS: undefined,
    ...config,
  }));
  return import('./haul.js');
};

const said = (fragment: string) =>
  world.log.mock.calls.some(([line]) => String(line).includes(fragment));

const beetle = (serial: number, extra: Partial<Mobile> = {}) =>
  mobile({ serial, graphic: BEETLE, x: 100, y: 100, isRenamable: true, ...extra });

// The animal's pack resolves off the Backpack layer, and moves are asynchronous - so the fake
// empties the player's pack as moveItem is called, the way a rescan would see it
const packAcceptsEverything = (contents: Item[]) => {
  const remaining = [...contents];

  Object.defineProperty(world.player, 'backpack', {
    configurable: true,
    get: () => ({ serial: 0x40000000, contents: remaining }),
  });

  world.client.findItemOnLayer.mockImplementation((_serial: number, layer: number) =>
    layer === Layers.Backpack ? item({ serial: ANIMAL_PACK, graphic: 0x0e76 }) : undefined,
  );

  world.player.moveItem.mockImplementation((serial: number) => {
    const at = remaining.findIndex((i) => i.serial === serial);
    if (at >= 0) remaining.splice(at, 1);
  });
};

beforeEach(() => {
  vi.resetModules();
  vi.doUnmock('./config.js');
  world = installGlobals({ player: { x: 100, y: 100 } });
});

describe('findPackAnimals', () => {
  it('finds nothing when none is nearby', async () => {
    const { findPackAnimals } = await loadHaul();

    expect(findPackAnimals()).toEqual([]);
  });

  it('searches by body graphic', async () => {
    world.client.findAllMobilesOfType.mockImplementation((graphic: number) =>
      graphic === BEETLE ? [beetle(1)] : [],
    );
    const { findPackAnimals } = await loadHaul();

    expect(findPackAnimals().map((a) => a.serial)).toEqual([1]);
  });

  // Only your own pets can be renamed, so that is what tells yours from a stranger's
  it('prefers a renamable animal over a stranger of the same body', async () => {
    world.client.findAllMobilesOfType.mockImplementation((graphic: number) =>
      graphic === BEETLE ? [beetle(1, { isRenamable: false }), beetle(2)] : [],
    );
    const { findPackAnimals } = await loadHaul();

    expect(findPackAnimals().map((a) => a.serial)).toEqual([2]);
  });

  it('falls back to a stranger when none of them is yours', async () => {
    world.client.findAllMobilesOfType.mockImplementation((graphic: number) =>
      graphic === BEETLE ? [beetle(1, { isRenamable: false })] : [],
    );
    const { findPackAnimals } = await loadHaul();

    expect(findPackAnimals().map((a) => a.serial)).toEqual([1]);
  });

  // Nearest first, so the closest one fills before you walk past it to another
  it('sorts them nearest first', async () => {
    world.client.findAllMobilesOfType.mockImplementation((graphic: number) =>
      graphic === BEETLE
        ? [beetle(1, { x: 108 }), beetle(2, { x: 102 }), beetle(3, { x: 105 })]
        : [],
    );
    const { findPackAnimals } = await loadHaul();

    expect(findPackAnimals().map((a) => a.serial)).toEqual([2, 3, 1]);
  });

  it('names them once rather than every scan', async () => {
    world.client.findAllMobilesOfType.mockImplementation((graphic: number) =>
      graphic === BEETLE ? [beetle(1, { name: 'Bessie' })] : [],
    );
    const { findPackAnimals } = await loadHaul();

    findPackAnimals();
    findPackAnimals();

    expect(world.log.mock.calls.filter(([line]) => String(line).includes('Bessie'))).toHaveLength(1);
  });

  describe('pinned serials', () => {
    it('uses a pinned serial instead of searching', async () => {
      world.client.findObject.mockImplementation((serial: number) => beetle(serial));
      const { findPackAnimals } = await loadHaul({ PACK_ANIMAL_SERIALS: [0x123] });

      expect(findPackAnimals().map((a) => a.serial)).toEqual([0x123]);
      expect(world.client.findAllMobilesOfType).not.toHaveBeenCalled();
    });

    // findObject answers with an Item for anything that is not a mobile, and a pinned serial is
    // only ever hand-written
    it('discards a pinned serial that turns out to be an item', async () => {
      world.client.findObject.mockImplementation(() => item({ serial: 0x123, graphic: 0x0e76 }));
      const { findPackAnimals } = await loadHaul({ PACK_ANIMAL_SERIALS: [0x123] });

      expect(findPackAnimals()).toEqual([]);
    });

    it('discards a pinned serial that resolves to nothing', async () => {
      const { findPackAnimals } = await loadHaul({ PACK_ANIMAL_SERIALS: [0x123] });

      expect(findPackAnimals()).toEqual([]);
    });

    it('walks to the nearest of them first', async () => {
      world.client.findObject.mockImplementation((serial: number) =>
        beetle(serial, { x: 100 + serial, y: 100 }),
      );
      const { findPackAnimals } = await loadHaul({ PACK_ANIMAL_SERIALS: [9, 2, 5] });

      expect(findPackAnimals().map((a) => a.serial)).toEqual([2, 5, 9]);
    });
  });
});

describe('pickPackAnimals', () => {
  // The cursor answers each click in turn and then, for everything after them, nothing - which is
  // what the client does when ESC is pressed, and the only sign it gives that it was
  const clicks = (...answers: (object | undefined)[]) => {
    let click = 0;

    world.target.query = vi.fn(() => answers[click++]);
  };

  const knownAt = (serials: Record<number, number>) => {
    world.client.findObject.mockImplementation((serial: number) =>
      serial in serials ? beetle(serial, { x: serials[serial], y: 100 }) : undefined,
    );
  };

  it('pins what was clicked and hands it back nearest first', async () => {
    knownAt({ 7: 109, 8: 102 });
    clicks({ serial: 7 }, { serial: 8 });
    const { findPackAnimals, pickPackAnimals } = await loadHaul();

    expect(pickPackAnimals().map((a) => a.serial)).toEqual([7, 8]);
    expect(findPackAnimals().map((a) => a.serial)).toEqual([8, 7]);
    expect(world.client.findAllMobilesOfType).not.toHaveBeenCalled();
  });

  // pickMany calls keyOf before its own dedupe, so a side-effecting keyOf would pin this one twice
  it('pins an animal clicked twice only once', async () => {
    knownAt({ 7: 100, 8: 101 });
    clicks({ serial: 7 }, { serial: 7 }, { serial: 8 });
    const { pickPackAnimals } = await loadHaul();

    expect(pickPackAnimals().map((a) => a.serial)).toEqual([7, 8]);
  });

  it('keeps asking after a click that landed on something that is not a mobile', async () => {
    world.client.findObject.mockImplementation((serial: number) =>
      serial === 7 ? item({ serial: 7, graphic: 0x0e76 }) : beetle(serial, { x: 100, y: 100 }),
    );
    clicks({ serial: 7 }, { serial: 8 });
    const { pickPackAnimals } = await loadHaul();

    expect(pickPackAnimals().map((a) => a.serial)).toEqual([8]);
  });

  it('uses a body PACK_ANIMAL_GRAPHICS has never heard of, and says so', async () => {
    world.client.findObject.mockImplementation((serial: number) =>
      mobile({ serial, graphic: 0x99, x: 100, y: 100 }),
    );
    clicks({ serial: 7 });
    const { pickPackAnimals } = await loadHaul();

    expect(pickPackAnimals().map((a) => a.serial)).toEqual([7]);
    expect(said('is not a body PACK_ANIMAL_GRAPHICS knows')).toBe(true);
  });

  it('leaves the config pinning alone when the first cursor is cancelled', async () => {
    knownAt({ 0x123: 100 });
    clicks(undefined);
    const { findPackAnimals, pickPackAnimals } = await loadHaul({ PACK_ANIMAL_SERIALS: [0x123] });

    expect(pickPackAnimals()).toEqual([]);
    expect(findPackAnimals().map((a) => a.serial)).toEqual([0x123]);
  });

  it('falls back to the search when nothing was picked and nothing was pinned', async () => {
    world.client.findAllMobilesOfType.mockImplementation((graphic: number) =>
      graphic === BEETLE ? [beetle(1)] : [],
    );
    clicks(undefined);
    const { findPackAnimals, pickPackAnimals } = await loadHaul();

    pickPackAnimals();

    expect(findPackAnimals().map((a) => a.serial)).toEqual([1]);
  });
});

describe('unload', () => {
  const oneAnimalNearby = () => {
    world.client.findAllMobilesOfType.mockImplementation((graphic: number) =>
      graphic === BEETLE ? [beetle(1)] : [],
    );
    world.client.findObject.mockImplementation((serial: number) => beetle(serial));
  };

  it('says so when there is no animal', async () => {
    const { unload } = await loadHaul();

    expect(unload()).toBe(false);
    expect(world.log).toHaveBeenCalledWith(expect.stringContaining('no pack animal nearby'));
  });

  it('moves boards onto the animal', async () => {
    oneAnimalNearby();
    packAcceptsEverything([item({ serial: 5, graphic: BOARD, amount: 20 })]);
    const { unload } = await loadHaul();

    expect(unload()).toBe(true);
    expect(world.player.moveItem).toHaveBeenCalledWith(5, ANIMAL_PACK);
  });

  // A log merely waiting its turn stays in the pack: it is worth more as boards, and the next
  // haul retries it
  it('leaves a log that has not been given up on', async () => {
    oneAnimalNearby();
    packAcceptsEverything([item({ serial: 5, graphic: LOG, amount: 20, hue: 0 })]);
    const { unload } = await loadHaul();

    unload();

    expect(world.player.moveItem).not.toHaveBeenCalled();
  });

  it('moves the logs of a hue the conversion gave up on', async () => {
    oneAnimalNearby();
    packAcceptsEverything([item({ serial: 5, graphic: LOG, amount: 20, hue: 0x4a8 })]);
    const { unload } = await loadHaul();
    const { unconvertible } = await import('./boards.js');
    unconvertible.add(0x4a8);

    expect(unload()).toBe(true);
    expect(world.player.moveItem).toHaveBeenCalledWith(5, ANIMAL_PACK);
  });

  // The verdict may have been reached during a throttle or against a cursor the conversion lost, and
  // once these leave as logs they never come back as boards
  it('reconsiders a given-up-on hue before shipping it', async () => {
    oneAnimalNearby();
    packAcceptsEverything([item({ serial: 5, graphic: LOG, amount: 20, hue: 0x4a8 })]);
    const { unload } = await loadHaul();
    const { unconvertible } = await import('./boards.js');
    unconvertible.add(0x4a8);

    unload();

    expect(world.log).toHaveBeenCalledWith(expect.stringContaining('another go'));
  });

  // A makeBoards cut short by a save or the pass backstop writes nothing off, so retryUnconvertible
  // declines - and gating the conversion on it shipped every log raw without ever trying
  it('still converts when there is no verdict to reconsider', async () => {
    oneAnimalNearby();
    packAcceptsEverything([item({ serial: 5, graphic: LOG, amount: 20, hue: 0 })]);
    world.player.weight = 390;
    world.player.weightMax = 400;
    const { unload } = await loadHaul();

    unload();

    expect(world.player.useItemInHand).toHaveBeenCalled();
  });

  // A frozen shard converts nothing, so the verdict is worthless and the logs keep
  it('keeps the logs rather than shipping them raw during a save', async () => {
    oneAnimalNearby();
    packAcceptsEverything([item({ serial: 5, graphic: LOG, amount: 20, hue: 0 })]);
    world.player.weight = 390;
    world.player.weightMax = 400;
    world.journal.containsText.mockReturnValue(true);
    const { unload } = await loadHaul();

    unload();

    expect(world.player.moveItem).not.toHaveBeenCalled();
    expect(world.log).toHaveBeenCalledWith(expect.stringContaining('keeping the logs'));
  });

  // Ending the run overweight would be worse than carrying logs across
  it('moves the leftover logs anyway when still overweight afterwards', async () => {
    oneAnimalNearby();
    packAcceptsEverything([item({ serial: 5, graphic: LOG, amount: 20, hue: 0 })]);
    world.player.weight = 390;
    world.player.weightMax = 400;
    const { unload } = await loadHaul();

    expect(unload()).toBe(true);
    expect(world.player.moveItem).toHaveBeenCalledWith(5, ANIMAL_PACK);
    expect(world.log).toHaveBeenCalledWith(expect.stringContaining('would not convert in time'));
  });

  // A giant beetle is rideable, so the double-click would mount you instead of opening the pack
  it('asks the backpack layer before resorting to a double-click', async () => {
    oneAnimalNearby();
    packAcceptsEverything([item({ serial: 5, graphic: BOARD, amount: 20 })]);
    const { unload } = await loadHaul();

    unload();

    expect(world.client.findItemOnLayer).toHaveBeenCalledWith(1, Layers.Backpack);
    expect(world.player.use).not.toHaveBeenCalled();
  });

  it('falls back to a double-click only when the layer comes back empty', async () => {
    oneAnimalNearby();
    packAcceptsEverything([item({ serial: 5, graphic: BOARD, amount: 20 })]);
    world.client.findItemOnLayer.mockReturnValue(undefined);
    const { unload } = await loadHaul();

    unload();

    expect(world.player.use).toHaveBeenCalledWith(1);
    expect(world.log).toHaveBeenCalledWith(expect.stringContaining('no reachable backpack'));
  });

  // An animal that stops accepting is full rather than broken, so what is left goes to the next
  it('carries the leftovers on to the next animal when one fills up', async () => {
    const full = beetle(1, { x: 100 });
    const spare = beetle(2, { x: 101 });
    world.client.findAllMobilesOfType.mockImplementation((graphic: number) =>
      graphic === BEETLE ? [full, spare] : [],
    );
    world.client.findObject.mockImplementation((serial: number) =>
      serial === 1 ? full : serial === 2 ? spare : undefined,
    );

    const remaining = [
      item({ serial: 5, graphic: BOARD, amount: 20 }),
      item({ serial: 6, graphic: BOARD, amount: 20 }),
    ];
    Object.defineProperty(world.player, 'backpack', {
      configurable: true,
      get: () => ({ serial: 0x40000000, contents: remaining }),
    });
    world.client.findItemOnLayer.mockImplementation((serial: number) =>
      item({ serial: serial === 1 ? ANIMAL_PACK : ANIMAL_PACK + 1, graphic: 0x0e76 }),
    );
    // The first animal takes one stack and then refuses the rest
    world.player.moveItem.mockImplementation((serial: number, into: number) => {
      if (into === ANIMAL_PACK && serial !== 5) return;
      const at = remaining.findIndex((i) => i.serial === serial);
      if (at >= 0) remaining.splice(at, 1);
    });

    const { unload } = await loadHaul();

    expect(unload()).toBe(true);
    expect(world.player.moveItem).toHaveBeenCalledWith(6, ANIMAL_PACK + 1);
    expect(world.log).toHaveBeenCalledWith(expect.stringContaining('trying the next'));
  });
});
