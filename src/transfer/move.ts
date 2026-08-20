import { contentsOf, isContainer } from '../lib/containers.js';
import { hex, isMobile } from '../lib/entity.js';
import type { Picked } from '../lib/pick.js';
import { MAX_PASSES, MOVE_DELAY, OPEN_DELAY } from './config.js';

export type TransferOutcome = 'emptied' | 'stalled' | 'unopened';

export interface Wanted {
  has: (item: Item) => boolean;
  describe: () => string;
}

export interface Survey {
  loose: Item[];
  containers: Item[];

  // False for contents the client would not answer for, which is what an unopened container reads as
  readable: boolean;
}

export interface Transferred {
  outcome: TransferOutcome;
  stacks: number;
  items: number;
  left: number;
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

const walk = (
  contents: Item[] | undefined,
  destSerial: number,
  opened: Set<number>,
  into: Survey,
): void => {
  for (const item of contents ?? []) {
    // A destination sitting inside the source would otherwise be emptied into itself
    if (item.serial === destSerial) {
      continue;
    }

    if (holdsThings(item, opened)) {
      into.containers.push(item);
      walk(contentsOf(item), destSerial, opened, into);
      continue;
    }

    into.loose.push(item);
  }
};

export const survey = (sourceSerial: number, destSerial: number, opened: Set<number>): Survey => {
  const contents = contentsOf(resolveItem(sourceSerial));
  const found: Survey = { loose: [], containers: [], readable: contents !== undefined };

  walk(contents, destSerial, opened, found);

  return found;
};

export const movables = (
  sourceSerial: number,
  destSerial: number,
  wanted: Wanted,
  opened = new Set<number>(),
): Item[] => survey(sourceSerial, destSerial, opened).loose.filter((item) => wanted.has(item));

// Contents stay undefined until a container has been opened, so one pass of double-clicks reaches
// exactly one level deeper than the last
export const openNested = (
  sourceSerial: number,
  destSerial: number,
  opened: Set<number>,
): boolean => {
  let openedAny = false;

  for (const bag of survey(sourceSerial, destSerial, opened).containers) {
    if (opened.has(bag.serial)) {
      continue;
    }

    opened.add(bag.serial);
    player.use(bag.serial);
    sleep(OPEN_DELAY);
    openedAny = true;
  }

  return openedAny;
};

export const transfer = (
  sourceSerial: number,
  destSerial: number,
  wanted: Wanted,
  onMove?: (item: Item) => void,
): Transferred => {
  player.use(sourceSerial);
  sleep(OPEN_DELAY);

  // Amounts are read at the moment of the move, because a stack that has already gone answers for
  // wherever it is now. Keyed by serial, so an item a failed pass left behind is not counted twice.
  const sent = new Map<number, number>();
  const opened = new Set<number>();

  const result = (outcome: TransferOutcome, left: number): Transferred => ({
    outcome,
    stacks: sent.size,
    items: [...sent.values()].reduce((total, amount) => total + amount, 0),
    left,
  });

  let previous = Infinity;

  for (let pass = 0; pass < MAX_PASSES; pass++) {
    if (!survey(sourceSerial, destSerial, opened).readable) {
      return result('unopened', 0);
    }

    if (openNested(sourceSerial, destSerial, opened)) {
      // What has just become readable has never been counted, so the stall check starts over
      previous = Infinity;
      continue;
    }

    const todo = movables(sourceSerial, destSerial, wanted, opened);

    if (todo.length === 0) {
      return result('emptied', 0);
    }

    // Moves are asynchronous - moveItem's return says only that the packet went out - so a pass is
    // judged by rescanning, and one that shifted nothing is a stall rather than an empty container
    if (todo.length >= previous) {
      return result('stalled', todo.length);
    }
    previous = todo.length;

    for (const item of todo) {
      player.moveItem(item.serial, destSerial);
      sent.set(item.serial, item.amount ?? 1);
      onMove?.(item);
      sleep(MOVE_DELAY);
    }
  }

  return result('stalled', movables(sourceSerial, destSerial, wanted, opened).length);
};
