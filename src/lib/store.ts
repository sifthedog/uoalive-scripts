// State that has to outlive a run. The QuickJS context persists between runs - it is why the bundle
// is IIFE-wrapped - so a property parked on globalThis survives a restart of the script, though not
// of the client. Held by reference rather than serialised: there is no JSON round trip anywhere, so
// a stored Map is still a Map on the way back.

const scope = globalThis as unknown as Record<string, unknown>;

export interface Store<T> {
  read: () => T;
  forget: () => void;
}

// Each caller passes its own key, so one script's store can never be read as another's - the two
// harvest scripts hold the same kind of thing about different tiles, and one's bans suppressing the
// other's would be invisible from either side.
//
// A store whose `version` does not match is discarded rather than read: an edit to the shape would
// otherwise crash the first scan after a rebuild.
export const createStore = <T extends object>(options: {
  key: string;
  version: number;
  seed: () => T;
  describe?: (found: T) => string | undefined;
}): Store<T> => {
  interface Versioned {
    version: number;
  }

  let held: (T & Versioned) | undefined;

  const load = (): T & Versioned => {
    const found = scope[options.key] as (T & Versioned) | undefined;

    if (found?.version === options.version) {
      const described = options.describe?.(found);
      if (described) {
        log(described);
      }
      return found;
    }

    const fresh = { ...options.seed(), version: options.version };
    scope[options.key] = fresh;

    return fresh;
  };

  return {
    // Read through a call rather than handed out as the object itself, so forget() can actually
    // forget: a module-scope `const memory = load()` would give every importer a reference that
    // outlives it.
    read: () => (held ??= load()),

    // vi.resetModules() gives each test a fresh module registry but leaves globalThis alone, which
    // is precisely what this store is designed to survive.
    forget: () => {
      delete scope[options.key];
      held = undefined;
    },
  };
};
