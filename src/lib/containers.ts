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

// A known contents array proves it is a container; otherwise fall back to the graphic list.
// This matters because player.use() on a non-container *uses* it - potions get drunk.
export const isContainer = (item: Item): boolean =>
  Array.isArray(item.contents) || CONTAINER_GRAPHICS.has(item.graphic);

// Contents stay undefined until a container has been opened, so open them before giving up
export const openContainers = (preferredSerial?: number): boolean => {
  if (preferredSerial) {
    player.use(preferredSerial);
    sleep(800);
    return true;
  }

  let opened = false;

  for (const item of player.backpack?.contents ?? []) {
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

    if (item.contents && item.contents.length > 0) {
      const foundInSub = findIn(item.contents, matches);
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

    if (item.contents && item.contents.length > 0) {
      found.push(...collectIn(item.contents, matches));
    }
  }

  return found;
};
