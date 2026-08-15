import { createStore } from '../lib/store.js';

// Not shared with lumberjacking's: one script's bans suppressing the other's veins would be
// invisible from either side.
const KEY = '__mining_memory';

// Bump whenever the shape below changes, or a store left by an older build crashes the first scan.
const VERSION = 1;

export interface Memory {
  // Tile key -> the moment it is worth swinging at again, Infinity for one written off for good
  blocked: Map<string, number>;

  // Keyed 'land:231' / 'static:1339' rather than by the number alone: the two tiledata tables are
  // numbered separately, so a shared key would have one ban hide an unrelated art in the other.
  notOre: Set<string>;
}

const store = /* @__PURE__ */ createStore<Memory>({
  key: KEY,
  version: VERSION,
  seed: () => ({ blocked: new Map(), notOre: new Set() }),
  describe: (found) =>
    found.blocked.size > 0 || found.notOre.size > 0
      ? `memory: resuming with ${found.blocked.size} blocked tiles, ${found.notOre.size} arts`
      : undefined,
});

export const memory = store.read;

// Tests only
export const forget = store.forget;

export { now } from '../lib/clock.js';
