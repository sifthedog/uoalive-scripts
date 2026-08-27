import { beforeEach, describe, expect, it } from 'vitest';

import { type FakeWorld, installGlobals, item } from '../test-support/uo.js';
import { landed, settle, sweep } from './grab.js';

const PACK = 0x40000000;

let world: FakeWorld;

beforeEach(() => {
  world = installGlobals();
});

describe('sweep', () => {
  it('moves every stack into the pack', () => {
    sweep(PACK, [item({ serial: 1, graphic: 0x0f3f }), item({ serial: 2, graphic: 0x1bfb })]);

    expect(world.player.moveItem.mock.calls).toEqual([
      [1, PACK],
      [2, PACK],
    ]);
  });

  // A sweep of one used to pay a delay it had nothing to space itself out from
  it('spaces the moves out without paying a delay for a single stack', () => {
    sweep(PACK, [item({ serial: 1, graphic: 0x0f3f })]);
    expect(world.sleep).not.toHaveBeenCalled();

    sweep(PACK, [item({ serial: 1, graphic: 0x0f3f }), item({ serial: 2, graphic: 0x0f3f })]);
    expect(world.sleep).toHaveBeenCalledTimes(1);
  });
});

describe('landed', () => {
  const arrow = (serial: number, amount?: number) =>
    item({ serial, graphic: 0x0f3f, ...(amount === undefined ? {} : { amount }) });

  it('counts what is no longer on the floor', () => {
    const swept = [arrow(1, 12), arrow(2, 5)];

    expect(landed(swept, [swept[1]])).toEqual({ stacks: 1, items: 12 });
  });

  it('counts a stack the client gave no amount for as one', () => {
    expect(landed([arrow(1)], [])).toEqual({ stacks: 1, items: 1 });
  });

  it('counts nothing when the sweep was refused', () => {
    const swept = [arrow(1, 12)];

    expect(landed(swept, swept)).toEqual({ stacks: 0, items: 0 });
  });

  it('does not count a stack twice when a later sweep gets it', () => {
    const stack = arrow(1, 12);

    const first = landed([stack], [stack]);
    const second = landed([stack], []);

    expect(first.items + second.items).toBe(12);
  });
});

describe('settle', () => {
  const arrow = (serial: number, amount?: number) =>
    item({ serial, graphic: 0x0f3f, ...(amount === undefined ? {} : { amount }) });

  // The whole point of polling: a floor already clear costs one rescan, not the timeout
  it('does not wait at all when everything has already gone', () => {
    expect(settle([arrow(1, 4)], () => [])).toEqual({ stacks: 1, items: 4 });
    expect(world.sleep).not.toHaveBeenCalled();
  });

  it('waits for a move still in flight', () => {
    const stack = arrow(1, 4);
    let floor = [stack];

    const took = settle([stack], () => {
      const now = floor;
      floor = [];

      return now;
    });

    expect(took).toEqual({ stacks: 1, items: 4 });
    expect(world.sleep).toHaveBeenCalledTimes(1);
  });

  it('gives up on a refused move rather than polling forever', () => {
    const stack = arrow(1, 4);

    expect(settle([stack], () => [stack])).toEqual({ stacks: 0, items: 0 });
  });

  it('counts a partial sweep, so a throttling shard is not read as a stall', () => {
    const left = arrow(2, 3);

    expect(settle([arrow(1, 4), left], () => [left])).toEqual({ stacks: 1, items: 4 });
  });
});
