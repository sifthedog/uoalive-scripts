import { beforeEach, describe, expect, it, vi } from 'vitest';
import { installGlobals, item, type FakeWorld } from '../test-support/uo.js';

// meditate.ts latches a refusal and a lost weapon for the life of the module, and weapon.ts learns a
// graphic, so every test gets a fresh copy of both
const freshMeditate = async () => {
  vi.resetModules();

  return import('./meditate.js');
};

const katana = item({ serial: 0x4000_0101, graphic: 0x13ff, name: 'a katana' });

let world: FakeWorld;

// A character holding a weapon, on a client that lets it be stowed and drawn again
const armed = (): void => {
  world.player.equippedItems.oneHanded = katana;

  world.player.moveItem.mockImplementation(() => {
    world.player.equippedItems.oneHanded = undefined;
    world.player.backpack = { serial: 0x40000000, contents: [katana] };

    return 1;
  });

  world.player.equip.mockImplementation(() => {
    world.player.equippedItems.oneHanded = katana;
  });
};

const fillsThePool = (): void => {
  world.player.useSkill.mockImplementation(() => {
    world.player.mana = 50;
  });
};

beforeEach(() => {
  world = installGlobals();
  world.player.mana = 0;
  world.player.maxMana = 50;
});

describe('manaTarget', () => {
  it('is the whole pool, so one trance pays for many casts', async () => {
    const { manaTarget } = await freshMeditate();

    expect(manaTarget(10)).toBe(50);
  });

  // The stat-refresh fault. Taken raw, a ceiling of 0 would make every wait end the instant it
  // started, and the run would cast with no mana forever.
  it('never takes a maximum of 0 as the target', async () => {
    const { manaTarget } = await freshMeditate();

    world.player.maxMana = 0;

    expect(manaTarget(10)).toBe(10);
  });
});

describe('regainMana', () => {
  it('does nothing when the pool is already there', async () => {
    const { regainMana } = await freshMeditate();

    world.player.mana = 50;
    armed();

    expect(regainMana(10)).toBe(true);
    expect(world.player.moveItem).not.toHaveBeenCalled();
    expect(world.player.useSkill).not.toHaveBeenCalled();
  });

  // The comparison the original script got wrong. It waited on `mana != maxMana`, and a regenerating
  // pool passes a figure as often as it lands on it - so a pool that overshot never satisfied it.
  it('is satisfied by a pool that overshot the target', async () => {
    const { regainMana } = await freshMeditate();

    world.player.mana = 60;

    expect(regainMana(10)).toBe(true);
    expect(world.player.useSkill).not.toHaveBeenCalled();
  });

  it('does not read a maximum of 0 as a pool that is already full', async () => {
    const { regainMana } = await freshMeditate();

    world.player.maxMana = 0;
    world.player.mana = 5;
    fillsThePool();

    regainMana(10);

    expect(world.player.useSkill).toHaveBeenCalled();
  });

  // Meditation is refused with anything in hand, so the stow is what makes the trance possible at all
  it('stows the weapon before it uses the skill', async () => {
    const { regainMana } = await freshMeditate();

    armed();
    fillsThePool();

    regainMana(10);

    expect(world.player.moveItem).toHaveBeenCalledWith(katana.serial, 0x40000000);
    expect(world.player.useSkill).toHaveBeenCalledWith(Skills.Meditation);
  });

  it('draws the weapon again once the pool is full', async () => {
    const { regainMana, weaponLost } = await freshMeditate();

    armed();
    fillsThePool();

    expect(regainMana(10)).toBe(true);
    expect(world.player.equippedItems.oneHanded).toBe(katana);
    expect(weaponLost()).toBeUndefined();
  });

  // The invariant that matters: every way out of the wait goes past the draw. A character left
  // holding nothing casts into a permanent refusal and cannot defend itself.
  it('draws the weapon again even when the mana never came back', async () => {
    const { regainMana } = await freshMeditate();

    armed();

    expect(regainMana(10)).toBe(false);
    expect(world.player.equippedItems.oneHanded).toBe(katana);
  });

  it('draws the weapon again when a guard ends the wait', async () => {
    const { regainMana } = await freshMeditate();

    armed();
    world.player.isDead = true;

    expect(regainMana(10)).toBe(false);
    expect(world.player.equippedItems.oneHanded).toBe(katana);
  });

  it('reports a weapon it could not get back, which is the one thing that ends the run', async () => {
    const { regainMana, weaponLost } = await freshMeditate();

    armed();
    fillsThePool();
    world.player.equip.mockImplementation(() => undefined);

    regainMana(10);

    expect(weaponLost()).toBeDefined();
  });

  // Using the skill again is at best a wasted action and at worst the shard ending the very trance
  // this attempt is waiting on
  it('does not use the skill again while a trance is already running', async () => {
    const { regainMana } = await freshMeditate();

    armed();
    world.player.hasBuffDebuff.mockReturnValue(true);

    regainMana(10);

    expect(world.player.useSkill).not.toHaveBeenCalled();
  });

  it('gives up rather than hanging when the pool never moves', async () => {
    const { regainMana } = await freshMeditate();

    armed();

    expect(regainMana(10)).toBe(false);
    expect(world.player.useSkill).toHaveBeenCalledTimes(4);
  });

  // The weapon is already stowed by the time this fires, so whatever is refusing the trance is
  // something the run cannot take off - and nothing retried fixes it
  it('stops meditating for the rest of the run once the shard refuses outright', async () => {
    const { regainMana } = await freshMeditate();

    armed();
    world.journal.waitForTextAny.mockReturnValue(
      'You cannot focus your concentration with an equipped shield',
    );

    regainMana(10);
    world.player.moveItem.mockClear();
    regainMana(10);

    expect(world.player.moveItem).not.toHaveBeenCalled();
  });

  // A world save is silent in exactly the way a refusal is, so it must not be read as one
  it('does not give up meditation over a world save', async () => {
    const { regainMana } = await freshMeditate();

    armed();
    world.journal.waitForTextAny.mockReturnValue('The world is saving');

    regainMana(10);
    world.player.moveItem.mockClear();
    regainMana(10);

    expect(world.player.moveItem).toHaveBeenCalled();
  });
});
