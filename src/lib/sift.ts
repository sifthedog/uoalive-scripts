import { contentsOf, forgetUnreadable, isContainer } from './containers.js';
import { hex, isMobile } from './entity.js';
import type { Picked } from './pick.js';

export interface Wanted {
  has: (item: Item) => boolean;
  describe: () => string;
}

export interface Survey {
  loose: Item[];
  containers: Item[];

  // False for contents the client would not answer for, which is what an unopened container reads
  // as
  readable: boolean;
}

export interface SiftOptions {
  // Skipped whole, contents and all: a destination inside the source would be fed into itself
  skipSerial: number;

  opened: Set<number>;

  // Judged before the container check, so a bag someone asked for is taken rather than emptied
  isLoose?: (item: Item) => boolean;
}

export const artKey = (item: { graphic: number; hue?: number }): string =>
  `${hex(item.graphic)}/${item.hue ?? 0}`;

// No picks is no filter: ESC on the first cursor means the whole container goes across
export const wantedFrom = (picks: Picked[]): Wanted => {
  if (picks.length === 0) {
    return { has: () => true, describe: () => 'everything' };
  }

  const keys = new Set(picks.map((picked) => artKey(picked)));

  return { has: (item) => keys.has(artKey(item)), describe: () => [...keys].join(', ') };
};

const resolveItem = (serial: number): Item | undefined => {
  const found = client.findObject(serial);

  return found && !isMobile(found) ? found : undefined;
};

// A bag emptied by an earlier pass answers `[]`, which isContainer cannot tell from a plain item -
// so what has been opened once stays a container for the rest of the run and is left where it is
const holdsThings = (item: Item, opened: Set<number>): boolean =>
  opened.has(item.serial) || isContainer(item);

const walk = (contents: Item[] | undefined, options: SiftOptions, into: Survey): void => {
  for (const item of contents ?? []) {
    if (item.serial === options.skipSerial) {
      continue;
    }

    if (options.isLoose?.(item)) {
      into.loose.push(item);
      continue;
    }

    if (holdsThings(item, options.opened)) {
      into.containers.push(item);
      walk(contentsOf(item), options, into);
      continue;
    }

    into.loose.push(item);
  }
};

export const siftContents = (contents: Item[] | undefined, options: SiftOptions): Survey => {
  const found: Survey = { loose: [], containers: [], readable: contents !== undefined };

  walk(contents, options, found);

  return found;
};

export const sift = (rootSerial: number, options: SiftOptions): Survey =>
  siftContents(contentsOf(resolveItem(rootSerial)), options);

export const movables = (found: Survey, wanted: Wanted): Item[] =>
  found.loose.filter((item) => wanted.has(item));

// Contents stay undefined until a container has been opened, so one pass of double-clicks reaches
// exactly one level deeper than the last
export const openNested = (bags: Item[], opened: Set<number>, openDelay: number): boolean => {
  let openedAny = false;

  for (const bag of bags) {
    if (opened.has(bag.serial)) {
      continue;
    }

    opened.add(bag.serial);
    player.use(bag.serial);
    sleep(openDelay);
    forgetUnreadable(bag.serial);
    openedAny = true;
  }

  return openedAny;
};
