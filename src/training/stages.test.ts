import { beforeEach, describe, expect, it } from 'vitest';
import { createPlan } from '../lib/stages.js';
import { installGlobals } from '../test-support/uo.js';
import { STAGES } from './config.js';

// The shipped Bushido table, as opposed to src/lib/stages.test.ts which is about the mechanism. These
// are the regression tests for the script this module replaced.

beforeEach(() => {
  installGlobals();
});

describe('STAGES', () => {
  it('is already in ascending order, so the plan is the table as written', () => {
    expect(createPlan(STAGES).stages.map((stage) => stage.upTo)).toEqual(
      STAGES.map((stage) => stage.upTo),
    );
  });

  // The bug this module was written for: the original read `bushido.value < 105`, which is 10.5 in
  // the tenths getSkill reports, so that band never ran and Evasion was never trained.
  it('states every bound in the tenths getSkill reports', () => {
    for (const stage of STAGES) {
      expect(stage.upTo).toBeGreaterThanOrEqual(100);
      expect(stage.upTo).toBeLessThanOrEqual(1200);
    }
  });

  it('aims at 105.0', () => {
    expect(createPlan(STAGES).goal).toBe(1050);
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

  // These are cast at nobody, and a cursor opened by a run that never answers it breaks every action
  // after it
  it('wants a target cursor for nothing', () => {
    for (const stage of STAGES) {
      expect(stage.target).toBeUndefined();
    }
  });
});

describe('stageNow', () => {
  // The three cases the original script's if/else chain was trying to express, plus the ending it
  // had no way to express at all
  it('works the bands the script it replaced meant to work', () => {
    const { stageNow } = createPlan(STAGES);

    expect(stageNow(500)?.spell).toBe(Spells.Confidence);
    expect(stageNow(700)?.spell).toBe(Spells.CounterAttack);
    expect(stageNow(800)?.spell).toBe(Spells.Evasion);
  });

  it('is finished at 105.0, which the original loop had no way of noticing', () => {
    expect(createPlan(STAGES).stageNow(1050)).toBeUndefined();
  });
});
