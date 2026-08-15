import { beforeEach, describe, expect, it, vi } from 'vitest';
import { installGlobals, type FakeWorld } from '../test-support/uo.js';
import type { CastOutcome } from './cast.js';
import type { SkillReader } from './skill.js';
import type { Stage } from './stages.js';
import { runTrainer, type TrainerOptions, type TrainerTimings } from './trainer.js';

// The loop, on a fake skill and a fake cast. It used to be an entry point that ran on import and so
// had no tests at all; what is pinned here is the arithmetic of the endings, which is where every
// counter that stops a run either works or quietly does not.

let world: FakeWorld;

const STAGES: Stage[] = [
  { upTo: 600, spell: Spells.Confidence, mana: 10, buff: BuffDebuffs.Confidence },
  { upTo: 800, spell: Spells.Evasion, mana: 10, buff: BuffDebuffs.Evasion },
];

const TIMINGS: TrainerTimings = {
  castDelay: 1,
  castTimeout: 1,
  buffWait: 1,
  castingWait: 7,
  stepDelay: 1,
  maxCycles: 20,
  maxBlindReads: 5,
  regenTimeout: 4,
  maxThrottled: 4,
  maxStale: 8,
  logEvery: 25,
  cooldownBackoff: 1,
  cooldownBackoffMax: 1,
  throttleBackoff: 1,
  throttleBackoffMax: 1,
};

// A skill the client answers for, which the caller moves by hand
const reader = (start: number | undefined, cap?: number): SkillReader & { at: number | undefined } => {
  const state = {
    at: start,
    value: () => state.at,
    cap: () => cap,
    name: () => 'Bushido',
    waitForSkill: () => state.at,
  };

  return state;
};

const run = (overrides: Partial<TrainerOptions> = {}): void =>
  runTrainer({
    prefix: 'test',
    stages: STAGES,
    skill: reader(500),
    castOnce: () => 'cast',
    regainMana: () => true,
    stopReason: () => undefined,
    beat: vi.fn(),
    waitOutSave: vi.fn(),
    timings: TIMINGS,
    ...overrides,
  });

// What the run ended with, which is the line every ending goes through
const ending = (): string => {
  const calls = world.exit.mock.calls;

  return String(calls[calls.length - 1]?.[0]);
};

const said = (fragment: string): boolean =>
  world.log.mock.calls.some((call) => String(call[0]).includes(fragment));

beforeEach(() => {
  world = installGlobals();
});

describe('runTrainer', () => {
  it('stops before it casts anything when the skill is already past the last band', () => {
    const castOnce = vi.fn((): CastOutcome => 'cast');

    run({ skill: reader(800), castOnce });

    expect(castOnce).not.toHaveBeenCalled();
    expect(ending()).toContain('already at 80.0');
  });

  it('works the bands in order and stops when the last one is passed', () => {
    const skill = reader(500);
    const cast: Spells[] = [];

    run({
      skill,
      castOnce: (stage) => {
        cast.push(stage.spell);
        skill.at = (skill.at ?? 0) + 100;

        return 'cast';
      },
    });

    expect(cast).toEqual([
      Spells.Confidence,
      Spells.Evasion,
      Spells.Evasion,
    ]);
    expect(ending()).toContain('the last stage is finished');
  });

  it('says the table aims past what the shard will allow', () => {
    run({ skill: reader(500, 700) });

    expect(said('it will not finish without a power scroll')).toBe(true);
  });

  // 0 is a real skill value and a blind client is not one, so a client that has gone quiet gets a
  // budget of its own rather than being read either way
  it('gives up on a client that stops reporting the skill', () => {
    const skill = reader(500);
    skill.value = () => undefined;

    run({ skill });

    expect(ending()).toContain('stopped reporting the skill');
  });

  it('gathers mana before a cast the pool cannot pay for', () => {
    const regainMana = vi.fn(() => {
      world.player.mana = 50;

      return true;
    });

    world.player.mana = 0;

    run({ regainMana });

    expect(regainMana).toHaveBeenCalledWith(10);
  });

  // No ending of its own any more: a dry stretch is charged what it cost in casting cycles and spends
  // the same budget an unreadable outcome does, because from in here both are the run getting nowhere
  it('gives up when the mana never comes back', () => {
    world.player.mana = 0;

    run({ regainMana: () => false });

    expect(ending()).toContain('without a cast or a change in the skill');
  });

  // Weighted rather than counted one-for-one: a stretch that spent the whole regenTimeout standing
  // still must not cost the same as a cycle that spent one cast
  it('charges a dry mana stretch for what it cost, not one cycle', () => {
    world.player.mana = 0;

    const regainMana = vi.fn(() => false);

    run({ regainMana });

    // regenTimeout / (castTimeout + castDelay) = 2 idle per stretch, against a ceiling of 8
    expect(regainMana).toHaveBeenCalledTimes(4);
  });

  // Priced on castDelay alone the denominator left out the window castOnce stands in - which a
  // successful cast spends all of - so a folder that shortened its pacing found one dry stretch
  // charged most of the ceiling and two of them ending the run.
  it('prices a dry stretch against the whole cast cycle, not the pause after it', () => {
    world.player.mana = 0;

    const regainMana = vi.fn(() => false);

    run({ regainMana, timings: { ...TIMINGS, castTimeout: 3 } });

    // regenTimeout / (3 + 1) = 1 idle per stretch, so the ceiling of 8 takes eight of them
    expect(regainMana).toHaveBeenCalledTimes(8);
  });

  // A row's own figures price its cycle, so the slow band is not charged the fast band's rate
  it('prices the dry stretch on the row s own figures where it has them', () => {
    world.player.mana = 0;

    const regainMana = vi.fn(() => false);
    const slow: Stage[] = [{ ...STAGES[0]!, castTimeout: 3, castDelay: 1 }];

    run({ regainMana, stages: slow });

    expect(regainMana).toHaveBeenCalledTimes(8);
  });

  // The bug the extraction found: every `stop` the switch set was overwritten by the line asking the
  // mana half whether it lost the weapon, so these two endings never ended anything.
  it('ends on an outcome nothing can retry away, even with a mana half to ask', () => {
    run({ castOnce: () => 'unskilled', manaBlocked: () => undefined });

    expect(ending()).toContain('cannot use');
  });

  it('ends after enough throttles rather than counting past the limit', () => {
    const castOnce = vi.fn((): CastOutcome => 'throttled');

    run({ castOnce, manaBlocked: () => undefined });

    expect(castOnce).toHaveBeenCalledTimes(TIMINGS.maxThrottled);
    expect(ending()).toContain('kept refusing the cast');
  });

  // The count is consecutive - the backoff grows with it and the ceiling reads it as "twenty in a
  // row" - but only some branches cleared it, so on a run whose successes were unreadable it climbed
  // monotonically and twenty throttles spread over hours ended a run nothing was refusing.
  it('forgets the throttles either side of a cycle that was not one', () => {
    const outcomes: CastOutcome[] = [];

    for (let pair = 0; pair < TIMINGS.maxThrottled; pair++) {
      outcomes.push('throttled', 'fizzled');
    }

    const castOnce = vi.fn((): CastOutcome => outcomes.shift() ?? 'fizzled');

    run({ castOnce });

    expect(ending()).not.toContain('kept refusing the cast');
    expect(ending()).toContain('cycle backstop');
  });

  // An unread outcome is the one that mattered: it is what a successful cast looks like on a shard
  // whose wordings the table has not got, and it is not evidence of anything being refused
  it('forgets the throttles either side of an outcome it could not read', () => {
    const outcomes: CastOutcome[] = [];

    for (let pair = 0; pair < TIMINGS.maxThrottled; pair++) {
      outcomes.push('throttled');
      outcomes.push(undefined as unknown as CastOutcome);
    }

    const castOnce = vi.fn((): CastOutcome => outcomes.shift() as CastOutcome);

    run({ castOnce });

    expect(ending()).not.toContain('kept refusing the cast');
  });

  // Nothing waited for fixes an empty pouch, and a run that carried on would spend the rest of its
  // cycles casting nothing at all
  it('ends the run when the reagents run out', () => {
    run({ castOnce: () => 'noReagents' });

    expect(ending()).toContain('out of reagents');
  });

  it('ends the run when the tithing points run out', () => {
    run({ castOnce: () => 'noTithing' });

    expect(ending()).toContain('out of tithing points');
  });

  // The loop asking too early, not the shard refusing. Never counted towards a stop, or an
  // eighth-circle band would end every run that reached it.
  it('backs off a cast that came in before the last one finished, and never stops for it', () => {
    const castOnce = vi.fn((): CastOutcome => 'alreadyCasting');

    run({ castOnce });

    expect(castOnce).toHaveBeenCalledTimes(TIMINGS.maxCycles);
    expect(ending()).toContain('cycle backstop');
    expect(said('unreadable')).toBe(false);
  });

  it('ends the run when the shard will not cast in the form the character is in', () => {
    run({ castOnce: () => 'formLocked' });

    expect(ending()).toContain('cannot train itself');
  });

  it('ends on the mana half losing what it stowed', () => {
    run({ manaBlocked: () => 'could not get the weapon back in hand' });

    expect(ending()).toContain('could not get the weapon back in hand');
  });

  it('draws the weapon again rather than stopping when a cast wants one', () => {
    const rearm = vi.fn(() => true);

    run({ castOnce: () => 'noWeapon', rearm });

    expect(rearm).toHaveBeenCalled();
    expect(ending()).toContain('cycle backstop');
  });

  it('stops when the weapon cannot be drawn at all', () => {
    run({ castOnce: () => 'noWeapon', rearm: () => false });

    expect(ending()).toContain('none could be drawn');
  });

  // Only because nothing else was happening either. An unreadable outcome is never the reason on its
  // own - see the two tests below.
  it('gives up on unreadable outcomes only once the skill has stopped moving too', () => {
    run({ castOnce: () => undefined });

    expect(ending()).toContain('without a cast or a change in the skill');
  });

  // The fault this was written for: a stage whose buff was already up has no transition to show, so a
  // client that has not refreshed the mana figure leaves the loop nothing to read - while the skill
  // climbs perfectly well. The run must not die of that.
  it('never stops while the skill is still moving, however unreadable the outcomes are', () => {
    const skill = reader(500);
    const castOnce = vi.fn((): CastOutcome | undefined => {
      skill.at = (skill.at ?? 0) + 1;

      return undefined;
    });

    run({ skill, castOnce });

    expect(castOnce).toHaveBeenCalledTimes(TIMINGS.maxCycles);
    expect(ending()).toContain('cycle backstop');
  });

  // Movement is the proof, so the casts it could not read were casts after all
  it('credits the casts it could not read once the skill moves', () => {
    const skill = reader(500);
    let cast = 0;
    const castOnce = (): CastOutcome | undefined => {
      cast++;

      if (cast === 3) {
        skill.at = (skill.at ?? 0) + 1;
      }

      return undefined;
    };

    run({ skill, castOnce });

    expect(said('3 casts')).toBe(true);
  });

  it('says so once per stretch rather than once per cast', () => {
    run({ castOnce: () => undefined });

    const lines = world.log.mock.calls.flat().filter((line) => String(line).includes('unreadable'));

    expect(lines).toHaveLength(1);
  });

  it('owns up to what it could not read in the closing lines', () => {
    run({ castOnce: () => undefined });

    expect(said('outcome(s) went unread')).toBe(true);
  });

  // A fizzle is read, not missed: it clears the unknown budget, and it is counted apart from the
  // casts because the two together are the run's real rate
  it('counts a fizzle without ever calling it unreadable', () => {
    run({ castOnce: () => 'fizzled' });

    expect(said('unreadable')).toBe(false);
    expect(said(`0 casts, ${TIMINGS.maxCycles} fizzles`)).toBe(true);
  });

  // The shard saying the last cast is still going is it working as designed, so it is read rather
  // than missed and never counted: this ran for every cycle it had rather than ending on a budget
  it('waits out a cast still in flight rather than ending the run over it', () => {
    const castOnce = vi.fn((): CastOutcome => 'alreadyCasting');

    run({ castOnce });

    expect(said('unreadable')).toBe(false);
    expect(castOnce).toHaveBeenCalledTimes(TIMINGS.maxCycles);
    expect(ending()).toContain('cycle backstop');
  });

  // Sharing the cooldown's growing backoff - sized for an ability timer most of a minute long - left
  // a band of two-second casts idling twenty seconds between attempts.
  it('waits the same short time for every cast in flight, never a growing one', () => {
    run({ castOnce: () => 'alreadyCasting' });

    const waits = world.sleep.mock.calls
      .map((call) => Number(call[0]))
      .filter((ms) => ms !== TIMINGS.castDelay);

    expect(waits).toHaveLength(TIMINGS.maxCycles);
    expect(new Set(waits)).toEqual(new Set([TIMINGS.castingWait]));
  });

  // A table whose rows are seconds apart in cast time cannot be paced by one number: at the slow
  // row's figure every fast row idles for a cast it has already finished.
  it('paces on the row s own delay where it has one', () => {
    const paced: Stage[] = [{ ...STAGES[0]!, castDelay: 9 }];

    run({ stages: paced, skill: reader(500) });

    expect(world.sleep.mock.calls.map((call) => Number(call[0]))).toContain(9);
    expect(world.sleep).not.toHaveBeenCalledWith(TIMINGS.castDelay);
  });

  it('paces on the folder s delay for a row with none', () => {
    run();

    expect(world.sleep.mock.calls.map((call) => Number(call[0]))).toContain(TIMINGS.castDelay);
  });

  // On a table of transformations the toggle-off is how the character leaves the form: the shard
  // rolled the skill and charged the mana for it, so it is a cast
  it('counts a toggle-off as a cast where the stages are transformations', () => {
    run({ castOnce: () => 'disabled', disabledIsProgress: true });

    expect(said(`${TIMINGS.maxCycles} casts`)).toBe(true);
    expect(said('check its buff in STAGES')).toBe(false);
  });

  // On a table of moves that stack it is a cast paid for and thrown away, and worth saying so
  it('complains about a toggle-off where the stages are meant to stack', () => {
    run({ castOnce: () => 'disabled', disabledIsProgress: false });

    expect(said('0 casts')).toBe(true);
    expect(said('check its buff in STAGES')).toBe(true);
  });

  it('stops when a guard fires', () => {
    run({ stopReason: () => 'you are dead' });

    expect(ending()).toContain('you are dead');
  });

  // The order is the whole point of the hook: the guard that ends the run for a hurt character is the
  // same floor the healing works back up to, so a mend that ran after it would never run at all
  it('mends the character before the guards judge it', () => {
    const order: string[] = [];

    run({
      recover: () => order.push('recover'),
      stopReason: () => {
        order.push('guard');

        return 'hurt (10/100)';
      },
    });

    expect(order).toEqual(['recover', 'guard']);
  });

  it('reports the gain it made, which is the point of the run', () => {
    const skill = reader(500);

    run({
      skill,
      castOnce: () => {
        skill.at = 800;

        return 'cast';
      },
    });

    expect(said('Bushido 50.0 -> 80.0')).toBe(true);
  });

  // die() exits and then throws, so that the compiler narrows on it - the throw is what a test sees,
  // because the fake exit does not halt anything
  it('refuses to run at all on an empty table', () => {
    expect(() => run({ stages: [] })).toThrow();
    expect(ending()).toContain('STAGES is empty');
  });

  it('refuses to guess at a skill the client is not reporting', () => {
    const skill = reader(undefined);

    expect(() => run({ skill })).toThrow();
    expect(ending()).toContain('not reporting the skill');
  });
});
