import { collectIn, isContainer } from '../lib/containers.js';
import { MAX_HOIST_PASSES, MOVE_DELAY, OPEN_DELAY, OPL_TIMEOUT } from './config.js';

// Serials come back as signed 32-bit ints, so a plain toString(16) yields "0x-3266af2f"
export const hex = (value: number): string => `0x${(value >>> 0).toString(16)}`;

// An item the client already has tooltip data for names itself, and asking again costs a round trip
// per item. Only the nameless ones are worth OPL_TIMEOUT.
const nameOf = (item: Item): string => {
  const known = (item.name ?? '').trim();

  return known || (client.queryItemOPL(item.serial, OPL_TIMEOUT)?.name ?? '').trim();
};

// Everything under the pack except its top level - those are already where the vendor can see them,
// and skipping them before nameOf keeps the tooltip queries down to the items that might move
export const nestedMatches = (name: string): Item[] => {
  const contents = player.backpack?.contents;
  const topLevel = new Set((contents ?? []).map((item) => item.serial));
  const wanted = name.toLowerCase();

  return collectIn(
    contents,
    (item) => !topLevel.has(item.serial) && nameOf(item).toLowerCase() === wanted,
  );
};

// The other half of the same split: what a sell gump would list if it were reopened. A vendor is
// shown the top level of the pack and nothing below it, so this is the whole of what is still on
// offer - which is how the sale knows whether another pass has anything to find.
export const looseMatches = (name: string): Item[] => {
  const wanted = name.toLowerCase();

  return (player.backpack?.contents ?? []).filter((item) => nameOf(item).toLowerCase() === wanted);
};

// Contents stay undefined until a container has been opened, so an unopened bag hides everything in
// it and nestedMatches reports an empty pack quite honestly. Only containers not already opened, so
// each pass reaches one level deeper than the last instead of double-clicking the same bags again.
// Returns whether anything new was opened, which is half of what says the run is finished.
const openUnopened = (opened: Set<number>): boolean => {
  const containers = collectIn(player.backpack?.contents, isContainer).filter(
    (container) => !opened.has(container.serial),
  );

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
