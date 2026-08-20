import { beforeEach, describe, expect, it, vi } from 'vitest';

import { installGlobals, type FakeWorld } from '../test-support/uo.js';
import { type Picked, pickMany, pickOne } from './pick.js';

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

const byArt = (picked: Picked): string | undefined => `${picked.graphic}/${picked.hue}`;

const many = (keyOf: (picked: Picked) => string | undefined = byArt) =>
  pickMany({ prefix: 'pick', prompt: 'click things', maxPicks: 3, oplTimeout: 1, keyOf });

const one = () => pickOne({ prefix: 'pick', prompt: 'click a thing', oplTimeout: 1 });

describe('pickOne', () => {
  it('takes the serial, art and hue off the query and the name off the tooltip', () => {
    world.target.query = clicks({ serial: 0x4011, graphic: 0x1bf2, hue: 0x08a5 });
    world.client.queryItemOPL = vi.fn(() => ({ name: 'valorite ingot' }));

    expect(one()).toEqual({
      serial: 0x4011,
      name: 'valorite ingot',
      graphic: 0x1bf2,
      hue: 0x08a5,
    });
  });

  it('falls back to the object for an art and a hue the query did not carry', () => {
    world.target.query = clicks({ serial: 0x4011 });
    world.client.findObject = vi.fn(() => ({ name: 'ingot', graphic: 0x1bf2, hue: 7 }));

    expect(one()).toMatchObject({ name: 'ingot', graphic: 0x1bf2, hue: 7 });
  });

  // Zero matches nothing, which is the safe direction - undefined would match every item nothing
  // knows the art of
  it('answers zero for an art and a hue nothing knows', () => {
    world.target.query = clicks({ serial: 0x4011 });

    expect(one()).toMatchObject({ name: '', graphic: 0, hue: 0 });
  });

  it('comes back with nothing when the cursor is cancelled', () => {
    expect(one()).toBeUndefined();
    expect(world.log).toHaveBeenCalledWith('pick: nothing targeted', undefined);
  });
});

describe('pickMany', () => {
  it('keeps asking until the cursor is cancelled', () => {
    world.target.query = clicks({ serial: 1, graphic: 0x1bf2 }, { serial: 2, graphic: 0x13b6 });

    expect(many().map((picked) => picked.serial)).toEqual([1, 2]);
    expect(world.target.query).toHaveBeenCalledTimes(3);
  });

  // ESC on the first cursor. The callers treat an empty list as a choice rather than a fault.
  it('comes back empty when the first pick is cancelled', () => {
    expect(many()).toEqual([]);
  });

  it('takes a key once however many things carrying it are clicked', () => {
    world.target.query = clicks(
      { serial: 1, graphic: 0x1bf2, hue: 0 },
      { serial: 2, graphic: 0x1bf2, hue: 0 },
    );

    expect(many()).toHaveLength(1);
    expect(world.log).toHaveBeenCalledWith(expect.stringContaining('already on the list'));
  });

  // The trap a `while (pickItem())` loop falls into: ending the whole selection over one pick the
  // caller cannot key is not what clicking it meant
  it('skips a pick the caller will not key and carries on asking', () => {
    world.target.query = clicks({ serial: 1, graphic: 0x1bf2 }, { serial: 2, graphic: 0x13b6 });

    const picks = many((picked) => (picked.serial === 1 ? undefined : byArt(picked)));

    expect(picks.map((picked) => picked.serial)).toEqual([2]);
  });

  // A cursor left open by whatever ran last would swallow the query, and a live one would spend the
  // double-clicks and gumps that follow a selection as target clicks instead
  it('clears any leftover cursor before opening its own', () => {
    world.target.query = clicks({ serial: 1, graphic: 0x1bf2 });

    many();

    expect(world.target.cancel.mock.invocationCallOrder[0]).toBeLessThan(
      world.target.query.mock.invocationCallOrder[0],
    );
  });

  it('cancels the cursor again when the selection ends', () => {
    world.target.query = clicks({ serial: 1, graphic: 0x1bf2 });

    many();

    // One before each of the two queries, and one more for the cursor the cancelled query left up
    expect(world.target.cancel).toHaveBeenCalledTimes(3);
  });

  // A backstop, not the way the selection is meant to end: a client that answered every query would
  // otherwise keep this loop asking forever
  it('stops asking after maxPicks clicks', () => {
    let serial = 0;

    world.target.query = vi.fn(() => ({ serial: ++serial, graphic: serial }));

    expect(many()).toHaveLength(3);
    expect(world.log).toHaveBeenCalledWith(expect.stringContaining('as many as one run takes'));
  });
});
