import { beforeEach, describe, expect, it, vi } from 'vitest';

import { installGlobals, item, type FakeWorld } from '../test-support/uo.js';
import { pickItem } from './pick.js';

let world: FakeWorld;

beforeEach(() => {
  world = installGlobals();
});

// The shape the shard answers a click with, copper key included: query() carries the serial, and
// nothing else on `target` moves
const clicks = (serial: number) =>
  vi.fn(() => ({ serial, graphic: 0x100e, x: 115, y: 67, z: 0, hue: 0 }));

const tooltip = (name: string) => vi.fn(() => ({ serial: 0x41785ff6, name, graphic: 0x100e }));

describe('pickItem', () => {
  it('names the targeted item from its tooltip', () => {
    world.target.query = clicks(0x41785ff6);
    world.client.queryItemOPL = tooltip('Copper Key');

    expect(pickItem()).toEqual({ serial: 0x41785ff6, name: 'Copper Key' });
  });

  // Re-running against the same item is the normal case, not a cancelled cursor. Reading the serial
  // off anything that persists between runs got this wrong the first time it was tried on the shard
  it('picks the same item twice in a row', () => {
    world.target.query = clicks(0x41785ff6);
    world.client.queryItemOPL = tooltip('Copper Key');

    expect(pickItem()).toEqual(pickItem());
  });

  it('falls back to the object when no tooltip arrives', () => {
    world.target.query = clicks(0x401);
    world.client.findObject = vi.fn(() => item({ serial: 0x401, graphic: 0x9a9, name: 'wooden box' }));

    expect(pickItem()).toEqual({ serial: 0x401, name: 'wooden box' });
  });

  // A tooltip that arrives without a name is the same situation as no tooltip at all
  it('falls back when the tooltip has a blank name', () => {
    world.target.query = clicks(0x401);
    world.client.queryItemOPL = tooltip('   ');
    world.client.findObject = vi.fn(() => item({ serial: 0x401, graphic: 0x9a9, name: 'wooden box' }));

    expect(pickItem()?.name).toBe('wooden box');
  });

  it('gives up when the cursor is cancelled', () => {
    world.client.queryItemOPL = tooltip('Copper Key');

    expect(pickItem()).toBeUndefined();
    expect(world.log).toHaveBeenCalledWith(expect.stringContaining('nothing targeted'), undefined);
  });

  // Ground and terrain clicks come back without a serial, and there is no item to sell behind those
  it('gives up when the click carries no serial', () => {
    world.target.query = vi.fn(() => ({ graphic: 0x3, x: 115, y: 67, z: 0 }));

    expect(pickItem()).toBeUndefined();
  });

  // Without a name there is nothing to match the vendor's list against, so this cannot be guessed at
  it('gives up when the item has no name', () => {
    world.target.query = clicks(0x401);

    expect(pickItem()).toBeUndefined();
    expect(world.log).toHaveBeenCalledWith(expect.stringContaining('no name for 0x401'));
  });
});
