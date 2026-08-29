import { beforeEach, describe, expect, it, vi } from 'vitest';

import { installGlobals, item, type FakeWorld } from '../test-support/uo.js';

let world: FakeWorld;

const loadKeep = async () => import('./keep.js');
const loadConfig = async () => import('./config.js');

beforeEach(() => {
  vi.resetModules();
  world = installGlobals();
});

const katana = item({ serial: 0x4001, graphic: 0x13ff, name: 'a katana' });

describe('KEEP', () => {
  it('names the same spell in spell and buff on every entry', async () => {
    const { KEEP } = await loadConfig();

    for (const entry of KEEP) {
      expect(BuffDebuffs[entry.buff]).toBe(Spells[entry.spell]);
    }
  });

  it('charges mana for every entry, so the gate always has a figure', async () => {
    const { KEEP } = await loadConfig();

    for (const entry of KEEP) {
      expect(entry.mana).toBeGreaterThan(0);
    }
  });

  // A cursor opened by a run that never answers it breaks every action after it
  it('wants a target cursor for nothing', async () => {
    const { KEEP } = await loadConfig();

    for (const entry of KEEP) {
      expect(entry.target).toBeUndefined();
    }
  });

  it('marks the weapon enchant as needing a weapon and the rest as not', async () => {
    const { KEEP } = await loadConfig();
    const needy = KEEP.filter((entry) => entry.needsWeapon);

    expect(needy.map((entry) => entry.spell)).toEqual([Spells.ConsecrateWeapon]);
  });
});

describe('standing', () => {
  it('asks the client for the entry s own buff', async () => {
    const { roster, standing } = await loadKeep();
    const [consecrate] = roster();

    world.player.hasBuffDebuff.mockImplementation(
      (buff: number) => buff === BuffDebuffs.ConsecrateWeapon,
    );

    expect(standing(consecrate.entry)).toBe(true);
    expect(world.player.hasBuffDebuff).toHaveBeenCalledWith(BuffDebuffs.ConsecrateWeapon);
  });

  it('is false for a buff nobody put up', async () => {
    const { roster, standing } = await loadKeep();

    expect(standing(roster()[0].entry)).toBe(false);
  });
});

describe('armed', () => {
  it('takes either hand', async () => {
    const { armed } = await loadKeep();

    expect(armed()).toBe(false);

    world.player.equippedItems.oneHanded = katana;
    expect(armed()).toBe(true);

    world.player.equippedItems.oneHanded = undefined;
    world.player.equippedItems.twoHanded = katana;
    expect(armed()).toBe(true);
  });
});

describe('due', () => {
  it('is true for a fresh entry', async () => {
    const { due, roster } = await loadKeep();

    expect(due(roster()[0])).toBe(true);
  });

  it('is false while an entry is set aside, and false for good once retired', async () => {
    const { due, retire, roster, setAside } = await loadKeep();
    const [aside, gone] = roster();

    setAside(aside, 60_000);
    retire(gone, 'out of tithing points');

    expect(due(aside)).toBe(false);
    expect(due(gone)).toBe(false);
  });

  // Or a shard that refuses one cast would leave the run believing it had misread five
  it('clears the misses an entry had collected when it is set aside', async () => {
    const { roster, setAside } = await loadKeep();
    const [entry] = roster();

    entry.misses = 4;
    setAside(entry, 60_000);

    expect(entry.misses).toBe(0);
  });
});

describe('spent', () => {
  it('is true only once every entry has been retired', async () => {
    const { retire, roster, spent } = await loadKeep();
    const table = roster();

    expect(spent(table)).toBe(false);

    retire(table[0], 'no weapon');
    expect(spent(table)).toBe(false);

    table.forEach((entry) => retire(entry, 'no tithing'));
    expect(spent(table)).toBe(true);
  });
});

describe('settled', () => {
  it('waits for every buff to be standing', async () => {
    const { roster, settled } = await loadKeep();
    const table = roster();

    expect(settled(table)).toBe(false);

    world.player.hasBuffDebuff.mockReturnValue(true);
    expect(settled(table)).toBe(true);
  });

  // A retired entry is never going up, so counting it as unsettled would never let a one-pass run end
  it('counts a retired entry as settled', async () => {
    const { retire, roster, settled } = await loadKeep();
    const table = roster();

    table.forEach((entry) => retire(entry, 'no tithing'));

    expect(settled(table)).toBe(true);
  });
});

describe('castOnce', () => {
  it('does not re-issue a buff that is already standing', async () => {
    const { castOnce, roster } = await loadKeep();
    world.player.hasBuffDebuff.mockReturnValue(true);

    expect(castOnce(roster()[0].entry)).toBe('alreadyUp');
    expect(world.player.cast).not.toHaveBeenCalled();
  });

  it('casts when the buff is down', async () => {
    const { castOnce, roster } = await loadKeep();

    castOnce(roster()[1].entry);

    expect(world.player.cast).toHaveBeenCalledWith(Spells.DivineFury);
  });

  // The buff arriving is the proof that does not depend on how this shard words its journal
  it('reads the buff going up as the cast, when the shard says nothing', async () => {
    const { castOnce, roster } = await loadKeep();
    let up = false;

    world.player.hasBuffDebuff.mockImplementation(() => up);
    world.player.cast.mockImplementation(() => {
      up = true;
    });

    expect(castOnce(roster()[1].entry)).toBe('cast');
  });
});
