import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { installGlobals, type FakeWorld } from '../test-support/uo.js';
import { createHeartbeat } from './heartbeat.js';

const HEARTBEAT_EVERY = 30_000;

let world: FakeWorld;

// The factory holds the clock of the last beat, so every test needs its own - the same way a
// restart of the script gives the script one
const loadHeartbeat = async () =>
  createHeartbeat({ prefix: 'lumberjack', noun: 'chops', everyMs: HEARTBEAT_EVERY });

const at = (ms: number) => vi.setSystemTime(new Date(ms));

beforeEach(() => {
  world = installGlobals();
  vi.useFakeTimers();
  at(0);
});

afterEach(() => {
  vi.useRealTimers();
});

describe('beat', () => {
  // The run has just logged what it is doing, so a beat on top of that says nothing new
  it('stays quiet on the first call', async () => {
    const { beat } = await loadHeartbeat();

    beat('chopped', 0, 0);

    expect(world.log).not.toHaveBeenCalled();
  });

  it('stays quiet until the interval has passed', async () => {
    const { beat } = await loadHeartbeat();

    beat('chopped', 0, 0);
    at(HEARTBEAT_EVERY - 1);
    beat('chopped', 1, 1);

    expect(world.log).not.toHaveBeenCalled();
  });

  it('reports once the interval has passed', async () => {
    const { beat } = await loadHeartbeat();

    beat('chopped', 0, 0);
    at(HEARTBEAT_EVERY);
    beat('throttled', 7, 3);

    expect(world.log).toHaveBeenCalledWith(expect.stringContaining('still here - throttled'));
  });

  // The whole point of the module: whatever the loop is doing, the console can say where it is
  it('names the phase, the cycle, the position and the tally', async () => {
    const { beat } = await loadHeartbeat();
    world.player.x = 2450;
    world.player.y = 500;
    world.player.weight = 210;
    world.player.weightMax = 400;

    beat('walking', 0, 0);
    at(HEARTBEAT_EVERY);
    beat('walking', 42, 17);

    const line = world.log.mock.calls[0][0] as string;
    expect(line).toContain('walking');
    expect(line).toContain('cycle 42');
    expect(line).toContain('2450,500');
    expect(line).toContain('210/400');
    expect(line).toContain('17 chops');
  });

  // A cycle can be 300ms or 8s depending on which waits it hit, so the cadence has to come off the
  // clock. Counting calls would make it a function of whatever fault the run is stuck in.
  it('reports on the clock rather than per call', async () => {
    const { beat } = await loadHeartbeat();

    beat('chopped', 0, 0);
    for (let cycle = 1; cycle <= 500; cycle++) {
      beat('chopped', cycle, cycle);
    }

    expect(world.log).not.toHaveBeenCalled();

    at(HEARTBEAT_EVERY);
    beat('chopped', 501, 501);

    expect(world.log).toHaveBeenCalledTimes(1);
  });

  it('starts the interval again after reporting', async () => {
    const { beat } = await loadHeartbeat();

    beat('chopped', 0, 0);
    at(HEARTBEAT_EVERY);
    beat('chopped', 1, 1);
    at(HEARTBEAT_EVERY * 2 - 1);
    beat('chopped', 2, 2);

    expect(world.log).toHaveBeenCalledTimes(1);

    at(HEARTBEAT_EVERY * 2);
    beat('chopped', 3, 3);

    expect(world.log).toHaveBeenCalledTimes(2);
  });
});

describe('resetBeat', () => {
  // The regrow wait logs on its own cadence, so a beat should not land on top of the line it just
  // printed - it should be a full interval after it
  it('pushes the next report a full interval out', async () => {
    const { beat, resetBeat } = await loadHeartbeat();

    beat('chopped', 0, 0);
    at(HEARTBEAT_EVERY);
    resetBeat();
    beat('chopped', 1, 1);

    expect(world.log).not.toHaveBeenCalled();

    at(HEARTBEAT_EVERY * 2);
    beat('chopped', 2, 2);

    expect(world.log).toHaveBeenCalledTimes(1);
  });
});
