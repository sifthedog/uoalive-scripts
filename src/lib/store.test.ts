import { beforeEach, describe, expect, it, vi } from 'vitest';

import { installGlobals, type FakeWorld } from '../test-support/uo.js';
import { createStore } from './store.js';

interface Held {
  blocked: Map<string, number>;
}

const scope = globalThis as unknown as Record<string, unknown>;

let world: FakeWorld;

const store = (key: string, version = 1, describe?: (found: Held) => string | undefined) =>
  createStore<Held>({ key, version, seed: () => ({ blocked: new Map() }), describe });

beforeEach(() => {
  world = installGlobals();
  delete scope.__a;
  delete scope.__b;
});

describe('createStore', () => {
  it('seeds an empty store the first time it is read', () => {
    expect(store('__a').read().blocked.size).toBe(0);
  });

  it('hands back the same object on every read', () => {
    const held = store('__a');

    expect(held.read()).toBe(held.read());
  });

  // The QuickJS context persists between runs, which is the whole point: a 25-minute cooldown is
  // longer than most runs, so a restart that forgot would swing at the tiles it had just emptied
  it('survives a restart of the script', () => {
    store('__a').read().blocked.set('1,2,3,4', 999);

    // A fresh createStore is what a rebuilt bundle gets; globalThis is what it finds waiting
    expect(store('__a').read().blocked.get('1,2,3,4')).toBe(999);
  });

  // Held by reference rather than serialised, so a stored Map is still a Map on the way back
  it('brings a Map back as a Map', () => {
    store('__a').read().blocked.set('k', 1);

    expect(store('__a').read().blocked).toBeInstanceOf(Map);
  });

  // Two scripts hold the same kind of thing about different tiles, and one's bans suppressing the
  // other's would be invisible from either side
  it('keeps two keys entirely apart', () => {
    store('__a').read().blocked.set('shared', 1);

    expect(store('__b').read().blocked.has('shared')).toBe(false);
  });

  // A store left behind by an older build would otherwise be read as if it were this one, and a
  // restart after an edit would crash on the first scan
  it('discards a store whose shape has changed', () => {
    store('__a', 1).read().blocked.set('old', 1);

    expect(store('__a', 2).read().blocked.size).toBe(0);
  });

  it('says so when it resumes something worth mentioning', () => {
    store('__a').read().blocked.set('k', 1);

    store('__a', 1, (found) => (found.blocked.size ? `resuming ${found.blocked.size}` : undefined))
      .read();

    expect(world.log).toHaveBeenCalledWith('resuming 1');
  });

  it('stays quiet about a store with nothing in it', () => {
    store('__a', 1, (found) => (found.blocked.size ? 'resuming' : undefined)).read();

    expect(world.log).not.toHaveBeenCalled();
  });

  it('forgets on demand, which is what the suite needs', () => {
    const held = store('__a');
    held.read().blocked.set('k', 1);

    held.forget();

    expect(held.read().blocked.size).toBe(0);
    expect(scope.__a).toBeDefined();
  });
});
