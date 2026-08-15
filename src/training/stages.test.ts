import { beforeEach, describe, expect, it } from 'vitest';
import { installGlobals } from '../test-support/uo.js';
import { STAGES } from './config.js';
import { PLAN, TARGET, stageNow } from './plan.js';

// The shipped Bushido table, as opposed to src/lib/stages.test.ts which is about the mechanism. These
// are the regression tests for the script this module replaced.

beforeEach(() => {
  installGlobals();
});

describe('STAGES', () => {
  it('is already in ascending order, so the plan is the table as written', () => {
    expect(PLAN.map((stage) => stage.upTo)).toEqual(STAGES.map((stage) => stage.upTo));
  });

  // The bug this module was written for. The original read `bushido.value < 105`, which is 10.5 in
  // the tenths getSkill reports - a band below every other one, sitting after them in an if/else
  // chain, so it never ran and Evasion was never trained. Any bound that is not a plausible skill
  // value is that typo coming back.
  it('states every bound in the tenths getSkill reports', () => {
    for (const stage of STAGES) {
      expect(stage.upTo).toBeGreaterThanOrEqual(100);
      expect(stage.upTo).toBeLessThanOrEqual(1200);
    }
  });

  it('aims at 105.0', () => {
    expect(TARGET).toBe(1050);
  });

  it('charges mana for every band, so the mana wait always has a figure', () => {
    for (const stage of STAGES) {
      expect(stage.mana).toBeGreaterThan(0);
    }
  });

  // A row whose buff belongs to a different ability would gate the wrong thing: the run would skip
  // casts because some other move was standing, and read those skips as successes
  it('names the same ability in spell and buff on every row', () => {
    for (const stage of STAGES) {
      expect(stage.buff).toBeDefined();
      expect(BuffDebuffs[stage.buff as BuffDebuffs]).toBe(Spells[stage.spell]);
    }
  });
});

describe('stageNow', () => {
  // The three cases the original script's if/else chain was trying to express, plus the ending it
  // had no way to express at all
  it('works the bands the script it replaced meant to work', () => {
    expect(stageNow(500)?.spell).toBe(Spells.Confidence);
    expect(stageNow(700)?.spell).toBe(Spells.CounterAttack);
    expect(stageNow(800)?.spell).toBe(Spells.Evasion);
  });

  it('is finished at 105.0, which the original loop had no way of noticing', () => {
    expect(stageNow(1050)).toBeUndefined();
  });
});
