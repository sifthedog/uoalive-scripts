import { beforeEach, describe, expect, it } from 'vitest';
import { installGlobals, type FakeWorld } from '../test-support/uo.js';
import { hitsCeiling, manaCeiling } from './vitals.js';

let world: FakeWorld;

beforeEach(() => {
  world = installGlobals();
});

describe('manaCeiling', () => {
  it('is the pool the client reports', () => {
    world.player.maxMana = 120;

    expect(manaCeiling()).toBe(120);
  });

  // A ceiling of 0 makes "wait until the pool is full" true the instant it is asked, so a trainer
  // built on the raw read meditates for no time at all and then casts with no mana, forever.
  it('refuses a maximum of 0, which is a client that has not been told yet', () => {
    world.player.maxMana = 0;

    expect(manaCeiling()).toBeUndefined();
  });
});

describe('hitsCeiling', () => {
  it('is the health the client reports', () => {
    world.player.maxHits = 95;

    expect(hitsCeiling()).toBe(95);
  });

  // A health floor measured against 0 is every character at once, and the guard built on it would
  // either never fire or fire on cycle zero
  it('refuses a maximum of 0, which is a client that has not been told yet', () => {
    world.player.maxHits = 0;

    expect(hitsCeiling()).toBeUndefined();
  });
});
