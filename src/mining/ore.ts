import { packContents } from '../lib/containers.js';
import { totalMatching } from '../lib/pack.js';
import {
  COMBINE_DELAY,
  ORE_GRAPHICS,
  ORE_NAME,
  ORE_SETTLE_POLL,
  ORE_SETTLE_TIMEOUT,
  TARGET_TIMEOUT,
} from './config.js';

// Named for the item rather than the tile, because vein.ts already owns `isOre` for the ground.
//
// Graphic first and name second, the way isPickaxe does it: names are empty until the client has
// tooltip data for an item, so the graphic is what carries the match most of the time. The name is
// what covers a shard whose ore wears an art the seeded set has never heard of - and since the
// stack-size table those graphics come from is already known to be wrong here, that is not a remote
// possibility. An art learned this way joins the set, so it costs one tooltip and no more.
export const isOrePile = (item: Item): boolean => {
  if (ORE_GRAPHICS.has(item.graphic)) {
    return true;
  }

  if (!ORE_NAME.test(item.name ?? '')) {
    return false;
  }

  ORE_GRAPHICS.add(item.graphic);
  log(`ore: 0x${item.graphic.toString(16)} '${item.name}' is ore too, remembering the art`);

  return true;
};

// Hue-blind on purpose: every ore type counts toward the pack, whatever it smelts into
export const oreTotal = (contents?: Item[]): number => totalMatching(isOrePile, contents);

// The swing's ore turning up in the pack, which is what makes it worth grouping. Reads the total
// rather than the number of piles so a shard that does merge the ore on arrival is satisfied
// immediately instead of waiting out the timeout on every swing.
//
// False is not a failure worth acting on: the caller groups anyway, and a pile that arrived late is
// picked up by the next swing's grouping.
export const waitForOre = (before: number): boolean => {
  for (let waited = 0; waited < ORE_SETTLE_TIMEOUT; waited += ORE_SETTLE_POLL) {
    // Read before the first sleep, unlike convert.ts's waitForChange: that one has just issued a
    // gesture the shard cannot possibly have answered yet, while this is reading a delivery that has
    // usually already happened by the time the journal line announcing it is read.
    if (oreTotal() > before) {
      return true;
    }

    sleep(ORE_SETTLE_POLL);
  }

  return false;
};

// Top level only, unlike oreTotal: these are the piles the combine and the smelt actually work on,
// and both act by serial on loose items in the pack.
export const oresByHue = (): Map<number, Item[]> => {
  const groups = new Map<number, Item[]>();

  for (const item of packContents() ?? []) {
    if (!isOrePile(item)) {
      continue;
    }

    const oreHue = item.hue ?? 0;
    const group = groups.get(oreHue);

    if (group) {
      group.push(item);
    } else {
      groups.set(oreHue, [item]);
    }
  }

  return groups;
};

export const groupOres = (): void => {
  let previousPiles = Infinity;

  // A combine consumes one of the two piles, so rescan the pack between passes
  while (true) {
    const groups = oresByHue();
    const piles = [...groups.values()].reduce((total, items) => total + items.length, 0);

    if (piles >= previousPiles) {
      log(`groupOres: stalled at ${piles} piles`);
      return;
    }
    previousPiles = piles;

    let combined = false;

    for (const [oreHue, items] of groups) {
      if (items.length <= 1) {
        continue;
      }

      const primary = items.reduce((a, b) => ((b.amount ?? 1) > (a.amount ?? 1) ? b : a));
      const dup = items.find((item) => item.serial !== primary.serial);
      if (!dup) {
        continue;
      }

      player.use(dup.serial);
      if (!target.waitTargetEntity(primary.serial, TARGET_TIMEOUT)) {
        log(`groupOres: no target cursor for hue ${oreHue}`);
        target.cancel();
      }

      combined = true;
      sleep(COMBINE_DELAY);
    }

    if (!combined) {
      return;
    }
  }
};
