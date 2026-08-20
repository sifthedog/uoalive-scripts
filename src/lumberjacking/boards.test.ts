import { beforeEach, describe, expect, it, vi } from 'vitest';

import { installGlobals, item, type FakeWorld } from '../test-support/uo.js';
import { CONVERT_ATTEMPTS, MAX_CONVERT_PASSES, THROTTLED_TEXT } from './config.js';

const LOG = 0x1bdd;
const BOARD = 0x1bd7;
// Whatever this shard's board art turns out to be. Not in BOARD_GRAPHICS, so it has to be learned.
const UNKNOWN_BOARD = 0x1a2b;

let world: FakeWorld;

// boards.ts counts silent misses per hue, remembers the hues it gave up on, and adds to the
// config's own BOARD_GRAPHICS as it learns - all of which has to start clean each test.
const loadBoards = async () => import('./boards.js');

const pack = (...contents: Item[]) => {
  world.player.backpack = { serial: 0x40000000, contents };
};

// The conversion is read from a pack diff, so a successful convert is modelled as the pack
// changing when the target lands - not on a read count, since the code snapshots the pack more
// than once before it ever presses anything
const convertsTo = (before: Item[], after: Item[]) => {
  let converted = false;

  Object.defineProperty(world.player, 'backpack', {
    configurable: true,
    get: () => ({ serial: 0x40000000, contents: converted ? after : before }),
  });

  world.target.waitTargetEntity.mockImplementation(() => {
    converted = true;
    return true;
  });
};

beforeEach(() => {
  vi.resetModules();
  world = installGlobals({ player: { x: 100, y: 100 } });
});

describe('isBoard', () => {
  it('matches a seeded board graphic', async () => {
    const { isBoard } = await loadBoards();

    expect(isBoard(item({ serial: 1, graphic: BOARD }))).toBe(true);
  });

  it('rejects a log', async () => {
    const { isBoard } = await loadBoards();

    expect(isBoard(item({ serial: 1, graphic: LOG }))).toBe(false);
  });
});

describe('makeBoards', () => {
  // A frozen shard answers a conversion exactly the way an unworkable wood does, so without this a
  // world save costs CONVERT_ATTEMPTS and writes the hue off for the rest of the run
  it('leaves the logs alone while the world is saving', async () => {
    world.player.backpack = { serial: 0x40000000, contents: [item({ serial: 1, graphic: LOG, amount: 20 })] };
    world.journal.containsText.mockImplementation((text: string) => text.includes('world is saving'));
    const { makeBoards, unconvertible } = await loadBoards();

    expect(makeBoards()).toBe(false);
    expect(world.player.useItemInHand).not.toHaveBeenCalled();
    expect(unconvertible.has(0)).toBe(false);
  });

  it('reports success when the pack holds nothing to convert', async () => {
    pack();
    const { makeBoards } = await loadBoards();

    expect(makeBoards()).toBe(true);
    expect(world.player.useItemInHand).not.toHaveBeenCalled();
  });

  it('targets the log stack with whatever is in hand', async () => {
    pack(item({ serial: 5, graphic: LOG, amount: 10 }));
    const { makeBoards } = await loadBoards();

    makeBoards();

    expect(world.player.useItemInHand).toHaveBeenCalled();
    expect(world.target.waitTargetEntity).toHaveBeenCalledWith(5, expect.any(Number));
  });

  // A cursor left open by the last chop would swallow this one
  it('cancels a leftover cursor before starting', async () => {
    pack(item({ serial: 5, graphic: LOG, amount: 10 }));
    world.target.open = true;
    const { makeBoards } = await loadBoards();

    makeBoards();

    expect(world.target.cancel).toHaveBeenCalled();
  });

  // An unconditional cancel shortly before the action leaves target.open false for the cursor that
  // follows, and a conversion that loses its cursor is counted against the wood - three of those
  // write hue 0 off, which puts every ordinary log on the pack animal
  it('leaves the cursor alone when there was none to cancel', async () => {
    convertsTo([item({ serial: 5, graphic: LOG, amount: 10 })], [item({ serial: 6, graphic: BOARD })]);
    const { makeBoards } = await loadBoards();

    makeBoards();

    expect(world.target.cancel).not.toHaveBeenCalled();
  });

  it('gives up on the attempt when no target cursor appears', async () => {
    pack(item({ serial: 5, graphic: LOG, amount: 10 }));
    world.target.waitTargetEntity.mockReturnValue(false);
    const { makeBoards } = await loadBoards();

    makeBoards();

    expect(world.log).toHaveBeenCalledWith(expect.stringContaining('no target cursor'));
  });

  // The conversion sends no message on stock RunUO, only a sound, so the pack diff is the only
  // evidence - and that diff also names the board graphic, whatever this shard's art id is
  it('learns the shard board graphic from the pack diff', async () => {
    convertsTo(
      [item({ serial: 5, graphic: LOG, amount: 10 })],
      [item({ serial: 6, graphic: UNKNOWN_BOARD, amount: 20 })],
    );
    const { isBoard, makeBoards } = await loadBoards();

    expect(isBoard(item({ serial: 6, graphic: UNKNOWN_BOARD }))).toBe(false);

    makeBoards();

    expect(isBoard(item({ serial: 6, graphic: UNKNOWN_BOARD }))).toBe(true);
    expect(world.log).toHaveBeenCalledWith(expect.stringContaining('board graphic is 0x1a2b'));
  });

  it('does not mistake the logs it consumed for a board', async () => {
    convertsTo(
      [item({ serial: 5, graphic: LOG, amount: 10 })],
      [item({ serial: 6, graphic: UNKNOWN_BOARD, amount: 20 })],
    );
    const { unconvertible, makeBoards } = await loadBoards();

    makeBoards();

    expect(unconvertible.has(0)).toBe(false);
  });

  // The wording is the shard saying it is busy, not a verdict on the wood. smelt.ts has always passed
  // THROTTLED_TEXT to the converter and this did not, so three busy moments wrote hue 0 off.
  it('does not count a throttled conversion against the hue', async () => {
    pack(item({ serial: 5, graphic: LOG, amount: 10 }));
    world.journal.containsText.mockImplementation((text: string) =>
      THROTTLED_TEXT.includes(text),
    );
    const { makeBoards, unconvertible } = await loadBoards();

    makeBoards();

    expect(unconvertible.has(0)).toBe(false);
    expect(world.log).toHaveBeenCalledWith(expect.stringContaining('the shard says wait'));
  });

  describe('giving up on a hue', () => {
    // One silent attempt proves nothing - the action throttle and a stale serial look exactly like
    // a wood that cannot be worked - and giving up there put ordinary logs on the pack animal.
    it('retries a silent hue rather than writing it off on the first miss', async () => {
      pack(item({ serial: 5, graphic: LOG, amount: 10, hue: 0 }));
      const { makeBoards } = await loadBoards();

      makeBoards();

      expect(world.player.useItemInHand.mock.calls.length).toBe(CONVERT_ATTEMPTS);
      expect(CONVERT_ATTEMPTS).toBeGreaterThan(1);
    });

    it('gives up once the silent tries reach CONVERT_ATTEMPTS', async () => {
      pack(item({ serial: 5, graphic: LOG, amount: 10, hue: 0 }));
      const { makeBoards, unconvertible } = await loadBoards();

      makeBoards();

      expect(unconvertible.has(0)).toBe(true);
      expect(world.log).toHaveBeenCalledWith(expect.stringContaining('hue 0 failed 3 times'));
    });

    // A cursor that never came used to return before the miss was counted, so the candidate stack
    // was identical next pass and every pass spent TARGET_TIMEOUT on a cursor never coming.
    it('counts a missing target cursor against the hue like any other failure', async () => {
      pack(item({ serial: 5, graphic: LOG, amount: 10, hue: 0 }));
      world.target.waitTargetEntity.mockReturnValue(false);
      const { makeBoards, unconvertible } = await loadBoards();

      makeBoards();

      expect(unconvertible.has(0)).toBe(true);
      expect(world.player.useItemInHand.mock.calls.length).toBe(CONVERT_ATTEMPTS);
    });

    it('does not hit the pass backstop when the cursor never comes', async () => {
      pack(item({ serial: 5, graphic: LOG, amount: 10, hue: 0 }));
      world.target.waitTargetEntity.mockReturnValue(false);
      const { makeBoards } = await loadBoards();

      makeBoards();

      expect(world.log).not.toHaveBeenCalledWith(expect.stringContaining('backstop'));
    });

    // Bounded by the hue count, not by MAX_CONVERT_PASSES: the candidate set always shrinks, so
    // the pass backstop should never be what stops it
    it('stops well short of the pass backstop', async () => {
      pack(item({ serial: 5, graphic: LOG, amount: 10, hue: 0 }));
      const { makeBoards } = await loadBoards();

      makeBoards();

      expect(world.player.useItemInHand.mock.calls.length).toBeLessThan(MAX_CONVERT_PASSES);
      expect(world.log).not.toHaveBeenCalledWith(expect.stringContaining('backstop'));
    });

    // The shard saying it outright is the one failure retrying cannot fix
    it('gives up at once when the journal says the skill is lacking', async () => {
      pack(item({ serial: 5, graphic: LOG, amount: 10, hue: 0x4a8 }));
      world.journal.containsText.mockImplementation((text: string) =>
        text.startsWith('You are not skilled enough'),
      );
      const { makeBoards, unconvertible } = await loadBoards();

      makeBoards();

      expect(unconvertible.has(0x4a8)).toBe(true);
      expect(world.log).toHaveBeenCalledWith(expect.stringContaining('not skilled enough'));
    });

    it('leaves other hues alone when one is given up on', async () => {
      pack(item({ serial: 5, graphic: LOG, amount: 10, hue: 0x4a8 }));
      world.journal.containsText.mockImplementation((text: string) =>
        text.startsWith('You are not skilled enough'),
      );
      const { makeBoards, unconvertible } = await loadBoards();

      makeBoards();

      expect(unconvertible.has(0)).toBe(false);
    });

    it('stops trying a hue it has given up on', async () => {
      pack(item({ serial: 5, graphic: LOG, amount: 10, hue: 0 }));
      const { makeBoards, unconvertible } = await loadBoards();

      makeBoards();
      expect(unconvertible.has(0)).toBe(true);

      world.player.useItemInHand.mockClear();
      expect(makeBoards()).toBe(true);
      expect(world.player.useItemInHand).not.toHaveBeenCalled();
    });
  });
});
