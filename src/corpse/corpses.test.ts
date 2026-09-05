import { beforeEach, describe, expect, it, vi } from 'vitest';
import { type FakeWorld, installGlobals, item } from '../test-support/uo.js';
import { CORPSE_GRAPHIC } from './config.js';
import {
  type Candidate,
  chooseMine,
  describeGround,
  inRange,
  matchOf,
  nearest,
  onGround,
  survey,
} from './corpses.js';

let world: FakeWorld;

const corpse = (serial: number, fields: Partial<Item> = {}) =>
  item({ serial, graphic: CORPSE_GRAPHIC, x: 100, y: 100, ...fields });

const candidate = (serial: number, name: string, distance: number): Candidate => ({
  serial,
  name,
  distance,
});

beforeEach(() => {
  world = installGlobals({ player: { x: 100, y: 100 } });
});

describe('onGround', () => {
  it('takes every corpse the client is tracking, in a pile or on its own', () => {
    world.client.findAllItemsOfType = vi.fn(() => [corpse(1), corpse(2, { x: 108 })]);

    expect(onGround().map((one) => one.serial)).toEqual([1, 2]);
  });

  it('drops one the client no longer knows the art of', () => {
    world.client.findAllItemsOfType = vi.fn(() => [corpse(1), corpse(2, { graphic: 0 })]);

    expect(onGround().map((one) => one.serial)).toEqual([1]);
  });
});

describe('inRange', () => {
  it('measures diagonally as well as straight', () => {
    const found = inRange([corpse(1, { x: 102, y: 102 }), corpse(2, { x: 103, y: 100 })], 2);

    expect(found.map((one) => one.serial)).toEqual([1]);
  });
});

describe('nearest', () => {
  it('answers with nothing for an empty field', () => {
    expect(nearest([])).toBeUndefined();
  });

  it('gives the closest distance, which is what the out-of-range line reports', () => {
    expect(nearest([corpse(1, { x: 109 }), corpse(2, { x: 104 })])).toBe(4);
  });
});

describe('survey', () => {
  it('reads the nearest corpses first, so a capped run spends its asks on the likely one', () => {
    const surveyed = survey([corpse(1, { x: 106 }), corpse(2, { x: 101 })], 8, 2000);

    expect(surveyed.map((one) => one.serial)).toEqual([2, 1]);
    expect(surveyed.map((one) => one.distance)).toEqual([1, 6]);
  });

  it('takes the name the client already has without paying for a tooltip', () => {
    const surveyed = survey([corpse(1, { name: 'a corpse of Fenwick' })], 8, 2000);

    expect(surveyed[0]?.name).toBe('a corpse of Fenwick');
    expect(world.client.queryItemOPL).not.toHaveBeenCalled();
  });

  it('asks the tooltip only for the corpses the client has not named', () => {
    world.client.queryItemOPL = vi.fn(() => ({ name: 'a corpse of Fenwick' }));

    survey([corpse(1, { name: 'a corpse of a rat' }), corpse(2, { x: 101 })], 8, 2000);

    expect(world.client.queryItemOPL).toHaveBeenCalledTimes(1);
    expect(world.client.queryItemOPL).toHaveBeenCalledWith(2, 2000);
  });

  it('stops asking once MAX_OPL_ASKS is spent, and leaves the rest unnamed', () => {
    world.client.queryItemOPL = vi.fn(() => ({ name: 'a corpse of Fenwick' }));

    const surveyed = survey([corpse(1), corpse(2, { x: 101 }), corpse(3, { x: 102 })], 2, 2000);

    expect(world.client.queryItemOPL).toHaveBeenCalledTimes(2);
    expect(surveyed.map((one) => one.name)).toEqual([
      'a corpse of Fenwick',
      'a corpse of Fenwick',
      '',
    ]);
  });

  it('leaves the name empty rather than guessing when the tooltip says nothing', () => {
    expect(survey([corpse(1)], 8, 2000)[0]?.name).toBe('');
  });
});

describe('matchOf', () => {
  it('reads a corpse of your own name as exactly yours', () => {
    expect(matchOf('a corpse of Fenwick', 'Fenwick')).toBe('exact');
  });

  it('is case-insensitive, because the shard capitalises what it likes', () => {
    expect(matchOf('A Corpse Of FENWICK', 'fenwick')).toBe('exact');
  });

  it('reads a name that carries yours without the prefix as a loose match', () => {
    expect(matchOf("Fenwick's corpse", 'Fenwick')).toBe('loose');
  });

  it('does not read a guildmate named Fenwick the Bold as Fen', () => {
    expect(matchOf('a corpse of Fenwick the Bold', 'Fen')).toBeUndefined();
  });

  it('matches nothing at all for a corpse whose name never arrived', () => {
    expect(matchOf('', 'Fenwick')).toBeUndefined();
  });

  it('matches nothing at all when the client has not said your own name yet', () => {
    expect(matchOf('a corpse of Fenwick', '')).toBeUndefined();
  });
});

describe('chooseMine', () => {
  it('takes the corpse named for you over the one at your feet', () => {
    const choice = chooseMine(
      [candidate(1, 'a corpse of a mongbat', 0), candidate(2, 'a corpse of Fenwick', 9)],
      'Fenwick',
    );

    expect(choice).toMatchObject({ picked: { serial: 2 }, why: 'exact', named: 1 });
  });

  it('prefers an exact name match to a loose one, even from further away', () => {
    const choice = chooseMine(
      [candidate(1, "Fenwick's corpse", 1), candidate(2, 'a corpse of Fenwick', 7)],
      'Fenwick',
    );

    expect(choice).toMatchObject({ picked: { serial: 2 }, why: 'exact', named: 2 });
  });

  it('takes the nearest when nothing is named for you', () => {
    const choice = chooseMine(
      [candidate(1, 'a corpse of a rat', 4), candidate(2, '', 1)],
      'Fenwick',
    );

    expect(choice).toMatchObject({ picked: { serial: 2 }, why: 'nearest', named: 0 });
  });

  it('takes the nearest of several corpses named for you, and counts them', () => {
    const choice = chooseMine(
      [candidate(1, 'a corpse of Fenwick', 6), candidate(2, 'a corpse of Fenwick', 2)],
      'Fenwick',
    );

    expect(choice).toMatchObject({ picked: { serial: 2 }, named: 2 });
  });

  it('returns a corpse that is out of reach, and leaves the range to the caller', () => {
    const choice = chooseMine([candidate(1, 'a corpse of Fenwick', 12)], 'Fenwick');

    expect(choice?.picked.distance).toBe(12);
  });

  it('answers with nothing for an empty field', () => {
    expect(chooseMine([], 'Fenwick')).toBeUndefined();
  });
});

describe('describeGround', () => {
  it('counts what the client can see, so a wrong graphic shows up at startup', () => {
    expect(describeGround([corpse(1), corpse(2)])).toBe('0x2006 x2');
  });
});
