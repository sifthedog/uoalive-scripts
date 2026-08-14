import { beforeEach, describe, expect, it, vi } from 'vitest';

import { installGlobals, item, type FakeWorld } from '../test-support/uo.js';
import { EQUIP_ATTEMPTS } from './config.js';

const PICKAXE = 0x0e86;
const BAG = 0x0e76;

let world: FakeWorld;

// pickaxe.ts remembers the graphic it learned, the bag it came from, and whether it has already
// complained about an empty pack, so each test needs a fresh copy of the module.
const loadPickaxe = async () => import('./pickaxe.js');

const pickaxe = (serial: number, extra: Partial<Item> = {}) =>
  item({ serial, graphic: PICKAXE, name: 'a pickaxe', ...extra });

// An equip that lands: the item shows up on the hand layer once player.equip is called
const equipWorks = () => {
  world.player.equip.mockImplementation((serial: number) => {
    world.player.equippedItems.oneHanded = item({ serial, graphic: PICKAXE, name: 'a pickaxe' });
  });
};

beforeEach(() => {
  vi.resetModules();
  world = installGlobals({
    client: { findObject: vi.fn((serial: number) => pickaxe(serial)) } as never,
  });
});

describe('isPickaxe', () => {
  it('matches by name', async () => {
    const { isPickaxe } = await loadPickaxe();

    expect(isPickaxe(pickaxe(1))).toBe(true);
  });

  it('is case-insensitive about the name', async () => {
    const { isPickaxe } = await loadPickaxe();

    expect(isPickaxe(item({ serial: 1, graphic: PICKAXE, name: 'A PICKAXE' }))).toBe(true);
  });

  it('rejects an item that is neither named nor known', async () => {
    const { isPickaxe } = await loadPickaxe();

    expect(isPickaxe(item({ serial: 1, graphic: 0x1234, name: 'a shovel' }))).toBe(false);
  });

  // Names are empty until the client has tooltip data, which is the normal case in a pack, so the
  // graphic is what carries the match once one has been seen
  it('matches by graphic once one has been seen, even with no name', async () => {
    const { isPickaxe, rememberPickaxe } = await loadPickaxe();

    expect(isPickaxe(item({ serial: 1, graphic: PICKAXE, name: '' }))).toBe(false);

    rememberPickaxe(pickaxe(1));

    expect(isPickaxe(item({ serial: 2, graphic: PICKAXE, name: '' }))).toBe(true);
  });

  it('keeps the first graphic it learned', async () => {
    const { isPickaxe, rememberPickaxe } = await loadPickaxe();

    rememberPickaxe(pickaxe(1));
    rememberPickaxe(item({ serial: 2, graphic: 0x9999, name: 'a pickaxe' }));

    expect(isPickaxe(item({ serial: 3, graphic: 0x9999, name: '' }))).toBe(false);
  });

  it('ignores being handed nothing', async () => {
    const { isPickaxe, rememberPickaxe } = await loadPickaxe();

    rememberPickaxe(undefined);

    expect(isPickaxe(item({ serial: 1, graphic: PICKAXE, name: '' }))).toBe(false);
  });
});

describe('equipPickaxe', () => {
  it('keeps a pickaxe that is already in hand', async () => {
    world.player.equippedItems.oneHanded = pickaxe(1);
    const { equipPickaxe } = await loadPickaxe();

    expect(equipPickaxe()).toBe(true);
    expect(world.player.equip).not.toHaveBeenCalled();
  });

  // A broken pickaxe can linger in equippedItems and would match by graphic. A destroyed serial
  // stops resolving, so the world is asked rather than the layer.
  it('replaces a held pickaxe whose serial no longer resolves', async () => {
    world.player.equippedItems.oneHanded = pickaxe(1);
    world.client.findObject.mockImplementation((serial: number) =>
      serial === 1 ? undefined : pickaxe(serial),
    );
    world = installGlobals({
      client: world.client as never,
      player: world.player as never,
      backpack: [pickaxe(2)],
    });
    equipWorks();
    const { equipPickaxe } = await loadPickaxe();

    expect(equipPickaxe()).toBe(true);
    expect(world.player.equip).toHaveBeenCalledWith(2);
  });

  it('equips a spare out of the pack', async () => {
    world = installGlobals({
      client: { findObject: vi.fn((serial: number) => pickaxe(serial)) } as never,
      backpack: [pickaxe(2)],
    });
    equipWorks();
    const { equipPickaxe } = await loadPickaxe();

    expect(equipPickaxe()).toBe(true);
    expect(world.player.equip).toHaveBeenCalledWith(2);
  });

  it('finds a spare inside a bag', async () => {
    world = installGlobals({
      client: { findObject: vi.fn((serial: number) => pickaxe(serial)) } as never,
      backpack: [item({ serial: 9, graphic: BAG, contents: [pickaxe(2)] })],
    });
    equipWorks();
    const { equipPickaxe } = await loadPickaxe();

    expect(equipPickaxe()).toBe(true);
    expect(world.player.equip).toHaveBeenCalledWith(2);
  });

  it('says so when the pack holds no pickaxe', async () => {
    installGlobals({ backpack: [item({ serial: 1, graphic: 0x1234 })] });
    const { equipPickaxe } = await loadPickaxe();

    expect(equipPickaxe()).toBe(false);
  });

  it('shows the graphics it did see, so a missed pickaxe can be diagnosed', async () => {
    world = installGlobals({ backpack: [item({ serial: 1, graphic: 0x1234 })] });
    const { equipPickaxe } = await loadPickaxe();

    equipPickaxe();

    expect(world.client.headMsg).toHaveBeenCalledWith('No pickaxe!', expect.anything(), 33);
    expect(world.log).toHaveBeenCalledWith(expect.stringContaining('0x1234'));
  });

  it('complains about an empty pack only once', async () => {
    world = installGlobals({ backpack: [item({ serial: 1, graphic: 0x1234 })] });
    const { equipPickaxe } = await loadPickaxe();

    equipPickaxe();
    equipPickaxe();

    expect(world.log.mock.calls.filter(([line]) => String(line).includes('none found'))).toHaveLength(1);
  });

  // A container's contents stay undefined until it has been opened, which is why the containers
  // are opened before concluding there is no spare
  it('opens containers before giving up', async () => {
    world = installGlobals({ backpack: [item({ serial: 9, graphic: BAG })] });
    const { equipPickaxe } = await loadPickaxe();

    equipPickaxe();

    expect(world.player.use).toHaveBeenCalledWith(9);
  });

  // A cursor left open by the swing that broke the pickaxe would swallow the equip
  it('cancels a leftover target cursor before equipping', async () => {
    world = installGlobals({
      client: { findObject: vi.fn((serial: number) => pickaxe(serial)) } as never,
      backpack: [pickaxe(2)],
    });
    equipWorks();
    const { equipPickaxe } = await loadPickaxe();

    equipPickaxe();

    expect(world.target.cancel).toHaveBeenCalled();
  });

  // equip is asynchronous, so the swing must not start until it has landed on the hand layer
  it('reissues the equip when it does not land', async () => {
    world = installGlobals({
      client: { findObject: vi.fn((serial: number) => pickaxe(serial)) } as never,
      backpack: [pickaxe(2)],
    });
    const { equipPickaxe } = await loadPickaxe();

    expect(equipPickaxe()).toBe(false);
    expect(world.player.equip).toHaveBeenCalledTimes(EQUIP_ATTEMPTS);
    expect(world.log).toHaveBeenCalledWith(expect.stringContaining('equip pickaxe: gave up'));
  });

  it('remembers the bag a spare came from', async () => {
    world = installGlobals({
      client: { findObject: vi.fn((serial: number) => pickaxe(serial)) } as never,
      backpack: [item({ serial: 9, graphic: BAG, contents: [pickaxe(2, { container: 9 })] })],
    });
    equipWorks();
    const { equipPickaxe } = await loadPickaxe();

    equipPickaxe();

    // The next break should reopen only that bag rather than every container in the pack
    world.player.equippedItems.oneHanded = undefined;
    world.player.backpack = { serial: 0x40000000, contents: [] };
    world.player.use.mockClear();

    equipPickaxe();

    expect(world.player.use.mock.calls).toEqual([[9]]);
  });
});
