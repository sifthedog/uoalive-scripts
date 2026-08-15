import { beforeEach, describe, expect, it, vi } from 'vitest';
import type { Stage } from '../lib/stages.js';
import { installGlobals, type FakeWorld } from '../test-support/uo.js';
import { ALL_OUTCOME_TEXT, castOnce, outcomeFor } from './cast.js';
import { OUTCOME_TEXT } from './config.js';

let world: FakeWorld;

const withBuff: Stage = {
  upTo: 600,
  spell: Spells.Confidence,
  mana: 10,
  buff: BuffDebuffs.Confidence,
};

const withoutBuff: Stage = { upTo: 600, spell: Spells.Confidence, mana: 10 };

beforeEach(() => {
  world = installGlobals();
});

describe('outcomeFor', () => {
  // Table-driven off the config itself, so adding a phrase to OUTCOME_TEXT without wiring up its
  // category is caught here rather than showing up in game as an 'unknown' outcome
  for (const [name, phrases] of Object.entries(OUTCOME_TEXT)) {
    for (const phrase of phrases) {
      it(`maps '${phrase}' to ${name}`, () => {
        expect(outcomeFor(phrase)).toBe(name);
      });
    }
  }

  it('does not recognise a phrase from another shard', () => {
    expect(outcomeFor('You feel a strange sensation')).toBeUndefined();
  });

  // An ability on its own timer is not the shard refusing the run, and only one of the two is worth
  // giving up over. They are told apart by wording alone, so the wording is pinned.
  it('tells an ability cooldown apart from the action throttle', () => {
    expect(outcomeFor('You must wait before trying again')).toBe('cooldown');
    expect(outcomeFor('You must wait to perform another action')).toBe('throttled');
  });

  // waitForTextAny hands back whichever supplied string it found, and the cooldown sentence contains
  // the throttle's bare fallback - so the full wording has to be offered first or the client decides
  it('offers the cooldown wording before the bare throttle prefix', () => {
    expect(ALL_OUTCOME_TEXT.indexOf('You must wait before trying again')).toBeLessThan(
      ALL_OUTCOME_TEXT.indexOf('You must wait'),
    );
  });
});

describe('ALL_OUTCOME_TEXT', () => {
  it('is every phrase from every category, flattened', () => {
    expect(ALL_OUTCOME_TEXT).toEqual(Object.values(OUTCOME_TEXT).flat());
  });

  it('holds no duplicates, so a match is never ambiguous', () => {
    expect(new Set(ALL_OUTCOME_TEXT).size).toBe(ALL_OUTCOME_TEXT.length);
  });
});

describe('castOnce', () => {
  it('reads the shard s own wording when there is one', () => {
    world.journal.waitForTextAny.mockReturnValue('You must wait');

    expect(castOnce(withBuff)).toBe('throttled');
  });

  // A fizzle costs nothing on this shard, so it reads as silence to the mana proof and has to come
  // from the words. Asserted with mana falling anyway: if a shard does charge for a fizzle, the
  // wording still has to win, or every failed roll would be booked as a cast that landed.
  it('reads a fizzle from the journal even when mana was spent', () => {
    world.journal.waitForTextAny.mockReturnValue('The spell fizzles');
    world.player.cast.mockImplementation(() => {
      world.player.mana -= 10;
    });

    expect(castOnce(withBuff)).toBe('fizzled');
  });

  // This shard lets the same ability be recast while its buff is up, and casting once per buff
  // duration instead would throw away most of the run's throughput
  it('casts again into a buff that is already standing', () => {
    world.player.hasBuffDebuff.mockReturnValue(true);
    world.player.cast.mockImplementation(() => {
      world.player.mana -= 10;
    });

    expect(castOnce(withBuff)).toBe('cast');
    expect(world.player.cast).toHaveBeenCalledWith(Spells.Confidence);
  });

  // The transition test cannot fire on a recast, so the mana leaving the pool is the whole proof
  it('proves a recast from the mana alone, with the buff up the whole time', () => {
    world.player.hasBuffDebuff.mockReturnValue(true);

    expect(castOnce(withBuff)).toBeUndefined();
    expect(world.player.cast).toHaveBeenCalled();
  });

  // The success wording differs from shard to shard, so the proof of a cast is the buff arriving
  it('reads a buff that went up as a cast, even with the journal silent', () => {
    let up = false;
    world.player.hasBuffDebuff.mockImplementation(() => up);
    world.player.cast.mockImplementation(() => {
      up = true;
    });

    expect(castOnce(withBuff)).toBe('cast');
  });

  // The only proof a row with no buff of its own has: mana can only fall by being spent
  it('reads mana leaving the pool as a cast', () => {
    world.player.cast.mockImplementation(() => {
      world.player.mana -= 10;
    });

    expect(castOnce(withoutBuff)).toBe('cast');
  });

  // The setting is there for a shard where these are SpecialMoves and a second cast disables the
  // first, which is real elsewhere even though it is not what this shard does
  it('leaves a standing buff alone when SKIP_WHEN_BUFFED is on', async () => {
    vi.resetModules();
    vi.doMock('./config.js', async () => ({
      ...(await vi.importActual<typeof import('./config.js')>('./config.js')),
      SKIP_WHEN_BUFFED: true,
    }));

    const { castOnce: gated } = await import('./cast.js');
    world.player.hasBuffDebuff.mockReturnValue(true);

    expect(gated(withBuff)).toBe('alreadyUp');
    expect(world.player.cast).not.toHaveBeenCalled();

    vi.doUnmock('./config.js');
  });

  it('casts a stage with no buff rather than gating it', () => {
    world.player.hasBuffDebuff.mockReturnValue(true);

    castOnce(withoutBuff);

    expect(world.player.cast).toHaveBeenCalledWith(Spells.Confidence);
  });

  // Nothing said, nothing spent and nothing standing: the loop counts this against MAX_UNKNOWN rather
  // than booking it as a cast that happened
  it('answers with nothing when the world did not move either', () => {
    expect(castOnce(withBuff)).toBeUndefined();
  });

  it('clears the journal before casting, so what it reads arrived because of this cast', () => {
    castOnce(withBuff);

    expect(world.journal.clear).toHaveBeenCalled();
  });
});
