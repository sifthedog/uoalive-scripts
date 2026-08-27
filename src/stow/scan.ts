import { contentsOf, packContents } from '../lib/containers.js';
import {
  movables,
  openNested,
  siftContents,
  type Survey,
  type Wanted,
} from '../lib/sift.js';
import { MAX_REOPENS, OPEN_DELAY, OPEN_NESTED } from './config.js';

export interface Scan {
  look: () => Survey;
  openNew: (bags: Item[]) => boolean;
  wantedIn: (found: Survey) => Item[];
}

// A factory rather than a module-level set: `opened` lives for the run, and two runs in one test
// process must not share it
export const createScan = (options: { destSerial: number; wanted: Wanted }): Scan => {
  const opened = new Set<number>();
  const reopens = new Map<number, number>();

  // A watcher can have a bag closed under it, which a one-shot cannot: left in `opened` it is never
  // re-clicked and is a blind spot for the rest of the run
  const rearm = (bags: Item[]): void => {
    for (const bag of bags) {
      if (!opened.has(bag.serial) || contentsOf(bag) !== undefined) {
        continue;
      }

      const spent = reopens.get(bag.serial) ?? 0;
      if (spent >= MAX_REOPENS) {
        continue;
      }

      reopens.set(bag.serial, spent + 1);
      opened.delete(bag.serial);
    }
  };

  return {
    look: () =>
      siftContents(packContents(), {
        skipSerial: options.destSerial,
        opened,
        isLoose: options.wanted.has,
      }),

    openNew: (bags) => {
      if (!OPEN_NESTED) {
        return false;
      }

      rearm(bags);

      return openNested(bags, opened, OPEN_DELAY);
    },

    wantedIn: (found) => movables(found, options.wanted),
  };
};
