import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { installGlobals, type FakeWorld } from '../test-support/uo.js';
import { createHeartbeat } from './heartbeat.js';
import { backoffFor, createIdleWait, createStallWatch, minutesLeft } from './loop.js';

let world: FakeWorld;

const quiet = () => createHeartbeat({ prefix: 'test', noun: 'things', everyMs: Infinity });

beforeEach(() => {
  world = installGlobals();
  vi.useFakeTimers();
  vi.setSystemTime(new Date(0));
});

afterEach(() => {
  vi.useRealTimers();
});

describe('backoffFor', () => {
  // A fixed retry shorter than the shard's own timer re-arms the throttle it is waiting out
  it('grows with the count and then stops at the cap', () => {
    expect(backoffFor(1, 1000, 8000)).toBe(1000);
    expect(backoffFor(3, 1000, 8000)).toBe(3000);
    expect(backoffFor(50, 1000, 8000)).toBe(8000);
  });
});

describe('minutesLeft', () => {
  it('never rounds a wait down to nothing', () => {
    expect(minutesLeft(1000)).toBe(1);
    expect(minutesLeft(25 * 60_000)).toBe(25);
  });
});

describe('createStallWatch', () => {
  const watching = (stopAt = 3) =>
    createStallWatch({
      prefix: 'test',
      without: 'cycles without progress',
      warnAt: 2,
      stopAt,
      heartbeat: quiet(),
    });

  it('has no reason to stop while the run is young', () => {
    const stall = watching();

    stall.endCycle('walking', 0, 0);

    expect(stall.reason()).toBeUndefined();
  });

  it('warns once on the way to giving up', () => {
    const stall = watching();

    stall.endCycle('walking', 0, 0);
    stall.endCycle('walking', 1, 0);
    stall.endCycle('walking', 2, 0);

    const warnings = world.log.mock.calls.filter(([line]) =>
      String(line).includes('cycles without progress'),
    );
    expect(warnings).toHaveLength(1);
  });

  it('gives up once nothing has progressed for long enough', () => {
    const stall = watching();

    stall.endCycle('walking', 0, 0);
    stall.endCycle('walking', 1, 0);
    stall.endCycle('walking', 2, 0);

    expect(stall.reason()).toBe("no progress in 3 cycles, last was 'walking'");
  });

  // The defect this exists to prevent: sitting out a world save is the script working, not the
  // script stuck, so a shard that saves often must not walk a run to its stop a save at a time
  it('forgets the count for a branch that reports progress', () => {
    const stall = watching();

    stall.endCycle('saving', 0, 0);
    stall.endCycle('saving', 1, 0);
    stall.progressed();
    stall.endCycle('saving', 2, 0);
    stall.endCycle('saving', 3, 0);

    expect(stall.reason()).toBeUndefined();
  });
});

describe('createIdleWait', () => {
  const waiting = (stopReason: () => string | undefined = () => undefined) =>
    createIdleWait({
      prefix: 'test',
      waitingFor: 'everything in reach is regrowing',
      pollMs: 10_000,
      logEveryMs: 60_000,
      stopReason,
      onDone: () => {},
    });

  it('does not wait at all for a moment already past', () => {
    waiting()(-1);

    expect(world.sleep).not.toHaveBeenCalled();
  });

  // Sliced rather than slept through in one go: a quarter of an hour is long enough to be killed
  // standing there, and one long sleep would carry on regardless
  it('slices the wait rather than blocking through it', () => {
    waiting()(60_000);

    expect(world.sleep).toHaveBeenCalledTimes(6);
    expect(world.sleep).toHaveBeenCalledWith(10_000);
  });

  it('abandons the wait when the run has a reason to stop', () => {
    waiting(() => 'you are dead')(60_000);

    expect(world.sleep).toHaveBeenCalledTimes(1);
  });

  it('says how long is left rather than going silent for the whole wait', () => {
    waiting()(120_000);

    const updates = world.log.mock.calls.filter(([line]) => String(line).includes('to go'));
    expect(updates.length).toBeGreaterThan(0);
  });
});
