import { beforeEach, describe, expect, it, vi } from 'vitest';

import { Layers, installGlobals, item, mobile, type FakeWorld } from '../test-support/uo.js';

const BOARD = 0x1bd7;
const LOG = 0x1bdd;
const BEETLE = 0x317;
const ANIMAL_PACK = 0x50000000;

let world: FakeWorld;

// haul.ts latches "already reported the animals" after the first search, so it is imported fresh
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
  const oneAnimalNearby = (extra: Partial<Mobile> = {}) => {
    world.client.findAllMobilesOfType.mockImplementation((graphic: number) =>
      graphic === BEETLE ? [beetle(1, extra)] : [],
    );
    world.client.findObject.mockImplementation((serial: number) => beetle(serial, extra));
  };

  // A full animal from here is one whose pack takes the moves and lets nothing leave the backpack -
  // moveItem answers nothing at all, the way installGlobals leaves it
  const packRefusesEverything = (contents: Item[]) => {
    Object.defineProperty(world.player, 'backpack', {
      configurable: true,
      get: () => ({ serial: 0x40000000, contents }),
    });

    world.client.findItemOnLayer.mockImplementation((_serial: number, layer: number) =>
      layer === Layers.Backpack ? item({ serial: ANIMAL_PACK, graphic: 0x0e76 }) : undefined,
    );
  };

  // Two animals, the first of which only ever accepts stack 5. Hands back the backpack it reads, so
  // a test can load it and then load it again for a second haul.
  const oneFullOneSpare = (): Item[] => {
    const full = beetle(1, { x: 100 });
    const spare = beetle(2, { x: 101 });

    world.client.findAllMobilesOfType.mockImplementation((graphic: number) =>
      graphic === BEETLE ? [full, spare] : [],
    );
    world.client.findObject.mockImplementation((serial: number) =>
      serial === 1 ? full : serial === 2 ? spare : undefined,
    );

    const remaining: Item[] = [];

    Object.defineProperty(world.player, 'backpack', {
      configurable: true,
      get: () => ({ serial: 0x40000000, contents: remaining }),
    });
    world.client.findItemOnLayer.mockImplementation((serial: number) =>
      item({ serial: serial === 1 ? ANIMAL_PACK : ANIMAL_PACK + 1, graphic: 0x0e76 }),
    );
    world.player.moveItem.mockImplementation((serial: number, into: number) => {
      if (into === ANIMAL_PACK && serial !== 5) return;

      const at = remaining.findIndex((i) => i.serial === serial);
      if (at >= 0) remaining.splice(at, 1);
    });

    return remaining;
  };

  const overweight = () => {
    world.player.weight = 390;
    world.player.weightMax = 400;
  };

  it('says so when there is no animal', async () => {
    const { unload } = await loadHaul();

    expect(unload()).toBe(false);
    expect(said('no pack animal nearby')).toBe(true);
  });

  // An animal that takes nothing is full rather than missing, and only a missing one is worth
  // giving up the search for
  it('reports the animal even when it takes nothing', async () => {
    oneAnimalNearby();
    packAcceptsEverything([]);
    const { unload } = await loadHaul();

    expect(unload()).toBe(true);
  });

  it('moves boards onto the animal', async () => {
    oneAnimalNearby();
    packAcceptsEverything([item({ serial: 5, graphic: BOARD, amount: 20 })]);
    const { unload } = await loadHaul();

    expect(unload()).toBe(true);
    expect(world.player.moveItem).toHaveBeenCalledWith(5, ANIMAL_PACK);
  });

  it('leaves a log that has not been given up on', async () => {
    oneAnimalNearby();
    packAcceptsEverything([item({ serial: 5, graphic: LOG, amount: 20, hue: 0 })]);
    const { unload } = await loadHaul();

    unload();

    expect(world.player.moveItem).not.toHaveBeenCalled();
  });

  // A log that leaves as a log never comes back as a board, and the verdict may only have been a
  // throttle or a lost cursor - so it stays in the pack for the next haul's conversion instead
  it('leaves the logs of a hue the conversion gave up on', async () => {
    oneAnimalNearby();
    packAcceptsEverything([item({ serial: 5, graphic: LOG, amount: 20, hue: 0x4a8 })]);
    overweight();
    const { unload } = await loadHaul();
    const { unconvertible } = await import('./boards.js');
    unconvertible.add(0x4a8);

    unload();

    expect(world.player.moveItem).not.toHaveBeenCalled();
  });

  // Otherwise a pack that stops shedding weight says nothing about why
  it('says the logs are staying when it is still overweight', async () => {
    oneAnimalNearby();
    packAcceptsEverything([item({ serial: 5, graphic: LOG, amount: 20, hue: 0 })]);
    overweight();
    const { unload } = await loadHaul();

    unload();

    expect(said('20 logs would not convert, keeping them in the pack')).toBe(true);
  });

  it('says nothing about the logs while there is still room to carry them', async () => {
    oneAnimalNearby();
    packAcceptsEverything([item({ serial: 5, graphic: LOG, amount: 20, hue: 0 })]);
    const { unload } = await loadHaul();

    unload();

    expect(said('keeping them in the pack')).toBe(false);
  });

  // A giant beetle is rideable, so the double-click would mount you instead of opening the pack
  it('asks the backpack layer before resorting to a double-click', async () => {
    oneAnimalNearby();
    packAcceptsEverything([item({ serial: 5, graphic: BOARD, amount: 20 })]);
    const { unload } = await loadHaul();

    unload();

    expect(world.client.findItemOnLayer).toHaveBeenCalledWith(1, Layers.Backpack);
    expect(world.player.use).not.toHaveBeenCalledWith(1);
  });

  it('falls back to a double-click only when the layer comes back empty', async () => {
    oneAnimalNearby();
    packAcceptsEverything([item({ serial: 5, graphic: BOARD, amount: 20 })]);
    world.client.findItemOnLayer.mockReturnValue(undefined);
    const { unload } = await loadHaul();

    unload();

    expect(world.player.use).toHaveBeenCalledWith(1);
    expect(said('no reachable backpack')).toBe(true);
  });

  // An animal that stops accepting is full rather than broken, so what is left goes to the next
  it('carries the leftovers on to the next animal when one fills up', async () => {
    const remaining = oneFullOneSpare();
    remaining.push(
      item({ serial: 5, graphic: BOARD, amount: 20 }),
      item({ serial: 6, graphic: BOARD, amount: 20 }),
    );

    const { unload } = await loadHaul();

    expect(unload()).toBe(true);
    expect(world.player.moveItem).toHaveBeenCalledWith(6, ANIMAL_PACK + 1);
    expect(said('leaving it out of the rest of the run')).toBe(true);
  });

  describe('an animal that has already refused a load', () => {
    // The point of the whole thing: the walk and one move per stack, paid again every haul, to prove
    // what the last haul had already found out
    it('is not walked to again', async () => {
      oneAnimalNearby();
      packRefusesEverything([item({ serial: 5, graphic: BOARD, amount: 20 })]);
      const { unload } = await loadHaul();

      unload();
      world.player.moveItem.mockClear();
      unload();

      expect(world.player.moveItem).not.toHaveBeenCalled();
    });

    it('is named when it is written off', async () => {
      oneAnimalNearby({ name: 'Bessie' });
      packRefusesEverything([item({ serial: 5, graphic: BOARD, amount: 20 })]);
      const { unload } = await loadHaul();

      unload();

      expect(said("'Bessie' took 0 of 20, leaving it out of the rest of the run")).toBe(true);
    });

    // Only the full one: the animal that took the leftovers has room and is the one to fill next
    it('does not take the rest of the herd with it', async () => {
      const remaining = oneFullOneSpare();
      remaining.push(
        item({ serial: 5, graphic: BOARD, amount: 20 }),
        item({ serial: 6, graphic: BOARD, amount: 20 }),
      );

      const { unload } = await loadHaul();

      unload();
      world.player.moveItem.mockClear();
      remaining.push(item({ serial: 7, graphic: BOARD, amount: 20 }));
      unload();

      expect(world.player.moveItem).toHaveBeenCalledWith(7, ANIMAL_PACK + 1);
      expect(world.player.moveItem).not.toHaveBeenCalledWith(7, ANIMAL_PACK);
    });

    // A save refuses every move at once, so an animal would be written off for the rest of the run
    // over a five second pause
    it('is not written off over a world save', async () => {
      oneAnimalNearby();
      packRefusesEverything([item({ serial: 5, graphic: BOARD, amount: 20 })]);
      world.journal.containsText.mockReturnValue(true);
      const { unload } = await loadHaul();

      unload();
      world.player.moveItem.mockClear();
      unload();

      expect(world.player.moveItem).toHaveBeenCalledWith(5, ANIMAL_PACK);
      expect(said('trying the next')).toBe(true);
    });

    // The animal is still there, so the run goes on converting and chopping until the overweight
    // stop or the stall watch ends it - it just stops walking the herd to find out
    it('leaves the run hauling once every one of them is full', async () => {
      oneAnimalNearby();
      packRefusesEverything([item({ serial: 5, graphic: BOARD, amount: 20 })]);
      const { unload } = await loadHaul();

      unload();

      expect(unload()).toBe(true);
      expect(said('all 1 pack animal(s) are full')).toBe(true);
    });

    it('says they are all full once rather than once a haul', async () => {
      oneAnimalNearby();
      packRefusesEverything([item({ serial: 5, graphic: BOARD, amount: 20 })]);
      const { unload } = await loadHaul();

      unload();
      unload();
      unload();

      expect(world.log.mock.calls.filter(([line]) => String(line).includes('are full'))).toHaveLength(
        1,
      );
    });
  });

  describe('the boards an animal is loaded to', () => {
    // The animal's own pack, read for the cap. Moves land in it, splitting the stack when moveItem
    // is passed an amount, so a second pass sees what the first one left behind.
    const animalHolding = (held: Item[], carried: Item[]) => {
      const inside = [...held];
      const remaining = [...carried];

      Object.defineProperty(world.player, 'backpack', {
        configurable: true,
        get: () => ({ serial: 0x40000000, contents: remaining }),
      });

      world.client.findItemOnLayer.mockImplementation((_serial: number, layer: number) =>
        layer === Layers.Backpack
          ? item({ serial: ANIMAL_PACK, graphic: 0x0e76, contents: inside })
          : undefined,
      );

      world.player.moveItem.mockImplementation(
        (serial: number, _into: number, _x?: number, _y?: number, _z?: number, amount?: number) => {
          const at = remaining.findIndex((i) => i.serial === serial);
          if (at < 0) return;

          const stack = remaining[at];
          const whole = stack.amount ?? 1;
          const moved = Math.min(amount ?? whole, whole);

          if (moved >= whole) remaining.splice(at, 1);
          else stack.amount = whole - moved;

          inside.push(item({ serial: 0x900 + inside.length, graphic: stack.graphic, amount: moved }));
        },
      );

      return { inside, remaining };
    };

    it('walks past an animal that is already at its cap', async () => {
      oneAnimalNearby({ name: 'Bessie' });
      animalHolding(
        [item({ serial: 9, graphic: BOARD, amount: 1600 })],
        [item({ serial: 5, graphic: BOARD, amount: 20 })],
      );
      const { unload } = await loadHaul();

      unload();

      expect(world.player.moveItem).not.toHaveBeenCalled();
      expect(said("'Bessie' already holds 1600, its 1600")).toBe(true);
    });

    // The requirement: hue1 + hue2 + ... = 1600, so coloured wood counts towards the same cap
    it('counts every hue towards the one cap', async () => {
      oneAnimalNearby();
      animalHolding(
        [
          item({ serial: 9, graphic: BOARD, amount: 800, hue: 0 }),
          item({ serial: 10, graphic: BOARD, amount: 800, hue: 0x4a8 }),
        ],
        [item({ serial: 5, graphic: BOARD, amount: 20 })],
      );
      const { unload } = await loadHaul();

      unload();

      expect(world.player.moveItem).not.toHaveBeenCalled();
    });

    it('splits the stack that would take it past the cap', async () => {
      oneAnimalNearby();
      const { remaining } = animalHolding(
        [item({ serial: 9, graphic: BOARD, amount: 1500 })],
        [item({ serial: 5, graphic: BOARD, amount: 300 })],
      );
      const { unload } = await loadHaul();

      unload();

      expect(world.player.moveItem).toHaveBeenCalledWith(
        5,
        ANIMAL_PACK,
        undefined,
        undefined,
        undefined,
        100,
      );
      expect(remaining.map((i) => i.amount)).toEqual([200]);
    });

    it('leaves an animal it filled out of the rest of the run', async () => {
      oneAnimalNearby({ name: 'Bessie' });
      animalHolding(
        [item({ serial: 9, graphic: BOARD, amount: 1500 })],
        [item({ serial: 5, graphic: BOARD, amount: 300 })],
      );
      const { unload } = await loadHaul();

      unload();
      world.player.moveItem.mockClear();
      unload();

      expect(said("'Bessie' took 100, loaded to its 1600")).toBe(true);
      expect(world.player.moveItem).not.toHaveBeenCalled();
    });

    it('moves whole stacks without an amount while there is room for them', async () => {
      oneAnimalNearby();
      animalHolding(
        [],
        [
          item({ serial: 5, graphic: BOARD, amount: 100 }),
          item({ serial: 6, graphic: BOARD, amount: 100 }),
        ],
      );
      const { unload } = await loadHaul();

      unload();

      expect(world.player.moveItem).toHaveBeenCalledWith(5, ANIMAL_PACK);
      expect(world.player.moveItem).toHaveBeenCalledWith(6, ANIMAL_PACK);
      expect(said('loaded to its')).toBe(false);
    });

    // An unopened pack answers undefined, and read as 0 an animal already carrying its load would
    // be filled all over again
    it('loads until it refuses when the pack will not say what is in it', async () => {
      oneAnimalNearby();
      packAcceptsEverything([item({ serial: 5, graphic: BOARD, amount: 2000 })]);
      const { unload } = await loadHaul();

      unload();

      expect(world.player.moveItem).toHaveBeenCalledWith(5, ANIMAL_PACK);
    });

    it('loads until it refuses when the cap is off', async () => {
      oneAnimalNearby();
      animalHolding(
        [item({ serial: 9, graphic: BOARD, amount: 1600 })],
        [item({ serial: 5, graphic: BOARD, amount: 20 })],
      );
      const { unload } = await loadHaul({ BOARDS_PER_ANIMAL: 0 });

      unload();

      expect(world.player.moveItem).toHaveBeenCalledWith(5, ANIMAL_PACK);
    });
  });
});
