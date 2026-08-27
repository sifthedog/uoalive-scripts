import { beforeEach, describe, expect, it, vi } from 'vitest';

import { forgetUnreadable } from '../lib/containers.js';
import { wantedFrom } from '../lib/sift.js';
import { installGlobals, type FakeWorld } from '../test-support/uo.js';
import { createScan } from './scan.js';

const PACK = 0x40000000;
const BAG = 0x0e76;
const POUCH = 0x0e79;
const INGOT = 0x1bf2;
const GEM = 0x0f16;

const VALORITE = 0x08a5;

interface Node {
  serial: number;
  graphic: number;
  hue?: number;
  amount?: number;
  children?: Node[];
  open?: boolean;
  closedAgain?: boolean;
}

let world: FakeWorld;
let nodes: Map<number, Node>;
let pack: Node;

const asItem = (node: Node): Item =>
  ({
    serial: node.serial,
    graphic: node.graphic,
    hue: node.hue,
    amount: node.amount,
    contents: node.children && node.open ? node.children.map(asItem) : undefined,
  }) as unknown as Item;

const register = (node: Node): Node => {
  nodes.set(node.serial, node);
  node.children?.forEach(register);

  return node;
};

// The pack itself is what packContents reads, so it is wired separately from findObject
const holds = (...children: Node[]): void => {
  pack = register({ serial: PACK, graphic: BAG, open: true, children });
  world.player.backpack = asItem(pack);
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

    if (node && !node.closedAgain) {
      node.open = true;
    }
  });

  holds();
});

// player.backpack answers a fresh handle each read on the client, and the fixture has to as well or
// a bag opened mid-test stays shut in the tree the scan already holds
const refresh = (): void => {
  world.player.backpack = asItem(pack);
};

const scanFor = (destSerial: number, ...picks: Array<{ graphic: number; hue?: number }>) =>
  createScan({
    destSerial,
    wanted: wantedFrom(
      picks.map((pick) => ({ serial: 0, name: '', graphic: pick.graphic, hue: pick.hue ?? 0 })),
    ),
  });

const stowable = (scan: ReturnType<typeof createScan>): number[] => {
  refresh();

  return scan.wantedIn(scan.look()).map((item) => item.serial);
};

describe('createScan', () => {
  it('finds a watched item at the top of the pack', () => {
    holds({ serial: 10, graphic: INGOT });

    expect(stowable(scanFor(2, { graphic: INGOT }))).toEqual([10]);
  });

  it('finds one inside a bag, and one two bags deep', () => {
    holds(
      { serial: 10, graphic: INGOT },
      {
        serial: 20,
        graphic: BAG,
        open: true,
        children: [
          { serial: 21, graphic: INGOT },
          { serial: 30, graphic: BAG, open: true, children: [{ serial: 31, graphic: INGOT }] },
        ],
      },
    );

    expect(stowable(scanFor(2, { graphic: INGOT }))).toEqual([10, 21, 31]);
  });

  it('leaves an art nobody picked alone', () => {
    holds({ serial: 10, graphic: INGOT }, { serial: 11, graphic: GEM });

    expect(stowable(scanFor(2, { graphic: INGOT }))).toEqual([10]);
  });

  it('leaves a hue nobody picked alone', () => {
    holds(
      { serial: 10, graphic: INGOT, hue: VALORITE },
      { serial: 11, graphic: INGOT, hue: 0 },
    );

    expect(stowable(scanFor(2, { graphic: INGOT, hue: VALORITE }))).toEqual([10]);
  });

  it('offers neither a destination inside the pack nor anything already in it', () => {
    holds(
      { serial: 2, graphic: POUCH, open: true, children: [{ serial: 30, graphic: INGOT }] },
      { serial: 31, graphic: INGOT },
    );

    expect(stowable(scanFor(2, { graphic: INGOT }))).toEqual([31]);
  });

  it('offers everything watched when the destination is outside the pack', () => {
    holds(
      { serial: 10, graphic: INGOT },
      { serial: 20, graphic: BAG, open: true, children: [{ serial: 21, graphic: INGOT }] },
    );
    register({ serial: 0x4001, graphic: BAG, open: true, children: [] });

    expect(stowable(scanFor(0x4001, { graphic: INGOT }))).toEqual([10, 21]);
  });

  it('takes a watched bag whole rather than emptying it', () => {
    holds({ serial: 20, graphic: POUCH, open: true, children: [{ serial: 21, graphic: GEM }] });

    const scan = scanFor(2, { graphic: POUCH });

    expect(stowable(scan)).toEqual([20]);
    expect(scan.openNew(scan.look().containers)).toBe(false);
  });

  it('opens a bag dropped in after the first look, and clicks it exactly once', () => {
    const scan = scanFor(2, { graphic: INGOT });

    expect(stowable(scan)).toEqual([]);

    holds({ serial: 20, graphic: BAG, children: [{ serial: 21, graphic: INGOT }] });

    for (let round = 0; round < 3; round++) {
      refresh();
      scan.openNew(scan.look().containers);
    }

    expect(world.player.use).toHaveBeenCalledTimes(1);
    expect(stowable(scan)).toEqual([21]);
  });

  it('reopens a bag that went shut under it, and gives up after MAX_REOPENS', () => {
    holds({ serial: 20, graphic: BAG, children: [{ serial: 21, graphic: INGOT }] });

    const scan = scanFor(2, { graphic: INGOT });

    refresh();
    scan.openNew(scan.look().containers);
    expect(stowable(scan)).toEqual([21]);

    const bag = nodes.get(20) as Node;
    bag.open = false;
    bag.closedAgain = true;

    for (let round = 0; round < 6; round++) {
      refresh();
      scan.openNew(scan.look().containers);
    }

    // The first open, then MAX_REOPENS retries, and then it is left alone
    expect(world.player.use).toHaveBeenCalledTimes(4);
  });

  it('does not share what it has opened with another scan', () => {
    holds({ serial: 20, graphic: BAG, children: [{ serial: 21, graphic: INGOT }] });

    const first = scanFor(2, { graphic: INGOT });
    refresh();
    first.openNew(first.look().containers);

    const second = scanFor(2, { graphic: INGOT });
    (nodes.get(20) as Node).open = false;
    refresh();
    second.openNew(second.look().containers);

    expect(world.player.use).toHaveBeenCalledTimes(2);
  });
});

describe('createScan with OPEN_NESTED off', () => {
  it('still reads a bag the client has open, but never double-clicks one', async () => {
    vi.resetModules();
    vi.doMock('./config.js', async () => ({
      ...(await vi.importActual<typeof import('./config.js')>('./config.js')),
      OPEN_NESTED: false,
    }));

    const { createScan: createQuietScan } = await import('./scan.js');

    holds(
      { serial: 20, graphic: BAG, open: true, children: [{ serial: 21, graphic: INGOT }] },
      { serial: 30, graphic: BAG, children: [{ serial: 31, graphic: INGOT }] },
    );

    const scan = createQuietScan({
      destSerial: 2,
      wanted: wantedFrom([{ serial: 0, name: '', graphic: INGOT, hue: 0 }]),
    });

    refresh();
    const found = scan.look();

    expect(scan.openNew(found.containers)).toBe(false);
    expect(world.player.use).not.toHaveBeenCalled();
    expect(scan.wantedIn(found).map((item) => item.serial)).toEqual([21]);

    vi.doUnmock('./config.js');
    vi.resetModules();
  });
});
