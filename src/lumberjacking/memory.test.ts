import { beforeEach, describe, expect, it, vi } from 'vitest';

import { installGlobals, type FakeWorld } from '../test-support/uo.js';

const KEY = '__lumberjack_memory';

let world: FakeWorld;

const scope = globalThis as unknown as Record<string, unknown>;

// A fresh module registry is what a restart of the script looks like from here: new module state,
// same globalThis. Every test loads the module rather than importing it at the top, so it can
// arrange what the previous "run" left behind first.
const loadMemory = async () => {
  vi.resetModules();
  return import('./memory.js');
};

beforeEach(() => {
  delete scope[KEY];
  world = installGlobals();
});

describe('memory', () => {
  it('starts empty when nothing has run before', async () => {
    const { memory } = await loadMemory();

    expect(memory().blocked.size).toBe(0);
    expect(memory().notTree.size).toBe(0);
  });

  it('parks the store on globalThis so it can outlive the run', async () => {
    const { memory } = await loadMemory();

    memory().blocked.set('1,2,0,0xce0', 123);

    expect((scope[KEY] as { blocked: Map<string, number> }).blocked.get('1,2,0,0xce0')).toBe(123);
  });

  it('hands back the same store on every call', async () => {
    const { memory } = await loadMemory();

    expect(memory()).toBe(memory());
  });

  // The point of the whole module: a 25 minute cooldown is longer than most runs, so a restart has
  // to inherit what the last one learned rather than swinging at the tiles that just went empty
  it('picks up the store a previous run left behind', async () => {
    const first = await loadMemory();
    first.memory().blocked.set('1,2,0,0xce0', 999);
    first.memory().notTree.add(0xc9e);

    const second = await loadMemory();

    expect(second.memory().blocked.get('1,2,0,0xce0')).toBe(999);
    expect(second.memory().notTree.has(0xc9e)).toBe(true);
  });

  it('says so when it resumes, so a restart is visible in the console', async () => {
    const first = await loadMemory();
    first.memory().blocked.set('1,2,0,0xce0', 999);

    const second = await loadMemory();
    second.memory();

    expect(world.log).toHaveBeenCalledWith(expect.stringContaining('memory: resuming'));
  });

  it('stays quiet when there was nothing to resume', async () => {
    await loadMemory();
    const { memory } = await loadMemory();

    memory();

    expect(world.log).not.toHaveBeenCalled();
  });

  // A store left by an older build has a shape this one does not know, and reading it would crash
  // the first scan after an edit rather than the run that wrote it
  it('discards a store from an older version rather than reading it', async () => {
    scope[KEY] = { version: 0, blocked: new Map([['1,2,0,0xce0', 999]]), notTree: new Set() };

    const { memory } = await loadMemory();

    expect(memory().blocked.size).toBe(0);
  });

  it('discards whatever else may be sitting on that name', async () => {
    scope[KEY] = 'not a store at all';

    const { memory } = await loadMemory();

    expect(memory().blocked.size).toBe(0);
  });
});

describe('forget', () => {
  // Tests only, and the reason it exists: vi.resetModules() gives each test a fresh module registry
  // but leaves globalThis alone, which is exactly what this store is built to survive
  it('clears the store the next run would have inherited', async () => {
    const first = await loadMemory();
    first.memory().blocked.set('1,2,0,0xce0', 999);
    first.forget();

    const second = await loadMemory();

    expect(second.memory().blocked.size).toBe(0);
  });

  it('drops the module handle too, not just the global', async () => {
    const { memory, forget } = await loadMemory();

    const before = memory();
    forget();

    expect(memory()).not.toBe(before);
  });
});

describe('now', () => {
  it('reads the wall clock', async () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date('2026-08-14T12:00:00Z'));

    const { now } = await loadMemory();

    expect(now()).toBe(Date.parse('2026-08-14T12:00:00Z'));

    vi.useRealTimers();
  });
});
