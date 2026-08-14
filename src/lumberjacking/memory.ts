// State that has to outlive a run. The QuickJS context persists between runs - it is why the bundle
// is IIFE-wrapped - so a property parked on globalThis survives a restart of the script, though not
// of the client. A regrow cooldown is longer than most runs, so without this every restart would
// swing at the tiles that had just gone empty and re-learn the whole forest from scratch.
const KEY = '__lumberjack_memory';

// Bump this whenever the shape below changes: a store left behind by an older build would otherwise
// be read as if it were this one, and a restart after an edit would crash on the first scan.
const VERSION = 1;

export interface Memory {
  version: number;

  // Tile key -> the moment it is worth swinging at again, Infinity for one written off for good.
  // A cooldown and a permanent ban being the same lookup is what keeps the scan's filter to one line.
  blocked: Map<string, number>;

  // Graphics the shard refuses to chop at all, learned at runtime
  notTree: Set<number>;
}

// The one clock in the scripts, so tests have one thing to fake
export const now = (): number => Date.now();

const scope = globalThis as unknown as Record<string, unknown>;

const load = (): Memory => {
  const found = scope[KEY] as Memory | undefined;

  if (found?.version === VERSION) {
    if (found.blocked.size > 0 || found.notTree.size > 0) {
      log(`memory: resuming with ${found.blocked.size} blocked tiles, ${found.notTree.size} arts`);
    }
    return found;
  }

  const store: Memory = { version: VERSION, blocked: new Map(), notTree: new Set() };
  scope[KEY] = store;

  return store;
};

let store: Memory | undefined;

// Read through a call rather than exported as the object itself, so forget() can actually forget:
// a module-scope `const memory = load()` would hand every importer a reference that outlives it.
export const memory = (): Memory => (store ??= load());

// Tests only. The suite's vi.resetModules() gives each test a fresh module registry but leaves
// globalThis alone, which is precisely what this store is designed to survive.
export const forget = (): void => {
  delete scope[KEY];
  store = undefined;
};
