import { beforeEach, describe, expect, it } from 'vitest';
import { installGlobals, type FakeWorld } from '../test-support/uo.js';
import { createCaster, type OutcomeText } from './cast.js';
import type { Stage } from './stages.js';

let world: FakeWorld;

// A table of the shape a folder writes, small enough to read. The shipped ones are checked against
// their own shard's wordings in src/training/outcomes.test.ts and src/necromancy/outcomes.test.ts.
const TEXT: OutcomeText = {
  fizzled: ['The spell fizzles'],
  noReagents: ['You do not have enough reagents'],
  cooldown: ['You must wait before trying again'],
  throttled: ['You must wait to perform another action', 'You must wait'],
};

const caster = (skipWhenBuffed = false) =>
  createCaster({ outcomeText: TEXT, timeoutMs: 500, skipWhenBuffed });

const withBuff: Stage = {
  upTo: 600,
  spell: Spells.Confidence,
  mana: 10,
  buff: BuffDebuffs.Confidence,
};

const withoutBuff: Stage = { upTo: 600, spell: Spells.Confidence, mana: 10 };

const atSelf: Stage = { upTo: 500, spell: Spells.PainSpike, mana: 5, target: 'self' };

beforeEach(() => {
  world = installGlobals();
});

describe('outcomeFor', () => {
  it('maps a phrase back to the bucket it was written in', () => {
    expect(caster().outcomeFor('The spell fizzles')).toBe('fizzled');
    expect(caster().outcomeFor('You do not have enough reagents')).toBe('noReagents');
  });

  it('does not recognise a phrase from another shard', () => {
    expect(caster().outcomeFor('You feel a strange sensation')).toBeUndefined();
  });

  // An ability on its own timer is not the shard refusing the run, and only one of the two is worth
  // giving up over. They are told apart by wording alone, so the wording is pinned.
  it('tells an ability cooldown apart from the action throttle', () => {
    expect(caster().outcomeFor('You must wait before trying again')).toBe('cooldown');
    expect(caster().outcomeFor('You must wait to perform another action')).toBe('throttled');
  });
});

describe('allText', () => {
  it('is every phrase from every bucket, flattened in the order they were written', () => {
    expect(caster().allText).toEqual(Object.values(TEXT).flat());
  });

  // A folder writes down only what its shard can say to it, and a missing bucket has to cost nothing
  it('skips a bucket the table leaves out entirely', () => {
    const sparse = createCaster({
      outcomeText: { fizzled: ['The spell fizzles'] },
      timeoutMs: 500,
      skipWhenBuffed: false,
    });

    expect(sparse.allText).toEqual(['The spell fizzles']);
    expect(sparse.outcomeFor('You must wait')).toBeUndefined();
  });
});

describe('castOnce', () => {
  it('reads the shard s own wording when there is one', () => {
    world.journal.waitForTextAny.mockReturnValue('You must wait');

    expect(caster().castOnce(withBuff)).toBe('throttled');
  });

  // A fizzle costs nothing here, so it reads as silence to the mana proof. Asserted with mana
  // falling anyway: on a shard that does charge, the wording still has to win.
  it('reads a fizzle from the journal even when mana was spent', () => {
    world.journal.waitForTextAny.mockReturnValue('The spell fizzles');
    world.player.cast.mockImplementation(() => {
      world.player.mana -= 10;
    });

    expect(caster().castOnce(withBuff)).toBe('fizzled');
  });

  // This shard lets the same ability be recast while its buff is up, and casting once per buff
  // duration instead would throw away most of the run's throughput
  it('casts again into a buff that is already standing', () => {
    world.player.hasBuffDebuff.mockReturnValue(true);
    world.player.cast.mockImplementation(() => {
      world.player.mana -= 10;
    });

    expect(caster().castOnce(withBuff)).toBe('cast');
    expect(world.player.cast).toHaveBeenCalledWith(Spells.Confidence);
  });

  // The transition test cannot fire on a recast, so the mana leaving the pool is the whole proof
  it('proves a recast from the mana alone, with the buff up the whole time', () => {
    world.player.hasBuffDebuff.mockReturnValue(true);

    expect(caster().castOnce(withBuff)).toBeUndefined();
    expect(world.player.cast).toHaveBeenCalled();
  });

  // The success wording differs from shard to shard, so the proof of a cast is the buff arriving
  it('reads a buff that went up as a cast, even with the journal silent', () => {
    let up = false;
    world.player.hasBuffDebuff.mockImplementation(() => up);
    world.player.cast.mockImplementation(() => {
      up = true;
    });

    expect(caster().castOnce(withBuff)).toBe('cast');
  });

  // The only proof a row with no buff of its own has: mana can only fall by being spent
  it('reads mana leaving the pool as a cast', () => {
    world.player.cast.mockImplementation(() => {
      world.player.mana -= 10;
    });

    expect(caster().castOnce(withoutBuff)).toBe('cast');
  });

  // A successful cast says nothing this table knows, so it spends the whole window every time. One
  // figure for a table of 3rd- and 8th-circle rows means the fast rows buy the slow row's incantation.
  it('gives a row its own listening window where it names one', () => {
    caster().castOnce({ ...withBuff, castTimeout: 3200 });

    expect(world.journal.waitForTextAny).toHaveBeenCalledWith(
      expect.anything(),
      undefined,
      3200,
    );
  });

  it('falls back on the folder s window for a row that names none', () => {
    caster().castOnce(withBuff);

    expect(world.journal.waitForTextAny).toHaveBeenCalledWith(expect.anything(), undefined, 500);
  });

  // The setting is there for a shard where these are SpecialMoves and a second cast disables the
  // first, and for a transformation that stands until it is re-cast
  it('leaves a standing buff alone when skipWhenBuffed is on', () => {
    world.player.hasBuffDebuff.mockReturnValue(true);

    expect(caster(true).castOnce(withBuff)).toBe('alreadyUp');
    expect(world.player.cast).not.toHaveBeenCalled();
  });

  it('casts a stage with no buff rather than gating it', () => {
    world.player.hasBuffDebuff.mockReturnValue(true);

    caster(true).castOnce(withoutBuff);

    expect(world.player.cast).toHaveBeenCalledWith(Spells.Confidence);
  });

  // A cursor that opens and is never answered breaks every action after it, so a row that wants one
  // goes through castTo and a row that does not is never sent through it
  it('casts a self-targeted row at the character, with no cursor left open', () => {
    caster().castOnce(atSelf);

    expect(world.player.castTo).toHaveBeenCalledWith(Spells.PainSpike, world.player);
    expect(world.player.cast).not.toHaveBeenCalled();
  });

  it('casts an untargeted row without a cursor at all', () => {
    caster().castOnce(withoutBuff);

    expect(world.player.castTo).not.toHaveBeenCalled();
  });

  // Nothing said, nothing spent and nothing standing: the loop logs this and carries on rather
  // than booking it as a cast that happened
  it('answers with nothing when the world did not move either', () => {
    expect(caster().castOnce(withBuff)).toBeUndefined();
  });

  it('clears the journal before casting, so what it reads arrived because of this cast', () => {
    caster().castOnce(withBuff);

    expect(world.journal.clear).toHaveBeenCalled();
  });

  // A cursor left open by anything else would swallow the answer castTo queues, and the row after it
  // would be cast at nothing
  it('cancels a cursor left open before it casts', () => {
    caster().castOnce(atSelf);

    expect(world.target.cancel).toHaveBeenCalled();
  });
});
