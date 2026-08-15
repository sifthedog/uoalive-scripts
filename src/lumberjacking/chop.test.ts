import { beforeEach, describe, expect, it, vi } from 'vitest';

import { installGlobals, item, type FakeWorld } from '../test-support/uo.js';
import { ALL_OUTCOME_TEXT, chopOnce, isLog, logTotal, outcomeFor } from './chop.js';
import { LOG_GRAPHICS, OUTCOME_TEXT } from './config.js';
import type { Tree } from './tree.js';

const AXE = 1;
const TREE: Tree = { x: 100, y: 101, z: 0, graphic: 0x0ce0, distance: 1 };

let world: FakeWorld;

beforeEach(() => {
  world = installGlobals();
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

// Not the same as nothing having happened: the shard usually refused the swing and said why.
// Reaching noCursor instead of the throttle or the save ended a live mining run in fifteen seconds.
describe('chopOnce, when no cursor opens', () => {
  beforeEach(() => {
    world.target.wait.mockReturnValue(false);

    // An axe that still resolves, so the silent read below is about the chop rather than the tool
    world.client.findObject.mockReturnValue(item({ serial: AXE, graphic: 0x0f43 }));
  });

  it('reads the refusal the shard already worded', () => {
    world.journal.waitForTextAny.mockReturnValue('You must wait');

    expect(chopOnce(TREE, AXE)).toBe('throttled');
  });

  it('knows a world save for what it is here too', () => {
    world.journal.waitForTextAny.mockReturnValue('The world is saving');

    expect(chopOnce(TREE, AXE)).toBe('saving');
  });

  // The swing that breaks the axe leaves the next one with an empty hand, which is a swing no cursor
  // opens for - so the loop swaps rather than backing off against an empty hand.
  it('reads an axe serial that stopped resolving as a worn out tool', () => {
    world.client.findObject.mockReturnValue(undefined);

    expect(chopOnce(TREE, AXE)).toBe('wornOut');
  });

  it('reads logs arriving in the pack as a chop that landed anyway', () => {
    const logs = (amount: number) => item({ serial: 50, graphic: 0x1bdd, amount });
    const packs = [[logs(3)], [logs(4)]];
    let swung = 0;

    Object.defineProperty(world.player, 'backpack', {
      configurable: true,
      get: () => ({ serial: 0x40000000, contents: packs[Math.min(swung, 1)] }),
    });

    world.player.useItemInHand.mockImplementation(() => {
      swung = 1;
    });

    expect(chopOnce(TREE, AXE)).toBe('chopped');
  });

  it('reports a cursor that never opened when nothing explains it', () => {
    expect(chopOnce(TREE, AXE)).toBe('noCursor');
  });

  // The old line guessed at an empty hand and was wrong about it on the run that found this
  it('says what is in the hand rather than guessing at it', () => {
    world.player.equippedItems.twoHanded = item({ serial: AXE, graphic: 0x0f43, name: 'axe' });

    chopOnce(TREE, AXE);

    expect(world.log).toHaveBeenCalledWith(expect.stringContaining("0xf43 'axe'"));
  });

  // Nothing was aimed at, so nothing should have been: the tile is named only once a cursor is up
  it('never names the tree', () => {
    chopOnce(TREE, AXE);

    expect(world.target.terrain).not.toHaveBeenCalled();
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
