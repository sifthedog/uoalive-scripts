import { beforeEach, describe, expect, it, vi } from 'vitest';
import { installGlobals, item, type FakeWorld } from '../test-support/uo.js';

// The module keeps a learned graphic between calls, so every test gets a fresh copy of it
const freshWeapon = async () => {
  vi.resetModules();

  return import('./weapon.js');
};

const katana = item({ serial: 0x4000_0101, graphic: 0x13ff, name: 'a katana' });

let world: FakeWorld;

beforeEach(() => {
  world = installGlobals();
});

describe('disarm', () => {
  it('moves what is in hand into the backpack', async () => {
    const { disarm } = await freshWeapon();

    world.player.equippedItems.oneHanded = katana;
    world.player.moveItem.mockImplementation(() => {
      world.player.equippedItems.oneHanded = undefined;

      return 1;
    });

    expect(disarm()).toBe(true);
    expect(world.player.moveItem).toHaveBeenCalledWith(katana.serial, 0x40000000);
  });

  // A no-dachi is two-handed and a katana one-handed, and both train the same abilities
  it('stows a two-handed weapon in preference to a one-handed one', async () => {
    const { disarm } = await freshWeapon();

    const noDachi = item({ serial: 0x4000_0202, graphic: 0x27a2, name: 'a no-dachi' });
    world.player.equippedItems.twoHanded = noDachi;
    world.player.equippedItems.oneHanded = katana;
    world.player.moveItem.mockImplementation(() => {
      world.player.equippedItems.twoHanded = undefined;

      return 1;
    });

    disarm();

    expect(world.player.moveItem).toHaveBeenCalledWith(noDachi.serial, 0x40000000);
  });

  it('does nothing and succeeds with empty hands', async () => {
    const { disarm } = await freshWeapon();

    expect(disarm()).toBe(true);
    expect(world.player.moveItem).not.toHaveBeenCalled();
  });

  // Answered rather than thrown: the caller falls back on natural regeneration with the weapon still
  // in hand, which is slower and always available
  it('gives up when the client reports no backpack', async () => {
    const { disarm } = await freshWeapon();

    world.player.equippedItems.oneHanded = katana;
    world.player.backpack = undefined;

    expect(disarm()).toBe(false);
    expect(world.player.moveItem).not.toHaveBeenCalled();
  });

  it('gives up when the weapon never leaves the hand', async () => {
    const { disarm } = await freshWeapon();

    world.player.equippedItems.oneHanded = katana;

    expect(disarm()).toBe(false);
  });
});

describe('rearm', () => {
  it('does nothing when the weapon is already held', async () => {
    const { rearm, rememberWeapon } = await freshWeapon();

    rememberWeapon(katana);
    world.player.equippedItems.oneHanded = katana;
    world.client.findObject.mockReturnValue(katana);

    expect(rearm()).toBe(true);
    expect(world.player.equip).not.toHaveBeenCalled();
  });

  // The graphic learned at start-up is what matches, so the draw finds the weapon actually being
  // trained with rather than whatever WEAPON_NAME happens to turn up
  it('finds the stowed weapon by the graphic it learned', async () => {
    const { disarm, rearm } = await freshWeapon();

    world.player.equippedItems.oneHanded = katana;
    world.player.moveItem.mockImplementation(() => {
      world.player.equippedItems.oneHanded = undefined;
      world.player.backpack = { serial: 0x40000000, contents: [katana] };

      return 1;
    });
    world.player.equip.mockImplementation(() => {
      world.player.equippedItems.oneHanded = katana;
    });

    disarm();

    expect(rearm()).toBe(true);
    expect(world.player.equip).toHaveBeenCalledWith(katana.serial);
  });

  it('gives up when nothing matching is in the pack', async () => {
    const { rearm } = await freshWeapon();

    expect(rearm()).toBe(false);
  });
});
