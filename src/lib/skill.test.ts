import { beforeEach, describe, expect, it } from 'vitest';
import { installGlobals, skill as skillFixture, type FakeWorld } from '../test-support/uo.js';
import { createSkillReader, tenths } from './skill.js';

let world: FakeWorld;

const reader = () =>
  createSkillReader({
    skill: Skills.Bushido,
    label: 'Bushido',
    timeoutMs: 1000,
    pollMs: 500,
  });

beforeEach(() => {
  world = installGlobals();
});

describe('tenths', () => {
  it('reads the client s integer as a person does', () => {
    expect(tenths(746)).toBe('74.6');
    expect(tenths(1050)).toBe('105.0');
    expect(tenths(0)).toBe('0.0');
  });
});

describe('value', () => {
  it('is the value the client reports', () => {
    world.player.getSkill.mockReturnValue(skillFixture({ value: 746 }));

    expect(reader().value()).toBe(746);
  });

  // Never coerced to 0: 0 is a real skill value, and reading a blind client as 0 would train the
  // first band's ability at a character who has capped the skill
  it('passes a client that has not been told through as nothing, not as 0', () => {
    expect(reader().value()).toBeUndefined();
  });

  it('reads the skill it was built for', () => {
    reader().value();

    expect(world.player.getSkill).toHaveBeenCalledWith(Skills.Bushido);
  });
});

describe('name', () => {
  it('prefers the shard s own name for the skill', () => {
    world.player.getSkill.mockReturnValue(skillFixture({ value: 500, name: 'Bushido' }));

    expect(reader().name()).toBe('Bushido');
  });

  it('falls back on the configured label before the skill list arrives', () => {
    expect(reader().name()).toBe('Bushido');
  });
});

describe('cap', () => {
  it('is what the shard says the skill can reach', () => {
    world.player.getSkill.mockReturnValue(skillFixture({ value: 500, cap: 1000 }));

    expect(reader().cap()).toBe(1000);
  });
});

describe('waitForSkill', () => {
  it('returns at once when the list has already arrived', () => {
    world.player.getSkill.mockReturnValue(skillFixture({ value: 500 }));

    expect(reader().waitForSkill()).toBe(500);
    expect(world.sleep).not.toHaveBeenCalled();
  });

  it('waits for a list that arrives late', () => {
    let asked = 0;
    world.player.getSkill.mockImplementation(() =>
      ++asked < 3 ? undefined : skillFixture({ value: 500 }),
    );

    expect(reader().waitForSkill()).toBe(500);
  });

  it('gives up rather than hanging when the client never answers', () => {
    expect(reader().waitForSkill()).toBeUndefined();
  });
});
