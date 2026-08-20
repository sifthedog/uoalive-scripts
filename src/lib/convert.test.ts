import { beforeEach, describe, expect, it, vi } from 'vitest';

import { installGlobals, item, type FakeWorld } from '../test-support/uo.js';
import { createConverter, type Converter } from './convert.js';

// The engine behind smelting and board-making. What is pinned here is what it counts against a hue:
// a frozen shard answers a conversion the same way an unworkable material does, and reading one as
// the other wrote off 3 hues and ended a live mining run overweight next to a working beetle.

let world: FakeWorld;

const ORE = new Set([0x19b7]);
const INGOT = new Set([0x1bef]);

const stack = (hue: number) => item({ serial: 1, graphic: 0x19b7, hue, amount: 4 });

const make = (
  overrides: Partial<Parameters<typeof createConverter>[0]> = {},
): Converter & { perform: ReturnType<typeof vi.fn> } => {
  const perform = vi.fn(() => true);

  const converter = createConverter({
    label: 'smelt',
    leftAs: 'leaving it as ore',
    attempts: 3,
    timeoutMs: 2,
    pollMs: 1,
    delayMs: 0,
    maxPasses: 20,
    unskilledText: ['You are not skilled enough'],
    throttledText: ['You must wait'],
    isSaving: () => false,
    nextStack: (writtenOff) => (writtenOff.has(2413) ? undefined : stack(2413)),
    perform,
    known: () => [ORE, INGOT],
    learn: (graphic) => INGOT.add(graphic),
    learned: 'ingot graphic',
    ...overrides,
  });

  return Object.assign(converter, { perform });
};

const said = (fragment: string): boolean =>
  world.log.mock.calls.some((call) => String(call[0]).includes(fragment));

beforeEach(() => {
  world = installGlobals();
});

describe('createConverter', () => {
  it('writes a hue off once it has failed silently enough times', () => {
    const converter = make();

    converter.run();

    expect(converter.writtenOff.has(2413)).toBe(true);
    expect(said('hue 2413 failed 3 times, leaving it as ore')).toBe(true);
  });

  it('leaves the pass to the caller when a save is already up', () => {
    const converter = make({ isSaving: () => true });

    expect(converter.run()).toBe(false);
    expect(converter.perform).not.toHaveBeenCalled();
    expect(said('smelt: the world is saving, leaving it for now')).toBe(true);
  });

  // The failure the log opened with: the beetle's cursor never came, and the run counted the frozen
  // shard against the ore. Clean at the top of the pass and frozen by the time the attempt is
  // judged, which is the window `perform`'s journal.clear() opens.
  describe('a save that starts mid-attempt', () => {
    const savesAfterTheFirstLook = () => {
      let looks = 0;

      return () => looks++ > 0;
    };

    it('does not count a cursor that never opened', () => {
      const converter = make({
        isSaving: savesAfterTheFirstLook(),
        perform: vi.fn(() => false),
      });

      converter.run();

      expect(converter.writtenOff.has(2413)).toBe(false);
      expect(said('the world is saving, not counting it against hue 2413')).toBe(true);
    });

    it('does not count an attempt the pack diff never answered', () => {
      const converter = make({ isSaving: savesAfterTheFirstLook() });

      converter.run();

      expect(converter.writtenOff.has(2413)).toBe(false);
      expect(said('the world is saving, not counting it against hue 2413')).toBe(true);
    });

    // Ahead of both wordings, because a frozen shard's verdict on the material is worthless - and
    // unskilled is the one no amount of retrying takes back
    it('is asked before the unskilled wording', () => {
      world.journal.containsText.mockImplementation((text: string) =>
        text.includes('skilled enough'),
      );

      const converter = make({ isSaving: savesAfterTheFirstLook() });

      converter.run();

      expect(converter.writtenOff.has(2413)).toBe(false);
      expect(said('not skilled enough for hue 2413')).toBe(false);
    });
  });

  describe('the retry', () => {
    it('reopens the hues given up on', () => {
      const converter = make();

      converter.run();

      expect(converter.retry()).toBe(true);
      expect(converter.writtenOff.size).toBe(0);
      expect(said('giving 1 hue(s) written off earlier another go')).toBe(true);
    });

    // Granted twice over it answers true again every cycle, which in mining is hours of 'smelting'
    // phases before the stall watchdog ends the run
    it('is spent once until something converts', () => {
      const converter = make();

      converter.run();
      converter.retry();
      converter.run();

      expect(converter.retry()).toBe(false);
    });
  });
});
