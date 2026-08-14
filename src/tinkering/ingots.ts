import { INGOT_GRAPHICS, INGOT_HUE } from './config.js';

export const isIngot = (item: Item): boolean =>
  INGOT_GRAPHICS.has(item.graphic) && (item.hue ?? 0) === INGOT_HUE;

// Recursing through this rather than through ingotTotal itself: a plain item has no `contents`,
// and passing undefined back into a defaulted parameter would restart at the backpack forever.
const totalIn = (contents: Item[] | undefined): number =>
  (contents ?? []).reduce(
    (total, item) => total + (isIngot(item) ? item.amount ?? 1 : 0) + totalIn(item.contents),
    0,
  );

// The shard spends resources out of sub-containers too, so count the way it spends. This is a
// lower bound either way: an unopened container reports `contents: undefined`.
export const ingotTotal = (contents: Item[] | undefined = player.backpack?.contents): number =>
  totalIn(contents);
