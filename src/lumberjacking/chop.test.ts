import { beforeEach, describe, expect, it } from 'vitest';

import { installGlobals, item } from '../test-support/uo.js';
import { ALL_OUTCOME_TEXT, isLog, logTotal, outcomeFor } from './chop.js';
import { LOG_GRAPHICS, OUTCOME_TEXT } from './config.js';

beforeEach(() => {
  installGlobals();
});

describe('outcomeFor', () => {
  // Table-driven off the config itself, so adding a phrase to OUTCOME_TEXT without wiring up its
  // category is caught here rather than showing up in game as an 'unknown' outcome
  for (const [name, phrases] of Object.entries(OUTCOME_TEXT)) {
    for (const phrase of phrases) {
      it(`maps '${phrase}' to ${name}`, () => {
        expect(outcomeFor(phrase)).toBe(name);
      });
    }
  }

  it('does not recognise a phrase from another shard', () => {
    expect(outcomeFor('You feel a strange sensation')).toBeUndefined();
  });

  // It is a whole-string lookup, not a substring one - waitForTextAny hands back one of the exact
  // strings it was given
  it('does not match a phrase that merely contains a known one', () => {
    expect(outcomeFor('You put some logs in your pack')).toBeUndefined();
  });
});

// Without a bucket of its own a world save reads as five unreadable outcomes in a row, which is the
// run's stop condition - the shard being busy for a moment should not end the afternoon
describe('the world save', () => {
  it('is an outcome of its own rather than an unreadable one', () => {
    expect(outcomeFor('The world is saving')).toBe('saving');
  });
});

describe('ALL_OUTCOME_TEXT', () => {
  it('is every phrase from every category, flattened', () => {
    expect(ALL_OUTCOME_TEXT).toEqual(Object.values(OUTCOME_TEXT).flat());
  });

  it('holds no duplicates, so a match is never ambiguous', () => {
    expect(new Set(ALL_OUTCOME_TEXT).size).toBe(ALL_OUTCOME_TEXT.length);
  });
});

describe('isLog', () => {
  it('matches every graphic a log stack takes as it grows', () => {
    for (const graphic of LOG_GRAPHICS) {
      expect(isLog(item({ serial: 1, graphic }))).toBe(true);
    }
  });

  // Deliberately hue-blind: special woods are hued and still have to be counted and hauled
  it('matches a hued special-wood log', () => {
    expect(isLog(item({ serial: 1, graphic: 0x1bdd, hue: 0x4a8 }))).toBe(true);
  });

  it('rejects a board', () => {
    expect(isLog(item({ serial: 1, graphic: 0x1bd7 }))).toBe(false);
  });
});

describe('logTotal', () => {
  it('sums the amounts of every log stack', () => {
    expect(
      logTotal([
        item({ serial: 1, graphic: 0x1bdd, amount: 12 }),
        item({ serial: 2, graphic: 0x1be0, amount: 8 }),
      ]),
    ).toBe(20);
  });

  it('counts a stack with no amount as one', () => {
    expect(logTotal([item({ serial: 1, graphic: 0x1bdd })])).toBe(1);
  });

  it('ignores everything that is not a log', () => {
    expect(
      logTotal([
        item({ serial: 1, graphic: 0x1bdd, amount: 5 }),
        item({ serial: 2, graphic: 0x1bd7, amount: 99 }),
      ]),
    ).toBe(5);
  });

  it('finds logs inside a bag', () => {
    expect(
      logTotal([
        item({ serial: 1, graphic: 0x1bdd, amount: 5 }),
        item({
          serial: 2,
          graphic: 0x0e76,
          contents: [item({ serial: 3, graphic: 0x1bdd, amount: 7 })],
        }),
      ]),
    ).toBe(12);
  });

  it('reads the backpack when given no contents', () => {
    installGlobals({ backpack: [item({ serial: 1, graphic: 0x1bdd, amount: 4 })] });

    expect(logTotal()).toBe(4);
  });

  // A plain item has no `contents`, and recursing through the defaulted parameter would restart at
  // the backpack forever
  it('terminates on an unopened container', () => {
    expect(logTotal(undefined)).toBe(0);
  });
});
