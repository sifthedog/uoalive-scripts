import { createStore } from '../lib/store.js';

const KEY = '__carving_memory';

// Bump whenever the shape below changes, or a store left by an older build crashes the first scan.
const VERSION = 1;

export interface Memory {
  // Carved, or refused in a way no amount of asking again fixes
  done: Set<number>;

  // Opened after carving and holding nothing worth taking
  emptied: Set<number>;

  // Serial -> the moment it is worth another try
  blocked: Map<number, number>;
}

const store = /* @__PURE__ */ createStore<Memory>({
  key: KEY,
  version: VERSION,
  seed: () => ({ done: new Set(), emptied: new Set(), blocked: new Map() }),
  describe: (found) =>
    found.done.size > 0 ? `memory: resuming with ${found.done.size} corpses already dealt with` : undefined,
});

export const memory = store.read;

// Tests only
export const forget = store.forget;

export { now } from '../lib/clock.js';
