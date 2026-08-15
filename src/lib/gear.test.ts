import { beforeEach, describe, expect, it, vi } from 'vitest';
import { installGlobals, item, type FakePlayer, type FakeWorld } from '../test-support/uo.js';
import { createGear, type Gear, type GearOptions } from './gear.js';

const katana = item({ serial: 0x4000_0101, graphic: 0x13ff, name: 'a katana' });
const helmet = item({ serial: 0x4000_0202, graphic: 0x140a, name: 'a norse helm' });
const gloves = item({ serial: 0x4000_0303, graphic: 0x13c6, name: 'leather gloves' });
const tunic = item({ serial: 0x4000_0404, graphic: 0x1fa1, name: 'a leather tunic' });

// Which key each test piece shows up under, so the mocks can dress and undress the character the way
// the client would. The fixture derives findItemOnLayer from the same object, so the two views of a
// layer cannot drift apart here any more than they can in the real client.
const KEYS: Record<number, keyof FakePlayer['equippedItems']> = {
  [katana.serial]: 'oneHanded',
  [helmet.serial]: 'helmet',
  [gloves.serial]: 'gloves',
  [tunic.serial]: 'tunic',
};

const ITEMS: Record<number, Item> = {
  [katana.serial]: katana,
  [helmet.serial]: helmet,
  [gloves.serial]: gloves,
  [tunic.serial]: tunic,
};

const ARMOUR = [helmet, gloves, tunic];

let world: FakeWorld;

// A fresh one per test, which is what the factory is for: it latches both the remembered pieces and
// the lesson about this shard, and two scripts in one process must not share either.
const gearFor = (overrides: Partial<GearOptions> = {}): Gear =>
  createGear({
    prefix: 'mage',
    layers: [Layers.OneHanded, Layers.TwoHanded, Layers.Helmet, Layers.Gloves, Layers.Tunic],
    moveDelayMs: 0,
    equip: { attempts: 3, timeoutMs: 2000, pollMs: 200 },
    disarm: { attempts: 3, timeoutMs: 2000, pollMs: 200 },
    ...overrides,
  });

const wearing = (piece: Item): boolean => world.player.equippedItems[KEYS[piece.serial]] !== undefined;

// A character in a weapon and three pieces of armour, on a client that lets all four be moved and
// equipped again
const dressed = (): void => {
  for (const piece of [katana, ...ARMOUR]) {
    world.player.equippedItems[KEYS[piece.serial]] = piece;
  }

  world.player.moveItem.mockImplementation((serial: number) => {
    delete world.player.equippedItems[KEYS[serial]];

    return 1;
  });

  world.player.equip.mockImplementation((serial: number) => {
    world.player.equippedItems[KEYS[serial]] = ITEMS[serial];
  });

  // Everything still resolves: the pieces are sitting in the pack, not destroyed
  world.client.findObject.mockImplementation((serial: number) => ITEMS[serial]);
};

beforeEach(() => {
  world = installGlobals();
});

describe('stow', () => {
  it('takes the hands and leaves the armour on, which is what a first trance costs', () => {
    dressed();

    expect(gearFor().stow()).toBe(true);
    expect(wearing(katana)).toBe(false);
    expect(ARMOUR.every(wearing)).toBe(true);
  });

  it('moves what it takes into the backpack, by serial', () => {
    dressed();

    gearFor().stow();

    expect(world.player.moveItem).toHaveBeenCalledWith(katana.serial, 0x40000000);
    expect(world.player.moveItem).toHaveBeenCalledTimes(1);
  });

  it('does nothing and succeeds on a character wearing none of it', () => {
    expect(gearFor().stow()).toBe(true);
    expect(world.player.moveItem).not.toHaveBeenCalled();
  });

  it('moves nothing when the client reports no backpack', () => {
    dressed();
    world.player.backpack = undefined;

    expect(gearFor().stow()).toBe(false);
    expect(world.player.moveItem).not.toHaveBeenCalled();
  });

  // The hands are the half meditation universally refuses. A glove that will not move must not stop
  // this run meditating ever again.
  it('answers on the hands alone, not on the armour it could not shift', () => {
    dressed();
    world.player.moveItem.mockImplementation((serial: number) => {
      if (serial === katana.serial) {
        delete world.player.equippedItems.oneHanded;
      }

      return 1;
    });

    const gear = gearFor({ stripAtOnce: true });

    expect(gear.stow()).toBe(true);
    expect(wearing(tunic)).toBe(true);
  });

  it('strips everything from the first trance when the shard is already known to block on armour', () => {
    dressed();

    expect(gearFor({ stripAtOnce: true }).stow()).toBe(true);
    expect(wearing(katana)).toBe(false);
    expect(ARMOUR.some(wearing)).toBe(false);
  });

  // untilLanded reissues act() wholesale, and a reissue that bounces what already landed back out of
  // the pack and in again is how a slow strip turns into a failed one
  it('reissues only what is still on, not the pieces that already came off', () => {
    dressed();

    const landed = new Set<number>();

    world.player.moveItem.mockImplementation((serial: number) => {
      if (serial === helmet.serial || landed.has(serial)) {
        delete world.player.equippedItems[KEYS[serial]];
      }

      landed.add(serial);

      return 1;
    });

    gearFor({ stripAtOnce: true }).stow();

    const forHelmet = world.player.moveItem.mock.calls.filter(
      ([serial]) => serial === helmet.serial,
    );

    expect(forHelmet).toHaveLength(1);
    expect(ARMOUR.some(wearing)).toBe(false);
  });
});

describe('stripMore', () => {
  it('takes the armour off and says something came off', () => {
    dressed();

    const gear = gearFor();
    gear.stow();

    expect(gear.stripMore()).toBe(true);
    expect(ARMOUR.some(wearing)).toBe(false);
  });

  // What stops the caller escalating for ever, with no counter to do it
  it('answers false the second time, because there is nothing left to take', () => {
    dressed();

    const gear = gearFor();
    gear.stow();
    gear.stripMore();

    expect(gear.stripMore()).toBe(false);
  });

  it('answers false on a character with no armour on to begin with', () => {
    world.player.equippedItems.oneHanded = katana;
    world.player.moveItem.mockImplementation(() => {
      delete world.player.equippedItems.oneHanded;

      return 1;
    });

    const gear = gearFor();
    gear.stow();

    expect(gear.stripMore()).toBe(false);
  });

  it('latches the lesson, so the next trance strips everything in one pass', () => {
    dressed();

    const gear = gearFor();
    gear.stow();
    gear.stripMore();
    gear.restore();

    world.player.moveItem.mockClear();
    gear.stow();

    expect(ARMOUR.some(wearing)).toBe(false);
    expect(world.player.moveItem).toHaveBeenCalledTimes(4);
  });

  it('does not carry the lesson over into another script s gear', () => {
    dressed();

    const learned = gearFor();
    learned.stow();
    learned.stripMore();
    learned.restore();

    const fresh = gearFor();
    fresh.stow();

    expect(ARMOUR.every(wearing)).toBe(true);
  });
});

describe('restore', () => {
  // The whole reason this module exists rather than reusing createTool's by-graphic search: the
  // properties worth wearing ride on the serial, not on the graphic
  it('puts back the exact serials it took, and nothing else', () => {
    dressed();

    const gear = gearFor({ stripAtOnce: true });
    gear.stow();
    world.player.equip.mockClear();

    expect(gear.restore()).toBe(true);
    expect(world.player.equip.mock.calls.map(([serial]) => serial).sort()).toEqual(
      [katana, ...ARMOUR].map((piece) => piece.serial).sort(),
    );
    expect([katana, ...ARMOUR].every(wearing)).toBe(true);
  });

  // Load bearing rather than tidy: the caller calls this on every way out of a wait, including the
  // ones where the stow found nothing to take
  it('does nothing at all when nothing was stowed', () => {
    expect(gearFor().restore()).toBe(true);
    expect(world.player.equip).not.toHaveBeenCalled();
    expect(world.target.cancel).not.toHaveBeenCalled();
  });

  it('reissues only what is still off', () => {
    dressed();

    const gear = gearFor({ stripAtOnce: true });
    gear.stow();

    const tried = new Set<number>();

    world.player.equip.mockImplementation((serial: number) => {
      if (serial === katana.serial || tried.has(serial)) {
        world.player.equippedItems[KEYS[serial]] = ITEMS[serial];
      }

      tried.add(serial);
    });

    gear.restore();

    const forKatana = world.player.equip.mock.calls.filter(([serial]) => serial === katana.serial);

    expect(forKatana).toHaveLength(1);
  });

  it('fails when a hand it emptied is still empty, which is the one thing worth ending a run over', () => {
    dressed();

    const gear = gearFor();
    gear.stow();
    world.player.equip.mockImplementation(() => undefined);

    expect(gear.restore()).toBe(false);
  });

  // A slower character beats a stopped one
  it('succeeds when only armour would not go back, and says which piece', () => {
    dressed();

    const gear = gearFor({ stripAtOnce: true });
    gear.stow();
    world.player.equip.mockImplementation((serial: number) => {
      if (serial !== tunic.serial) {
        world.player.equippedItems[KEYS[serial]] = ITEMS[serial];
      }
    });

    expect(gear.restore()).toBe(true);
    expect(world.log.mock.calls.flat().join('\n')).toContain('would not go back on');
  });

  it('keeps armour it could not return, so the next trance tries it again', () => {
    dressed();

    const gear = gearFor({ stripAtOnce: true });
    gear.stow();
    world.player.equip.mockImplementation((serial: number) => {
      if (serial !== tunic.serial) {
        world.player.equippedItems[KEYS[serial]] = ITEMS[serial];
      }
    });
    gear.restore();

    world.player.equip.mockImplementation((serial: number) => {
      world.player.equippedItems[KEYS[serial]] = ITEMS[serial];
    });

    expect(gear.restore()).toBe(true);
    expect(wearing(tunic)).toBe(true);
  });

  // The rung of the ladder that loses the properties, and still worth taking: a character with the
  // wrong katana casts, and one with an empty hand does not
  it('falls back on the by-graphic draw when the weapon it stowed has stopped resolving', () => {
    dressed();

    const gear = gearFor({ rearm: vi.fn(() => true) as unknown as () => boolean });
    gear.stow();

    world.client.findObject.mockImplementation((serial: number) =>
      serial === katana.serial ? undefined : ITEMS[serial],
    );
    world.player.equip.mockImplementation(() => undefined);

    expect(gear.restore()).toBe(true);
    expect(world.log.mock.calls.flat().join('\n')).toContain('is gone');
  });

  it('stops retrying a piece the client no longer resolves', () => {
    dressed();

    const rearm = vi.fn(() => true);
    const gear = gearFor({ rearm });
    gear.stow();

    world.client.findObject.mockImplementation((serial: number) =>
      serial === katana.serial ? undefined : ITEMS[serial],
    );
    world.player.equip.mockImplementation(() => undefined);
    gear.restore();

    world.player.equip.mockClear();

    expect(gear.restore()).toBe(true);
    expect(world.player.equip).not.toHaveBeenCalled();
  });
});

describe('survey', () => {
  it('names every piece that comes off for a trance', () => {
    dressed();

    const line = gearFor().survey();

    expect(line).toContain('4 piece(s)');
    expect(line).toContain('a katana');
    expect(line).toContain('a leather tunic');
  });

  // The line that catches a client whose findItemOnLayer does not answer for the player: an empty
  // survey on a dressed character means nothing will ever be stripped
  it('says so when it can see nothing to take, and points at the config', () => {
    expect(gearFor().survey()).toContain('STRIP_LAYERS');
  });
});
