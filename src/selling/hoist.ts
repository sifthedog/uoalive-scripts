import { collectIn, isContainer, packContents } from '../lib/containers.js';
import { hex } from '../lib/entity.js';
import { queryOPL } from '../lib/opl.js';
import { MAX_HOIST_PASSES, MOVE_DELAY, OPEN_DELAY, OPL_TIMEOUT } from './config.js';

export { hex };

// The pack is walked several times a run, and without this every walk pays OPL_TIMEOUT again for
// every item the client has no name for. A name does not change, and a serial survives a moveItem.
const names = new Map<number, string>();

// One unanswered tooltip is an item; three in a row is the shard. Otherwise a pack of thirty
// un-hovered items costs a minute of nothing, per walk.
let oplAnswersNames = true;
let misses = 0;

// Only the nameless ones are worth OPL_TIMEOUT: the rest name themselves.
const nameOf = (item: Item): string => {
  const known = (item.name ?? '').trim();
  if (known) {
    return known;
  }

  const cached = names.get(item.serial);
  if (cached !== undefined) {
    return cached;
  }

  if (!oplAnswersNames) {
    return '';
  }

  const fromTooltip = (queryOPL(item.serial, OPL_TIMEOUT, 'sell')?.name ?? '').trim();
  names.set(item.serial, fromTooltip);

  misses = fromTooltip ? 0 : misses + 1;
  if (misses >= 3) {
    oplAnswersNames = false;
    log('sell: tooltips are not answering here, so only items the client has already named can match');
  }

  return fromTooltip;
};

// Everything under the pack except its top level - those are already where the vendor can see them,
// and skipping them before nameOf keeps the tooltip queries down to the items that might move
export const nestedMatches = (name: string): Item[] => {
  const contents = packContents();
  const topLevel = new Set((contents ?? []).map((item) => item.serial));
  const wanted = name.toLowerCase();

  return collectIn(
    contents,
    (item) => !topLevel.has(item.serial) && nameOf(item).toLowerCase() === wanted,
  );
};

// How the sale knows whether another pass has anything to find. Every depth, because this shard's
// vendors sell out of a bag as readily as off the top of the pack - reading the top level alone
// stopped the run with the bags still full. On a shard whose vendors are blind to sub-containers
// this over-counts by one gump, which says 'no X on offer' and stops; set HOIST_FROM_BAGS there.
export const sellableMatches = (name: string): Item[] => {
  const wanted = name.toLowerCase();

  return collectIn(packContents(), (item) => nameOf(item).toLowerCase() === wanted);
};

const CONTAINER_WORDS = /\b(bag|pouch|box|chest|crate|basket|backpack)\b/i;

// Serials already named, so a bag is mentioned once rather than once per pass
const unlisted = new Set<number>();

// A shard with container art CONTAINER_GRAPHICS has never heard of would hide whatever is inside one
// - silently, which is the worst way to lose an item. Costs no tooltip query: it reads only names
// the client has already sent, and prints the graphic to add to lib/containers.ts.
const warnIfContainerish = (item: Item): void => {
  const name = (item.name ?? '').trim();

  if (!CONTAINER_WORDS.test(name) || unlisted.has(item.serial)) {
    return;
  }

  unlisted.add(item.serial);
  log(
    `sell: '${name}' (${hex(item.serial)}) reads like a container, but its graphic ${hex(item.graphic)} is not in CONTAINER_GRAPHICS, so it will not be opened`,
  );
};

// Contents stay undefined until a container has been opened, so an unopened bag hides everything in
// it. Only containers not already opened, so each pass reaches one level deeper instead of
// double-clicking the same bags. Returns whether anything new was opened.
const openUnopened = (opened: Set<number>): boolean => {
  const everything = collectIn(packContents(), () => true);
  const containers: Item[] = [];

  for (const item of everything) {
    if (!isContainer(item)) {
      warnIfContainerish(item);
      continue;
    }

    if (!opened.has(item.serial)) {
      containers.push(item);
    }
  }

  for (const container of containers) {
    player.use(container.serial);
    opened.add(container.serial);
    sleep(OPEN_DELAY);
  }

  return containers.length > 0;
};

// For a vendor that only lists the top level of your pack. Moves are asynchronous, so the pack is
// rescanned between passes; what stops the loop is a pass with nothing new to move and nothing new
// opened, because opening a deeper bag legitimately makes a match count go up.
export const hoistToPack = (name: string): number => {
  const packSerial = player.backpack?.serial;

  if (!packSerial) {
    log('sell: no backpack to move anything into');
    return 0;
  }

  const opened = new Set<number>();
  // Keyed by serial so a move that does not land is never retried forever, and a stack that merged
  // into another on arrival is not counted twice
  const attempted = new Set<number>();
  let moved = 0;

  for (let pass = 0; pass < MAX_HOIST_PASSES; pass++) {
    const openedAny = openUnopened(opened);
    const fresh = nestedMatches(name).filter((item) => !attempted.has(item.serial));

    if (fresh.length === 0 && !openedAny) {
      break;
    }

    for (const item of fresh) {
      player.moveItem(item.serial, packSerial);
      attempted.add(item.serial);
      moved++;
      sleep(MOVE_DELAY);
    }
  }

  if (moved > 0) {
    log(`sell: moved ${moved} x '${name}' out of bags so the vendor can see them`);
  }

  return moved;
};
