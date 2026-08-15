import { beforeEach, describe, expect, it } from 'vitest';
import { createPlan } from '../lib/stages.js';
import { installGlobals } from '../test-support/uo.js';
import { STAGES } from './config.js';

// The shipped Magery table, as opposed to src/lib/stages.test.ts which is about the mechanism

beforeEach(() => {
  installGlobals();
});

describe('STAGES', () => {
  it('is already in ascending order, so the plan is the table as written', () => {
    expect(createPlan(STAGES).stages.map((stage) => stage.upTo)).toEqual(
      STAGES.map((stage) => stage.upTo),
    );
  });

  // Bushido's table was written with `105` where 105.0 was meant - a band below every other one,
  // which therefore never ran. Any bound that is not a plausible skill value is that typo coming back.
  it('states every bound in the tenths getSkill reports', () => {
    for (const stage of STAGES) {
      expect(stage.upTo).toBeGreaterThanOrEqual(100);
      expect(stage.upTo).toBeLessThanOrEqual(1200);
    }
  });

  it('aims at 120.0, which needs the power scrolls', () => {
    expect(createPlan(STAGES).goal).toBe(1200);
  });

  it('charges the circle s mana for every band, so the mana wait always has a figure', () => {
    for (const stage of STAGES) {
      expect(stage.mana).toBeGreaterThan(0);
    }
  });

  // The whole point of the table: the mana cost rises band by band, because gaining Magery means
  // casting something hard enough for the skill you have and the circle is what makes it hard
  it('climbs the circles rather than casting one spell all the way up', () => {
    const costs = createPlan(STAGES).stages.map((stage) => stage.mana);

    for (let index = 1; index < costs.length; index++) {
      expect(costs[index]).toBeGreaterThan(costs[index - 1]);
    }
  });

  it('names the same spell in spell and buff on every row that has one', () => {
    for (const stage of STAGES) {
      if (stage.buff === undefined) {
        continue;
      }

      expect(BuffDebuffs[stage.buff]).toBe(Spells[stage.spell]);
    }
  });

  // The row that has to train on the mana proof alone
  it('leaves Earthquake without a buff, because the client publishes none for it', () => {
    const quake = STAGES.find((stage) => stage.spell === Spells.Earthquake);

    expect(quake?.buff).toBeUndefined();
  });

  // Every row that opens a cursor answers it with the character, and the one that opens none says so.
  // A cursor a run never answers breaks every action after it.
  it('casts everything at the character except the one spell that takes no target', () => {
    for (const stage of STAGES) {
      expect(stage.target).toBe(stage.spell === Spells.Earthquake ? undefined : 'self');
    }
  });
});

describe('stageNow', () => {
  it('works the bands the table was written for', () => {
    const { stageNow } = createPlan(STAGES);

    expect(stageNow(300)?.spell).toBe(Spells.Bless);
    expect(stageNow(500)?.spell).toBe(Spells.ArchProtection);
    expect(stageNow(650)?.spell).toBe(Spells.Invisibility);
    expect(stageNow(850)?.spell).toBe(Spells.Earthquake);
  });

  it('is finished at 120.0', () => {
    expect(createPlan(STAGES).stageNow(1200)).toBeUndefined();
  });
});
