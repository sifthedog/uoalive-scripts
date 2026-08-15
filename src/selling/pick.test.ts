import { beforeEach, describe, expect, it, vi } from 'vitest';

import { installGlobals, type FakeWorld } from '../test-support/uo.js';
import { pickItem } from './pick.js';

let world: FakeWorld;

beforeEach(() => {
  world = installGlobals();
});

describe('pickItem', () => {
  it('reads the serial off the query and names it from the tooltip', () => {
    world.target.query = vi.fn(() => ({ serial: 0x4011, graphic: 0x13b6 }));
    world.client.queryItemOPL = vi.fn(() => ({ serial: 0x4011, name: 'Scimitar' }));

    expect(pickItem()).toEqual({ serial: 0x4011, name: 'Scimitar', graphic: 0x13b6 });
  });

  it('falls back to the object when the tooltip has nothing', () => {
    world.target.query = vi.fn(() => ({ serial: 0x4011 }));
    world.client.findObject = vi.fn(() => ({ serial: 0x4011, name: 'Scimitar' }));

    expect(pickItem()?.name).toBe('Scimitar');
  });

  // sell-watch counts the pack by art, so the graphic has to survive the pick
  it('falls back to the object for a graphic the query did not carry', () => {
    world.target.query = vi.fn(() => ({ serial: 0x4011 }));
    world.client.findObject = vi.fn(() => ({ serial: 0x4011, name: 'Scimitar', graphic: 0x13b6 }));

    expect(pickItem()?.graphic).toBe(0x13b6);
  });

  // Zero matches nothing, which is the safe direction for a counter that decides when to sell -
  // the alternative, undefined, would match every item the pack holds no art for
  it('answers zero when nothing knows the graphic', () => {
    world.target.query = vi.fn(() => ({ serial: 0x4011 }));
    world.client.queryItemOPL = vi.fn(() => ({ serial: 0x4011, name: 'Scimitar' }));

    expect(pickItem()?.graphic).toBe(0);
  });

  // Every other targeting site in the repo brackets itself this way. A cursor left open by whatever
  // ran last would swallow the query, and the hoist that follows is all double-clicks - a live
  // cursor would spend those as target clicks instead.
  it('clears any leftover cursor before opening its own', () => {
    world.target.query = vi.fn(() => ({ serial: 0x4011 }));
    world.client.queryItemOPL = vi.fn(() => ({ serial: 0x4011, name: 'Scimitar' }));

    pickItem();

    expect(world.target.cancel).toHaveBeenCalled();
    expect(world.target.cancel.mock.invocationCallOrder[0]).toBeLessThan(
      world.target.query.mock.invocationCallOrder[0],
    );
  });

  it('cancels the cursor again when nothing was targeted', () => {
    world.target.query = vi.fn(() => undefined);

    expect(pickItem()).toBeUndefined();
    expect(world.target.cancel).toHaveBeenCalledTimes(2);
    expect(world.log).toHaveBeenCalledWith('sell: nothing targeted', undefined);
  });

  // The vendor list is matched by name, so a serial without one is no use
  it('gives up on an item nothing will name', () => {
    world.target.query = vi.fn(() => ({ serial: 0x4011 }));

    expect(pickItem()).toBeUndefined();
    expect(world.log).toHaveBeenCalledWith(expect.stringContaining('no name for'));
  });
});
