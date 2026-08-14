import { totalMatching } from '../lib/pack.js';
import { COMBINE_DELAY, ORE_GRAPHICS, ORE_NAME, TARGET_TIMEOUT } from './config.js';

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

// Top level only, unlike oreTotal: these are the piles the combine and the smelt actually work on,
// and both act by serial on loose items in the pack.
export const oresByHue = (): Map<number, Item[]> => {
  const groups = new Map<number, Item[]>();

  for (const item of player.backpack?.contents ?? []) {
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
