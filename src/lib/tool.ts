import { contentsOf, findIn, openContainers, packContents } from './containers.js';
import { hex } from './entity.js';
import { untilLanded } from './retry.js';

// Finding a tool, knowing when it has broken, and getting a replacement onto the right hand layer.

// One level down included: listing only the top level read as an empty pack when the spares were in
// a bag, which is exactly the case this message exists for.
const describeContents = (contents: Item[] | undefined): string =>
  (contents ?? [])
    .map((item) => {
      const sub = contentsOf(item);

      return sub?.length ? `${hex(item.graphic)}[${describeContents(sub)}]` : hex(item.graphic);
    })
    .join(', ');

export interface Tool {
  is: (item: Item) => boolean;
  remember: (item: Item | undefined) => void;

  // Whatever the action is swung with, so a worn-out one can be spotted by it no longer resolving
  serial: () => number | undefined;

  // Searches the pack, opening containers if the first pass misses, and returns what it found
  // without equipping it - for a tool that is used rather than worn.
  find: () => Item | undefined;

  equip: () => boolean;
}

export const createTool = (options: {
  // Names the tool in the log lines, and names the function in the ones about giving up
  label: string;

  name: string;
  graphics?: Set<number>;
  spareBagSerial?: number;

  // Which layer the tool ends up on. An axe is two-handed and a hatchet one-handed, so lumberjacking
  // reads `twoHanded ?? oneHanded`; a pickaxe is only ever one-handed.
  held: () => Item | undefined;

  equip: { attempts: number; timeoutMs: number; pollMs: number };
}): Tool => {
  let learned: number | undefined;
  let spareBagSerial = options.spareBagSerial;
  let reportedEmpty = false;

  // Names are empty until the client has tooltip data, so prefer the graphic once we know it
  const is = (item: Item): boolean =>
    (learned !== undefined && item.graphic === learned) ||
    (options.graphics?.has(item.graphic) ?? false) ||
    (item.name ?? '').toLowerCase().includes(options.name);

  const remember = (item: Item | undefined): void => {
    if (item && learned === undefined) {
      learned = item.graphic;
      log(`${options.label}: graphic is ${hex(item.graphic)}`);
    }
  };

  const reportEmptyPack = (): void => {
    if (reportedEmpty) {
      return;
    }

    log(`${options.label}: none found. Pack holds: ${describeContents(packContents())}`);
    log(`${options.label}: if the spares are in a bag inside a bag, pin it as SPARE_BAG_SERIAL`);
    reportedEmpty = true;
  };

  const find = (): Item | undefined => {
    let found = findIn(packContents(), is);

    if (!found && openContainers(spareBagSerial)) {
      found = findIn(packContents(), is);
    }

    if (!found) {
      reportEmptyPack();
      return undefined;
    }

    reportedEmpty = false;
    remember(found);

    // Remember the bag it came from so the next break reopens only that one
    if (found.container && found.container !== player.backpack?.serial) {
      spareBagSerial = found.container;
    }

    return found;
  };

  // A broken tool can linger in equippedItems, and `is` would happily match it by graphic.
  // A destroyed serial stops resolving, so ask the world rather than the layer.
  const stillHolding = (): boolean => {
    const item = options.held();

    return !!item && is(item) && client.findObject(item.serial) !== undefined;
  };

  return {
    is,
    remember,
    find,
    serial: () => options.held()?.serial,

    equip: () => {
      if (stillHolding()) {
        return true;
      }

      const found = find();

      if (!found) {
        client.headMsg(`No ${options.name}!`, player, 33);
        return false;
      }

      // A cursor left open by the swing that broke the tool would swallow the equip
      target.cancel();

      // Asynchronous - do not act until it has landed on a hand layer
      return untilLanded({
        label: `equip ${options.name}`,
        attempts: options.equip.attempts,
        timeoutMs: options.equip.timeoutMs,
        pollMs: options.equip.pollMs,
        act: () => player.equip(found.serial),
        landed: () => options.held()?.serial === found.serial,
      });
    },
  };
};
