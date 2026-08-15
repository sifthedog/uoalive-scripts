import {
  namedExactly,
  openSellGump,
  totalOf,
  waitForSale,
  withKeepBack,
  type VendorEntry,
} from '../lib/vendor.js';
import { isBox } from './boxes.js';
import {
  BOX_NAME,
  GUMP_TIMEOUT,
  KEEP,
  MAX_SELL_PASSES,
  SALE_POLL,
  SALE_TIMEOUT,
  SELL_DELAY,
} from './config.js';

const isBoxEntry = namedExactly(BOX_NAME);

export type Offer =
  | { kind: 'offer'; entries: VendorEntry[] }
  | { kind: 'none'; listed: string[] }
  | { kind: 'mismatch'; named: number };

// The safety-critical decision. With every box confirmed empty a name match is enough; with one
// skipped, only the boxes watched going empty may be offered - and if none of the gump's serials
// line up with those, selling by name would hand over the box that would not open, contents and
// all. That case stops.
export const pickOffer = (
  items: VendorEntry[],
  emptied: Set<number>,
  skipped: number,
): Offer => {
  const named = items.filter(isBoxEntry);

  if (named.length === 0) {
    return { kind: 'none', listed: [...new Set(items.map((item) => item.name))] };
  }

  if (skipped === 0) {
    return { kind: 'offer', entries: named };
  }

  const bySerial = named.filter((entry) => emptied.has(entry.serial));

  return bySerial.length === 0
    ? { kind: 'mismatch', named: named.length }
    : { kind: 'offer', entries: bySerial };
};

// What a reopened sell gump could still list, on the same terms pickOffer would offer it. A box that
// would not open is therefore not a reason to go round again - it is never going to be sold.
const stillSellable = (emptied: Set<number>, skipped: number): number =>
  (player.backpack?.contents ?? []).filter(
    (item) => isBox(item) && (skipped === 0 || emptied.has(item.serial)),
  ).length;

// Returns how many boxes the vendor took across every pass
export const sellBoxes = (emptied: Set<number>, skipped: number): number => {
  let sold = 0;

  for (let pass = 0; pass < MAX_SELL_PASSES; pass++) {
    const data = openSellGump('boxes', GUMP_TIMEOUT);
    if (!data) {
      break;
    }

    const offer = pickOffer(data.items, emptied, skipped);

    if (offer.kind === 'none') {
      log(`boxes: no '${BOX_NAME}' on offer. Vendor listed: ${offer.listed.join(', ')}`);
      break;
    }

    if (offer.kind === 'mismatch') {
      log(
        `boxes: the vendor lists ${offer.named} x ${BOX_NAME} but none of their serials match the ` +
          'boxes this run emptied, so selling by name could hand over a box that never opened. ' +
          'Stopping - empty the skipped boxes by hand and run again.',
      );
      break;
    }

    const toSell = withKeepBack(offer.entries, KEEP);
    if (toSell.length === 0) {
      log(`boxes: ${totalOf(offer.entries)} left, keeping them back`);
      break;
    }

    const offered = toSell.reduce((sum, entry) => sum + entry.amount, 0);
    client.sendSellRequest(data.vendor, toSell);

    // The boxes leaving the pack is the proof, not sendSellRequest's return: that says the packet
    // went out, and a vendor refusing does so in silence
    const taken = waitForSale(toSell, SALE_TIMEOUT, SALE_POLL);
    sold += taken;
    log(`boxes: sell pass ${pass + 1}, offered ${offered} x ${BOX_NAME}, vendor took ${taken}`);

    if (taken === 0) {
      log(`boxes: stalled with ${offered} left, vendor is not taking them`);
      break;
    }

    // Reopening means saying 'vendor sell' again, so it is only worth it when something is left for
    // the gump to list.
    if (stillSellable(emptied, skipped) <= KEEP) {
      break;
    }

    sleep(SELL_DELAY);
  }

  return sold;
};
