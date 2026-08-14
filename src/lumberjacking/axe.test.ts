import { beforeEach, describe, expect, it, vi } from 'vitest';

import { installGlobals, item, type FakeWorld } from '../test-support/uo.js';
import { EQUIP_ATTEMPTS } from './config.js';

const AXE = 0x0f47;
const HATCHET = 0x0f43;

let world: FakeWorld;

const loadAxe = async () => import('./axe.js');

const axe = (serial: number, extra: Partial<Item> = {}) =>
  item({ serial, graphic: AXE, name: 'a hatchet axe', ...extra });

const equipWorks = (layer: 'oneHanded' | 'twoHanded' = 'twoHanded') => {
  world.player.equip.mockImplementation((serial: number) => {
    world.player.equippedItems[layer] = axe(serial);
  });
};

beforeEach(() => {
  vi.resetModules();
  world = installGlobals({
    client: { findObject: vi.fn((serial: number) => axe(serial)) } as never,
  });
});

describe('isAxe', () => {
  it('matches by name', async () => {
    const { isAxe } = await loadAxe();

    expect(isAxe(item({ serial: 1, graphic: AXE, name: 'a large battle axe' }))).toBe(true);
  });

  it('rejects an unrelated item', async () => {
    const { isAxe } = await loadAxe();

    expect(isAxe(item({ serial: 1, graphic: 0x1234, name: 'a dagger' }))).toBe(false);
  });

  it('matches by graphic once one has been seen, even with no name', async () => {
    const { isAxe, rememberAxe } = await loadAxe();

    expect(isAxe(item({ serial: 1, graphic: AXE, name: '' }))).toBe(false);

    rememberAxe(axe(1));

    expect(isAxe(item({ serial: 2, graphic: AXE, name: '' }))).toBe(true);
  });
});

describe('axeSerial', () => {
  // Axes are two-handed and hatchets are one-handed, so both layers have to be read - unlike
  // mining, which only ever holds a pickaxe one-handed
  it('finds a two-handed axe', async () => {
    world.player.equippedItems.twoHanded = axe(1);
    const { axeSerial } = await loadAxe();

    expect(axeSerial()).toBe(1);
  });

  it('finds a one-handed hatchet', async () => {
    world.player.equippedItems.oneHanded = item({ serial: 2, graphic: HATCHET, name: 'a hatchet' });
    const { axeSerial } = await loadAxe();

    expect(axeSerial()).toBe(2);
  });

  it('prefers the two-handed layer when both are filled', async () => {
    world.player.equippedItems.twoHanded = axe(1);
    world.player.equippedItems.oneHanded = axe(2);
    const { axeSerial } = await loadAxe();

    expect(axeSerial()).toBe(1);
  });

  it('finds nothing with empty hands', async () => {
    const { axeSerial } = await loadAxe();

    expect(axeSerial()).toBeUndefined();
  });
});

describe('equipAxe', () => {
  it('keeps an axe that is already in hand', async () => {
    world.player.equippedItems.twoHanded = axe(1);
    const { equipAxe } = await loadAxe();

    expect(equipAxe()).toBe(true);
    expect(world.player.equip).not.toHaveBeenCalled();
  });

  // A broken axe can linger on the layer and would match by graphic; a destroyed serial stops
  // resolving, so the world is asked rather than the layer
  it('replaces a held axe whose serial no longer resolves', async () => {
    world = installGlobals({
      client: {
        findObject: vi.fn((serial: number) => (serial === 1 ? undefined : axe(serial))),
      } as never,
      backpack: [axe(2)],
    });
    world.player.equippedItems.twoHanded = axe(1);
    equipWorks();
    const { equipAxe } = await loadAxe();

    expect(equipAxe()).toBe(true);
    expect(world.player.equip).toHaveBeenCalledWith(2);
  });

  it('equips a spare out of the pack', async () => {
    world = installGlobals({
      client: { findObject: vi.fn((serial: number) => axe(serial)) } as never,
      backpack: [axe(2)],
    });
    equipWorks();
    const { equipAxe } = await loadAxe();

    expect(equipAxe()).toBe(true);
    expect(world.player.equip).toHaveBeenCalledWith(2);
  });

  it('accepts a hatchet landing on the one-handed layer', async () => {
    world = installGlobals({
      client: { findObject: vi.fn((serial: number) => axe(serial)) } as never,
      backpack: [axe(2)],
    });
    equipWorks('oneHanded');
    const { equipAxe } = await loadAxe();

    expect(equipAxe()).toBe(true);
  });

  it('opens containers before giving up', async () => {
    world = installGlobals({ backpack: [item({ serial: 9, graphic: 0x0e76 })] });
    const { equipAxe } = await loadAxe();

    expect(equipAxe()).toBe(false);
    expect(world.player.use).toHaveBeenCalledWith(9);
  });

  it('reissues the equip when it does not land', async () => {
    world = installGlobals({
      client: { findObject: vi.fn((serial: number) => axe(serial)) } as never,
      backpack: [axe(2)],
    });
    const { equipAxe } = await loadAxe();

    expect(equipAxe()).toBe(false);
    expect(world.player.equip).toHaveBeenCalledTimes(EQUIP_ATTEMPTS);
  });

  it('shows the graphics it did see when there is no axe', async () => {
    world = installGlobals({ backpack: [item({ serial: 1, graphic: 0x1234 })] });
    const { equipAxe } = await loadAxe();

    equipAxe();

    expect(world.log).toHaveBeenCalledWith(expect.stringContaining('0x1234'));
  });
});
