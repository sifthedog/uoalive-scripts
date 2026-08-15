import { beforeEach, describe, expect, it } from 'vitest';
import { installGlobals, item, type FakeWorld } from '../test-support/uo.js';
import { createWeapon, type Weapon } from './weapon.js';

const katana = item({ serial: 0x4000_0101, graphic: 0x13ff, name: 'a katana' });

let world: FakeWorld;

// A fresh one per test, which is what the factory is for: it latches the graphic it learned, and two
// scripts in one process must not share that
const weapon = (): Weapon =>
  createWeapon({
    prefix: 'train',
    name: 'katana',
    equip: { attempts: 3, timeoutMs: 2000, pollMs: 200 },
    disarm: { attempts: 3, timeoutMs: 2000, pollMs: 200 },
  });

beforeEach(() => {
  world = installGlobals();
});

describe('disarm', () => {
  it('moves what is in hand into the backpack', () => {
    world.player.equippedItems.oneHanded = katana;
    world.player.moveItem.mockImplementation(() => {
      world.player.equippedItems.oneHanded = undefined;

      return 1;
    });

    expect(weapon().disarm()).toBe(true);
    expect(world.player.moveItem).toHaveBeenCalledWith(katana.serial, 0x40000000);
  });

  // A no-dachi is two-handed and a katana one-handed, and both train the same abilities
  it('stows a two-handed weapon in preference to a one-handed one', () => {
    const noDachi = item({ serial: 0x4000_0202, graphic: 0x27a2, name: 'a no-dachi' });
    world.player.equippedItems.twoHanded = noDachi;
    world.player.equippedItems.oneHanded = katana;
    world.player.moveItem.mockImplementation(() => {
      world.player.equippedItems.twoHanded = undefined;

      return 1;
    });

    weapon().disarm();

    expect(world.player.moveItem).toHaveBeenCalledWith(noDachi.serial, 0x40000000);
  });

  it('does nothing and succeeds with empty hands', () => {
    expect(weapon().disarm()).toBe(true);
    expect(world.player.moveItem).not.toHaveBeenCalled();
  });

  // Answered rather than thrown: the caller falls back on natural regeneration with the weapon still
  // in hand, which is slower and always available
  it('gives up when the client reports no backpack', () => {
    world.player.equippedItems.oneHanded = katana;
    world.player.backpack = undefined;

    expect(weapon().disarm()).toBe(false);
    expect(world.player.moveItem).not.toHaveBeenCalled();
  });

  it('gives up when the weapon never leaves the hand', () => {
    world.player.equippedItems.oneHanded = katana;

    expect(weapon().disarm()).toBe(false);
  });
});

describe('rearm', () => {
  it('does nothing when the weapon is already held', () => {
    const armed = weapon();

    armed.remember(katana);
    world.player.equippedItems.oneHanded = katana;
    world.client.findObject.mockReturnValue(katana);

    expect(armed.rearm()).toBe(true);
    expect(world.player.equip).not.toHaveBeenCalled();
  });

  // The graphic learned at start-up is what matches, so the draw finds the weapon actually being
  // trained with rather than whatever the configured name happens to turn up
  it('finds the stowed weapon by the graphic it learned', () => {
    const armed = weapon();

    world.player.equippedItems.oneHanded = katana;
    world.player.moveItem.mockImplementation(() => {
      world.player.equippedItems.oneHanded = undefined;
      world.player.backpack = { serial: 0x40000000, contents: [katana] };

      return 1;
    });
    world.player.equip.mockImplementation(() => {
      world.player.equippedItems.oneHanded = katana;
    });

    armed.disarm();

    expect(armed.rearm()).toBe(true);
    expect(world.player.equip).toHaveBeenCalledWith(katana.serial);
  });

  it('gives up when nothing matching is in the pack', () => {
    expect(weapon().rearm()).toBe(false);
  });
});

describe('held', () => {
  it('is what a script with nothing in hand sees, which is nothing', () => {
    expect(weapon().held()).toBeUndefined();
  });
});
