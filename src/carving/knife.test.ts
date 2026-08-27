import { beforeEach, describe, expect, it, vi } from 'vitest';

import { type FakeWorld, installGlobals, item } from '../test-support/uo.js';
import { KNIFE_GRAPHICS } from './config.js';

const BUTCHER = 0x13f6;
const SWORD = 0x0f5e;

let world: FakeWorld;

// The tool latches the graphic it learns, so each test gets its own module
const load = () => import('./knife.js');

beforeEach(() => {
  vi.resetModules();
  world = installGlobals();
});

describe('knifeSerial', () => {
  it('finds one in the pack', async () => {
    world = installGlobals({ backpack: [item({ serial: 5, graphic: BUTCHER })] });

    expect((await load()).knifeSerial()).toBe(5);
  });

  it('finds one inside a bag in the pack', async () => {
    world = installGlobals({
      backpack: [
        item({ serial: 4, graphic: 0x0e76, contents: [item({ serial: 5, graphic: BUTCHER })] }),
      ],
    });

    expect((await load()).knifeSerial()).toBe(5);
  });

  it('takes the one already in hand', async () => {
    world = installGlobals({ player: { equippedItems: { oneHanded: item({ serial: 7, graphic: BUTCHER }) } } });

    expect((await load()).knifeSerial()).toBe(7);
  });

  // Tool.serial does not check what the layer holds, and this runs on a character mid-fight
  it('never answers with the weapon in hand', async () => {
    world = installGlobals({
      player: { equippedItems: { oneHanded: item({ serial: 7, graphic: SWORD, name: 'a longsword' }) } },
    });

    expect((await load()).knifeSerial()).toBeUndefined();
  });

  it('is nothing at all when the pack holds none', async () => {
    world = installGlobals({ backpack: [item({ serial: 5, graphic: SWORD })] });

    expect((await load()).knifeSerial()).toBeUndefined();
  });

  it('looks again once the one it was using stops resolving', async () => {
    world = installGlobals({ backpack: [item({ serial: 5, graphic: BUTCHER })] });
    world.client.findObject = vi.fn(() => undefined);

    const { knifeSerial } = await load();

    expect(knifeSerial()).toBe(5);
    expect(knifeSerial()).toBe(5);
    expect(world.player.use).not.toHaveBeenCalled();
  });

  it('matches by name where the client has no graphic this script knows', async () => {
    world = installGlobals({
      backpack: [item({ serial: 5, graphic: 0x1234, name: 'a skinning knife' })],
    });

    expect((await load()).knifeSerial()).toBe(5);
  });

  it('seeds every knife art it ships with', () => {
    expect(KNIFE_GRAPHICS.has(BUTCHER)).toBe(true);
    expect(KNIFE_GRAPHICS.has(SWORD)).toBe(false);
  });
});
