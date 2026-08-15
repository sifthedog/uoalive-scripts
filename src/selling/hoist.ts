import { collectIn, isContainer, packContents } from '../lib/containers.js';
import { hex } from '../lib/entity.js';
import { MAX_HOIST_PASSES, MOVE_DELAY, OPEN_DELAY, OPL_TIMEOUT } from './config.js';

export { hex };

// Answers already had, keyed by serial. The pack is walked several times over a run - once per
// hoist pass, twice per sell pass - and without this every walk pays OPL_TIMEOUT again for every
// item the client has no name for. A name does not change, and a serial survives a moveItem, so
// what is cached here stays true for as long as the run does.
const names = new Map<number, string>();

// One unanswered tooltip is an item; three in a row is the shard. Asked once and then left alone,
// the way peek.ts stops asking for a "contents" line - otherwise a pack of thirty un-hovered items
// costs a minute of nothing, per walk.
let oplAnswersNames = true;
let misses = 0;

// An item the client already has tooltip data for names itself, and asking again costs a round trip
// per item. Only the nameless ones are worth OPL_TIMEOUT.
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

  const fromTooltip = (client.queryItemOPL(item.serial, OPL_TIMEOUT)?.name ?? '').trim();
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

// What a sell gump would list if it were reopened, which is how the sale knows whether another pass
// has anything to find. Every depth, because this shard's vendors sell out of a bag as readily as
// off the top of the pack - reading the top level alone stopped the run with the bags still full.
//
// On a shard whose vendors are blind to sub-containers this is a lower bound on the wrong side: it
// costs one more gump, which says 'no X on offer' and stops. HOIST_FROM_BAGS is what to set there.
export const sellableMatches = (name: string): Item[] => {
  const wanted = name.toLowerCase();

  return collectIn(packContents(), (item) => nameOf(item).toLowerCase() === wanted);
};

const CONTAINER_WORDS = /\b(bag|pouch|box|chest|crate|basket|backpack)\b/i;

// Serials already named, so a bag is mentioned once rather than once per pass
const unlisted = new Set<number>();

// An unopened container is known by its graphic and nothing else, so a shard with container art
// that CONTAINER_GRAPHICS has never heard of would hide whatever is inside one - silently, which is
// the worst way to lose an item. This costs no tooltip query: it reads only the name the client has
// already sent, and skips anything still nameless. What it prints is the graphic to add to the list
// in lib/containers.ts.
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
// it and nestedMatches reports an empty pack quite honestly. Only containers not already opened, so
// each pass reaches one level deeper than the last instead of double-clicking the same bags again.
// Returns whether anything new was opened, which is half of what says the run is finished.
//
// One walk of the pack serves both halves: what to open, and what only looks like it.
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

// A vendor's sell gump only lists the top level of your pack, so anything in a bag inside it is
// invisible to the sale until it is moved out. Returns how many were shifted.
//
// Moves are asynchronous, so the pack is rescanned between passes rather than trusting moveItem.
// What stops the loop is a pass with nothing new to move and nothing new opened: counting matches
// per pass would not do, because opening a deeper bag legitimately makes the number go up.
export const hoistToPack = (name: string): number => {
  const packSerial = player.backpack?.serial;

  if (!packSerial) {
    log('sell: no backpack to move anything into');
    return 0;
  }

  const opened = new Set<number>();
  // Keyed by serial so a move that does not land is never retried into an infinite loop, and a
  // stack that merged into another on arrival is not counted twice
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
