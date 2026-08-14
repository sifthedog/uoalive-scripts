import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { installGlobals, type FakeWorld } from '../test-support/uo.js';

// The shared beat is covered in heartbeat.test.ts. What is worth pinning per folder is the pair of
// words each one binds it with, because that prefix is how a console with two scripts in it says
// which one is still alive.
let world: FakeWorld;

beforeEach(() => {
  world = installGlobals();
  vi.useFakeTimers();
  vi.setSystemTime(new Date(0));
});

afterEach(() => {
  vi.useRealTimers();
});

const beatTwice = async (path: string) => {
  vi.resetModules();
  const { beat } = await import(path);

  beat('working', 0, 3);
  vi.setSystemTime(new Date(30_000));
  beat('working', 1, 3);

  return world.log.mock.calls[0][0] as string;
};

describe('the folder bindings', () => {
  it('says lumberjack, and counts chops', async () => {
    const line = await beatTwice('../lumberjacking/heartbeat.js');

    expect(line).toContain('lumberjack: still here');
    expect(line).toContain('3 chops');
  });

  it('says mining, and counts swings', async () => {
    const line = await beatTwice('../mining/heartbeat.js');

    expect(line).toContain('mining: still here');
    expect(line).toContain('3 swings');
  });
});
