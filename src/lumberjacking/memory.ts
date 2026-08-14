import { createStore } from '../lib/store.js';

// Lumberjacking's own key, deliberately not shared with mining's: the two stores hold the same kind
// of thing about different tiles, and one script's bans suppressing the other's trees would be
// invisible from either side.
const KEY = '__lumberjack_memory';

// Bump this whenever the shape below changes: a store left behind by an older build would otherwise
// be read as if it were this one, and a restart after an edit would crash on the first scan.
const VERSION = 1;

export interface Memory {
  // Tile key -> the moment it is worth swinging at again, Infinity for one written off for good.
  // A cooldown and a permanent ban being the same lookup is what keeps the scan's filter to one line.
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

// Tests only
export const forget = store.forget;

export { now } from '../lib/clock.js';
