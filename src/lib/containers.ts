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

// Serials already complained about, so a bag that answers badly says so once instead of once per
// scan - and the pack is scanned after every swing
const unreadable = new Set<number>();

// Reading `contents` is a question put to the client, and the client can fail the question rather
// than answer it. A live run died on
//
//   Exception executing 'itemGetContents': Unexpected end of JSON input
//
// thrown out of a pack count in the middle of a smelt, which is the client holding no data for a
// sub-bag and saying so with a truncated answer instead of an empty one. Every read goes through
// here and a throw is treated as the `undefined` the same container reports before it has been
// opened: a case every caller already handles, rather than a new one. The cost of being wrong is a
// count that is low by whatever was in that bag, which is what these counts already promise; the
// cost of not catching it is the whole run, because nothing above this has a try in it.
export const contentsOf = (item: Item | undefined): Item[] | undefined => {
  try {
    return item?.contents;
  } catch (error) {
    const serial = item?.serial ?? 0;

    if (!unreadable.has(serial)) {
      unreadable.add(serial);
      log(`contents: ${hex(serial)} would not answer - ${String(error)}`);
    }

    return undefined;
  }
};

// The same read one level up. `player.backpack` is a getter too, so it is inside the try as well.
export const packContents = (): Item[] | undefined => {
  try {
    return contentsOf(player.backpack);
  } catch (error) {
    if (!unreadable.has(0)) {
      unreadable.add(0);
      log(`contents: the backpack would not answer - ${String(error)}`);
    }

    return undefined;
  }
};

// A *non-empty* contents array proves it is a container; otherwise fall back to the graphic list.
// This matters because player.use() on a non-container *uses* it - potions get drunk.
//
// An empty array proves nothing, because this client answers `[]` for plain items rather than the
// `undefined` the type says. Its own docs for `Item.contents` give it away: the example loops the
// pack calling `item.contents.length` on everything without a guard, and treats `length > 0` as
// what makes an item a sub-container. Trusting `Array.isArray` here made every item in the pack a
// container, and a sell run double-clicked the lot - equipping the weapon it had been asked to
// sell. The false negative left over costs nothing: an opened, empty container whose graphic is
// not listed has nothing in it to find.
export const isContainer = (item: Item): boolean =>
  (contentsOf(item)?.length ?? 0) > 0 || CONTAINER_GRAPHICS.has(item.graphic);

// Contents stay undefined until a container has been opened, so open them before giving up
export const openContainers = (preferredSerial?: number): boolean => {
  if (preferredSerial) {
    player.use(preferredSerial);
    sleep(800);
    return true;
  }

  let opened = false;

  for (const item of packContents() ?? []) {
    if (!isContainer(item)) {
      continue;
    }

    player.use(item.serial);
    sleep(800);
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
