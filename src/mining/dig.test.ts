import { beforeEach, describe, expect, it, vi } from 'vitest';

import { installGlobals, item, type FakeWorld } from '../test-support/uo.js';
import { ORE_GRAPHICS } from './config.js';
import { ALL_OUTCOME_TEXT, digOnce, outcomeFor } from './dig.js';

const PICKAXE = 1;
const ORE = [...ORE_GRAPHICS][3];

let world: FakeWorld;

const ore = (amount: number) => item({ serial: 50, graphic: ORE, hue: 0, amount });

// A pack that gains an ore the moment the swing goes out, which is what a swing the shard said
// nothing about looks like from the pack side
const oreArrivesOnTheSwing = (): void => {
  const packs = [[ore(3)], [ore(4)]];
  let swung = 0;

  Object.defineProperty(world.player, 'backpack', {
    configurable: true,
    get: () => ({ serial: 0x40000000, contents: packs[Math.min(swung, 1)] }),
  });

  world.player.useItemInHand.mockImplementation(() => {
    swung = 1;
  });
};

beforeEach(() => {
  world = installGlobals({
    client: { findObject: vi.fn(() => item({ serial: PICKAXE, graphic: 0x0e86 })) } as never,
  });
});

describe('outcomeFor', () => {
  it('maps a phrase back to its bucket', () => {
    expect(outcomeFor('There is no metal here to mine')).toBe('empty');
    expect(outcomeFor("You can't mine that")).toBe('notOre');
    expect(outcomeFor('Target cannot be seen')).toBe('notSeen');
  });

  it('offers every phrase to the journal, not just one bucket', () => {
    expect(ALL_OUTCOME_TEXT).toContain('You must wait');
    expect(ALL_OUTCOME_TEXT).toContain('Your backpack is full');
  });

  // Without a bucket of its own a world save reads as five unreadable outcomes in a row, which is
  // the run's stop condition - the shard being busy for a moment should not end the afternoon
  it('knows the world save for what it is', () => {
    expect(outcomeFor('The world is saving')).toBe('saving');
  });
});

describe('digOnce', () => {
  // Where this parts company with lumberjacking's chop: the swing is answered with yourself, so the
  // shard picks the ore, and no tile is ever named. Which means nothing here has to be right about
  // land versus static, or about which of the arts on a tile is the one carrying ore.
  it('answers the cursor with yourself rather than a tile', () => {
    digOnce(PICKAXE);

    expect(world.target.waitTargetSelf).toHaveBeenCalled();
    expect(world.target.terrain).not.toHaveBeenCalled();
  });

  it('cancels a cursor left open by the previous swing', () => {
    digOnce(PICKAXE);

    expect(world.target.cancel).toHaveBeenCalled();
  });

  it('reads the shard back as the outcome it worded', () => {
    world.journal.waitForTextAny.mockReturnValue('There is no metal here to mine');

    expect(digOnce(PICKAXE)).toBe('empty');
  });

  // A cursor that never opened is not the same as nothing having happened: the shard usually
  // refused the swing and said why, and the journal has been clear since just before it. Reading
  // that is what tells a throttle or a world save apart from a script that cannot read an outcome -
  // and reaching noCursor instead of either ended a live run in fifteen seconds.
  describe('when no cursor opens', () => {
    beforeEach(() => {
      world.target.waitTargetSelf.mockReturnValue(false);
    });

    it('reads the refusal the shard already worded', () => {
      world.journal.waitForTextAny.mockReturnValue('You must wait');

      expect(digOnce(PICKAXE)).toBe('throttled');
    });

    it('knows a world save for what it is here too', () => {
      world.journal.waitForTextAny.mockReturnValue('The world is saving');

      expect(digOnce(PICKAXE)).toBe('saving');
    });

    // The swing that breaks the pickaxe leaves the next one with an empty hand, and an empty hand
    // is a swing no cursor opens for. Read as the broken tool it is, so the loop swaps rather than
    // backing off against a hand that has nothing to back off with.
    it('reads a pickaxe serial that stopped resolving as a worn out tool', () => {
      world.client.findObject.mockReturnValue(undefined);

      expect(digOnce(PICKAXE)).toBe('wornOut');
    });

    it('reads ore arriving in the pack as a swing that landed anyway', () => {
      oreArrivesOnTheSwing();

      expect(digOnce(PICKAXE)).toBe('dug');
    });

    it('reports a cursor that never opened when nothing explains it', () => {
      expect(digOnce(PICKAXE)).toBe('noCursor');
    });

    // The old line guessed at an empty hand and was wrong about it on the run that found this
    it('says what is in the hand rather than guessing at it', () => {
      world.player.equippedItems.oneHanded = item({
        serial: PICKAXE,
        graphic: 0x0e86,
        name: 'pickaxe',
      });

      digOnce(PICKAXE);

      expect(world.log).toHaveBeenCalledWith(expect.stringContaining("0xe86 'pickaxe'"));
    });

    // A cursor that turned up a moment after the wait gave up on it is TARGET_TIMEOUT being short,
    // not the shard refusing - and the cancel on this path closes it, so the read has to come first
    // or the line reports 'never opened' every time and settles nothing.
    it('tells a cursor that came late from one that never came', () => {
      world.target.open = true;

      digOnce(PICKAXE);

      expect(world.log).toHaveBeenCalledWith(expect.stringContaining('came late'));
    });

    it('says so when no cursor turned up at all', () => {
      digOnce(PICKAXE);

      expect(world.log).toHaveBeenCalledWith(expect.stringContaining('never opened'));
    });
  });

  describe('when the journal says nothing', () => {
    // A shard that words its messages differently leaves the journal silent, so read the world:
    // ore landing in the pack is the only proof of a swing that does not depend on wording
    it('reads ore arriving in the pack as a swing that landed', () => {
      oreArrivesOnTheSwing();

      expect(digOnce(PICKAXE)).toBe('dug');
    });

    // item.hits is 0 for anything the client knows nothing about, and a RunUO tool tracks
    // UsesRemaining anyway, so a serial that stops resolving is the only evidence of a broken tool
    it('reads a pickaxe serial that stopped resolving as a worn out tool', () => {
      world.client.findObject.mockReturnValue(undefined);

      expect(digOnce(PICKAXE)).toBe('wornOut');
    });

    // Ahead of the ore check on purpose: a swing that breaks the pickaxe can still produce ore, and
    // reading that as an ordinary success would send the next cycle out with an empty hand
    it('prefers the worn out tool over the ore it also produced', () => {
      world.client.findObject.mockReturnValue(undefined);
      oreArrivesOnTheSwing();

      expect(digOnce(PICKAXE)).toBe('wornOut');
    });

    it('gives up and says so when nothing in the world changed either', () => {
      expect(digOnce(PICKAXE)).toBe('unknown');
    });

    // The loop stops after MAX_UNKNOWN of these, and a run with no tool serial to watch would
    // otherwise read every silent swing as a broken pickaxe
    it('does not claim a worn out tool when there was no serial to watch', () => {
      world.client.findObject.mockReturnValue(undefined);

      expect(digOnce(undefined)).toBe('unknown');
    });
  });
});
