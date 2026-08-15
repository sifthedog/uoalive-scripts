import { beforeEach, describe, expect, it } from 'vitest';
import { createPlan } from '../lib/stages.js';
import { installGlobals } from '../test-support/uo.js';
import { STAGES } from './config.js';

// The shipped Chivalry table, as opposed to src/lib/stages.test.ts which is about the mechanism

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

  it('charges mana for every band, so the mana wait always has a figure', () => {
    for (const stage of STAGES) {
      expect(stage.mana).toBeGreaterThan(0);
    }
  });

  // A row whose buff belongs to a different spell would gate the wrong thing. Only asserted of the
  // rows that carry one - Holy Light and Noble Sacrifice put nothing up.
  it('names the same spell in spell and buff on every row that has one', () => {
    for (const stage of STAGES) {
      if (stage.buff === undefined) {
        continue;
      }

      expect(BuffDebuffs[stage.buff]).toBe(Spells[stage.spell]);
    }
  });

  it('leaves the two instant spells without a buff, because the client publishes none', () => {
    const instant = STAGES.filter(
      (stage) => stage.spell === Spells.HolyLight || stage.spell === Spells.NobleSacrifice,
    );

    expect(instant).toHaveLength(2);

    for (const stage of instant) {
      expect(stage.buff).toBeUndefined();
    }
  });

  // Nothing a paladin casts here wants a cursor, and one opened by a run that never answers it breaks
  // every action after it
  it('wants a target cursor for nothing', () => {
    for (const stage of STAGES) {
      expect(stage.target).toBeUndefined();
    }
  });

  // The shard's own minimum for each spell, which a band that opened below would train nothing but
  // refusals against. The bound before each row is where that row starts.
  it('opens every band above the shard s minimum for its spell', () => {
    const minimum = new Map<Spells, number>([
      [Spells.ConsecrateWeapon, 150],
      [Spells.DivineFury, 250],
      [Spells.EnemyOfOne, 450],
      [Spells.HolyLight, 550],
      [Spells.NobleSacrifice, 650],
    ]);

    const plan = createPlan(STAGES);

    plan.stages.forEach((stage, index) => {
      const opensAt = index === 0 ? 400 : plan.stages[index - 1].upTo;

      expect(opensAt).toBeGreaterThanOrEqual(minimum.get(stage.spell) ?? 0);
    });
  });
});

describe('stageNow', () => {
  it('works the bands the table was written for', () => {
    const { stageNow } = createPlan(STAGES);

    expect(stageNow(400)?.spell).toBe(Spells.ConsecrateWeapon);
    expect(stageNow(450)?.spell).toBe(Spells.DivineFury);
    expect(stageNow(600)?.spell).toBe(Spells.EnemyOfOne);
    expect(stageNow(700)?.spell).toBe(Spells.HolyLight);
    expect(stageNow(900)?.spell).toBe(Spells.NobleSacrifice);
  });

  it('is finished at 120.0', () => {
    expect(createPlan(STAGES).stageNow(1200)).toBeUndefined();
  });
});
