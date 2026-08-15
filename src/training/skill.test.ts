import { beforeEach, describe, expect, it } from 'vitest';
import { installGlobals, skill, type FakeWorld } from '../test-support/uo.js';
import { skillCap, skillName, skillValue, tenths, waitForSkill } from './skill.js';

let world: FakeWorld;

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

describe('skillValue', () => {
  it('is the value the client reports', () => {
    world.player.getSkill.mockReturnValue(skill({ value: 746 }));

    expect(skillValue()).toBe(746);
  });

  // Never coerced to 0: 0 is a real skill value, and reading a blind client as 0 would train the
  // first band's ability at a character who has capped the skill
  it('passes a client that has not been told through as nothing, not as 0', () => {
    expect(skillValue()).toBeUndefined();
  });
});

describe('skillName', () => {
  it('prefers the shard s own name for the skill', () => {
    world.player.getSkill.mockReturnValue(skill({ value: 500, name: 'Bushido' }));

    expect(skillName()).toBe('Bushido');
  });

  it('falls back on the configured label before the skill list arrives', () => {
    expect(skillName()).toBe('Bushido');
  });
});

describe('skillCap', () => {
  it('is what the shard says the skill can reach', () => {
    world.player.getSkill.mockReturnValue(skill({ value: 500, cap: 1000 }));

    expect(skillCap()).toBe(1000);
  });
});

describe('waitForSkill', () => {
  it('returns at once when the list has already arrived', () => {
    world.player.getSkill.mockReturnValue(skill({ value: 500 }));

    expect(waitForSkill()).toBe(500);
    expect(world.sleep).not.toHaveBeenCalled();
  });

  it('waits for a list that arrives late', () => {
    let asked = 0;
    world.player.getSkill.mockImplementation(() => (++asked < 3 ? undefined : skill({ value: 500 })));

    expect(waitForSkill()).toBe(500);
  });

  it('gives up rather than hanging when the client never answers', () => {
    expect(waitForSkill()).toBeUndefined();
  });
});
