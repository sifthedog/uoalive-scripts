import { beforeEach, describe, expect, it, vi } from 'vitest';

import { installGlobals, type FakeWorld } from '../test-support/uo.js';
import { MAX_PICKS } from './config.js';
import { pickItems } from './pick.js';

let world: FakeWorld;

beforeEach(() => {
  world = installGlobals();
});

// The cursor answers each click in turn and then, for everything after them, nothing - which is
// what the client does when ESC is pressed, and the only sign it gives that it was
const clicks = (...answers: (object | undefined)[]) => {
  let click = 0;

  return vi.fn(() => answers[click++]);
};

const named = (names: Record<number, string>) =>
  vi.fn((serial: number) => ({ serial, name: names[serial] }));

describe('pickItems', () => {
  it('reads the serial off the query and names it from the tooltip', () => {
    world.target.query = clicks({ serial: 0x4011, graphic: 0x13b6 });
    world.client.queryItemOPL = named({ 0x4011: 'Scimitar' });

    expect(pickItems('sell')).toEqual([{ serial: 0x4011, name: 'Scimitar', graphic: 0x13b6 }]);
  });

  it('falls back to the object when the tooltip has nothing', () => {
    world.target.query = clicks({ serial: 0x4011 });
    world.client.findObject = vi.fn(() => ({ serial: 0x4011, name: 'Scimitar' }));

    expect(pickItems('sell')[0]?.name).toBe('Scimitar');
  });

  // sell-watch counts the pack by art, so the graphic has to survive the pick
  it('falls back to the object for a graphic the query did not carry', () => {
    world.target.query = clicks({ serial: 0x4011 });
    world.client.findObject = vi.fn(() => ({ serial: 0x4011, name: 'Scimitar', graphic: 0x13b6 }));

    expect(pickItems('sell')[0]?.graphic).toBe(0x13b6);
  });

  // Zero matches nothing, which is the safe direction for a counter that decides when to sell -
  // the alternative, undefined, would match every item the pack holds no art for
  it('answers zero when nothing knows the graphic', () => {
    world.target.query = clicks({ serial: 0x4011 });
    world.client.queryItemOPL = named({ 0x4011: 'Scimitar' });

    expect(pickItems('sell')[0]?.graphic).toBe(0);
  });

  it('keeps asking until the cursor is cancelled', () => {
    world.target.query = clicks({ serial: 1, graphic: 0x1bf2 }, { serial: 2, graphic: 0x13b6 });
    world.client.queryItemOPL = named({ 1: 'iron ingot', 2: 'Scimitar' });

    expect(pickItems('sell').map((item) => item.name)).toEqual(['iron ingot', 'Scimitar']);
    expect(world.target.query).toHaveBeenCalledTimes(3);
  });

  // ESC on the first cursor. The callers treat an empty list as nothing to do rather than a fault.
  it('comes back empty when the first pick is cancelled', () => {
    expect(pickItems('sell')).toEqual([]);
    expect(world.log).toHaveBeenCalledWith('sell: nothing targeted', undefined);
  });

  // The trap a `while (pickItem())` loop falls into: an un-hovered item has no name yet, and ending
  // the whole selection over one is not what clicking it meant
  it('skips an item nothing will name and carries on asking', () => {
    world.target.query = clicks({ serial: 1 }, { serial: 2, graphic: 0x13b6 });
    world.client.queryItemOPL = named({ 2: 'Scimitar' });

    expect(pickItems('sell').map((item) => item.name)).toEqual(['Scimitar']);
    expect(world.log).toHaveBeenCalledWith(expect.stringContaining('no name for'));
  });

  // The sale matches by name, so the same name twice would be trimmed to KEEP twice over
  it('takes a name once however many stacks of it are clicked', () => {
    world.target.query = clicks({ serial: 1, graphic: 0x1bf2 }, { serial: 2, graphic: 0x1bf2 });
    world.client.queryItemOPL = named({ 1: 'iron ingot', 2: 'Iron Ingot' });

    expect(pickItems('sell')).toEqual([{ serial: 1, name: 'iron ingot', graphic: 0x1bf2 }]);
    expect(world.log).toHaveBeenCalledWith(expect.stringContaining('already on the list'));
  });

  // Every other targeting site in the repo brackets itself this way. A cursor left open by whatever
  // ran last would swallow the query, and what follows a selection is double-clicks and gumps - a
  // live cursor would spend those as target clicks instead.
  it('clears any leftover cursor before opening its own', () => {
    world.target.query = clicks({ serial: 0x4011, graphic: 0x13b6 });
    world.client.queryItemOPL = named({ 0x4011: 'Scimitar' });

    pickItems('sell');

    expect(world.target.cancel.mock.invocationCallOrder[0]).toBeLessThan(
      world.target.query.mock.invocationCallOrder[0],
    );
  });

  it('cancels the cursor again when the selection ends', () => {
    world.target.query = clicks({ serial: 1, graphic: 0x1bf2 });
    world.client.queryItemOPL = named({ 1: 'iron ingot' });

    pickItems('sell');

    // One before each of the two queries, and one more for the cursor the cancelled query left up
    expect(world.target.cancel).toHaveBeenCalledTimes(3);
  });

  // A backstop, not the way the selection is meant to end: a client that answered every query would
  // otherwise keep this loop asking forever
  it('stops asking after MAX_PICKS clicks', () => {
    let serial = 0;

    world.target.query = vi.fn(() => ({ serial: ++serial, graphic: 0x1bf2 }));
    world.client.queryItemOPL = vi.fn((asked: number) => ({ serial: asked, name: `item ${asked}` }));

    expect(pickItems('sell')).toHaveLength(MAX_PICKS);
    expect(world.target.query).toHaveBeenCalledTimes(MAX_PICKS);
    expect(world.log).toHaveBeenCalledWith(expect.stringContaining('as many as one run takes'));
  });
});
