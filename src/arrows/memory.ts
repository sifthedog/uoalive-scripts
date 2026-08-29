import { createStore } from '../lib/store.js';

const KEY = '__arrows_memory';

// Bump whenever the shape below changes, or a store left by an older build crashes the first scan.
const VERSION = 1;

export interface Memory {
  // Serial -> the moment it is worth another try
  blocked: Map<number, number>;
}

const store = /* @__PURE__ */ createStore<Memory>({
  key: KEY,
  version: VERSION,
  seed: () => ({ blocked: new Map() }),
});

export const memory = store.read;

// Tests only
export const forget = store.forget;

export { now } from '../lib/clock.js';
