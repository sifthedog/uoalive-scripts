import { namedExactly, openSellGump, waitForSale } from '../lib/vendor.js';
import {
  GUMP_TIMEOUT,
  KEEP,
  MAX_PASSES,
  SALE_POLL,
  SALE_TIMEOUT,
  SELL_DELAY,
} from './config.js';
import { looseMatches } from './hoist.js';
import { withKeepBack } from './offer.js';

const amountOf = (items: Item[]): number =>
  items.reduce((sum, item) => sum + (item.amount ?? 1), 0);

// Returns how many units the vendor took, across every pass.
//
// The gump is reopened only when the pack still holds something sellable, because reopening it
// means saying 'vendor sell' again. That used to happen on every run: the loop reopened the gump
// to see what was left and, with nothing left, logged 'no X on offer' and stopped - a whole extra
// round trip to learn the sale had worked. Watching the goods leave the pack answers the same
// question without speaking, so a run that clears the pack in one pass now says it once.
//
// A sell gump lists a limited number of entries, so the reopen still earns its keep for a pile too
// big to list at once - that is the case where matches genuinely remain.
export const sellAll = (name: string): number => {
  const nameMatches = namedExactly(name);
  let sold = 0;

  for (let pass = 0; pass < MAX_PASSES; pass++) {
    const data = openSellGump('sell', GUMP_TIMEOUT);
    if (!data) {
      break;
    }

    const matches = data.items.filter(nameMatches);

    if (matches.length === 0) {
      const names = [...new Set(data.items.map((item) => item.name))];
      log(`sell: no '${name}' on offer. Vendor listed: ${names.join(', ')}`);
      break;
    }

    const toSell = withKeepBack(matches);
    if (toSell.length === 0) {
      log(`sell: ${amountOf(looseMatches(name))} left, keeping them back`);
      break;
    }

    const offered = toSell.reduce((sum, item) => sum + item.amount, 0);
    client.sendSellRequest(data.vendor, toSell);

    const taken = waitForSale(toSell, SALE_TIMEOUT, SALE_POLL);
    sold += taken;
    log(`sell: pass ${pass + 1}, offered ${offered} x ${name}, vendor took ${taken}`);

    // A vendor that refuses says nothing and leaves the goods where they are. A partial take - one
    // out of gold, say - stops on the next pass instead, having taken nothing that time.
    if (taken === 0) {
      log(`sell: stalled with ${offered} left, vendor is not taking them`);
      break;
    }

    const left = amountOf(looseMatches(name));
    if (left <= KEEP) {
      break;
    }

    sleep(SELL_DELAY);
  }

  return sold;
};
