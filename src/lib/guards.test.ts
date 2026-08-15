import { beforeEach, describe, expect, it } from 'vitest';

import { installGlobals, item } from '../test-support/uo.js';
import { dead, firstReason, heavy, hurt, packFull } from './guards.js';

beforeEach(() => {
  installGlobals();
});

describe('the individual checks', () => {
  it('stops a dead character', () => {
    installGlobals({ player: { isDead: true } });

    expect(dead()).toBe('you are dead');
  });

  it('stops a buffer short of the real weight cap', () => {
    installGlobals({ player: { weight: 370, weightMax: 400 } });

    expect(heavy(40)()).toBe('overweight (370/400)');
    expect(heavy(0)()).toBeUndefined();
  });

  it('stops a character who has been hurt past the floor', () => {
    installGlobals({ player: { hits: 40, maxHits: 100 } });

    expect(hurt(0.5)()).toBe('hurt (40/100)');
    expect(hurt(0.25)()).toBeUndefined();
  });

  // The stat-refresh fault again: a maximum of 0 makes the floor 0, and every reading of it is a lie
  // in one direction or the other
  it('says nothing about health while the client is refreshing stats', () => {
    installGlobals({ player: { hits: 0, maxHits: 0 } });

    expect(hurt(0.5)()).toBeUndefined();
  });

  it('stops once the top level of the pack is full', () => {
    installGlobals({
      backpack: Array.from({ length: 5 }, (_, index) => item({ serial: index, graphic: 0x1bdd })),
    });

    expect(packFull(5)()).toBe('pack is full (5 items at the top level)');
    expect(packFull(6)()).toBeUndefined();
  });
});

describe('firstReason', () => {
  // Order is the caller's, and it matters: death comes first everywhere, so a corpse is never
  // reported as merely overweight
  it('reports the first check that has something to say', () => {
    installGlobals({ player: { isDead: true, weight: 999, weightMax: 400 } });

    expect(firstReason(dead, heavy(40))).toBe('you are dead');
    expect(firstReason(heavy(40), dead)).toBe('overweight (999/400)');
  });

  it('finds no reason to stop in the ordinary case', () => {
    expect(firstReason(dead, heavy(40), packFull(120))).toBeUndefined();
  });

  it('has nothing to say when asked nothing', () => {
    expect(firstReason()).toBeUndefined();
  });
});
