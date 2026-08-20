import { hex } from '../lib/entity.js';
import { type Picked as Clicked, pickMany } from '../lib/pick.js';
import { MAX_PICKS, OPL_TIMEOUT } from './config.js';

export interface Picked {
  serial: number;
  name: string;

  // How sell-watch counts the pack: a graphic is on the item already, while a name may have to be
  // asked for, and a watch that runs for hours cannot go blind when the tooltips stop answering.
  // The sale still matches by name, because the gump only has names.
  graphic: number;
}

// Keyed by name, because that is what the sale matches on: offering one name twice would trim it to
// KEEP twice over. A pick nothing will name is skipped rather than kept - the click it was on is
// the whole cost, and ending the selection over an item you have never hovered is not what clicking
// it meant.
const byName = (prefix: string) => (picked: Clicked) => {
  if (!picked.name) {
    log(`${prefix}: no name for ${hex(picked.serial)}, the vendor list can only be matched by name`);
    return undefined;
  }

  return picked.name.toLowerCase();
};

export const pickItems = (prefix: string): Picked[] =>
  pickMany({
    prefix,
    prompt: 'target the items you want to sell, ESC when done',
    maxPicks: MAX_PICKS,
    oplTimeout: OPL_TIMEOUT,
    keyOf: byName(prefix),
  }).map(({ serial, name, graphic }) => ({ serial, name, graphic }));
