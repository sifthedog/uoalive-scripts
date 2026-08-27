import { beforeEach, describe, expect, it, vi } from 'vitest';

import { installGlobals, type FakeWorld } from '../test-support/uo.js';
import { transfer, wantedFrom } from './move.js';

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

const childrenOf = (serial: number): number[] =>
  (nodes.get(serial)?.children ?? []).map((child) => child.serial);

beforeEach(() => {
  world = installGlobals();
  nodes = new Map();

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

  world.player.moveItem = vi.fn((serial: number, destination: number) => {
    const moving = nodes.get(serial);

    for (const node of nodes.values()) {
      const at = node.children?.findIndex((child) => child.serial === serial) ?? -1;

      if (at >= 0) {
        node.children?.splice(at, 1);
      }
    }

    if (moving) {
      nodes.get(destination)?.children?.push(moving);
    }

    return 1;
  });
});

const destination = () => register({ serial: 2, graphic: BAG, children: [], open: true });

const everything = wantedFrom([]);

describe('transfer', () => {
  it('empties a flat container and counts what it sent', () => {
    register({
      serial: 1,
      graphic: BAG,
      children: [
        { serial: 10, graphic: INGOT, amount: 5 },
        { serial: 11, graphic: GEM, amount: 1 },
      ],
    });
    destination();

    expect(transfer(1, 2, everything)).toEqual({
      outcome: 'emptied',
      stacks: 2,
      items: 6,
      left: 0,
    });
    expect(childrenOf(2)).toEqual([10, 11]);
  });

  it('reaches a bag it had to open first, and leaves the empty bag behind', () => {
    register({
      serial: 1,
      graphic: BAG,
      children: [{ serial: 20, graphic: BAG, children: [{ serial: 21, graphic: INGOT }] }],
    });
    destination();

    expect(transfer(1, 2, everything).outcome).toBe('emptied');
    expect(childrenOf(1)).toEqual([20]);
    expect(childrenOf(2)).toEqual([21]);
  });

  // contentsOf stops asking a serial that threw, so opening one has to clear that or the bag is
  // skipped for the rest of the run
  it('reaches a bag that threw before it was opened', () => {
    register({
      serial: 1,
      graphic: BAG,
      children: [
        {
          serial: 20,
          graphic: BAG,
          throwsUntilOpened: true,
          children: [{ serial: 21, graphic: INGOT }],
        },
      ],
    });
    destination();

    expect(transfer(1, 2, everything).outcome).toBe('emptied');
    expect(childrenOf(2)).toEqual([21]);
  });

  // Emptied, a bag off CONTAINER_GRAPHICS answers `[]` like any other item, and moving it would
  // undo the flattening the run just did
  it('leaves a bag whose art it does not know behind once it has emptied it', () => {
    register({
      serial: 1,
      graphic: BAG,
      children: [
        {
          serial: 20,
          graphic: UNKNOWN_BAG,
          open: true,
          children: [{ serial: 21, graphic: INGOT }],
        },
      ],
    });
    destination();

    transfer(1, 2, everything);

    expect(childrenOf(1)).toEqual([20]);
    expect(childrenOf(2)).toEqual([21]);
  });

  // Nothing tells the two apart, and double-clicking to find out is what CONTAINER_GRAPHICS exists
  // to avoid: player.use() on a potion drinks it
  it('moves an unopened bag whole when its art is not a known container', () => {
    register({
      serial: 1,
      graphic: BAG,
      children: [{ serial: 20, graphic: UNKNOWN_BAG, children: [{ serial: 21, graphic: INGOT }] }],
    });
    destination();

    transfer(1, 2, everything);

    expect(childrenOf(2)).toEqual([20]);
  });

  it('moves only the art and the hue that were picked', () => {
    register({
      serial: 1,
      graphic: BAG,
      children: [
        { serial: 10, graphic: INGOT, hue: VALORITE },
        { serial: 11, graphic: INGOT, hue: 0 },
        { serial: 12, graphic: GEM, hue: VALORITE },
      ],
    });
    destination();

    transfer(1, 2, wantedFrom([{ serial: 0, name: '', graphic: INGOT, hue: VALORITE }]));

    expect(childrenOf(2)).toEqual([10]);
  });

  it('says the container never opened rather than that it was empty', () => {
    register({ serial: 1, graphic: BAG });
    destination();

    expect(transfer(1, 2, everything)).toMatchObject({ outcome: 'unopened', stacks: 0 });
  });

  // Moves are asynchronous, so a pass that shifted nothing is the only sign the client refused
  it('stops on a pass that moved nothing and says how much is left', () => {
    register({
      serial: 1,
      graphic: BAG,
      children: [
        { serial: 10, graphic: INGOT },
        { serial: 11, graphic: GEM },
      ],
    });
    destination();
    world.player.moveItem = vi.fn(() => 0);

    expect(transfer(1, 2, everything)).toMatchObject({ outcome: 'stalled', left: 2 });
  });
});
