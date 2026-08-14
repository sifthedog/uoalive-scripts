import { beforeEach, describe, expect, it } from 'vitest';

import { installGlobals, item } from '../test-support/uo.js';
import { INGOT_GRAPHICS } from './config.js';
import { ingotTotal, isIngot } from './ingots.js';

beforeEach(() => {
  installGlobals();
});

describe('isIngot', () => {
  // An ingot stack changes graphic with its size the way ore piles do, so it is a set, not one id
  it('matches every graphic an ingot stack takes as it grows', () => {
    for (const graphic of INGOT_GRAPHICS) {
      expect(isIngot(item({ serial: 1, graphic, hue: 0 }))).toBe(true);
    }
  });

  it('treats a missing hue as the iron hue', () => {
    expect(isIngot(item({ serial: 1, graphic: 0x1bef }))).toBe(true);
  });

  // Hue is part of the match here, unlike logs: dull copper spends differently, and the iron-only
  // count must not include it
  it('rejects a coloured ingot', () => {
    expect(isIngot(item({ serial: 1, graphic: 0x1bef, hue: 0x973 }))).toBe(false);
  });

  it('rejects a non-ingot', () => {
    expect(isIngot(item({ serial: 1, graphic: 0x1bdd, hue: 0 }))).toBe(false);
  });
});

describe('ingotTotal', () => {
  it('sums the amounts of every iron stack', () => {
    expect(
      ingotTotal([
        item({ serial: 1, graphic: 0x1bef, amount: 40 }),
        item({ serial: 2, graphic: 0x1bf2, amount: 60 }),
      ]),
    ).toBe(100);
  });

  it('ignores coloured ingots in the same pack', () => {
    expect(
      ingotTotal([
        item({ serial: 1, graphic: 0x1bef, amount: 40, hue: 0 }),
        item({ serial: 2, graphic: 0x1bef, amount: 60, hue: 0x973 }),
      ]),
    ).toBe(40);
  });

  // The shard spends resources out of sub-containers, so the count has to look there too
  it('counts ingots inside a bag', () => {
    expect(
      ingotTotal([
        item({ serial: 1, graphic: 0x1bef, amount: 40 }),
        item({
          serial: 2,
          graphic: 0x0e76,
          contents: [item({ serial: 3, graphic: 0x1bef, amount: 25 })],
        }),
      ]),
    ).toBe(65);
  });

  it('reads the backpack when given no contents', () => {
    installGlobals({ backpack: [item({ serial: 1, graphic: 0x1bef, amount: 12 })] });

    expect(ingotTotal()).toBe(12);
  });

  it('terminates on an unopened container', () => {
    expect(ingotTotal(undefined)).toBe(0);
  });
});
