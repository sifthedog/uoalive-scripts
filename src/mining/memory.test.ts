import { beforeEach, describe, expect, it, vi } from 'vitest';

import { installGlobals, type FakeWorld } from '../test-support/uo.js';

let world: FakeWorld;

// The store lives on globalThis precisely so it survives vi.resetModules(), so every test has to
// clear it by hand before the module under test has a chance to read it
const loadMemory = async () => {
  const fresh = await import('./memory.js');
  fresh.forget();
  return import('./memory.js');
};

beforeEach(() => {
  vi.resetModules();
  world = installGlobals();
});

describe('memory', () => {
  it('starts empty', async () => {
    const { memory } = await loadMemory();

    expect(memory().blocked.size).toBe(0);
    expect(memory().notOre.size).toBe(0);
  });

  it('hands every caller the same store rather than a copy', async () => {
    const { memory } = await loadMemory();

    memory().blocked.set('102,100,0,231', 123);

    expect(memory().blocked.get('102,100,0,231')).toBe(123);
  });

  // The whole point: a 25 minute respawn outlasts most runs, and the QuickJS context survives a
  // restart of the script even though it does not survive a restart of the client
  it('survives a restart of the script', async () => {
    const first = await loadMemory();
    first.memory().blocked.set('102,100,0,231', 123);

    vi.resetModules();
    const { memory } = await import('./memory.js');

    expect(memory().blocked.get('102,100,0,231')).toBe(123);
  });

  it('says what it inherited, so a restart is not silently working from old bans', async () => {
    const first = await loadMemory();
    first.memory().notOre.add('land:231');

    vi.resetModules();
    world.log.mockClear();
    const { memory } = await import('./memory.js');
    memory();

    expect(world.log).toHaveBeenCalledWith(expect.stringContaining('resuming'));
  });

  it('stays quiet when there was nothing worth inheriting', async () => {
    const first = await loadMemory();
    first.memory();

    vi.resetModules();
    world.log.mockClear();
    const { memory } = await import('./memory.js');
    memory();

    expect(world.log).not.toHaveBeenCalled();
  });

  // A store left behind by an older build would otherwise be read as if it were this one, and the
  // first scan after an edit would crash on a shape that no longer exists
  it('discards a store from an older version rather than reading it', async () => {
    const { memory } = await loadMemory();
    memory().blocked.set('102,100,0,231', 123);

    (globalThis as Record<string, unknown>).__mining_memory = {
      version: 0,
      blocked: new Map([['102,100,0,231', 123]]),
      notOre: new Set(),
    };

    vi.resetModules();
    const fresh = await import('./memory.js');

    expect(fresh.memory().blocked.size).toBe(0);
  });

  // Mining and lumberjacking hold the same kind of fact about different tiles. One store between
  // them would have either script's bans hide the other's tiles, invisibly from both sides.
  it('keeps its store apart from the lumberjack one', async () => {
    const { memory } = await loadMemory();
    memory().blocked.set('102,100,0,231', 123);

    const scope = globalThis as Record<string, unknown>;
    expect(scope.__mining_memory).toBeDefined();
    expect(scope.__lumberjack_memory).toBeUndefined();
  });
});
