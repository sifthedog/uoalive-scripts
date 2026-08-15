import { beforeEach, describe, expect, it } from 'vitest';
import { createPlan } from '../lib/stages.js';
import { installGlobals } from '../test-support/uo.js';
import { STAGES } from './config.js';

// The shipped Necromancy table, as opposed to src/lib/stages.test.ts which is about the mechanism

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

  // A row whose buff belongs to a different spell would gate the wrong thing: the run would skip
  // casts because something else was standing. Only asserted of the rows that carry one.
  it('names the same spell in spell and buff on every row that has one', () => {
    for (const stage of STAGES) {
      if (stage.buff === undefined) {
        continue;
      }

      expect(BuffDebuffs[stage.buff]).toBe(Spells[stage.spell]);
    }
  });

  it('leaves Wither without a buff, because the client publishes none for it', () => {
    const wither = STAGES.find((stage) => stage.spell === Spells.Wither);

    expect(wither?.buff).toBeUndefined();
  });

  // A cursor opened by a run that never answers it breaks every action after it, so the rows that
  // want one say so and the rest are cast at nobody
  it('asks for a cursor on Pain Spike alone, and points it at the character', () => {
    for (const stage of STAGES) {
      expect(stage.target).toBe(stage.spell === Spells.PainSpike ? 'self' : undefined);
    }
  });
});

describe('stageNow', () => {
  it('works the bands the table was written for', () => {
    const { stageNow } = createPlan(STAGES);

    expect(stageNow(400)?.spell).toBe(Spells.PainSpike);
    expect(stageNow(500)?.spell).toBe(Spells.HorrificBeast);
    expect(stageNow(700)?.spell).toBe(Spells.Wither);
    expect(stageNow(900)?.spell).toBe(Spells.LichForm);
    expect(stageNow(1000)?.spell).toBe(Spells.VampiricEmbrace);
  });

  // Exclusive bounds, so a skill sitting exactly on one has finished that band
  it('is finished at 120.0', () => {
    expect(createPlan(STAGES).stageNow(1200)).toBeUndefined();
  });
});
