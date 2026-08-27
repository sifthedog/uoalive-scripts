import { beforeEach, describe, expect, it, vi } from 'vitest';

import { type FakeWorld, installGlobals, item } from '../test-support/uo.js';
import { AMMO_GRAPHICS, GRAB_RANGE } from './config.js';
import { describeFloor, inReach, nearest, onFloor } from './floor.js';

const [ARROW, BOLT] = AMMO_GRAPHICS;

let world: FakeWorld;

// The client answers per graphic, so a fixture is a table of them
const answering = (byGraphic: Record<number, Item[]>) =>
  vi.fn((graphic: number) => byGraphic[graphic] ?? []);

beforeEach(() => {
  world = installGlobals();
});

describe('onFloor', () => {
  it('collects every configured graphic', () => {
    world.client.findAllItemsOfType = answering({
      [ARROW]: [item({ serial: 1, graphic: ARROW, container: 0 })],
      [BOLT]: [item({ serial: 2, graphic: BOLT, container: 0 })],
    });

    expect(onFloor().map((found) => found.serial)).toEqual([1, 2]);
  });

  it('leaves anything with a container where it is', () => {
    world.client.findAllItemsOfType = answering({
      [ARROW]: [
        item({ serial: 1, graphic: ARROW, container: 0 }),
        item({ serial: 2, graphic: ARROW, container: 0x40000000 }),
      ],
    });

    expect(onFloor().map((found) => found.serial)).toEqual([1]);
  });

  it('leaves them alone at your feet as readily as anywhere else', () => {
    world.client.findAllItemsOfType = answering({
      [ARROW]: [item({ serial: 2, graphic: ARROW, container: 0x40000000, x: 100, y: 100 })],
    });

    expect(onFloor()).toEqual([]);
  });

  it('reads a container serial the client sent as a negative int32', () => {
    world.client.findAllItemsOfType = answering({
      [ARROW]: [item({ serial: 2, graphic: ARROW, container: -0x3266af2f })],
    });

    expect(onFloor()).toEqual([]);
  });

  // Reading only 0 as the ground rejected every stack on the floor
  it('reads the world serial as the ground, signed or unsigned', () => {
    world.client.findAllItemsOfType = answering({
      [ARROW]: [
        item({ serial: 1, graphic: ARROW, container: 0xffffffff }),
        item({ serial: 2, graphic: ARROW, container: -1 }),
      ],
    });

    expect(onFloor().map((found) => found.serial)).toEqual([1, 2]);
  });

  it('picks a serial up once when two graphics answer for it', () => {
    const both = item({ serial: 1, graphic: ARROW, container: 0 });

    world.client.findAllItemsOfType = answering({ [ARROW]: [both], [BOLT]: [both] });

    expect(onFloor()).toHaveLength(1);
  });

  it('drops an entity the client has stopped tracking', () => {
    world.client.findAllItemsOfType = answering({
      [ARROW]: [item({ serial: 1, graphic: 0, container: 0 })],
    });

    expect(onFloor()).toEqual([]);
  });
});

describe('inReach', () => {
  const at = (x: number, y: number) => item({ serial: x * 1000 + y, graphic: ARROW, x, y });

  it('keeps what is exactly at the limit, diagonally as well as straight', () => {
    const found = inReach(
      [at(100, 100 + GRAB_RANGE), at(100 + GRAB_RANGE, 100 + GRAB_RANGE)],
      GRAB_RANGE,
    );

    expect(found).toHaveLength(2);
  });

  it('drops what is a tile past it', () => {
    expect(inReach([at(100, 100 + GRAB_RANGE + 1)], GRAB_RANGE)).toEqual([]);
  });
});

describe('describeFloor', () => {
  it('names the parent serials, which is what decides whether a stack counts', () => {
    world.client.findAllItemsOfType = answering({
      [ARROW]: [item({ serial: 1, graphic: ARROW, container: 0xffffffff })],
    });

    expect(describeFloor()).toContain('0xffffffff');
  });

  it('says a graphic nothing matched rather than leaving it out', () => {
    expect(describeFloor()).toContain('x0');
  });
});

describe('nearest', () => {
  it('answers with the closest of them', () => {
    const at = (x: number) => item({ serial: x, graphic: ARROW, x, y: 100 });

    expect(nearest([at(105), at(102)])).toBe(2);
  });

  it('answers with nothing for an empty floor', () => {
    expect(nearest([])).toBeUndefined();
  });
});
