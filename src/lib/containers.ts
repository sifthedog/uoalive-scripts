import { hex } from './entity.js';

// Add your own container graphics here if a bag is ever missed
export const CONTAINER_GRAPHICS = new Set([
  0x0e75, // backpack
  0x0e76, // bag
  0x0e79, // pouch
  0x0e7d, // wooden box
  0x0e43, // wooden chest
  0x09a8, // metal box
  0x09ab, // metal chest
  0x0e3c, // crate
  0x0e3d, // crate
  0x0e40, // gold chest
  0x0e41, // gold chest
]);

export type ItemPredicate = (item: Item) => boolean;

// Serials the client threw on, skipped rather than merely unlogged: the pack is walked several times
// per swing, so eight unreadable items cost a mining run hundreds of failed native calls per dig.
const unreadable = new Set<number>();

// Apart from `unreadable`, which opening a container clears - a bag reopened and still silent must
// not complain a second time.
const complained = new Set<number>();

let packComplained = false;

// Opening a container is what makes it readable, so whoever double-clicks one clears its serial here.
export const forgetUnreadable = (serial?: number): void => {
  if (serial === undefined) {
    unreadable.clear();

    return;
  }

  unreadable.delete(serial);
};

// graphic and name come off the same truncated payload that just threw, so reading them for the log
// can throw in turn - out of the catch, past the try that exists to stop exactly this.
const describe = (item: Item): string => {
  try {
    return `${hex(item.serial)} ${hex(item.graphic)} '${item.name ?? ''}'`;
  } catch {
    return `${hex(item.serial)} which will not say what it is`;
  }
};

// Reading `contents` can throw rather than answer: a live run died on "Exception executing
// 'itemGetContents': Unexpected end of JSON input". A throw reads as the `undefined` an unopened
// container reports, which every caller already handles.
export const contentsOf = (item: Item | undefined): Item[] | undefined => {
  if (!item || unreadable.has(item.serial)) {
    return undefined;
  }

  try {
    return item.contents;
  } catch (error) {
    unreadable.add(item.serial);

    if (!complained.has(item.serial)) {
      complained.add(item.serial);
      log(`contents: ${describe(item)} would not answer - ${String(error)}`);
    }

    return undefined;
  }
};

// Never latched, unlike everything else: one bad answer for the backpack would leave every later pack
// read empty, and a run that believes its pack is empty does nothing at all.
export const packContents = (): Item[] | undefined => {
  try {
    const pack = player.backpack;
    forgetUnreadable(pack?.serial);

    return contentsOf(pack);
  } catch (error) {
    if (!packComplained) {
      packComplained = true;
      log(`contents: the backpack would not answer - ${String(error)}`);
    }

    return undefined;
  }
};

// A *non-empty* contents array proves it is a container, because this client answers `[]` for plain
// items rather than the `undefined` the type says. player.use() on a non-container *uses* it: trusting
// `Array.isArray` here had a sell run equip the weapon it was asked to sell, and drink the potions.
export const isContainer = (item: Item): boolean =>
  (contentsOf(item)?.length ?? 0) > 0 || CONTAINER_GRAPHICS.has(item.graphic);

// Contents stay undefined until a container has been opened, so open them before giving up
export const openContainers = (preferredSerial?: number): boolean => {
  if (preferredSerial) {
    player.use(preferredSerial);
    sleep(800);
    forgetUnreadable(preferredSerial);

    return true;
  }

  let opened = false;

  for (const item of packContents() ?? []) {
    if (!isContainer(item)) {
      continue;
    }

    player.use(item.serial);
    sleep(800);
    forgetUnreadable(item.serial);
    opened = true;
  }

  return opened;
};

// Depth-first search through a container and its sub-containers
export const findIn = (contents: Item[] | undefined, matches: ItemPredicate): Item | null => {
  for (const item of contents ?? []) {
    if (matches(item)) {
      return item;
    }

    const sub = contentsOf(item);
    if (sub && sub.length > 0) {
      const foundInSub = findIn(sub, matches);
      if (foundInSub) return foundInSub;
    }
  }

  return null;
};

// Every match rather than the first, for the jobs that work through a pile of stacks
export const collectIn = (contents: Item[] | undefined, matches: ItemPredicate): Item[] => {
  const found: Item[] = [];

  for (const item of contents ?? []) {
    if (matches(item)) {
      found.push(item);
    }

    const sub = contentsOf(item);
    if (sub && sub.length > 0) {
      found.push(...collectIn(sub, matches));
    }
  }

  return found;
};
