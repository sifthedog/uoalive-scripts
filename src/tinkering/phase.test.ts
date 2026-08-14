import { beforeEach, describe, expect, it } from 'vitest';

import { installGlobals } from '../test-support/uo.js';
import { RING_FROM, STOP_AT } from './config.js';
import { currentPhase, skillBase, tenths } from './phase.js';

// Skills come back in tenths, so 95.0 is 950
const atSkill = (base: number, value = base) =>
  installGlobals({ player: { getSkill: () => ({ base, value }) } as never });

beforeEach(() => {
  installGlobals();
});

describe('tenths', () => {
  it('prints a skill in tenths', () => {
    expect(tenths(950)).toBe('95.0');
    expect(tenths(955)).toBe('95.5');
  });

  it('keeps one decimal place even at zero', () => {
    expect(tenths(0)).toBe('0.0');
  });
});

describe('skillBase', () => {
  it('reads the base skill', () => {
    atSkill(742);

    expect(skillBase()).toBe(742);
  });

  it('reads zero when the client knows no skill yet', () => {
    installGlobals({ player: { getSkill: () => undefined } as never });

    expect(skillBase()).toBe(0);
  });
});

describe('currentPhase', () => {
  it('starts on lockpicks', () => {
    atSkill(300);

    expect(currentPhase()).toBe('lockpicks');
  });

  it('switches to rings exactly at RING_FROM', () => {
    atSkill(RING_FROM - 1);
    expect(currentPhase()).toBe('lockpicks');

    atSkill(RING_FROM);
    expect(currentPhase()).toBe('rings');
  });

  it('finishes exactly at STOP_AT', () => {
    atSkill(STOP_AT - 1);
    expect(currentPhase()).toBe('rings');

    atSkill(STOP_AT);
    expect(currentPhase()).toBe('done');
  });

  // The whole reason it reads .base rather than .value: a +15 Tinkering ring inflates value, and
  // reading that would end the run early - then look like a skill drop when the ring falls off
  it('is not fooled into finishing early by a +Tinkering ring', () => {
    atSkill(STOP_AT - 50, STOP_AT + 100);

    expect(currentPhase()).toBe('rings');
  });

  it('does not read a ring falling off as a skill drop', () => {
    atSkill(RING_FROM + 10, RING_FROM + 10);

    expect(currentPhase()).toBe('rings');
  });
});
