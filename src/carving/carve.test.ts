import { beforeEach, describe, expect, it, vi } from 'vitest';

import { type FakeWorld, installGlobals, item } from '../test-support/uo.js';
import { ALL_OUTCOME_TEXT, carveOnce, outcomeFor } from './carve.js';
import { CORPSE_GRAPHIC, OUTCOME_TEXT } from './config.js';

const KNIFE = 0x40000010;

let world: FakeWorld;

const corpse = item({ serial: 0x40000001, graphic: CORPSE_GRAPHIC });

const says = (text: string | undefined) => vi.fn(() => text);

beforeEach(() => {
  world = installGlobals();
});

describe('the phrase table', () => {
  it('maps every phrase back to the bucket it was listed under', () => {
    for (const [bucket, phrases] of Object.entries(OUTCOME_TEXT)) {
      for (const phrase of phrases) {
        expect([phrase, outcomeFor(phrase)]).toEqual([phrase, bucket]);
      }
    }
  });

  it('offers every phrase to the one journal wait', () => {
    expect(ALL_OUTCOME_TEXT).toHaveLength(Object.values(OUTCOME_TEXT).flat().length);
  });
});

describe('carveOnce', () => {
  it('uses the knife and answers the cursor with the corpse', () => {
    world.journal.waitForTextAny = says('You pluck the bird');

    expect(carveOnce(corpse, KNIFE)).toBe('carved');
    expect(world.player.use).toHaveBeenCalledWith(KNIFE);
    expect(world.target.waitTargetEntity).toHaveBeenCalledWith(corpse.serial, expect.any(Number));
  });

  it('never puts the weapon down for it', () => {
    world.journal.waitForTextAny = says('You pluck the bird');

    carveOnce(corpse, KNIFE);

    expect(world.player.equip).not.toHaveBeenCalled();
    expect(world.player.useItemInHand).not.toHaveBeenCalled();
  });

  // An unconditional cancel shortly before the action leaves target.open false for the cursor that
  // follows, which is what dig.ts and boards.ts were fixed for
  it('cancels a cursor only when there is one to cancel', () => {
    world.journal.waitForTextAny = says('You pluck the bird');

    carveOnce(corpse, KNIFE);
    expect(world.target.cancel).not.toHaveBeenCalled();

    world.target.open = true;
    carveOnce(corpse, KNIFE);
    expect(world.target.cancel).toHaveBeenCalledTimes(1);
  });

  it('clears the journal before the use, so the wait cannot read a stale line', () => {
    const order: string[] = [];
    world.journal.clear = vi.fn(() => void order.push('clear'));
    world.player.use = vi.fn(() => void order.push('use'));
    world.journal.waitForTextAny = says('You pluck the bird');

    carveOnce(corpse, KNIFE);

    expect(order).toEqual(['clear', 'use']);
  });

  it('reads the shard refusing the corpse', () => {
    world.journal.waitForTextAny = says("You can't use a bladed item on that");

    expect(carveOnce(corpse, KNIFE)).toBe('notCarvable');
  });

  it('is unreadable rather than wrong when the shard says nothing it knows', () => {
    world.journal.waitForTextAny = says(undefined);

    expect(carveOnce(corpse, KNIFE)).toBe('unknown');
  });

  describe('a cursor that never opens', () => {
    beforeEach(() => {
      world.target.waitTargetEntity = vi.fn(() => false);
    });

    // The refusal has usually already arrived: the journal was cleared immediately before the use
    it('prefers a refusal that landed a moment late', () => {
      world.journal.waitForTextAny = says('You must wait a moment');

      expect(carveOnce(corpse, KNIFE)).toBe('throttled');
    });

    // Counted apart from the unreadable outcomes, which is why it is not simply 'unknown'
    it('is noCursor when nothing was said at all', () => {
      world.journal.waitForTextAny = says(undefined);

      expect(carveOnce(corpse, KNIFE)).toBe('noCursor');
      expect(world.target.cancel).toHaveBeenCalled();
    });
  });
});
