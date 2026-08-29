import { createStore } from '../lib/store.js';

// Not shared with mining's: one script's bans suppressing the other's trees would be invisible from
// either side.
const KEY = '__lumberjack_memory';

// Bump whenever the shape below changes, or a store left by an older build crashes the first scan.
const VERSION = 1;

export interface Memory {
  // Tile key -> the moment it is worth swinging at again, Infinity for one written off for good
  blocked: Map<string, number>;

  // Graphics the shard refuses to chop at all, learned at runtime
  notTree: Set<number>;
}

const store = /* @__PURE__ */ createStore<Memory>({
  key: KEY,
  version: VERSION,
  seed: () => ({ blocked: new Map(), notTree: new Set() }),
  describe: (found) =>
    found.blocked.size > 0 || found.notTree.size > 0
      ? `memory: resuming with ${found.blocked.size} blocked tiles, ${found.notTree.size} arts`
      : undefined,
});

export const memory = store.read;

export const forget = store.forget;

export { now } from '../lib/clock.js';
