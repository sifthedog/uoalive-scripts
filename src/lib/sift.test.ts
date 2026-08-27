import { beforeEach, describe, expect, it, vi } from 'vitest';

import { installGlobals, type FakeWorld } from '../test-support/uo.js';
import { forgetUnreadable } from './containers.js';
import { artKey, movables, openNested, sift, siftContents, wantedFrom } from './sift.js';

const BAG = 0x0e76;
const INGOT = 0x1bf2;
const GEM = 0x0f16;
const UNKNOWN_BAG = 0x9999;

const VALORITE = 0x08a5;

interface Node {
  serial: number;
  graphic: number;
  hue?: number;
  amount?: number;
  children?: Node[];
  open?: boolean;
  throwsUntilOpened?: boolean;
}

let world: FakeWorld;
let nodes: Map<number, Node>;

// A container answers `undefined` for its contents until it has been opened, so `children` is what
// is inside and `open` is whether the client has been told
const asItem = (node: Node): Item => {
  const built = {
    serial: node.serial,
    graphic: node.graphic,
    hue: node.hue,
    amount: node.amount,
    contents: node.children && node.open ? node.children.map(asItem) : undefined,
  } as unknown as Item;

  if (node.throwsUntilOpened && !node.open) {
    Object.defineProperty(built, 'contents', {
      configurable: true,
      get: () => {
        throw new SyntaxError('Unexpected end of JSON input');
      },
    });
  }

  return built;
};

const register = (node: Node): Node => {
  nodes.set(node.serial, node);
  node.children?.forEach(register);

  return node;
};

beforeEach(() => {
  world = installGlobals();
  nodes = new Map();
  forgetUnreadable();

  world.client.findObject = vi.fn((serial: number) => {
    const node = nodes.get(serial);

    return node && asItem(node);
  });

  world.player.use = vi.fn((serial: number) => {
    const node = nodes.get(serial);

    if (node) {
      node.open = true;
    }
  });
});

const everything = wantedFrom([]);

const look = (rootSerial: number, options: { skipSerial?: number; opened?: Set<number> } = {}) =>
  sift(rootSerial, {
    skipSerial: options.skipSerial ?? 0,
    opened: options.opened ?? new Set<number>(),
  });

describe('artKey', () => {
  it('reads a missing hue as the shard reads it, which is uncoloured', () => {
    expect(artKey({ graphic: INGOT })).toBe(artKey({ graphic: INGOT, hue: 0 }));
  });

  it('tells two colours of the same art apart', () => {
    expect(artKey({ graphic: INGOT, hue: VALORITE })).not.toBe(artKey({ graphic: INGOT, hue: 0 }));
  });
});

describe('wantedFrom', () => {
  it('matches everything when nothing was picked', () => {
    expect(everything.has({ graphic: GEM } as Item)).toBe(true);
  });

  it('matches the art and the hue together', () => {
    const wanted = wantedFrom([{ serial: 1, name: '', graphic: INGOT, hue: VALORITE }]);

    expect(wanted.has({ graphic: INGOT, hue: VALORITE } as Item)).toBe(true);
    expect(wanted.has({ graphic: INGOT, hue: 0 } as Item)).toBe(false);
    expect(wanted.has({ graphic: GEM, hue: VALORITE } as Item)).toBe(false);
  });
});

describe('movables', () => {
  it('takes the loose items and leaves the bags they are in', () => {
    register({
      serial: 1,
      graphic: BAG,
      open: true,
      children: [
        { serial: 10, graphic: INGOT },
        { serial: 20, graphic: BAG, open: true, children: [{ serial: 21, graphic: GEM }] },
      ],
    });

    expect(movables(look(1, { skipSerial: 2 }), everything).map((item) => item.serial)).toEqual([
      10, 21,
    ]);
  });

  it('leaves the destination and everything under it alone', () => {
    register({
      serial: 1,
      graphic: BAG,
      open: true,
      children: [
        { serial: 2, graphic: BAG, open: true, children: [{ serial: 30, graphic: INGOT }] },
        { serial: 31, graphic: INGOT },
      ],
    });

    expect(movables(look(1, { skipSerial: 2 }), everything).map((item) => item.serial)).toEqual([
      31,
    ]);
  });

  it('leaves the whole tree alone when the skipped serial is somewhere else', () => {
    register({
      serial: 1,
      graphic: BAG,
      open: true,
      children: [
        { serial: 10, graphic: INGOT },
        { serial: 20, graphic: BAG, open: true, children: [{ serial: 21, graphic: GEM }] },
      ],
    });

    expect(movables(look(1, { skipSerial: 0x4001 }), everything).map((item) => item.serial)).toEqual(
      [10, 21],
    );
  });
});

describe('siftContents', () => {
  it('reads contents the client would not answer for as unreadable', () => {
    expect(siftContents(undefined, { skipSerial: 0, opened: new Set() }).readable).toBe(false);
  });

  it('reads an opened container that is empty as readable', () => {
    expect(siftContents([], { skipSerial: 0, opened: new Set() })).toEqual({
      loose: [],
      containers: [],
      readable: true,
    });
  });

  it('takes a bag isLoose claims rather than walking into it', () => {
    register({
      serial: 1,
      graphic: BAG,
      open: true,
      children: [{ serial: 20, graphic: BAG, open: true, children: [{ serial: 21, graphic: GEM }] }],
    });

    const found = siftContents(asItem(nodes.get(1) as Node).contents, {
      skipSerial: 0,
      opened: new Set(),
      isLoose: (item) => item.graphic === BAG,
    });

    expect(found.loose.map((item) => item.serial)).toEqual([20]);
    expect(found.containers).toEqual([]);
  });

  it('skips the destination even when isLoose would have claimed it', () => {
    register({
      serial: 1,
      graphic: BAG,
      open: true,
      children: [
        { serial: 2, graphic: BAG, open: true, children: [{ serial: 30, graphic: GEM }] },
        { serial: 31, graphic: GEM },
      ],
    });

    const found = siftContents(asItem(nodes.get(1) as Node).contents, {
      skipSerial: 2,
      opened: new Set(),
      isLoose: () => true,
    });

    expect(found.loose.map((item) => item.serial)).toEqual([31]);
  });
});

describe('openNested', () => {
  it('opens what it was handed, once, and says it did', () => {
    const opened = new Set<number>();
    register({ serial: 20, graphic: BAG, children: [{ serial: 21, graphic: INGOT }] });

    const bags = [asItem(nodes.get(20) as Node)];

    expect(openNested(bags, opened, 0)).toBe(true);
    expect(openNested(bags, opened, 0)).toBe(false);
    expect(world.player.use).toHaveBeenCalledTimes(1);
  });

  it('says nothing happened when every bag has already been opened', () => {
    expect(openNested([], new Set(), 0)).toBe(false);
  });

  // contentsOf stops asking a serial that threw, so opening one has to clear that or the bag is
  // skipped for the rest of the run
  it('clears a bag that threw, so what is inside it becomes reachable', () => {
    const opened = new Set<number>();
    register({
      serial: 1,
      graphic: BAG,
      open: true,
      children: [
        {
          serial: 20,
          graphic: BAG,
          throwsUntilOpened: true,
          children: [{ serial: 21, graphic: INGOT }],
        },
      ],
    });

    const first = look(1);
    expect(movables(first, everything)).toEqual([]);

    openNested(first.containers, opened, 0);

    expect(movables(look(1, { opened }), everything).map((item) => item.serial)).toEqual([21]);
  });

  it('leaves an art it does not know for a container alone', () => {
    register({
      serial: 1,
      graphic: BAG,
      open: true,
      children: [{ serial: 20, graphic: UNKNOWN_BAG }],
    });

    const found = look(1);

    expect(found.containers).toEqual([]);
    expect(found.loose.map((item) => item.serial)).toEqual([20]);
  });
});
