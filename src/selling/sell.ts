import { namedAnyOf, openSellGump, waitForSaleBySerial } from '../lib/vendor.js';
import {
  GUMP_TIMEOUT,
  KEEP,
  MAX_PASSES,
  SALE_POLL,
  SALE_TIMEOUT,
  SELL_DELAY,
} from './config.js';
import { sellableMatches } from './hoist.js';
import { withKeepBack } from './offer.js';

export type Counted = Map<string, number>;

export interface Sold {
  // What the vendor took, all names together. The authoritative number: it comes from watching the
  // goods leave the pack, which is the only proof a sale landed.
  total: number;

  // The same figure split by name, for the report. Keyed by the name as it was picked.
  byName: Counted;
}

const amountOf = (items: Item[]): number =>
  items.reduce((sum, item) => sum + (item.amount ?? 1), 0);

// `12 x 'iron ingot', 3 x 'scimitar'`. Names nothing it has none of, so a run that sold one of the
// three items it was pointed at does not report the other two as zeroes.
export const describeCounts = (counts: Counted): string =>
  [...counts]
    .filter(([, amount]) => amount > 0)
    .map(([name, amount]) => `${amount} x '${name}'`)
    .join(', ');

const totalOfCounts = (counts: Counted): number =>
  [...counts.values()].reduce((sum, amount) => sum + amount, 0);

// What the pack still holds of each name, at any depth, which is what another gump could list
const stillHeld = (names: string[]): Counted =>
  new Map(names.map((name) => [name, amountOf(sellableMatches(name))]));

// Returns what the vendor took, across every pass.
//
// Every name goes through the one gump. Reopening it means saying 'vendor sell' again, so selling
// three items with a gump each would undo the saving the single-item version was built around - and
// the gump the vendor already has open lists all three anyway.
//
// The gump is reopened only when the pack still holds something sellable, because that is the only
// thing another pass could act on. That used to happen on every run: the loop reopened the gump to
// see what was left and, with nothing left, logged 'no X on offer' and stopped - a whole extra round
// trip to learn the sale had worked. Watching the goods leave the pack answers the same question
// without speaking, so a run that clears the pack in one pass now says it once.
//
// A sell gump lists a limited number of entries, so the reopen still earns its keep for a pile too
// big to list at once - that is the case where matches genuinely remain.
export const sellAll = (names: string[]): Sold => {
  const wanted = namedAnyOf(names);
  const byName: Counted = new Map(names.map((name) => [name, 0]));

  // The gump's spelling of a name need not be the one that was picked, and the report is keyed by
  // what was picked - so the two are tied together here, once, rather than compared stack by stack
  const asPicked = new Map(names.map((name) => [name.toLowerCase(), name]));
  const nameOf = (entry: { name?: string }): string =>
    asPicked.get((entry.name ?? '').toLowerCase()) ?? (entry.name ?? '');

  let total = 0;

  for (let pass = 0; pass < MAX_PASSES; pass++) {
    const data = openSellGump('sell', GUMP_TIMEOUT);
    if (!data) {
      break;
    }

    const matches = data.items.filter(wanted);

    if (matches.length === 0) {
      const listed = [...new Set(data.items.map((item) => item.name))];
      log(`sell: nothing of ${names.join(', ')} on offer. Vendor listed: ${listed.join(', ')}`);
      break;
    }

    const toSell = withKeepBack(matches);
    if (toSell.length === 0) {
      log(`sell: ${describeCounts(stillHeld(names))} left, keeping them back`);
      break;
    }

    const named = new Map(matches.map((entry) => [entry.serial, nameOf(entry)]));
    const offered: Counted = new Map();

    for (const item of toSell) {
      const name = named.get(item.serial) ?? '';
      offered.set(name, (offered.get(name) ?? 0) + item.amount);
    }

    client.sendSellRequest(data.vendor, toSell);

    const taken = waitForSaleBySerial(toSell, SALE_TIMEOUT, SALE_POLL);
    const tookByName: Counted = new Map();

    for (const [serial, amount] of taken) {
      const name = named.get(serial) ?? '';
      tookByName.set(name, (tookByName.get(name) ?? 0) + amount);
      byName.set(name, (byName.get(name) ?? 0) + amount);
    }

    const took = totalOfCounts(tookByName);
    total += took;

    log(
      `sell: pass ${pass + 1}, offered ${describeCounts(offered)}, vendor took ${describeCounts(tookByName) || 'nothing'}`,
    );

    // A vendor that refuses says nothing and leaves the goods where they are. A partial take - one
    // out of gold, say - stops on the next pass instead, having taken nothing that time.
    if (took === 0) {
      log(`sell: stalled with ${totalOfCounts(offered)} left, vendor is not taking them`);
      break;
    }

    // Anything over the keep-back is what another gump could list, whichever name it belongs to
    if ([...stillHeld(names).values()].every((held) => held <= KEEP)) {
      break;
    }

    sleep(SELL_DELAY);
  }

  return { total, byName };
};
