import { beforeEach, describe, expect, it, vi } from 'vitest';

import { installGlobals, item, type FakeWorld } from '../test-support/uo.js';

const KEY = 0x100e;
const BOX = 0x40000007;

let world: FakeWorld;

// drop.ts latches the method it proves, so every test takes a fresh module. DROP_METHOD is pinned
// to the proven call in the checked-in config, so the candidate-by-candidate path only exists under
// 'auto' and has to be mocked in - a config read at module scope cannot be assigned over.
const fresh = async (DROP_METHOD = 'auto') => {
  vi.resetModules();
  // A single tile, so the spread does not shift the offsets these assertions name
  vi.doMock('./config.js', () => ({
    DROP_METHOD,
    DROP_SPREAD: [{ x: 0, y: 0, z: 0 }],
    DROP_TIMEOUT: 600,
    DROP_POLL: 200,
  }));
  return import('./drop.js');
};

// The item is only ever looked up to see whether it left the box, so a test says where it is now
const livingAt = (container: number | undefined) =>
  vi.fn(() => (container === undefined ? undefined : item({ serial: 8, graphic: KEY, container })));

beforeEach(() => {
  vi.resetModules();
  vi.doUnmock('./config.js');
  world = installGlobals();
});

describe('dropToGround', () => {
  // The checked-in config pins what the probe proved on the shard, so no candidates are tried
  it('uses the pinned method without hunting for one', async () => {
    world.client.findObject = livingAt(0);

    const { dropToGround, dropMethod } = await fresh('groundOffset');

    expect(dropToGround(item({ serial: 8, graphic: KEY }), BOX)).toBe(true);
    expect(dropMethod()).toBe('groundOffset');
    expect(world.player.moveItem).not.toHaveBeenCalled();
  });

  // The bug that put keys in the main backpack: the drop had landed, the container was read back
  // before the client caught up, and the recovery picked the key off the floor again. Polling is
  // what fixes it, so a container that only changes on a later look still counts as a drop.
  it('waits for a drop that takes a moment to land', async () => {
    let looks = 0;
    world.client.findObject = vi.fn(() =>
      item({ serial: 8, graphic: KEY, container: looks++ < 2 ? BOX : 0xffffffff }),
    );

    const { dropToGround } = await fresh('groundOffset');

    expect(dropToGround(item({ serial: 8, graphic: KEY }), BOX)).toBe(true);
  });

  it('keeps the first call that moves the item', async () => {
    world.client.findObject = livingAt(0);

    const { dropToGround, dropMethod } = await fresh();

    expect(dropToGround(item({ serial: 8, graphic: KEY }), BOX)).toBe(true);
    expect(world.player.moveItemOnGroundOffset).toHaveBeenCalledWith(8, 0, 0, 0);
    expect(dropMethod()).toBe('groundOffset');
  });

  // The documented call is tried first and silently does nothing, so the run has to notice that
  // the key never left the box and go on to the next candidate rather than reporting success
  it('moves on to the next call when the item has not budged', async () => {
    world.client.findObject = livingAt(BOX);

    const { dropToGround, dropMethod } = await fresh();

    expect(dropToGround(item({ serial: 8, graphic: KEY }), BOX)).toBe(false);
    expect(world.player.moveItemOnGroundOffset).toHaveBeenCalledWith(8, 0, 0, 0);
    expect(world.player.moveItemOnGroundOffset).toHaveBeenCalledWith(8, 1, 0, 0);
    expect(world.player.moveItem).toHaveBeenCalledWith(8, 0xffffffff, 100, 100, 0);
    expect(dropMethod()).toBeUndefined();
  });

  it('settles on the protocol drop when only that one works', async () => {
    let dropped = false;
    world.player.moveItem = vi.fn(() => {
      dropped = true;
    });
    world.client.findObject = vi.fn(() =>
      item({ serial: 8, graphic: KEY, container: dropped ? 0 : BOX }),
    );

    const { dropToGround, dropMethod } = await fresh();

    expect(dropToGround(item({ serial: 8, graphic: KEY }), BOX)).toBe(true);
    expect(dropMethod()).toBe('worldSerial');
  });

  // An item the client can no longer resolve is off the character, which is what a drop looks like
  // on a shard that stops tracking it once it is on the floor
  it('reads an item that no longer resolves as dropped', async () => {
    world.client.findObject = livingAt(undefined);

    const { dropToGround } = await fresh();

    expect(dropToGround(item({ serial: 8, graphic: KEY }), BOX)).toBe(true);
  });

  it('uses the proven call on its own for every later key', async () => {
    world.client.findObject = livingAt(0);

    const { dropToGround } = await fresh();
    dropToGround(item({ serial: 8, graphic: KEY }), BOX);
    world.player.moveItemOnGroundOffset = vi.fn();

    dropToGround(item({ serial: 9, graphic: KEY }), BOX);

    expect(world.player.moveItemOnGroundOffset).toHaveBeenCalledTimes(1);
    expect(world.player.moveItemOnGroundOffset).toHaveBeenCalledWith(9, 0, 0, 0);
  });

  // Once nothing has worked there is no point paying three failed calls per key for the rest of
  // a hundred-box run
  it('stops trying once every call has failed', async () => {
    world.client.findObject = livingAt(BOX);

    const { dropToGround } = await fresh();
    dropToGround(item({ serial: 8, graphic: KEY }), BOX);
    world.player.moveItemOnGroundOffset = vi.fn();
    world.player.moveItem = vi.fn();

    expect(dropToGround(item({ serial: 9, graphic: KEY }), BOX)).toBe(false);
    expect(world.player.moveItemOnGroundOffset).not.toHaveBeenCalled();
    expect(world.player.moveItem).not.toHaveBeenCalled();
  });

  it('says so when nothing would put a key on the floor', async () => {
    world.client.findObject = livingAt(BOX);

    const { dropToGround } = await fresh();
    dropToGround(item({ serial: 8, graphic: KEY }), BOX);

    expect(world.log).toHaveBeenCalledWith(expect.stringContaining('would put a key on the floor'));
  });
});
