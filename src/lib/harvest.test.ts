import { beforeEach, describe, expect, it, vi } from 'vitest';

import { installGlobals, type FakeWorld } from '../test-support/uo.js';
import { runHarvest, type HarvestOptions, type HarvestTimings } from './harvest.js';
import type { StallWatch } from './loop.js';

// The loop the three harvesters share. They used to be entry points that ran on import and so had no
// tests at all; what is pinned here is the arithmetic of the endings, which is where every counter
// that stops a run either works or quietly does not.

let world: FakeWorld;

const TIMINGS: HarvestTimings = {
  stepDelay: 1,
  maxCycles: 20,
  maxUnknown: 5,
  maxThrottled: 4,
  maxNoCursor: 6,
  maxNoTool: 3,
  logEvery: 25,
  throttleBackoff: 1,
  throttleBackoffMax: 1,
};

// Counts what the loop asked of it, so a test can read the watchdog rather than the log
const watcher = (): StallWatch & { ended: string[]; progress: number } => {
  const state = {
    ended: [] as string[],
    progress: 0,
    endCycle: (phase: string) => {
      state.ended.push(phase);
    },
    progressed: () => {
      state.progress++;
    },
    reason: () => undefined,
  };

  return state;
};

let stall: ReturnType<typeof watcher>;

// A swing that answers with each of the given outcomes in turn, and with the last one for ever after
const swings = (...outcomes: (string | undefined)[]) => {
  let at = 0;

  return () => outcomes[Math.min(at++, outcomes.length - 1)];
};

const run = (overrides: Partial<HarvestOptions<string>> = {}): void =>
  runHarvest<string>({
    prefix: 'test',
    landed: 'dug',
    toolName: 'pickaxe',
    stopReason: () => undefined,
    equipTool: () => true,
    harvest: () => 'dug',
    handle: () => ({}),
    progress: (tally) => `${tally} swings`,
    isSaving: () => false,
    waitOutSave: vi.fn(),
    stall,
    timings: TIMINGS,
    ...overrides,
  });

const ending = (): string => {
  const calls = world.exit.mock.calls;

  return String(calls[calls.length - 1]?.[0]);
};

const said = (fragment: string): boolean =>
  world.log.mock.calls.some((call) => String(call[0]).includes(fragment));

beforeEach(() => {
  world = installGlobals();
  stall = watcher();
});

describe('runHarvest', () => {
  it('runs to the cycle backstop when nothing ever stops it', () => {
    const harvest = vi.fn(() => 'dug');

    run({ harvest });

    expect(harvest).toHaveBeenCalledTimes(TIMINGS.maxCycles);
    expect(ending()).toContain(`hit the ${TIMINGS.maxCycles} working cycle backstop`);
  });

  it('names the tool it could not equip', () => {
    run({ equipTool: () => false });

    expect(ending()).toContain('no pickaxe');
  });

  // The tool search reads the pack, and packContents answers undefined for a read that threw
  it('looks for the tool again before giving up on it', () => {
    const equipTool = vi.fn(() => false);

    run({ equipTool });

    expect(equipTool).toHaveBeenCalledTimes(TIMINGS.maxNoTool);
  });

  it('carries on when the tool turns up again inside the budget', () => {
    const found = swings(...Array(TIMINGS.maxNoTool - 1).fill(''), 'here');
    const harvest = vi.fn(() => 'dug');

    run({ equipTool: () => found() === 'here', harvest });

    expect(harvest).toHaveBeenCalled();
    expect(ending()).not.toContain('no pickaxe');
  });

  // A watcher polling an empty field used to spend the whole backstop standing still
  it('does not spend the backstop on cycles that only waited', () => {
    const harvest = vi.fn(() => 'dug');
    let waits = 0;

    run({
      approach: () => (waits++ < TIMINGS.maxCycles * 3 ? { waited: true } : { target: 'tile' }),
      harvest,
    });

    expect(harvest).toHaveBeenCalledTimes(TIMINGS.maxCycles);
  });

  it('says why it stopped when a client call throws', () => {
    run({
      harvest: () => {
        throw new Error('Unexpected end of JSON input');
      },
    });

    expect(ending()).toContain('threw - Error: Unexpected end of JSON input');
    expect(said('test: stopping - threw')).toBe(true);
  });

  it('stops on the guards before it swings', () => {
    const harvest = vi.fn(() => 'dug');

    run({ stopReason: () => 'you are dead', harvest });

    expect(harvest).not.toHaveBeenCalled();
    expect(ending()).toContain('you are dead');
  });

  // Mining's dismount: a step rather than a precondition, so it is asked every cycle
  it('stops when the cycle cannot be made ready', () => {
    run({ ready: () => 'could not get off the mount' });

    expect(ending()).toContain('could not get off the mount');
  });

  it('hands the stop reason to the log as well as to exit', () => {
    run({ equipTool: () => false });

    expect(said('test: stopping - no pickaxe')).toBe(true);
  });

  describe('the swing that lands', () => {
    it('counts it, tells the watchdog, and lets the script settle its produce', () => {
      const onLanded = vi.fn();

      run({ harvest: swings('dug', 'empty'), onLanded, handle: () => ({ stop: 'worked out' }) });

      expect(onLanded).toHaveBeenCalledTimes(1);
      expect(stall.progress).toBe(1);
    });

    it('reports every logEvery swings and not on the count alone', () => {
      run({ timings: { ...TIMINGS, logEvery: 3, maxCycles: 7 } });

      expect(world.log.mock.calls.filter((call) => String(call[0]).includes('swings')).length).toBe(
        2,
      );
    });
  });

  describe('the outcomes the script owns', () => {
    it('carries on when the handler recognised it', () => {
      const handle = vi.fn(() => ({}));

      run({ harvest: () => 'empty', handle, timings: { ...TIMINGS, maxCycles: 3 } });

      expect(handle).toHaveBeenCalledTimes(3);
      expect(ending()).toContain('cycle backstop');
    });

    it('ends the run when the handler asks for it', () => {
      run({ harvest: () => 'empty', handle: () => ({ stop: 'the spot is worked out' }) });

      expect(ending()).toContain('the spot is worked out');
    });

    // The handler answering with nothing is the one signal that a bucket is missing from
    // OUTCOME_TEXT, so it has to spend the unreadable budget rather than pass quietly
    it('counts one it does not recognise as unreadable', () => {
      run({ harvest: () => 'somethingElse', handle: () => undefined });

      expect(ending()).toContain(`${TIMINGS.maxUnknown} unreadable outcomes in a row`);
    });

    it('counts a swing that answered with nothing at all as unreadable', () => {
      run({ harvest: () => undefined });

      expect(ending()).toContain(`${TIMINGS.maxUnknown} unreadable outcomes in a row`);
      expect(said('check OUTCOME_TEXT')).toBe(true);
    });

    // A refusal is a read outcome, so it clears the unreadable count: left standing, a shard
    // alternating refusals with silence ends a run on maxUnknown without ever producing five
    // unreadable cycles in a row
    it('does not end on unreadable outcomes that were never in a row', () => {
      run({ harvest: swings(undefined, 'throttled', undefined, 'throttled', undefined, 'dug') });

      expect(ending()).toContain('cycle backstop');
    });
  });

  describe('the shard refusing', () => {
    it('gives up after maxThrottled refusals', () => {
      run({ harvest: () => 'throttled' });

      expect(ending()).toContain('the shard kept refusing the swing');
      expect(said(`(${TIMINGS.maxThrottled}/${TIMINGS.maxThrottled})`)).toBe(true);
    });

    it('gives up after maxNoCursor swings that never got a cursor', () => {
      run({ harvest: () => 'noCursor' });

      expect(ending()).toContain('the shard never opened a target cursor');
    });

    // Counted apart from the unreadable budget, because a refusal is not an outcome the script
    // failed to read - sharing it ended a live run in fifteen seconds with a tool plainly in hand
    it('spends a budget of its own rather than the unreadable one', () => {
      run({ harvest: () => 'noCursor', timings: { ...TIMINGS, maxUnknown: 2, maxNoCursor: 6 } });

      expect(ending()).toContain('never opened a target cursor');
    });

    // Two short streaks either side of a swing that landed. On a budget of three they only reach the
    // cap if the count was never cleared.
    it('forgets the streak as soon as any other outcome arrives', () => {
      run({
        harvest: swings('noCursor', 'noCursor', 'dug', 'noCursor', 'noCursor', 'dug'),
        timings: { ...TIMINGS, maxNoCursor: 3 },
      });

      expect(ending()).toContain('cycle backstop');
    });
  });

  // A world save is a pause, not a failure: counting it would walk a run to its stop a save at a time
  it('waits out a save without holding it against the run', () => {
    const waitOutSave = vi.fn();

    run({ harvest: swings('throttled', 'saving', 'dug'), waitOutSave });

    expect(waitOutSave).toHaveBeenCalledTimes(1);
    expect(stall.progress).toBeGreaterThan(0);
    expect(ending()).toContain('cycle backstop');
  });

  // The swing has always had a `saving` outcome; everything before it in a cycle had none, and a save
  // landing in the smelt ended a live mining run overweight next to a working beetle
  describe('a save that lands before the swing', () => {
    const saveFor = (cycles: number) => {
      let left = cycles;

      return () => left-- > 0;
    };

    it('waits it out and lets nothing else in the cycle run', () => {
      const waitOutSave = vi.fn();
      const relieve = vi.fn(() => undefined);
      const approach = vi.fn(() => ({ target: 'vein' }) as const);
      const harvest = vi.fn(() => 'dug');

      run({
        isSaving: saveFor(2),
        waitOutSave,
        relieve,
        approach,
        harvest,
        timings: { ...TIMINGS, maxCycles: 3 },
      });

      expect(waitOutSave).toHaveBeenCalledTimes(2);
      expect(relieve).toHaveBeenCalledTimes(1);
      expect(approach).toHaveBeenCalledTimes(1);
      expect(harvest).toHaveBeenCalledTimes(1);
    });

    // The counters were measured against a server that was not answering, and the watchdog would
    // otherwise walk a run to its stop a save at a time
    it('holds none of it against the run', () => {
      const waitOutSave = vi.fn();

      run({ isSaving: saveFor(5), waitOutSave, timings: { ...TIMINGS, maxCycles: 5 } });

      expect(waitOutSave).toHaveBeenCalledTimes(5);
      expect(stall.progress).toBe(5);
      expect(stall.ended).toEqual(Array(5).fill('saving'));
      expect(ending()).toContain('cycle backstop');
    });

    it('resumes the swing once the shard answers again', () => {
      const harvest = vi.fn(() => 'dug');

      run({ isSaving: saveFor(1), harvest, timings: { ...TIMINGS, maxCycles: 3 } });

      expect(harvest).toHaveBeenCalledTimes(2);
    });
  });

  it('swaps a tool the shard says wore out', () => {
    run({ harvest: swings('wornOut', 'dug') });

    expect(said('pickaxe worn out, swapping')).toBe(true);
  });

  describe('the cycle spent making room', () => {
    it('closes it on its own phase and never swings', () => {
      const harvest = vi.fn(() => 'dug');

      run({
        relieve: () => ({ phase: 'smelting' }),
        harvest,
        timings: { ...TIMINGS, maxCycles: 2 },
      });

      expect(harvest).not.toHaveBeenCalled();
      expect(stall.ended).toEqual(['smelting', 'smelting']);
    });

    it('ends the run when making room freed nothing', () => {
      run({ relieve: () => ({ stop: 'overweight and smelting freed nothing' }) });

      expect(ending()).toContain('smelting freed nothing');
    });

    it('carries on to the swing when there is nothing to make room for', () => {
      const harvest = vi.fn(() => 'dug');

      run({ relieve: () => undefined, harvest, timings: { ...TIMINGS, maxCycles: 1 } });

      expect(harvest).toHaveBeenCalledTimes(1);
    });
  });

  describe('the approach', () => {
    it('swings at what it found', () => {
      const harvest = vi.fn(() => 'dug');

      run({
        approach: () => ({ target: 'a vein' }),
        harvest,
        timings: { ...TIMINGS, maxCycles: 1 },
      });

      expect(harvest).toHaveBeenCalledWith('a vein');
    });

    it('hands the target to the outcome handler too', () => {
      const handle = vi.fn(() => ({ stop: 'done' }));

      run({ approach: () => ({ target: 'a vein' }), harvest: () => 'empty', handle });

      expect(handle).toHaveBeenCalledWith('empty', 'a vein');
    });

    it('spends a cycle walking, and says so to the watchdog', () => {
      const harvest = vi.fn(() => 'dug');

      run({ approach: () => ({ walked: true }), harvest, timings: { ...TIMINGS, maxCycles: 2 } });

      expect(harvest).not.toHaveBeenCalled();
      expect(stall.ended).toEqual(['walking', 'walking']);
    });

    // Waiting for a resource to come back is the script working, not stuck, so it walks the run
    // neither toward its stall stop nor toward its backstop - only a guard ends a waiting run
    it('leaves the watchdog and the backstop alone while it waits for a respawn', () => {
      let waits = 0;

      run({
        approach: () => ({ waited: true }),
        stopReason: () => (waits++ > TIMINGS.maxCycles * 3 ? 'you are dead' : undefined),
        timings: { ...TIMINGS, maxCycles: 3 },
      });

      expect(stall.ended).toEqual([]);
      expect(ending()).toContain('you are dead');
    });

    // Frozen rather than cleared without this, so a run that idled at 299 cycles without a swing
    // stopped on 'no progress in 300' the moment it came back to a forest that had regrown
    it('clears the watchdog count as it waits', () => {
      let waits = 0;

      run({
        approach: () => ({ waited: true }),
        stopReason: () => (waits++ > 2 ? 'you are dead' : undefined),
        timings: { ...TIMINGS, maxCycles: 3 },
      });

      expect(stall.progress).toBe(3);
    });

    it('ends the run when there is nothing left to approach', () => {
      run({ approach: () => ({ stop: 'no ore in range' }) });

      expect(ending()).toContain('no ore in range');
    });
  });

  describe('the ending', () => {
    it('gives the script its last word, with the tally and the reason', () => {
      const finish = vi.fn();

      run({ harvest: swings('dug', 'empty'), handle: () => ({ stop: 'worked out' }), finish });

      expect(finish).toHaveBeenCalledWith(1, 'worked out');
    });

    it('says the last word before the stop reason', () => {
      run({
        equipTool: () => false,
        finish: () => {
          log('test: 0 swings, 3 ore still in the pack');
        },
      });

      const lines = world.log.mock.calls.map((call) => String(call[0]));

      expect(lines.indexOf('test: 0 swings, 3 ore still in the pack')).toBeLessThan(
        lines.indexOf('test: stopping - no pickaxe'),
      );
    });

    // The watchdog's own reason is a stop like any other, and reading it only at the top of the next
    // cycle would let a run take one more swing after it had given up
    it('stops on the watchdog', () => {
      stall.reason = () => 'no progress in 300 cycles';

      run({ timings: { ...TIMINGS, maxCycles: 10 } });

      expect(ending()).toContain('no progress in 300 cycles');
    });
  });
});
