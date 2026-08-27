import { beforeEach, describe, expect, it, vi } from 'vitest';

import { installGlobals, item, type FakeWorld } from '../test-support/uo.js';
import { issue, landed, settle } from './move.js';

const INGOT = 0x1bf2;

let world: FakeWorld;

beforeEach(() => {
  world = installGlobals();
});

describe('issue', () => {
  it('moves each item to the destination', () => {
    issue([item({ serial: 10, graphic: INGOT }), item({ serial: 11, graphic: INGOT })], 2);

    expect(world.player.moveItem).toHaveBeenNthCalledWith(1, 10, 2);
    expect(world.player.moveItem).toHaveBeenNthCalledWith(2, 11, 2);
  });

  // A stack that merged into an identical one at the destination answers for wherever it is now, so
  // reading the amount back off the handle counts the merged total
  it('snapshots the amount at the moment of the move', () => {
    const moving = { serial: 10, graphic: INGOT, amount: 5 } as unknown as Item;

    const sent = issue([moving], 2);
    (moving as { amount: number }).amount = 400;

    expect(sent).toEqual([{ serial: 10, amount: 5 }]);
  });

  it('reads a missing amount as one', () => {
    expect(issue([item({ serial: 10, graphic: INGOT })], 2)).toEqual([{ serial: 10, amount: 1 }]);
  });
});

describe('landed', () => {
  it('counts only what left the pack', () => {
    const sent = [
      { serial: 10, amount: 5 },
      { serial: 11, amount: 2 },
    ];

    expect(landed(sent, [item({ serial: 11, graphic: INGOT })])).toEqual({ stacks: 1, items: 5 });
  });

  it('counts nothing for a pass the shard refused whole', () => {
    const sent = [{ serial: 10, amount: 5 }];

    expect(landed(sent, [item({ serial: 10, graphic: INGOT })])).toEqual({ stacks: 0, items: 0 });
  });
});

describe('settle', () => {
  it('stops looking as soon as everything has gone', () => {
    const rescan = vi.fn(() => [] as Item[]);

    expect(settle([{ serial: 10, amount: 5 }], rescan)).toEqual({ stacks: 1, items: 5 });
    expect(rescan).toHaveBeenCalledTimes(1);
  });

  it('waits for a move that lands late', () => {
    let looks = 0;
    const rescan = vi.fn(() => (looks++ < 3 ? [item({ serial: 10, graphic: INGOT })] : []));

    expect(settle([{ serial: 10, amount: 5 }], rescan)).toEqual({ stacks: 1, items: 5 });
  });

  it('gives up on a pass that never lands', () => {
    const rescan = vi.fn(() => [item({ serial: 10, graphic: INGOT })]);

    expect(settle([{ serial: 10, amount: 5 }], rescan)).toEqual({ stacks: 0, items: 0 });
  });
});
