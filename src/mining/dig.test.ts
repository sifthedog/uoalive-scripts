import { beforeEach, describe, expect, it, vi } from 'vitest';

import { installGlobals, item, type FakeWorld } from '../test-support/uo.js';
import { ORE_GRAPHICS } from './config.js';
import { ALL_OUTCOME_TEXT, digOnce, outcomeFor } from './dig.js';

const PICKAXE = 1;
const ORE = [...ORE_GRAPHICS][3];

let world: FakeWorld;

const ore = (amount: number) => item({ serial: 50, graphic: ORE, hue: 0, amount });

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

  it('reports a cursor that never opened', () => {
    world.target.waitTargetSelf.mockReturnValue(false);

    expect(digOnce(PICKAXE)).toBe('noCursor');
  });

  describe('when the journal says nothing', () => {
    // A shard that words its messages differently leaves the journal silent, so read the world:
    // ore landing in the pack is the only proof of a swing that does not depend on wording
    it('reads ore arriving in the pack as a swing that landed', () => {
      const packs = [[ore(3)], [ore(4)]];
      let swung = 0;
      Object.defineProperty(world.player, 'backpack', {
        configurable: true,
        get: () => ({ serial: 0x40000000, contents: packs[Math.min(swung, 1)] }),
      });
      world.player.useItemInHand.mockImplementation(() => {
        swung = 1;
      });

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
      const packs = [[ore(3)], [ore(4)]];
      let swung = 0;
      Object.defineProperty(world.player, 'backpack', {
        configurable: true,
        get: () => ({ serial: 0x40000000, contents: packs[Math.min(swung, 1)] }),
      });
      world.player.useItemInHand.mockImplementation(() => {
        swung = 1;
      });

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
