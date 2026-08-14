import { totalMatching } from '../lib/pack.js';
import { INGOT_GRAPHICS, INGOT_HUE } from './config.js';

export const isIngot = (item: Item): boolean =>
  INGOT_GRAPHICS.has(item.graphic) && (item.hue ?? 0) === INGOT_HUE;

export const ingotTotal = (contents?: Item[]): number => totalMatching(isIngot, contents);
