import { beforeEach, describe, expect, it } from 'vitest';

import { installGlobals, item } from '../test-support/uo.js';
import { countsByGraphic, describeDiff, diffCounts, type Counts } from './pack.js';

const counts = (entries: Record<string, number>): Counts => new Map(Object.entries(entries));

beforeEach(() => {
  installGlobals();
});

describe('countsByGraphic', () => {
  it('keys by graphic and hue together', () => {
    const result = countsByGraphic([item({ serial: 1, graphic: 0x1bdd, hue: 0, amount: 3 })]);

    expect([...result]).toEqual([['0x1bdd/0', 3]]);
  });

  it('sums amounts across separate stacks of the same graphic and hue', () => {
    const result = countsByGraphic([
      item({ serial: 1, graphic: 0x1bdd, amount: 3 }),
      item({ serial: 2, graphic: 0x1bdd, amount: 7 }),
    ]);

    expect(result.get('0x1bdd/0')).toBe(10);
  });

  it('counts an item with no amount as one', () => {
    const result = countsByGraphic([item({ serial: 1, graphic: 0x0f3f })]);

    expect(result.get('0xf3f/0')).toBe(1);
  });

  // Unpadded, because toString(16) drops the leading zero. boards.ts reads the graphic back out of
  // this key with Number(), which parses '0xf3f' fine - but a padded key would not round-trip
  // through a naive parseInt, so the shape is worth pinning.
  it('writes the graphic as unpadded hex', () => {
    const result = countsByGraphic([item({ serial: 1, graphic: 0x0e76 })]);

    expect([...result.keys()]).toEqual(['0xe76/0']);
    expect(Number('0xe76')).toBe(0x0e76);
  });

  it('treats a missing hue as 0', () => {
    const result = countsByGraphic([item({ serial: 1, graphic: 0x1bdd, amount: 1 })]);

    expect(result.get('0x1bdd/0')).toBe(1);
  });

  // The whole reason the key is a pair: a recipe's coloured output shares its graphic with the
  // plain one, and hauling only gives up on the hue it failed to convert
  it('keeps the same graphic in two hues apart', () => {
    const result = countsByGraphic([
      item({ serial: 1, graphic: 0x1bdd, hue: 0, amount: 4 }),
      item({ serial: 2, graphic: 0x1bdd, hue: 0x4a8, amount: 6 }),
    ]);

    expect(result.get('0x1bdd/0')).toBe(4);
    expect(result.get('0x1bdd/1192')).toBe(6);
  });

  it('recurses into sub-containers', () => {
    const result = countsByGraphic([
      item({
        serial: 1,
        graphic: 0x0e76,
        contents: [
          item({ serial: 2, graphic: 0x1bdd, amount: 5 }),
          item({
            serial: 3,
            graphic: 0x0e79,
            contents: [item({ serial: 4, graphic: 0x1bdd, amount: 2 })],
          }),
        ],
      }),
    ]);

    expect(result.get('0x1bdd/0')).toBe(7);
    expect(result.get('0xe76/0')).toBe(1);
  });

  it('reads the backpack when given no contents', () => {
    installGlobals({ backpack: [item({ serial: 1, graphic: 0x1bdd, amount: 9 })] });

    expect(countsByGraphic().get('0x1bdd/0')).toBe(9);
  });

  it('is empty for an unopened container', () => {
    expect(countsByGraphic(undefined).size).toBe(0);
  });
});

describe('diffCounts', () => {
  it('reports a key that gained', () => {
    const changes = diffCounts(counts({ '0x1bdd/0': 2 }), counts({ '0x1bdd/0': 5 }));

    expect(changes).toEqual([{ key: '0x1bdd/0', delta: 3 }]);
  });

  it('reports a key that lost but is still present', () => {
    const changes = diffCounts(counts({ '0x1bdd/0': 5 }), counts({ '0x1bdd/0': 2 }));

    expect(changes).toEqual([{ key: '0x1bdd/0', delta: -3 }]);
  });

  it('reports a brand new key as its full amount', () => {
    const changes = diffCounts(counts({}), counts({ '0x1bd7/0': 4 }));

    expect(changes).toEqual([{ key: '0x1bd7/0', delta: 4 }]);
  });

  // A conversion consumes the whole stack, so the logs' key vanishes rather than dropping to zero
  it('reports a key missing from after as its negated total', () => {
    const changes = diffCounts(counts({ '0x1bdd/0': 6 }), counts({}));

    expect(changes).toEqual([{ key: '0x1bdd/0', delta: -6 }]);
  });

  it('omits keys that did not change', () => {
    const changes = diffCounts(
      counts({ '0x1bdd/0': 5, '0x0f3f/0': 1 }),
      counts({ '0x1bdd/0': 5, '0x0f3f/0': 1 }),
    );

    expect(changes).toEqual([]);
  });

  it('reports both sides of a conversion in one diff', () => {
    const changes = diffCounts(counts({ '0x1bdd/0': 10 }), counts({ '0x1bd7/0': 20 }));

    expect(changes).toEqual(
      expect.arrayContaining([
        { key: '0x1bd7/0', delta: 20 },
        { key: '0x1bdd/0', delta: -10 },
      ]),
    );
    expect(changes).toHaveLength(2);
  });
});

describe('describeDiff', () => {
  it('says so when nothing changed', () => {
    expect(describeDiff([])).toBe('no change');
  });

  it('signs gains and losses', () => {
    expect(
      describeDiff([
        { key: '0x1bd7/0', delta: 20 },
        { key: '0x1bdd/0', delta: -10 },
      ]),
    ).toBe('0x1bd7/0 +20, 0x1bdd/0 -10');
  });
});
